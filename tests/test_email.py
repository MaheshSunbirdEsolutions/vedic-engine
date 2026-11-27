"""SMTP email sharing for daily horoscope (env-only config, auth restriction, preview, and mocked SMTP)."""
import smtplib

from fastapi.testclient import TestClient

from vedic_engine import auth, emailer
from vedic_engine.api import app

C = TestClient(app)


def test_email_env_status_and_preview(monkeypatch, tmp_path):
    monkeypatch.setattr(emailer, "_ROOT_ENV", tmp_path / ".env")
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "SMTP_SECURITY"):
        monkeypatch.delenv(k, raising=False)

    st0 = C.get("/email/status").json()
    assert st0["configured"] is False

    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_SECURITY", "starttls")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password-9876")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.com")

    st1 = C.get("/email/status").json()
    assert st1 == {
        "configured": True,
        "host": "smtp.example.com",
        "port": 587,
        "security": "starttls",
        "from_email": "noreply@example.com",
    }

    pv = C.post("/email/horoscope", json={
        "kind": "rashi", "sign": "Aquarius", "lang": "en", "day": "2026-11-27", "preview_only": True,
    }).json()
    assert "Aquarius" in pv["subject"] and "2026-11-27" in pv["subject"]
    assert "Area Outlook" in pv["text"] and "<table" in pv["html"]

    pvk = C.post("/email/horoscope", json={
        "kind": "kundli", "name": "Test User",
        "datetime_local": "1980-12-27T22:46:00", "tz": "Asia/Kolkata", "lat": 31.708, "lon": 76.932,
        "lang": "hi", "day": "2026-11-27", "preview_only": True,
    }).json()
    assert "Test User" in pvk["subject"] and "दैनिक कुंडली राशिफल" in pvk["text"]


def test_email_send_smtp_from_env_mocked(monkeypatch, tmp_path):
    monkeypatch.setattr(emailer, "_ROOT_ENV", tmp_path / ".env")
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_SECURITY", "starttls")
    monkeypatch.setenv("SMTP_USER", "jyotish@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret-app-pw")
    monkeypatch.setenv("SMTP_FROM", "jyotish@gmail.com")
    sent = []

    class FakeSMTP:
        def __init__(self, host, port, timeout=20, context=None):
            self.host, self.port = host, port
            self.tls = False
            self.logged_in = None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def ehlo(self):
            pass

        def starttls(self, context=None):
            self.tls = True

        def login(self, user, pw):
            self.logged_in = (user, pw)

        def send_message(self, msg):
            sent.append((self.host, self.port, self.tls, self.logged_in, msg))

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    bad = C.post("/email/horoscope", json={"to_email": "not-an-email", "kind": "rashi", "sign": "Aries"})
    assert bad.status_code == 400

    res = C.post("/email/horoscope", json={
        "to_email": "user1@example.com, user2@example.com",
        "kind": "rashi", "sign": "Leo", "lang": "en", "day": "2026-11-27",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["sent"] is True and body["to"] == ["user1@example.com", "user2@example.com"]
    assert len(sent) == 1
    host, port, tls, creds, msg = sent[0]
    assert (host, port, tls, creds) == ("smtp.gmail.com", 587, True, ("jyotish@gmail.com", "secret-app-pw"))
    assert "Leo" in msg["Subject"]
    assert "user1@example.com" in msg["To"] and "user2@example.com" in msg["To"]
    assert msg.is_multipart()


def test_email_restricted_to_signed_in_user_when_auth_enabled(monkeypatch, tmp_path):
    monkeypatch.setattr(emailer, "_ROOT_ENV", tmp_path / ".env")
    monkeypatch.setattr(auth, "auth_enabled", lambda: True)
    monkeypatch.setattr(auth, "verify_clerk_token", lambda tok: auth.AuthUser(
        user_id="user_123", token=tok, claims={"sub": "user_123", "email": "alice@example.com"},
    ))
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_SECURITY", "starttls")
    monkeypatch.setenv("SMTP_USER", "jyotish@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret-app-pw")
    monkeypatch.setenv("SMTP_FROM", "jyotish@gmail.com")

    sent = []

    class FakeSMTP:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def ehlo(self):
            pass

        def starttls(self, context=None):
            pass

        def login(self, user, pw):
            pass

        def send_message(self, msg):
            sent.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    # Unauthenticated request rejected
    r0 = C.post("/email/horoscope", json={"kind": "rashi", "sign": "Aries"})
    assert r0.status_code == 401

    # Trying to send to another email rejected
    r1 = C.post(
        "/email/horoscope",
        headers={"Authorization": "Bearer fake-jwt"},
        json={"to_email": "someone_else@example.com", "kind": "rashi", "sign": "Aries"},
    )
    assert r1.status_code == 403

    # Omitting to_email or matching signed-in email succeeds
    r2 = C.post(
        "/email/horoscope",
        headers={"Authorization": "Bearer fake-jwt"},
        json={"kind": "rashi", "sign": "Aries", "day": "2026-11-27"},
    )
    assert r2.status_code == 200
    assert r2.json()["to"] == ["alice@example.com"]
    assert len(sent) == 1 and sent[0]["To"] == "alice@example.com"
