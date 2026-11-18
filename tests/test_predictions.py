from fastapi.testclient import TestClient

from vedic_engine.api import app

B = {"datetime_local": "1980-12-27T22:46:00", "tz": "Asia/Kolkata", "lat": 31.708, "lon": 76.932,
     "lang": "en", "year": 2026, "at": "2026-11-18T13:00:00"}
C = TestClient(app)


def test_lifelong_covers_whole_life():
    r = C.post("/report/lifelong", json=B).json()
    j = r["journey"]
    assert j[0]["age_from"] == 0 and j[-1]["age_to"] >= 95
    assert sum(1 for m in j if m["current"]) == 1 and next(m for m in j if m["current"])["lord"] == "Jupiter"
    assert all(m["antardashas"] and m["text"] for m in j)
    kinds = {m["kind"] for m in r["milestones"]}
    assert {"sade_sati", "saturn_return", "jupiter_return"} <= kinds
    sr = [m for m in r["milestones"] if m["kind"] == "saturn_return"]
    assert 28 <= float(sr[0]["age"]) <= 30.5              # first Saturn return ~29.5 years


def test_yearly_transits_and_periods():
    y = C.post("/report/yearly", json=B).json()
    ju = [t for t in y["transits"] if t["planet"] == "Jupiter"]
    assert [t["sign"] for t in ju] == ["Gemini", "Cancer", "Leo"]        # 2026 Jupiter ingresses
    assert ju[1]["from"].startswith("2026-06") and ju[2]["from"].startswith("2026-1")
    assert {p["ad"] for p in y["periods"]} == {"Jupiter", "Saturn"}
    assert len(y["months"]) == 12 and len(y["years"]) == 12 and len(y["areas"]) == 8
    assert y["sade_sati"]["dhaiya"]


def test_hindi_renders():
    y = C.post("/report/yearly", json={**B, "lang": "hi"}).json()
    import re
    assert "वर्ष" in y["summary"] and not re.search(r"\d+वें भाव", y["transits"][0]["text"])


def test_life_story_tenses_and_chapters():
    for lang in ("en", "hi"):
        st = C.post("/report/lifelong", json={**B, "lang": lang}).json()["story"]
        assert len(st["prologue"]) >= 4 and st["epilogue"]
        status = [c["status"] for c in st["chapters"]]
        assert status.count("present") == 1 and status.index("present") == 5      # Jupiter chapter
        assert all(c["paragraphs"] for c in st["chapters"])
    en = C.post("/report/lifelong", json=B).json()["story"]["chapters"]
    assert " was above all about" in en[3]["paragraphs"][0] and " will be above all about" in en[7]["paragraphs"][0]
