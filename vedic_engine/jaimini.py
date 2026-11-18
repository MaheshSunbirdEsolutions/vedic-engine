"""PVR / Jaimini tools from 'Lessons on Vedic Astrology' (P.V.R. Narasimha Rao):
chara karakas, arudha padas, argala, and the 3rd/6th-from-AL attitude reading.

Conventions follow the lessons:
* 8 chara karakas including Rahu; Rahu's degree is counted as 30 - degree (Lesson 14).
* Arudha: count from the house to its lord, then the same count from the lord.
  If the result falls in the 1st or 7th from the house, take the 10th from it (Lesson 9).
* Dual lordship of Scorpio (Mars/Ketu) and Aquarius (Saturn/Rahu): use the stronger lord.
* Argala from the 2nd, 4th, 11th (and 5th), obstructed by the 12th, 10th, 3rd (and 9th);
  counting is reversed for Ketu (Lesson 9).
"""
from __future__ import annotations

from .constants import EXALTATION, SIGN_LORDS, SIGNS

KARAKA_NAMES = ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"]
KARAKA_MEANING = {
    "AK": "Atmakaraka – the soul, the chart's king", "AmK": "Amatyakaraka – career, advisers",
    "BK": "Bhratrikaraka – siblings, guru", "MK": "Matrikaraka – mother, education",
    "PiK": "Pitrikaraka – father", "PK": "Putrakaraka – children, creativity",
    "GK": "Gnatikaraka – rivals, obstacles, disease", "DK": "Darakaraka – spouse",
}


def chara_karakas(planets: dict) -> dict[str, str]:
    """planets: {name: {"longitude": deg}} -> {"AK": planet, ...} (8-karaka scheme)."""
    scores = []
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"):
        d = planets[p]["longitude"] % 30
        scores.append((30 - d if p == "Rahu" else d, p))
    scores.sort(reverse=True)
    return {KARAKA_NAMES[i]: p for i, (_, p) in enumerate(scores)}


def _sign(planets, p):
    return int(planets[p]["longitude"] // 30) % 12


def _occupants(planets, sign):
    return [p for p in planets if _sign(planets, p) == sign]


def lord_of_sign(planets: dict, sign: int) -> str:
    """Lord of a sign; for Scorpio/Aquarius pick the stronger co-lord (Jaimini rules)."""
    if sign == 7:
        a, b = "Mars", "Ketu"
    elif sign == 10:
        a, b = "Saturn", "Rahu"
    else:
        return SIGN_LORDS[sign]
    sa, sb = _sign(planets, a), _sign(planets, b)
    # 1. if one lord sits in the sign itself and the other outside, the other is stronger
    if sa == sign and sb != sign:
        return b
    if sb == sign and sa != sign:
        return a
    # 2. the one conjoined with more planets
    na, nb = len(_occupants(planets, sa)), len(_occupants(planets, sb))
    if na != nb:
        return a if na > nb else b
    # 3. exalted
    ex = {p: (p in EXALTATION and EXALTATION[p][0] == _sign(planets, p)) for p in (a, b)}
    if ex[a] != ex[b]:
        return a if ex[a] else b
    # 4. higher degree in sign
    return a if planets[a]["longitude"] % 30 >= planets[b]["longitude"] % 30 else b


def arudha_of_sign(planets: dict, sign: int) -> int:
    lord = lord_of_sign(planets, sign)
    ls = _sign(planets, lord)
    n = (ls - sign) % 12            # steps from house to lord
    ar = (ls + n) % 12              # same steps from lord
    if ar in (sign, (sign + 6) % 12):
        ar = (ar + 9) % 12          # 10th from the computed arudha
    return ar


def arudha_padas(planets: dict, lagna_sign: int) -> dict[str, int]:
    """A1 (AL) ... A12 (UL) as sign indices."""
    out = {}
    for h in range(1, 13):
        out["AL" if h == 1 else ("UL" if h == 12 else f"A{h}")] = arudha_of_sign(planets, (lagna_sign + h - 1) % 12)
    return out


def argala(planets: dict, ref_sign: int) -> dict:
    """Primary argala on a reference sign and what obstructs it."""
    pairs = {2: 12, 4: 10, 11: 3, 5: 9}
    res = {}
    for a, v in pairs.items():
        def occ(n):
            out = []
            for p in planets:
                if p == "Ketu":     # reverse count for Ketu
                    d = (ref_sign - _sign(planets, p)) % 12 + 1
                else:
                    d = (_sign(planets, p) - ref_sign) % 12 + 1
                if d == n:
                    out.append(p)
            return out
        ag, ob = occ(a), occ(v)
        if ag or ob:
            res[a] = {"argala": ag, "obstruction": ob,
                      "effective": len(ag) > len(ob) or (bool(ag) and not ob)}
    return res


BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}


def al_attitude(planets: dict, al_sign: int) -> dict:
    """Lesson 9: malefics/benefics in the 3rd and 6th from AL (initiative vs follow-through)."""
    def kind(n):
        occ = [p for p in planets if (_sign(planets, p) - al_sign) % 12 + 1 == n]
        if not occ:
            return "empty", occ
        mal = [p for p in occ if p not in BENEFICS]
        return ("malefic" if mal else "benefic"), occ
    k3, o3 = kind(3)
    k6, o6 = kind(6)
    m3, m6 = k3 == "malefic", k6 == "malefic"
    if m3 and m6:
        key = "high_initiative_completes"
    elif m3 and not m6:
        key = "initiative_without_execution"
    elif not m3 and m6:
        key = "slow_start_but_finishes"
    else:
        key = "gentle_saintly"
    return {"third": {"kind": k3, "planets": o3}, "sixth": {"kind": k6, "planets": o6}, "pattern": key}


def summary(chart: dict) -> dict:
    planets = chart["planets"]
    lagna = chart["lagna"]["sign_index"] - 1
    ak = chara_karakas(planets)
    ar = arudha_padas(planets, lagna)
    return {
        "karakas": {k: {"planet": v, "meaning": KARAKA_MEANING[k]} for k, v in ak.items()},
        "arudhas": {k: SIGNS[v] for k, v in ar.items()},
        "arudha_houses": {k: (v - lagna) % 12 + 1 for k, v in ar.items()},
        "argala_on_lagna": argala(planets, lagna),
        "argala_on_al": argala(planets, ar["AL"]),
        "al_attitude": al_attitude(planets, ar["AL"]),
    }
