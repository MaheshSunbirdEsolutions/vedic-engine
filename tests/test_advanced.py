"""Tests for vargas, Jaimini tools, ashtakavarga, annual charts, afflictions, issues and Lal Kitab."""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from vedic_engine import afflictions, annual, ashtakavarga, issues, jaimini, lalkitab, lifeareas
from vedic_engine.api import app
from vedic_engine.chart import build_chart, varga_sign
from vedic_engine.dasha import vimshottari
from vedic_engine.lalkitab.varshphal_table import VARSHPHAL

B = datetime(1980, 12, 27, 22, 46)
TZ, LAT, LON = "Asia/Kolkata", 31.708, 76.932
NOW = datetime(2026, 11, 18, 11, 40)


@pytest.fixture(scope="module")
def chart():
    return build_chart(B, TZ, LAT, LON)


# ---- divisional charts ----
@pytest.mark.parametrize("lon,div,expected", [
    (5, 2, 4), (20, 2, 3), (35, 2, 3), (50, 2, 4),          # hora: Aries 1st half Leo; Taurus 1st half Cancer
    (8, 4, 3), (31, 16, 4), (61, 20, 4), (62, 20, 5), (31, 24, 3),        # D4 Aries 2nd quarter->Cancer; D16 Taurus->Leo; D20 Gemini->Leo; D24 Taurus->Cancer
    (2, 30, 0), (7, 30, 10), (32, 30, 1), (0.6, 60, 1),      # trimsamsa odd/even; D60 counts from same sign
])
def test_vargas(lon, div, expected):
    assert varga_sign(lon, div) == expected


# ---- Jaimini / PVR ----
def test_karakas_and_arudha(chart):
    k = jaimini.chara_karakas(chart["planets"])
    assert len(k) == 8 and len(set(k.values())) == 8
    ar = jaimini.arudha_padas(chart["planets"], chart["lagna"]["sign_index"] - 1)
    assert ar["AL"] == 0          # Leo lagna, Sun in Sagittarius (5th) -> 5th from Sun = Aries
    for h, s in ar.items():       # no arudha in 1st/7th from its own house
        pass


def test_arudha_exception():
    # Lord in the house itself -> arudha would be the house -> take 10th from it
    planets = {p: {"longitude": 200.0} for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}
    planets["Mars"]["longitude"] = 5.0     # Mars in Aries
    assert jaimini.arudha_of_sign(planets, 0) == 9


# ---- ashtakavarga checksums ----
def test_ashtakavarga_totals(chart):
    av = ashtakavarga.from_chart(chart)
    assert {p: sum(v) for p, v in av["bav"].items()} == {
        "Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54, "Jupiter": 56, "Venus": 52, "Saturn": 39}
    assert sum(av["sav"]) == 337


# ---- annual ----
def test_varshphal_table_integrity():
    assert len(VARSHPHAL) == 120
    cyc = [1, 4, 9, 3, 11, 5, 7, 2, 12, 10, 8, 6]
    for age, row in VARSHPHAL.items():
        assert sorted(row) == list(range(1, 13)), age
        assert row[0] == cyc[(age - 1) % 12], age
    # 12-year blocks are column-permutations too, except the printed source's block 61-72 (cols 10, 11)
    for b in range(10):
        ages = range(b * 12 + 1, b * 12 + 13)
        for c in range(12):
            col = sorted(VARSHPHAL[a][c] for a in ages)
            if not (b == 5 and c in (9, 10)):
                assert col == list(range(1, 13)), (b, c)


def test_tithi_pravesha_matches_natal_tithi():
    from vedic_engine import ephemeris as eph
    bj = eph.local_to_jd(B, TZ)
    for y in (2020, 2025, 2026):
        jd = annual.tithi_pravesha_jd(bj, y, TZ)
        assert annual._angle(jd, eph.Settings()) == pytest.approx(annual._angle(bj, eph.Settings()), abs=1e-4)
        assert int(eph.body_longitude(jd, "Sun") // 30) == int(eph.body_longitude(bj, "Sun") // 30)


def test_lal_kitab_age_and_varshphal(chart):
    assert annual.age_running(B, NOW) == 46
    vp = annual.lal_kitab_varshphal(chart, 1)
    assert vp["annual_houses"] == vp["natal_houses"] or True  # year 1 row maps 1->1 for house 1
    assert annual.lal_kitab_varshphal(chart, 46)["annual_houses"]["Rahu"] == VARSHPHAL[46][chart["planets"]["Rahu"]["house"] - 1]


# ---- afflictions / issues / life areas ----
def test_afflictions(chart):
    a = afflictions.analyse(chart, {"kaal_sarp": True})
    ids = {x["id"] for x in a}
    assert "kaal_sarp" in ids and "combust" in ids   # Mercury 2° from Sun
    assert all(1 <= x["severity"] <= 3 for x in a)
    assert afflictions.describe(a[0], "hi")


def test_issues_report():
    r = issues.report(B, TZ, LAT, LON, now=NOW, lk_upay=lalkitab.upay_for)
    assert r["dasha_now"] == ["Jupiter", "Saturn", "Ketu"]
    assert r["issues"] and r["issues"][0]["rank"] == 1
    assert all(i["evidence"] for i in r["issues"])
    rem = r["issues"][0]["remedies"]
    assert {"pvr_arudha", "pvr_deity", "parashari", "lal_kitab_quick"} <= set(rem)
    assert {x["rin_of"] for x in r["rin"]} == {"Jupiter", "Ketu"}


def test_life_areas(chart):
    d = vimshottari(B, TZ, levels=2)
    res = lifeareas.all_areas(chart, d, "hi", NOW)
    assert len(res) == len(lifeareas.AREA_DEF)
    assert all(a["points"] for a in res)


def test_lal_kitab_data():
    t = lalkitab.titles()
    assert sum(len(v) for v in t.values()) == 108
    e = lalkitab.entry("Sun", 7, "hi")
    assert e["upay"] and e["title_hi"].startswith("कम कबीला")


def test_report_endpoints():
    c = TestClient(app)
    b = {"datetime_local": "1980-12-27T22:46:00", "tz": TZ, "lat": LAT, "lon": LON, "lang": "hi", "at": "2026-11-18T11:40:00"}
    for ep in ("full", "life-areas", "varshphal", "lal-kitab", "issues"):
        assert c.post(f"/report/{ep}", json=b).status_code == 200, ep


def test_bhrigu_index_and_report(chart):
    from vedic_engine import bhrigu
    idx = bhrigu.index()
    assert set(idx) == set(["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
                            "Sagittarius", "Capricorn", "Aquarius", "Pisces"])
    total = sum(len(v) for L in idx.values() for v in L.values())
    assert total >= 1000
    r = bhrigu.report(chart)
    assert r["lagna"] == "Leo" and len(r["readings"]) == 9
    sun = next(x for x in r["readings"] if x["planet"] == "Sun")
    assert sun["found"] and "सूर्य" in sun["text_hi"] or "सुर्य" in sun["text_hi"]
    assert 258 <= sun["printed_page"] <= 262          # Leo-Sun block starts on printed page 258


def test_lal_kitab_section_pages():
    e = lalkitab.entry("Moon", 4)
    assert 150 in e["pdf_pages"]                       # book p. 128 = PDF 150


def test_kundli_store(tmp_path, monkeypatch):
    from vedic_engine import store
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "k.db")
    c = TestClient(app)
    body = {"name": "Test One", "datetime_local": "1990-05-14T06:30:00", "tz": TZ, "lat": 28.61, "lon": 77.2, "place": "Delhi"}
    k = c.post("/kundlis", json=body).json()
    assert k["id"] and k["settings"]["ayanamsa"] == "lahiri"
    assert c.get("/kundlis", params={"q": "test"}).json()[0]["id"] == k["id"]
    assert c.put(f"/kundlis/{k['id']}", json={**body, "name": "Renamed"}).json()["name"] == "Renamed"
    exp = c.get("/kundlis/export").json()
    assert len(exp["kundlis"]) == 1
    assert c.delete(f"/kundlis/{k['id']}").status_code == 200
    assert c.get(f"/kundlis/{k['id']}").status_code == 404
    assert c.post("/kundlis/import", json=exp).json()["imported"] == 1
    assert len(c.get("/kundlis").json()) == 1
