"""Backend-only tests for Clerk JWT auth, user profiles, RLS headers, and webhooks."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from vedic_engine import auth, store
from vedic_engine.api import app

BIRTH = {
    "name": "Auth Test",
    "datetime_local": "1990-05-14T06:30:00",
    "tz": "Asia/Kolkata",
    "lat": 28.6139,
    "lon": 77.2090,
    "place": "Delhi",
}


@pytest.fixture(scope="module")
def rsa_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _make_token(private_key, sub: str = "user_alice", issuer: str = "https://clerk.example.dev", exp_delta_s: int = 300):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iss": issuer,
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=exp_delta_s)).timestamp()),
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "test-kid"})


@pytest.fixture()
def clerk_auth(monkeypatch, tmp_path, rsa_keys):
    private_key, public_key = rsa_keys
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "auth_test.db")
    monkeypatch.setenv("CLERK_ISSUER", "https://clerk.example.dev")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://clerk.example.dev/.well-known/jwks.json")

    fake_client = SimpleNamespace(get_signing_key_from_jwt=lambda _tok: SimpleNamespace(key=public_key))
    monkeypatch.setattr(auth, "_jwk_client", lambda _url: fake_client)

    return lambda sub="user_alice", **kw: _make_token(private_key, sub=sub, **kw)


def test_unauthenticated_requests_rejected(clerk_auth):
    c = TestClient(app)
    assert c.get("/health").status_code == 200  # public route remains open
    assert c.get("/me").status_code == 401
    assert c.get("/kundlis").status_code == 401
    assert c.post("/kundlis", json=BIRTH).status_code == 401
    assert c.post("/ask", json={**BIRTH, "question": "career"}).status_code == 401


def test_expired_and_wrong_issuer_tokens_rejected(clerk_auth):
    c = TestClient(app)
    expired = clerk_auth(exp_delta_s=-60)
    wrong_iss = clerk_auth(issuer="https://evil.example.com")
    assert c.get("/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    assert c.get("/me", headers={"Authorization": f"Bearer {wrong_iss}"}).status_code == 401


def test_me_and_user_isolation_sqlite(clerk_auth):
    c = TestClient(app)
    h_alice = {"Authorization": f"Bearer {clerk_auth('user_alice')}"}
    h_bob = {"Authorization": f"Bearer {clerk_auth('user_bob')}"}

    me = c.get("/me", headers=h_alice)
    assert me.status_code == 200 and me.json()["id"] == "user_alice"
    upd = c.patch("/me", json={"full_name": "Alice", "preferred_lang": "hi"}, headers=h_alice)
    assert upd.status_code == 200 and upd.json()["preferred_lang"] == "hi"

    created = c.post("/kundlis", json=BIRTH, headers=h_alice)
    assert created.status_code == 201
    kid = created.json()["id"]

    # Bob cannot see, open, edit, or delete Alice's kundli
    assert c.get("/kundlis", headers=h_bob).json() == []
    assert c.get(f"/kundlis/{kid}", headers=h_bob).status_code == 404
    assert c.put(f"/kundlis/{kid}", json={**BIRTH, "name": "Hacked"}, headers=h_bob).status_code == 404
    assert c.delete(f"/kundlis/{kid}", headers=h_bob).status_code == 404

    # Alice still owns it
    assert len(c.get("/kundlis", headers=h_alice).json()) == 1
    assert c.post("/ask/key", json={"api_key": "sk-ant-test"}, headers=h_alice).status_code == 403


def test_legacy_sqlite_migration(tmp_path, monkeypatch):
    db = tmp_path / "legacy.db"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE kundlis (id TEXT PRIMARY KEY, name TEXT NOT NULL, gender TEXT, "
            "datetime_local TEXT NOT NULL, tz TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL, "
            "place TEXT, settings TEXT NOT NULL DEFAULT '{}', notes TEXT DEFAULT '', "
            "tags TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO kundlis VALUES ('abc', 'Legacy', '', '1990-05-14T06:30:00', 'Asia/Kolkata', "
            "28.61, 77.20, 'Delhi', '{}', '', '', '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
        )
    monkeypatch.setattr(store, "DB_PATH", db)
    rows = store.list_kundlis(user_id="local")
    assert len(rows) == 1 and rows[0]["user_id"] == "local"


def test_supabase_headers_and_rls_forwarding(monkeypatch, clerk_auth):
    monkeypatch.setenv("SUPABASE_URL", "https://proj.supabase.co/rest/v1/")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_demo")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_demo")

    calls = []

    def fake_request(method, url, **kw):
        calls.append((method, url, kw.get("headers"), kw.get("params"), kw.get("json")))
        return httpx.Response(
            200,
            json=[{**BIRTH, "id": "11111111-1111-1111-1111-111111111111", "user_id": "user_alice", "settings": {}}],
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(store.httpx, "request", fake_request)
    c = TestClient(app)
    tok = clerk_auth("user_alice")
    res = c.post("/kundlis", json=BIRTH, headers={"Authorization": f"Bearer {tok}"})
    assert res.status_code == 201
    method, url, headers, _params, payload = calls[-1]
    assert method == "POST" and url == "https://proj.supabase.co/rest/v1/kundlis"
    assert headers["apikey"] == "sb_publishable_demo"
    assert headers["Authorization"] == f"Bearer {tok}"
    assert payload["user_id"] == "user_alice"

    # Admin cleanup must send sb_secret_ only in apikey, never in Authorization: Bearer
    store.delete_user_data_admin("user_alice")
    _, _, admin_headers, _, _ = calls[-1]
    assert admin_headers["apikey"] == "sb_secret_demo"
    assert "Authorization" not in admin_headers


def test_clerk_webhook_dispatch(monkeypatch):
    monkeypatch.setenv("CLERK_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setenv("SUPABASE_URL", "https://proj.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_demo")

    events = []
    monkeypatch.setattr(store, "upsert_profile_admin", lambda uid, **kw: events.append(("upsert", uid, kw)) or {"id": uid})
    monkeypatch.setattr(store, "delete_user_data_admin", lambda uid: events.append(("delete", uid)))

    async def fake_verify(_req):
        return {
            "type": "user.created",
            "data": {
                "id": "user_99",
                "first_name": "Aarav",
                "last_name": "Sharma",
                "primary_email_address_id": "em_1",
                "email_addresses": [{"id": "em_1", "email_address": "aarav@example.com"}],
            },
        }

    monkeypatch.setattr(auth, "verify_clerk_webhook", fake_verify)
    c = TestClient(app)
    r = c.post("/webhooks/clerk", json={})
    assert r.status_code == 200 and events == [("upsert", "user_99", {"email": "aarav@example.com", "full_name": "Aarav Sharma"})]
