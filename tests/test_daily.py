"""Daily horoscope: personalized chart reading (/report/daily) and 12-Rashi (/horoscope/daily)."""
import re

from fastapi.testclient import TestClient

from vedic_engine.api import app

C = TestClient(app)
B = {"datetime_local": "1980-12-27T22:46:00", "tz": "Asia/Kolkata", "lat": 31.708, "lon": 76.932,
     "lang": "en", "day": "2026-11-26", "at": "2026-11-26T10:00:00"}
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def test_personalized_daily_horoscope():
    r = C.post("/report/daily", json=B).json()
    assert r["date"] == "2026-11-26"
    assert r["rating"] in ("excellent", "good", "mixed", "challenging")
    assert r["panchang"]["vara"] == "Guruvara"
    assert r["chandrabala"]["moon_sign"]
    assert 1 <= r["chandrabala"]["house_from_moon"] <= 12
    assert r["tarabala"] and r["tarabala"]["name"]
    assert len(r["transits"]) == 9
    assert len(r["areas"]) == 8
    assert len(r["week"]) == 7
    assert r["week"][0]["date"] == "2026-11-26"
    assert r["daily_tip"]["mantra"] and r["daily_tip"]["colour"]


def test_personalized_daily_hindi():
    r = C.post("/report/daily", json={**B, "lang": "hi"}).json()
    assert DEVANAGARI.search(r["summary"])
    assert DEVANAGARI.search(r["chandrabala"]["note"])
    assert not re.search(r"\d+वें भाव", r["summary"])
    assert all(DEVANAGARI.search(a["title"]) for a in r["areas"])


def test_rashi_daily_horoscope():
    r = C.post("/horoscope/daily", json={"day": "2026-11-26", "lang": "en"}).json()
    assert len(r["signs"]) == 12
    assert {s["moon_house"] for s in r["signs"]} == set(range(1, 13))
    assert sum(1 for s in r["signs"] if s["chandrashtama"]) == 1
    assert all(
        s["highlights"] and s["tip"] and s["mantra"] and s["overview"]
        and len(s["areas"]) == 5 and len(s["transits"]) == 9 and len(s["week"]) == 7
        and s["lucky_numbers"] and s["deity"] and s["guidance"]["favour"] and s["guidance"]["avoid"]
        for s in r["signs"]
    )

    rg = C.get("/horoscope/daily?day=2026-11-26&lang=hi").json()
    assert len(rg["signs"]) == 12
    assert DEVANAGARI.search(rg["signs"][0]["summary"])
    assert DEVANAGARI.search(rg["signs"][0]["overview"])
    assert DEVANAGARI.search(rg["signs"][0]["tip"])
    assert all(DEVANAGARI.search(a["title"]) for a in rg["signs"][0]["areas"])
