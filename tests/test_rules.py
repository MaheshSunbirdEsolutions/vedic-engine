"""Rules-engine tests on hand-built charts (sign indices: Aries=0 ... Pisces=11)."""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from vedic_engine.api import app
from vedic_engine.chart import build_chart
from vedic_engine.rules import Facts, evaluate, facts_from_chart, interpret, load_rules
from vedic_engine.rules.engine import PRIMITIVES

# baseline: everything bunched in Aries, Lagna Aries
BASE = {p: 0 for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]}


def facts(lagna=0, dignity=None, d9=None, flags=None, **signs):
    s = {**BASE, "Rahu": 3, "Ketu": 9, **signs}
    return Facts(lagna=lagna, signs=s, dignity=dignity or {}, d9=d9 or {}, flags=flags or {})


def ids(f):
    return {h["id"] for h in interpret(f)}


def test_rule_files_are_valid():
    rules = load_rules()
    assert len(rules) >= 30
    for r in rules:
        assert r["status"] in ("draft", "reviewed")
        evaluate(r["when"], facts())  # every condition must evaluate without error
        def walk(c):
            (op, arg), = c.items()
            if op in ("all", "any"):
                [walk(x) for x in arg]
            elif op == "not":
                walk(arg)
            else:
                assert op in PRIMITIVES
        walk(r["when"])


def test_hamsa_yoga():
    # Jupiter exalted in Cancer, Lagna Aries -> 4th house
    f = facts(Jupiter=3, dignity={"Jupiter": "exalted"})
    assert "hamsa" in ids(f)
    f2 = facts(Jupiter=3, dignity={"Jupiter": "friend"})
    assert "hamsa" not in ids(f2)


def test_gajakesari_from_moon():
    assert "gajakesari" in ids(facts(Moon=2, Jupiter=8))      # 7th from Moon
    assert "gajakesari" not in ids(facts(Moon=2, Jupiter=4))  # 3rd from Moon


def test_kemadruma_and_its_cancellation():
    # Moon alone in Leo; others in Sagittarius (5th from Leo); Lagna Gemini -> Sag is 7th = kendra -> cancelled
    others = dict(Sun=8, Mars=8, Mercury=8, Jupiter=8, Venus=8, Saturn=8)
    assert "kemadruma" not in ids(facts(lagna=2, Moon=4, **others))
    # Lagna Aries -> Sag is 9th, Leo 5th: no planet in angles -> Kemadruma stands
    assert "kemadruma" in ids(facts(lagna=0, Moon=4, **others))


def test_sunapha_anapha_durudhura_exclusive():
    assert ids(facts(Moon=4, Mars=5)) & {"sunapha", "anapha", "durudhura"} == {"sunapha"}
    assert ids(facts(Moon=4, Mars=3)) & {"sunapha", "anapha", "durudhura"} == {"anapha"}
    assert ids(facts(Moon=4, Mars=3, Venus=5)) & {"sunapha", "anapha", "durudhura"} == {"durudhura"}


def test_yogakaraka_for_taurus_lagna_is_saturn():
    hit = [h for h in interpret(facts(lagna=1)) if h["id"] == "yogakaraka"]
    assert hit and hit[0]["planets"] == ["Saturn"]


def test_raja_yoga_mutual_aspect():
    # Lagna Aries: 10th lord Saturn, 9th lord Jupiter. Saturn in Libra, Jupiter in Aries:
    # 7th from each other -> mutual aspect -> Raja Yoga
    f = facts(Saturn=6, Jupiter=0)
    assert "raja_yoga_kendra_trikona" in ids(f)


def test_viparita_harsha():
    # Lagna Aries: 6th = Virgo, lord Mercury; Mercury in Scorpio (8th)
    assert "harsha" in ids(facts(Mercury=7))


def test_parivartana_exchange():
    # Sun in Cancer (Moon's sign), Moon in Leo (Sun's sign)
    assert "parivartana" in ids(facts(Sun=3, Moon=4))


def test_neecha_bhanga():
    # Saturn debilitated in Aries; Mars (lord of Aries) in Cancer = 4th from Aries lagna -> kendra
    f = facts(Saturn=0, Mars=3, dignity={"Saturn": "debilitated"})
    assert "neecha_bhanga" in ids(f)


def test_lagna_lord_template():
    f = facts(lagna=0, Mars=9)  # Mars (Aries lord) in Capricorn = 10th
    hit = [h for h in interpret(f) if h["id"] == "lagna_lord_h10"][0]
    assert hit["text"].startswith("Mars, the ascendant lord")


def test_dosha_flags():
    assert "manglik_dosha" in ids(facts(flags={"manglik": True}))
    assert "manglik_dosha" not in ids(facts(flags={"manglik": False}))


def test_draft_filter():
    assert interpret(facts(Moon=2, Jupiter=8), include_draft=False) == []


def test_real_chart_end_to_end():
    c = build_chart(datetime(1990, 5, 14, 6, 30), "Asia/Kolkata", 28.6139, 77.2090)
    hits = interpret(facts_from_chart(c))
    assert any(h["category"] == "placement" and h["id"].startswith("lagna_lord_h") for h in hits)


def test_interpret_api():
    r = TestClient(app).post("/interpret", json={
        "datetime_local": "1990-05-14T06:30:00", "tz": "Asia/Kolkata", "lat": 28.6139, "lon": 77.2090})
    assert r.status_code == 200
    body = r.json()
    assert body["findings"] and isinstance(body["remedy_tags"], list)
