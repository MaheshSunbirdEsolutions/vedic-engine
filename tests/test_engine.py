"""Engine tests.

1. Formula/unit tests (pure maths).
2. Astronomical reference checks against published panchang values
   (Drik-style, New Delhi) and well-known transits.
3. Parity tests against Jagannatha Hora exports placed in tests/fixtures/*.json
   (skipped automatically when no fixtures exist). See README for the format.
"""
import json
import pathlib
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from vedic_engine import ephemeris as eph
from vedic_engine.api import app
from vedic_engine.chart import build_chart, nakshatra, varga_sign
from vedic_engine.constants import DASHA_YEARS
from vedic_engine.dasha import birth_balance, vimshottari
from vedic_engine.doshas import kaal_sarp, manglik
from vedic_engine.matching import ashtakoota, nadi
from vedic_engine.panchang import karana_name, panchang

DELHI = dict(tz="Asia/Kolkata", lat=28.6139, lon=77.2090)


# ---------- 1. formulas ----------

def test_dasha_years_total_120():
    assert sum(DASHA_YEARS.values()) == 120


def test_nakshatra_boundaries():
    assert nakshatra(0)["name"] == "Ashwini" and nakshatra(0)["pada"] == 1
    assert nakshatra(13.34)["name"] == "Bharani"
    assert nakshatra(359.99)["name"] == "Revati" and nakshatra(359.99)["pada"] == 4
    assert nakshatra(3.34)["pada"] == 2


def test_dasha_balance_formula():
    # Moon at the very start of Ashwini -> full 7 years of Ketu remain
    assert birth_balance(0.0)["lord"] == "Ketu"
    assert birth_balance(0.0)["balance_years"] == pytest.approx(7)
    # Moon halfway through Bharani -> 10 of 20 Venus years remain
    b = birth_balance(13 + 1 / 3 + 20 / 3)
    assert b["lord"] == "Venus" and b["balance_years"] == pytest.approx(10)


def test_navamsa():
    assert varga_sign(0.5, 9) == 0      # Aries 0°30' -> Aries navamsa
    assert varga_sign(30.5, 9) == 9     # Taurus starts from Capricorn
    assert varga_sign(60.5, 9) == 6     # Gemini starts from Libra
    assert varga_sign(90.5, 9) == 3     # Cancer starts from Cancer (vargottama start)


def test_dashamsa_even_sign_starts_from_ninth():
    assert varga_sign(30.5, 10) == (1 + 8) % 12  # Taurus 0°30' -> Capricorn


def test_karana_cycle():
    assert karana_name(0) == "Kimstughna"
    assert karana_name(1) == "Bava" and karana_name(7) == "Vishti" and karana_name(8) == "Bava"
    assert [karana_name(k) for k in (57, 58, 59)] == ["Shakuni", "Chatushpada", "Naga"]


def test_nadi_pattern():
    assert [nadi(i) for i in range(9)] == [0, 1, 2, 2, 1, 0, 0, 1, 2]
    assert nadi(26) == 2  # Revati = Antya


def test_matching_same_nakshatra_has_nadi_dosha():
    r = ashtakoota(50.0, 50.0)
    assert r["kootas"]["nadi"]["score"] == 0 and r["doshas"]["nadi_dosha"]
    assert 0 <= r["total"] <= 36


# ---------- 2. astronomical references ----------

def test_lahiri_ayanamsa_j2000():
    jd = eph.local_to_jd(datetime(2000, 1, 1, 12), "UTC")
    assert eph.ayanamsa(jd) == pytest.approx(23.857, abs=0.005)  # 23°51'25"


def test_panchang_diwali_2024_delhi():
    p = panchang(date(2024, 11, 1), **DELHI)
    assert p["tithi"]["name"] == "Amavasya"
    assert p["tithi"]["ends"].startswith("2024-11-01T18:1")       # ~18:16
    assert p["nakshatra"]["name"] == "Swati"
    assert p["nakshatra"]["ends"].startswith("2024-11-02T03:3")   # ~03:31
    assert p["yoga"]["name"] == "Priti"
    assert p["vara"] == "Shukravara"
    assert p["sunrise"].startswith("2024-11-01T06:3")


def test_panchang_kartik_purnima_2024():
    p = panchang(date(2024, 11, 15), **DELHI)
    assert p["tithi"]["name"] == "Purnima"
    assert p["tithi"]["ends"].startswith("2024-11-16T02:5")       # ~02:58


def test_known_transits_june_2024():
    c = build_chart(datetime(2024, 6, 1, 12), **DELHI)
    assert c["planets"]["Saturn"]["sign"] == "Aquarius"
    assert c["planets"]["Jupiter"]["sign"] == "Taurus"
    assert c["planets"]["Rahu"]["sign"] == "Pisces"
    assert c["planets"]["Ketu"]["sign"] == "Virgo"


def test_dasha_timeline_is_contiguous_and_120_years():
    d = vimshottari(datetime(1990, 5, 14, 6, 30), "Asia/Kolkata", levels=2)
    mds = d["mahadashas"]
    assert len(mds) == 9
    for a, b in zip(mds, mds[1:]):
        assert a["end"] == b["start"]
    for md in mds:
        assert md["sub"][0]["lord"] == md["lord"]      # AD starts with MD lord
        assert md["sub"][0]["start"] == md["start"]
        assert md["sub"][-1]["end"] == md["end"]


def test_kaal_sarp_and_manglik_shapes():
    c = build_chart(datetime(1990, 5, 14, 6, 30), **DELHI)
    assert isinstance(kaal_sarp(c)["present"], bool)
    assert set(manglik(c)["from"]) == {"lagna", "moon", "venus"}


# ---------- API ----------

def test_api_endpoints():
    client = TestClient(app)
    birth = {"datetime_local": "1990-05-14T06:30:00", **DELHI}
    assert client.post("/chart", json=birth).status_code == 200
    assert client.post("/dasha", json={**birth, "levels": 2}).status_code == 200
    assert client.post("/panchang", json={"day": "2024-11-01", **DELHI}).status_code == 200
    r = client.post("/match", json={"groom": birth, "bride": {**birth, "datetime_local": "1992-08-02T14:10:00"}})
    assert r.status_code == 200 and r.json()["max"] == 36


# ---------- 3. Jagannatha Hora parity ----------

FIXTURES = sorted((pathlib.Path(__file__).parent / "fixtures").glob("*.json"))


@pytest.mark.skipif(not FIXTURES, reason="no Jagannatha Hora fixtures yet")
@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_parity_with_jagannatha_hora(path):
    fx = json.loads(path.read_text())
    b = fx["birth"]
    c = build_chart(datetime.fromisoformat(b["datetime_local"]), b["tz"], b["lat"], b["lon"])
    for name, exp_lon in fx["expected"]["longitudes"].items():
        got = c["lagna"]["longitude"] if name == "Lagna" else c["planets"][name]["longitude"]
        diff = abs((got - exp_lon + 180) % 360 - 180)
        assert diff * 60 < fx.get("tolerance_arcmin", 1.0), f"{name}: off by {diff * 60:.2f}′"
    if "mahadasha_start" in fx["expected"]:
        d = vimshottari(datetime.fromisoformat(b["datetime_local"]), b["tz"], levels=1)
        for md in d["mahadashas"]:
            exp = fx["expected"]["mahadasha_start"].get(md["lord"])
            if exp:
                delta = abs((datetime.fromisoformat(md["start"][:10]) - datetime.fromisoformat(exp)).days)
                assert delta <= fx.get("tolerance_days", 2), f"{md['lord']} MD start off by {delta} days"


def test_place_search_and_ui():
    client = TestClient(app)
    res = client.get("/places", params={"q": "mandi"}).json()
    assert res[0]["name"] == "Mandi" and res[0]["tz"] == "Asia/Kolkata"
    assert client.get("/").status_code == 200


def test_tzdata_available():
    # Windows has no system tz database; the tzdata package must be installed.
    import tzdata  # noqa: F401
    from zoneinfo import ZoneInfo
    from datetime import datetime, timedelta
    assert datetime(1980, 12, 27, tzinfo=ZoneInfo("Asia/Kolkata")).utcoffset() == timedelta(hours=5, minutes=30)
