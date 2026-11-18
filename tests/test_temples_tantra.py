from datetime import date, datetime

from fastapi.testclient import TestClient

from vedic_engine import nakshatra as N, tantra, temples
from vedic_engine.api import app
from vedic_engine.ephemeris import Settings

B = {"datetime_local": "1980-12-27T22:46:00", "tz": "Asia/Kolkata", "lat": 31.708, "lon": 76.932,
     "lang": "en", "at": "2026-11-18T13:00:00"}


def test_every_planet_has_a_temple_and_a_mahavidya():
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        assert temples.for_planet(p), p
        assert p in tantra.MAHAVIDYA


def test_temples_have_sources():
    for t in temples.TEMPLES:
        assert t["sources"] and all(u.startswith("http") for u in t["sources"]), t["id"]


def test_no_tantric_beeja_or_abhichara():
    text = repr(tantra.MAHAVIDYA) + repr(tantra.PRINCIPLES)
    for bad in ("क्रीं", "ह्लीं", "फट्", "vashikaran", "uchchatan"):
        assert bad not in text


def test_suggestions_follow_doshas():
    r = TestClient(app).post("/report/tirtha", json=B).json()
    ids = [t["id"] for t in r["suggested"]]
    assert "thirunallar" in ids              # Saturn dhaiya + Saturn dasha
    assert any(i in ids for i in ("trimbakeshwar", "kalahasti", "kukke"))   # Kaal Sarp present
    assert all(t["reasons"] for t in r["suggested"])


def test_full_set_has_tantra_and_temple():
    r = TestClient(app).post("/report/full", json=B).json()
    ids = [s["id"] for s in r["remedy_plan"][0]["systems"]]
    assert "tantra" in ids and "temple" in ids


def test_next_ashlesha_follows_lunar_month():
    d = N.next_days("Ashlesha", "Asia/Kolkata", 31.7, 76.93, Settings(), date(2026, 11, 18), 4)
    gaps = [(date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days for a, b in zip(d, d[1:])]
    assert len(d) == 4 and all(26 <= g <= 29 for g in gaps)
