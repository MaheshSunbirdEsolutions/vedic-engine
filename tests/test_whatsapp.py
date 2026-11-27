"""WhatsApp daily 7:00 AM delivery: formatting, schedule persistence, 7:00 AM trigger, and mocked send."""
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi.testclient import TestClient

from vedic_engine import store, whatsapp
from vedic_engine.api import app

C = TestClient(app)


def test_whatsapp_schedule_preview_and_7am_trigger(monkeypatch, tmp_path):
    monkeypatch.setattr(whatsapp, "CONFIG", tmp_path / "whatsapp.json")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "kundlis.db")

    # Requires phone when enabling
    bad = C.post("/whatsapp/schedule", json={"enabled": True, "phone": ""})
    assert bad.status_code == 400

    # Configure for 07:00 IST for Aquarius
    r = C.post("/whatsapp/schedule", json={
        "enabled": True, "phone": "+91 98765-43210", "kind": "rashi", "sign": "Aquarius",
        "time": "07:00", "tz": "Asia/Kolkata", "lang": "en",
        "provider": "callmebot", "provider_config": {"api_key": "secret-1234"},
    })
    assert r.status_code == 200
    st = r.json()
    assert st["subscription"]["enabled"] is True
    assert st["subscription"]["phone"] == "+919876543210"
    assert st["provider_config"]["api_key"] == ""
    assert st["provider_config"]["api_key_set"] is True
    assert st["provider_config"]["api_key_hint"] == "…1234"

    # Preview returns formatted text and wa.me URL
    pv = C.post("/whatsapp/preview", json={
        "phone": "+919876543210", "kind": "rashi", "sign": "Aquarius", "lang": "en", "day": "2026-11-26",
    }).json()
    assert "Aquarius" in pv["text"] and pv["wa_me_url"].startswith("https://wa.me/919876543210?text=")

    # Mock outbound HTTP send
    sent = []

    def fake_get(url, **kw):
        sent.append((url, kw["params"]))
        return httpx.Response(200, text="Message queued", request=httpx.Request("GET", url))

    monkeypatch.setattr(whatsapp.httpx, "get", fake_get)

    # Before 07:00 IST -> does not fire
    t_early = datetime(2026, 11, 26, 6, 59, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(ZoneInfo("UTC"))
    assert whatsapp.run_pending(t_early) is False

    # At 07:01 IST -> fires once and skips duplicates on same date
    t_seven = datetime(2026, 11, 26, 7, 1, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(ZoneInfo("UTC"))
    assert whatsapp.run_pending(t_seven) is True
    assert len(sent) == 1 and "Aquarius" in sent[0][1]["text"]
    assert whatsapp.run_pending(t_seven) is False

    # Disable schedule works
    off = C.post("/whatsapp/schedule", json={"enabled": False}).json()
    assert off["subscription"]["enabled"] is False
    assert off["subscription"]["next_run"] is None


def test_whatsapp_send_now_webhook(monkeypatch, tmp_path):
    monkeypatch.setattr(whatsapp, "CONFIG", tmp_path / "whatsapp.json")
    posted = []

    def fake_post(url, **kw):
        posted.append((url, kw["json"]))
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("POST", url))

    monkeypatch.setattr(whatsapp.httpx, "post", fake_post)
    r = C.post("/whatsapp/send-now", json={
        "phone": "+919876543210", "kind": "rashi", "sign": "Leo", "lang": "hi", "day": "2026-11-26",
        "provider": "webhook", "provider_config": {"webhook_url": "http://127.0.0.1:5678/wa"},
    }).json()
    assert r["sent"] is True
    assert len(posted) == 1 and "सिंह" in posted[0][1]["text"]
