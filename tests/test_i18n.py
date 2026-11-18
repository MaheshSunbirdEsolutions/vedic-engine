"""Every translatable item must have a Hindi version."""
import re

from fastapi.testclient import TestClient

from vedic_engine import i18n
from vedic_engine.api import app
from vedic_engine.constants import (
    MOVABLE_KARANAS, NAKSHATRAS, PLANETS, SIGNS, TITHI_NAMES, VARA_NAMES, YOGA_NAMES,
)
from vedic_engine.matching import GANA_NAMES, NADI_NAMES, VARNA_NAMES, VASHYA_ORDER, YONI
from vedic_engine.rules import facts_from_chart, interpret, load_rules

HI = i18n.load("hi")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def test_every_ui_key_translated():
    missing = set(i18n.load("en")["ui"]) - set(HI["ui"])
    assert not missing, missing


def test_every_term_translated():
    terms = [*PLANETS, *SIGNS, *NAKSHATRAS, *TITHI_NAMES, "Purnima", "Amavasya", "Shukla", "Krishna",
             *YOGA_NAMES, *MOVABLE_KARANAS, "Shakuni", "Chatushpada", "Naga", "Kimstughna", *VARA_NAMES,
             "exalted", "debilitated", "moolatrikona", "own", "friend", "neutral", "enemy",
             *VARNA_NAMES.values(), *VASHYA_ORDER, *set(YONI), *GANA_NAMES, *NADI_NAMES,
             "rising (12th)", "peak (1st)", "setting (2nd)", "Kantaka/Ardhashtama (4th)", "Ashtama (8th)"]
    missing = [x for x in terms if x not in HI["terms"]]
    assert not missing, missing
    assert set(PLANETS) <= set(HI["abbr"])


def test_every_rule_translated():
    missing = [r["id"] for r in load_rules() if r["id"] not in HI["rules"]]
    assert not missing, missing
    for rid, tr in HI["rules"].items():
        assert DEVANAGARI.search(tr["name"]) and DEVANAGARI.search(tr["text"]), rid


def test_interpret_in_hindi():
    from datetime import datetime
    from vedic_engine.chart import build_chart
    c = build_chart(datetime(1990, 5, 14, 6, 30), "Asia/Kolkata", 28.6139, 77.2090)
    hits = interpret(facts_from_chart(c), lang="hi")
    assert hits and all(DEVANAGARI.search(h["text"]) for h in hits)
    assert not any("{" in h["text"] for h in hits)  # templates filled


def test_i18n_endpoint():
    r = TestClient(app).get("/i18n/hi").json()
    assert r["terms"]["Saturn"] == "शनि" and r["ui"]["generate"] == "कुंडली बनाएँ"
    assert TestClient(app).get("/i18n/fr").status_code == 422
