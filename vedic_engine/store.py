"""Saved kundlis – a small SQLite store (file: data/kundlis.db next to the package).

A kundli record keeps only the birth data and settings; charts are always recomputed, so a
saved kundli benefits from engine fixes automatically.
"""
from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import uuid
from datetime import datetime, timezone

DB_PATH = pathlib.Path(os.environ.get("JYOTISH_DB", pathlib.Path(__file__).resolve().parent.parent / "data" / "kundlis.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS kundlis (
  id TEXT PRIMARY KEY,
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
"""
FIELDS = ("name", "gender", "datetime_local", "tz", "lat", "lon", "place", "settings", "notes", "tags")


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def _row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["settings"] = json.loads(d.get("settings") or "{}")
    return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_kundlis(q: str = "", limit: int = 200) -> list[dict]:
    with _conn() as c:
        if q:
            like = f"%{q.lower()}%"
            rows = c.execute("SELECT * FROM kundlis WHERE lower(name) LIKE ? OR lower(place) LIKE ? OR lower(tags) LIKE ? "
                             "ORDER BY updated_at DESC LIMIT ?", (like, like, like, limit)).fetchall()
        else:
            rows = c.execute("SELECT * FROM kundlis ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
    return [_row(r) for r in rows]


def get(kid: str) -> dict | None:
    with _conn() as c:
        r = c.execute("SELECT * FROM kundlis WHERE id = ?", (kid,)).fetchone()
    return _row(r) if r else None


def create(data: dict) -> dict:
    kid = data.get("id") or uuid.uuid4().hex[:12]
    now = _now()
    vals = {f: data.get(f) for f in FIELDS}
    vals["settings"] = json.dumps(vals.get("settings") or {})
    with _conn() as c:
        c.execute(f"INSERT INTO kundlis (id, {', '.join(FIELDS)}, created_at, updated_at) VALUES (?, {', '.join('?' * len(FIELDS))}, ?, ?)",
                  (kid, *vals.values(), data.get("created_at") or now, now))
    return get(kid)


def update(kid: str, data: dict) -> dict | None:
    if not get(kid):
        return None
    vals = {f: data[f] for f in FIELDS if f in data}
    if "settings" in vals:
        vals["settings"] = json.dumps(vals["settings"] or {})
    if vals:
        with _conn() as c:
            c.execute(f"UPDATE kundlis SET {', '.join(f'{k} = ?' for k in vals)}, updated_at = ? WHERE id = ?",
                      (*vals.values(), _now(), kid))
    return get(kid)


def delete(kid: str) -> bool:
    with _conn() as c:
        return c.execute("DELETE FROM kundlis WHERE id = ?", (kid,)).rowcount > 0


def import_many(items: list[dict]) -> int:
    n = 0
    for it in items:
        if it.get("id") and get(it["id"]):
            update(it["id"], it)
        else:
            create(it)
        n += 1
    return n
