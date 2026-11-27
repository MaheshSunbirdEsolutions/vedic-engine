"""Saved kundlis and user profiles – Supabase Postgres (via PostgREST) or local SQLite.

When SUPABASE_URL is set, reads and writes target Supabase REST APIs using the
caller's Clerk JWT (`apikey` + `Authorization: Bearer <token>`) so Postgres RLS
enforces user isolation on every query. Otherwise falls back to local SQLite
(`data/kundlis.db`), also scoped by `user_id`.

A kundli record keeps only birth data and settings; charts are always recomputed.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException


def _default_db_path() -> pathlib.Path:
    if os.environ.get("JYOTISH_DB"):
        return pathlib.Path(os.environ["JYOTISH_DB"])
    if os.environ.get("VERCEL"):
        return pathlib.Path(tempfile.gettempdir()) / "jyotish" / "kundlis.db"
    return pathlib.Path(__file__).resolve().parent.parent / "data" / "kundlis.db"


DB_PATH = _default_db_path()

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
  id TEXT PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  preferred_lang TEXT NOT NULL DEFAULT 'en',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kundlis (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL DEFAULT 'local',
  name TEXT NOT NULL,
  gender TEXT,
  datetime_local TEXT NOT NULL,
  tz TEXT NOT NULL,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  place TEXT,
  settings TEXT NOT NULL DEFAULT '{}',
  notes TEXT DEFAULT '',
  tags TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kundlis_name ON kundlis(name);
CREATE INDEX IF NOT EXISTS idx_kundlis_user ON kundlis(user_id, updated_at DESC);
"""
FIELDS = ("name", "gender", "datetime_local", "tz", "lat", "lon", "place", "settings", "notes", "tags")
PROFILE_FIELDS = ("email", "full_name", "preferred_lang")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _is_uuid(val: Any) -> bool:
    if not isinstance(val, str):
        return False
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False


# ---------------- Supabase PostgREST helpers ----------------

def _supabase_url() -> str:
    val = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    return re.sub(r"/rest/v1$", "", val)


def use_supabase() -> bool:
    return bool(_supabase_url())


def _publishable_key() -> str:
    return (
        os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or os.environ.get("SUPABASE_ANON_KEY", "").strip()
    )


def _secret_key() -> str:
    return (
        os.environ.get("SUPABASE_SECRET_KEY", "").strip()
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )


def _sb_headers(token: str | None, *, admin: bool = False, prefer: str | None = None) -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if admin:
        secret = _secret_key()
        if not secret:
            raise HTTPException(503, "SUPABASE_SECRET_KEY / SUPABASE_SERVICE_ROLE_KEY is not configured.")
        headers["apikey"] = secret
        # Legacy JWT service_role keys go in Authorization too; new sb_secret_ keys go only in apikey.
        if secret.startswith("eyJ"):
            headers["Authorization"] = f"Bearer {secret}"
    else:
        pub = _publishable_key()
        if not pub:
            raise HTTPException(503, "SUPABASE_PUBLISHABLE_KEY / SUPABASE_ANON_KEY is not configured.")
        if not token:
            raise HTTPException(401, "Missing user token for Supabase RLS request.")
        headers["apikey"] = pub
        headers["Authorization"] = f"Bearer {token}"
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _sb_request(
    method: str,
    table: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    token: str | None = None,
    admin: bool = False,
    prefer: str | None = None,
) -> Any:
    url = f"{_supabase_url()}/rest/v1/{table}"
    headers = _sb_headers(token, admin=admin, prefer=prefer)
    try:
        resp = httpx.request(method, url, params=params, json=json_body, headers=headers, timeout=15.0)
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Cannot reach Supabase: {exc}") from exc
    if resp.status_code >= 400:
        detail = resp.text[:300]
        try:
            err = resp.json()
            detail = err.get("message") or err.get("hint") or detail
        except ValueError:
            pass
        code = resp.status_code if resp.status_code in (400, 401, 403, 404, 409) else 502
        raise HTTPException(code, f"Supabase error: {detail}")
    return resp.json() if resp.content else None


def _norm_kundli(row: dict) -> dict:
    out = dict(row)
    s = out.get("settings")
    if isinstance(s, str):
        out["settings"] = json.loads(s or "{}")
    elif s is None:
        out["settings"] = {}
    return out


# ---------------- SQLite helpers ----------------

def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    # Migrate existing pre-auth kundlis.db smoothly before creating user index.
    cols = {r[1] for r in c.execute("PRAGMA table_info(kundlis)").fetchall()}
    if cols and "user_id" not in cols:
        c.execute("ALTER TABLE kundlis ADD COLUMN user_id TEXT NOT NULL DEFAULT 'local'")
    c.executescript(SCHEMA)
    return c


def _row(r: sqlite3.Row) -> dict:
    return _norm_kundli(dict(r))


# ---------------- Kundlis CRUD ----------------

def list_kundlis(q: str = "", limit: int = 200, *, user_id: str = "local", token: str | None = None) -> list[dict]:
    if use_supabase():
        params: dict[str, Any] = {
            "select": "*",
            "user_id": f"eq.{user_id}",
            "order": "updated_at.desc",
            "limit": limit,
        }
        safe_q = re.sub(r"[(),*]", " ", q).strip()
        if safe_q:
            pat = f"*{safe_q}*"
            params["or"] = f"(name.ilike.{pat},place.ilike.{pat},tags.ilike.{pat})"
        rows = _sb_request("GET", "kundlis", params=params, token=token) or []
        return [_norm_kundli(r) for r in rows]

    with _conn() as c:
        if q:
            like = f"%{q.lower()}%"
            rows = c.execute(
                "SELECT * FROM kundlis WHERE user_id = ? AND (lower(name) LIKE ? OR lower(place) LIKE ? OR lower(tags) LIKE ?) "
                "ORDER BY updated_at DESC LIMIT ?",
                (user_id, like, like, like, limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM kundlis WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
    return [_row(r) for r in rows]


def get(kid: str, *, user_id: str = "local", token: str | None = None) -> dict | None:
    if use_supabase():
        if not _is_uuid(kid):
            return None
        rows = _sb_request(
            "GET",
            "kundlis",
            params={"select": "*", "id": f"eq.{kid}", "user_id": f"eq.{user_id}", "limit": 1},
            token=token,
        ) or []
        return _norm_kundli(rows[0]) if rows else None

    with _conn() as c:
        r = c.execute("SELECT * FROM kundlis WHERE id = ? AND user_id = ?", (kid, user_id)).fetchone()
    return _row(r) if r else None


def create(data: dict, *, user_id: str = "local", token: str | None = None) -> dict:
    if use_supabase():
        payload: dict[str, Any] = {f: data.get(f) for f in FIELDS}
        payload["user_id"] = user_id
        payload["settings"] = payload.get("settings") or {}
        if _is_uuid(data.get("id")):
            payload["id"] = data["id"]
        rows = _sb_request("POST", "kundlis", json_body=payload, token=token, prefer="return=representation")
        return _norm_kundli(rows[0])

    kid = data.get("id") or uuid.uuid4().hex[:12]
    now = _now()
    vals = {f: data.get(f) for f in FIELDS}
    vals["settings"] = json.dumps(vals.get("settings") or {})
    with _conn() as c:
        c.execute(
            f"INSERT INTO kundlis (id, user_id, {', '.join(FIELDS)}, created_at, updated_at) "
            f"VALUES (?, ?, {', '.join('?' * len(FIELDS))}, ?, ?)",
            (kid, user_id, *vals.values(), data.get("created_at") or now, now),
        )
    return get(kid, user_id=user_id)


def update(kid: str, data: dict, *, user_id: str = "local", token: str | None = None) -> dict | None:
    if use_supabase():
        if not _is_uuid(kid):
            return None
        vals = {f: data[f] for f in FIELDS if f in data}
        vals["updated_at"] = _now()
        rows = _sb_request(
            "PATCH",
            "kundlis",
            params={"id": f"eq.{kid}", "user_id": f"eq.{user_id}"},
            json_body=vals,
            token=token,
            prefer="return=representation",
        ) or []
        return _norm_kundli(rows[0]) if rows else None

    if not get(kid, user_id=user_id):
        return None
    vals = {f: data[f] for f in FIELDS if f in data}
    if "settings" in vals:
        vals["settings"] = json.dumps(vals["settings"] or {})
    if vals:
        with _conn() as c:
            c.execute(
                f"UPDATE kundlis SET {', '.join(f'{k} = ?' for k in vals)}, updated_at = ? WHERE id = ? AND user_id = ?",
                (*vals.values(), _now(), kid, user_id),
            )
    return get(kid, user_id=user_id)


def delete(kid: str, *, user_id: str = "local", token: str | None = None) -> bool:
    if use_supabase():
        if not _is_uuid(kid):
            return False
        rows = _sb_request(
            "DELETE",
            "kundlis",
            params={"id": f"eq.{kid}", "user_id": f"eq.{user_id}"},
            token=token,
            prefer="return=representation",
        ) or []
        return len(rows) > 0

    with _conn() as c:
        return c.execute("DELETE FROM kundlis WHERE id = ? AND user_id = ?", (kid, user_id)).rowcount > 0


def import_many(items: list[dict], *, user_id: str = "local", token: str | None = None) -> int:
    n = 0
    for it in items:
        kid = it.get("id")
        if kid and get(kid, user_id=user_id, token=token):
            update(kid, it, user_id=user_id, token=token)
        else:
            clean = dict(it)
            if use_supabase() and not _is_uuid(clean.get("id")):
                clean.pop("id", None)
            create(clean, user_id=user_id, token=token)
        n += 1
    return n


# ---------------- User profiles ----------------

def get_profile(user_id: str, *, token: str | None = None) -> dict | None:
    if use_supabase():
        rows = _sb_request(
            "GET",
            "profiles",
            params={"select": "*", "id": f"eq.{user_id}", "limit": 1},
            token=token,
        ) or []
        return rows[0] if rows else None

    with _conn() as c:
        r = c.execute("SELECT * FROM profiles WHERE id = ?", (user_id,)).fetchone()
    return dict(r) if r else None


def ensure_profile(
    user_id: str,
    *,
    email: str | None = None,
    full_name: str | None = None,
    token: str | None = None,
) -> dict:
    """Register the user's profile row if missing (just-in-time registration)."""
    existing = get_profile(user_id, token=token)
    if existing:
        return existing
    if use_supabase():
        payload = {"id": user_id, "email": email, "full_name": full_name, "preferred_lang": "en"}
        rows = _sb_request(
            "POST",
            "profiles",
            params={"on_conflict": "id"},
            json_body=payload,
            token=token,
            prefer="resolution=ignore-duplicates,return=representation",
        ) or []
        return rows[0] if rows else (get_profile(user_id, token=token) or payload)

    now = _now()
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO profiles (id, email, full_name, preferred_lang, created_at, updated_at) "
            "VALUES (?, ?, ?, 'en', ?, ?)",
            (user_id, email, full_name, now, now),
        )
    return get_profile(user_id)  # type: ignore[return-value]


def update_profile(user_id: str, data: dict, *, token: str | None = None) -> dict:
    ensure_profile(user_id, token=token)
    vals = {k: v for k, v in data.items() if k in PROFILE_FIELDS and v is not None}
    if not vals:
        return get_profile(user_id, token=token)  # type: ignore[return-value]
    if use_supabase():
        vals["updated_at"] = _now()
        rows = _sb_request(
            "PATCH",
            "profiles",
            params={"id": f"eq.{user_id}"},
            json_body=vals,
            token=token,
            prefer="return=representation",
        ) or []
        return rows[0]

    with _conn() as c:
        c.execute(
            f"UPDATE profiles SET {', '.join(f'{k} = ?' for k in vals)}, updated_at = ? WHERE id = ?",
            (*vals.values(), _now(), user_id),
        )
    return get_profile(user_id)  # type: ignore[return-value]


def upsert_profile_admin(user_id: str, *, email: str | None = None, full_name: str | None = None) -> dict:
    """Admin-scoped upsert used by Clerk user.created / user.updated webhooks."""
    now = _now()
    if use_supabase():
        payload = {"id": user_id, "email": email, "full_name": full_name, "updated_at": now}
        rows = _sb_request(
            "POST",
            "profiles",
            params={"on_conflict": "id"},
            json_body=payload,
            admin=True,
            prefer="resolution=merge-duplicates,return=representation",
        ) or []
        return rows[0] if rows else payload

    with _conn() as c:
        c.execute(
            "INSERT INTO profiles (id, email, full_name, preferred_lang, created_at, updated_at) "
            "VALUES (?, ?, ?, 'en', ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET email = excluded.email, full_name = excluded.full_name, updated_at = excluded.updated_at",
            (user_id, email, full_name, now, now),
        )
    return get_profile(user_id)  # type: ignore[return-value]


def delete_user_data_admin(user_id: str) -> None:
    """Admin-scoped cascade cleanup used by Clerk user.deleted webhook."""
    if use_supabase():
        _sb_request("DELETE", "kundlis", params={"user_id": f"eq.{user_id}"}, admin=True)
        _sb_request("DELETE", "profiles", params={"id": f"eq.{user_id}"}, admin=True)
        return

    with _conn() as c:
        c.execute("DELETE FROM kundlis WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM profiles WHERE id = ?", (user_id,))
