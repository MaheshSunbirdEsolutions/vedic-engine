"""Ashtakoota (36 guna) kundli matching, North Indian convention.

Inputs are each person's Moon longitude (sidereal). Tables for Varna, Gana,
Graha Maitri, Tara, Bhakoot and Nadi are standard. Vashya and Yoni use
SIMPLIFIED scoring (marked below): replace with the full matrices from your
reviewing Jyotishi before launch.
"""
from __future__ import annotations

from .chart import nakshatra, sign_index
from .constants import ENEMIES, FRIENDS, SIGN_LORDS

# --- Varna (1) ---  rank: Brahmin 4 > Kshatriya 3 > Vaishya 2 > Shudra 1
VARNA_BY_SIGN = [3, 2, 1, 4, 3, 2, 1, 4, 3, 2, 1, 4]
VARNA_NAMES = {4: "Brahmin", 3: "Kshatriya", 2: "Vaishya", 1: "Shudra"}

# --- Vashya (2) ---
def vashya_group(lon: float) -> str:
    s, deg = sign_index(lon), lon % 30
    if s in (0, 1):
        return "Chatushpada"
    if s in (2, 5, 6, 10):
        return "Manava"
    if s in (3, 11):
        return "Jalachara"
    if s == 4:
        return "Vanachara"
    if s == 7:
        return "Keeta"
    if s == 8:
        return "Manava" if deg < 15 else "Chatushpada"
    if s == 9:
        return "Chatushpada" if deg < 15 else "Jalachara"
    raise AssertionError


VASHYA_ORDER = ["Chatushpada", "Manava", "Jalachara", "Vanachara", "Keeta"]
# SIMPLIFIED table (rows = groom, cols = bride) — verify with reviewer.
VASHYA_TABLE = [
    [2, 1, 1, 0.5, 1],
    [1, 2, 0.5, 0, 1],
    [1, 0.5, 2, 1, 1],
    [0.5, 0, 1, 2, 0],
    [1, 1, 1, 0, 2],
]

# --- Yoni (4) --- animal by nakshatra index
YONI = [
    "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat",
    "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer",
    "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse", "Lion", "Cow", "Elephant",
]
YONI_ENEMIES = {frozenset(p) for p in [
    ("Horse", "Buffalo"), ("Elephant", "Lion"), ("Sheep", "Monkey"), ("Serpent", "Mongoose"),
    ("Dog", "Deer"), ("Cat", "Rat"), ("Cow", "Tiger"),
]}

# --- Gana (6) --- 0 Deva, 1 Manushya, 2 Rakshasa
GANA = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1, 0, 2, 2, 1, 1, 0]
GANA_NAMES = ["Deva", "Manushya", "Rakshasa"]
GANA_TABLE = [  # rows = bride, cols = groom
    [6, 6, 0],
    [5, 6, 0],
    [1, 0, 6],
]

# --- Nadi (8) --- pattern Aadi, Madhya, Antya, Antya, Madhya, Aadi repeating
NADI_NAMES = ["Aadi", "Madhya", "Antya"]
def nadi(nak_index0: int) -> int:
    return [0, 1, 2, 2, 1, 0][nak_index0 % 6]


def _relation(a: str, b: str) -> str:
    if a == b or b in FRIENDS[a]:
        return "friend"
    if b in ENEMIES[a]:
        return "enemy"
    return "neutral"


def graha_maitri_score(lord_g: str, lord_b: str) -> float:
    if lord_g == lord_b:
        return 5
    pair = sorted([_relation(lord_g, lord_b), _relation(lord_b, lord_g)])
    return {
        ("friend", "friend"): 5, ("friend", "neutral"): 4, ("neutral", "neutral"): 3,
        ("enemy", "friend"): 1, ("enemy", "neutral"): 0.5, ("enemy", "enemy"): 0,
    }[tuple(pair)]


def _tara_ok(from_nak: int, to_nak: int) -> bool:
    count = (to_nak - from_nak) % 27 + 1
    return count % 9 not in (3, 5, 7)


def ashtakoota(groom_moon: float, bride_moon: float) -> dict:
    gs, bs = sign_index(groom_moon), sign_index(bride_moon)
    gn, bn = nakshatra(groom_moon)["index"] - 1, nakshatra(bride_moon)["index"] - 1

    varna = 1 if VARNA_BY_SIGN[gs] >= VARNA_BY_SIGN[bs] else 0
    vg, vb = vashya_group(groom_moon), vashya_group(bride_moon)
    vashya = VASHYA_TABLE[VASHYA_ORDER.index(vg)][VASHYA_ORDER.index(vb)]
    tara = 1.5 * _tara_ok(bn, gn) + 1.5 * _tara_ok(gn, bn)
    yg, yb = YONI[gn], YONI[bn]
    yoni = 4 if yg == yb else (0 if frozenset((yg, yb)) in YONI_ENEMIES else 2)
    maitri = graha_maitri_score(SIGN_LORDS[gs], SIGN_LORDS[bs])
    gana = GANA_TABLE[GANA[bn]][GANA[gn]]
    dist = (gs - bs) % 12 + 1  # bride -> groom
    bhakoot = 0 if dist in (2, 12, 5, 9, 6, 8) else 7
    nadi_score = 0 if nadi(gn) == nadi(bn) else 8

    kootas = {
        "varna": {"score": varna, "max": 1, "groom": VARNA_NAMES[VARNA_BY_SIGN[gs]], "bride": VARNA_NAMES[VARNA_BY_SIGN[bs]]},
        "vashya": {"score": vashya, "max": 2, "groom": vg, "bride": vb, "simplified": True},
        "tara": {"score": tara, "max": 3},
        "yoni": {"score": yoni, "max": 4, "groom": yg, "bride": yb, "simplified": True},
        "graha_maitri": {"score": maitri, "max": 5, "groom": SIGN_LORDS[gs], "bride": SIGN_LORDS[bs]},
        "gana": {"score": gana, "max": 6, "groom": GANA_NAMES[GANA[gn]], "bride": GANA_NAMES[GANA[bn]]},
        "bhakoot": {"score": bhakoot, "max": 7},
        "nadi": {"score": nadi_score, "max": 8, "groom": NADI_NAMES[nadi(gn)], "bride": NADI_NAMES[nadi(bn)]},
    }
    total = sum(k["score"] for k in kootas.values())
    return {"total": total, "max": 36, "kootas": kootas,
            "verdict": "acceptable (18+)" if total >= 18 else "below 18",
            "doshas": {"nadi_dosha": nadi_score == 0, "bhakoot_dosha": bhakoot == 0},
            "note": "Dosha cancellations not applied. Vashya and Yoni use simplified scoring."}
