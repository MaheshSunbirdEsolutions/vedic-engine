import copy
from datetime import date, datetime

import pytest

from vedic_engine import nakshatra as N, placements as P, remedies as R
from vedic_engine.chart import build_chart
from vedic_engine.ephemeris import Settings

S = Settings()
DT = datetime(1980, 12, 27, 22, 46)


@pytest.fixture(scope="module")
def chart():
    return build_chart(DT, "Asia/Kolkata", 31.708, 76.932, S)


def test_placement_explains_house_sign_lordship(chart):
    sat = P.explain(chart, "Saturn", "en")
    assert sat["house"] == 2 and sat["sign"] == "Virgo" and sat["owns"] == [6, 7]
    assert "Dhana bhav" in sat["text"] and "rules houses 6 & 7" in sat["text"]
    assert "Jupiter" in sat["with"]
    assert P.explain(chart, "Saturn", "hi")["text"].startswith("शनि दूसरे भाव")


def test_bhav_table(chart):
    rows = P.houses(chart, "en")
    assert len(rows) == 12 and rows[0]["sign"] == "Leo" and rows[0]["lord"] == "Sun"


def test_functional_nature_drives_gem_advice(chart):
    sat = R.full_set(chart, "Saturn", "en")          # rules 6 & 7 for Leo -> malefic
    assert sat["approach"] == "pacify" and sat["gem_verdict"] == "avoid"
    sun = R.full_set(chart, "Sun", "en")             # lagna lord
    assert sun["approach"] == "strengthen" and sun["gem_verdict"] == "suitable"
    ids = [s["id"] for s in sun["systems"]]
    for k in ("lal_kitab", "mantra", "path", "daana", "vrata", "karma", "deity", "rudraksha", "jadi", "gem", "yantra"):
        assert k in ids


def test_tara_matches_book_example():
    # Book p.179: native in Purva Phalguni – vadha = 7th/16th/25th = Anuradha, Uttara Bhadrapada, Pushya
    # (the book prints "Purva Bhadrapada" for the 16th – a slip; the other 8 nakshatras it lists match)
    b = N.IDX["Purva Phalguni"]
    for n in ("Swati", "Shatabhisha", "Ardra"):
        assert N.TARAS[N.tara(b, N.IDX[n])][0] == "Pratyari"
    for n in ("Anuradha", "Uttara Bhadrapada", "Pushya"):
        assert N.TARAS[N.tara(b, N.IDX[n])][0] == "Vadha"
    for n in ("Hasta", "Shravana", "Rohini"):
        assert N.TARAS[N.tara(b, N.IDX[n])][0] == "Vipat"


def test_birth_weekday_and_no_false_mool(chart):
    tithi, wd = N._birth_tithi_vara(DT, "Asia/Kolkata", 31.708, 76.932, S)
    assert wd == 6                                     # 27 Dec 1980 was a Saturday
    assert N.birth_doshas(chart, DT, "Asia/Kolkata", 31.708, 76.932, S) == []


def test_gand_mool_detection(chart):
    c = copy.deepcopy(chart)
    c["planets"]["Moon"]["longitude"] = 240.2          # Mula, inside gandanta and abhukta
    c["planets"]["Moon"]["nakshatra"]["index"] = N.IDX["Mula"] + 1
    d = N.birth_doshas(c, DT, "Asia/Kolkata", 31.708, 76.932, S)
    gm = [x for x in d if x["id"] == "gand_mool"][0]
    assert gm["severity"] == 3 and "Gandanta" in gm["text"] and "Abhukta" in gm["text"]


def test_remedy_days_exclude_bad_taras(chart):
    days = N.remedy_days(chart, "Asia/Kolkata", 31.708, 76.932, S, date(2026, 11, 18), 60, ["Saturn"])
    assert days
    birth = N.IDX[chart["planets"]["Moon"]["nakshatra"]["name"]]
    for d in days:
        assert N.tara(birth, N.IDX[d["nakshatra"]]) not in (0, 2, 4, 6)
        assert d["yogas"]


def test_health_dataset_complete():
    assert set(N.HEALTH) == set(N.NAK)
