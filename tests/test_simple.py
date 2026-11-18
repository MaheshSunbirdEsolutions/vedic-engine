"""Simple summary report and the open-ended Sade Sati regression (Windows 500 on /report/lifelong)."""
import re
from datetime import datetime

from fastapi.testclient import TestClient

from vedic_engine import predictions as P
from vedic_engine.api import app, build_chart, vimshottari
from vedic_engine.ephemeris import Settings

C = TestClient(app)
B = {"datetime_local": "1980-12-27T22:46:00", "tz": "Asia/Kolkata", "lat": 31.708, "lon": 76.932,
     "at": "2026-11-18T12:00:00"}


def test_sade_sati_running_at_window_end():
    birth = datetime(1980, 12, 27, 22, 46)
    s = Settings()
    c = build_chart(birth, "Asia/Kolkata", 31.708, 76.932, s)
    d = vimshottari(birth, "Asia/Kolkata", s, levels=2, at=datetime(2026, 11, 18))
    r = P.lifelong(c, d, birth, "Asia/Kolkata", s, "en", sade_sati=[{"start": "2079-04-01", "end": None}],
                   now=datetime(2026, 11, 18))
    ss = [m for m in r["milestones"] if m["kind"] == "sade_sati"]
    assert ss and ss[0]["end"]


def test_simple_report_both_languages():
    for lang in ("en", "hi"):
        r = C.post("/report/simple", json={**B, "lang": lang})
        assert r.status_code == 200, r.text
        r = r.json()
        ids = [s["id"] for s in r["sections"]]
        assert ids[:2] == ["now", "year"] and "remedies" in ids and "attention" in ids
        rem = next(s for s in r["sections"] if s["id"] == "remedies")
        assert rem["plans"] and all(p["steps"] for p in rem["plans"])
        text = str(r)
        if lang == "hi":
            assert "ॐ" in text and "कुल जप" not in text.split("मंत्र:")[1][:60]
            assert not re.search(r"\d+वें भाव", text)
        else:
            assert "Om " in text
