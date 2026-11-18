"""Life-area reports (career, marriage, wealth, children, property, foreign, education, health,
parents, siblings) following PVR's lessons: every area is judged from its house in the Rashi
chart, the same house in its divisional chart, its arudha, its karaka, and timed by dashas.

Area -> (house, divisional chart, natural karaka, chara karaka) per Lessons 6, 13, 16-20, 24-27, 42.
"""
from __future__ import annotations

from datetime import datetime

from . import i18n
from .chart import varga_sign
from .constants import SIGN_LORDS, SIGNS
from .jaimini import arudha_of_sign, chara_karakas, lord_of_sign
from .rules.engine import ASPECTS, NATURAL_BENEFICS

AREA_DEF = {
    "career":    {"house": 10, "varga": 10, "karaka": "Saturn",  "chara": "AmK", "en": "Career & profession", "hi": "करियर और व्यवसाय"},
    "marriage":  {"house": 7,  "varga": 9,  "karaka": "Venus",   "chara": "DK",  "en": "Marriage & spouse", "hi": "विवाह और जीवनसाथी"},
    "wealth":    {"house": 2,  "varga": 2,  "karaka": "Jupiter", "chara": None,  "en": "Wealth & finances", "hi": "धन और वित्त"},
    "gains":     {"house": 11, "varga": 2,  "karaka": "Jupiter", "chara": None,  "en": "Income & gains", "hi": "आय और लाभ"},
    "children":  {"house": 5,  "varga": 7,  "karaka": "Jupiter", "chara": "PK",  "en": "Children", "hi": "संतान"},
    "property":  {"house": 4,  "varga": 4,  "karaka": "Mars",    "chara": "MK",  "en": "Home, property & vehicles", "hi": "घर, संपत्ति और वाहन"},
    "education": {"house": 4,  "varga": 24, "karaka": "Mercury", "chara": "MK",  "en": "Education & learning", "hi": "शिक्षा और ज्ञान"},
    "foreign":   {"house": 12, "varga": 4,  "karaka": "Rahu",    "chara": None,  "en": "Foreign travel & settlement", "hi": "विदेश यात्रा और निवास"},
    "health":    {"house": 1,  "varga": 6,  "karaka": "Sun",     "chara": "GK",  "en": "Health & vitality", "hi": "स्वास्थ्य"},
    "parents":   {"house": 9,  "varga": 12, "karaka": "Sun",     "chara": "PiK", "en": "Parents", "hi": "माता-पिता"},
    "siblings":  {"house": 3,  "varga": 3,  "karaka": "Mars",    "chara": "BK",  "en": "Siblings", "hi": "भाई-बहन"},
}

DIGNITY_SCORE = {"exalted": 2, "moolatrikona": 1.5, "own": 1.5, "friend": 0.5, "neutral": 0, "enemy": -1, "debilitated": -2, "n/a": 0}


def _aspecting(planets: dict, target_sign: int) -> list[str]:
    out = []
    for p, v in planets.items():
        s = v["sign_index"] - 1
        dist = (target_sign - s) % 12 + 1
        if dist in ASPECTS.get(p, {7}) and s != target_sign:
            out.append(p)
    return out


def analyse_area(chart: dict, dasha: dict, area: str, lang: str = "en", now: datetime | None = None) -> dict:
    A = AREA_DEF[area]
    hi = lang == "hi"
    T = lambda x: i18n.term(lang, x)
    P = chart["planets"]
    lagna = chart["lagna"]["sign_index"] - 1
    h = A["house"]
    sign = (lagna + h - 1) % 12
    lord = SIGN_LORDS[sign]
    lord_v = P[lord]
    occupants = [p for p, v in P.items() if v["house"] == h]
    aspects = _aspecting(P, sign)
    score = 0.0
    points = []

    def pt(w, en, hi_txt):
        nonlocal score
        score += w
        points.append({"weight": w, "text": hi_txt if hi else en})

    # 1. house lord
    ds = DIGNITY_SCORE.get(lord_v.get("dignity", "n/a"), 0)
    pt(ds, f"House {h} lord {lord} is {lord_v.get('dignity')} in house {lord_v['house']}",
       f"भाव {h} का स्वामी {T(lord)} भाव {lord_v['house']} में {T(lord_v.get('dignity', ''))} है")
    if lord_v["house"] in (6, 8, 12) and h not in (6, 8, 12):
        pt(-1.5, f"…but placed in a dusthana ({lord_v['house']}), which strains this area",
           f"…परंतु दुःस्थान ({lord_v['house']}) में होने से इस क्षेत्र पर दबाव")
    elif lord_v["house"] in (1, 4, 5, 7, 9, 10):
        pt(1, f"…placed in a kendra/trikona ({lord_v['house']}), supportive",
           f"…केंद्र/त्रिकोण ({lord_v['house']}) में, सहायक")
    # 2. occupants & aspects
    for p in occupants:
        good = p in NATURAL_BENEFICS
        pt(1 if good else -0.7, f"{p} occupies house {h} ({'benefic' if good else 'malefic'} influence)",
           f"{T(p)} भाव {h} में ({'शुभ' if good else 'पाप'} प्रभाव)")
    for p in aspects:
        good = p in NATURAL_BENEFICS
        pt(0.5 if good else -0.4, f"{p} aspects house {h}", f"{T(p)} की भाव {h} पर दृष्टि")
    # 3. karaka
    k = A["karaka"]
    kd = DIGNITY_SCORE.get(P[k].get("dignity", "n/a"), 0)
    pt(kd * 0.5, f"Natural karaka {k} is {P[k].get('dignity')} in house {P[k]['house']}",
       f"नैसर्गिक कारक {T(k)} भाव {P[k]['house']} में {T(P[k].get('dignity', ''))}")
    ck = None
    if A["chara"]:
        ck = chara_karakas(P)[A["chara"]]
        ckd = DIGNITY_SCORE.get(P[ck].get("dignity", "n/a"), 0)
        pt(ckd * 0.5, f"Chara karaka {A['chara']} is {ck}, {P[ck].get('dignity')} in house {P[ck]['house']}",
           f"चर कारक {A['chara']}: {T(ck)}, भाव {P[ck]['house']} में")
    # 4. divisional chart
    D = A["varga"]
    vl = SIGNS.index(chart["vargas"][f"D{D}"]["lagna"])
    vs = (vl + h - 1) % 12
    vlord = SIGN_LORDS[vs]
    vlord_sign = SIGNS.index(chart["vargas"][f"D{D}"]["planets"][vlord])
    vlord_house = (vlord_sign - vl) % 12 + 1
    vocc = [p for p, s in chart["vargas"][f"D{D}"]["planets"].items() if SIGNS.index(s) == vs]
    w = 1 if vlord_house in (1, 4, 5, 7, 9, 10, 11) else (-1 if vlord_house in (6, 8, 12) else 0)
    pt(w, f"In D{D}, house {h} lord {vlord} sits in house {vlord_house}",
       f"D{D} में भाव {h} का स्वामी {T(vlord)} भाव {vlord_house} में")
    for p in vocc:
        pt(0.5 if p in NATURAL_BENEFICS else -0.4, f"In D{D}, {p} occupies house {h}", f"D{D} में {T(p)} भाव {h} में")
    # 5. arudha
    ar = arudha_of_sign(P, sign)
    ar_occ = [p for p, v in P.items() if v["sign_index"] - 1 == ar]
    ar_house = (ar - lagna) % 12 + 1
    if ar_occ:
        good = [p for p in ar_occ if p in NATURAL_BENEFICS]
        pt(0.5 * len(good) - 0.4 * (len(ar_occ) - len(good)),
           f"Arudha of house {h} falls in house {ar_house} ({SIGNS[ar]}) with {ar_occ} – the visible face of this area",
           f"भाव {h} का आरूढ़ भाव {ar_house} ({T(SIGNS[ar])}) में, साथ में {', '.join(T(x) for x in ar_occ)} – इस क्षेत्र का दृश्य रूप")
    # 6. timing: dasha periods (next 15 years) whose lords connect with the house
    connected = {lord, vlord, k} | set(occupants) | ({ck} if ck else set())
    now_iso = (now or datetime.now()).isoformat()
    windows = []
    for md in dasha["mahadashas"]:
        for ad in md.get("sub", []):
            if ad["end"] < now_iso or len(windows) >= 6:
                continue
            if ad["lord"] in connected or md["lord"] in connected and ad["lord"] in connected | {lord}:
                windows.append({"md": md["lord"], "ad": ad["lord"], "start": ad["start"][:10], "end": ad["end"][:10]})
    verdict = "strong" if score >= 2.5 else ("moderate" if score >= 0 else "needs care")
    verdict_hi = {"strong": "मज़बूत", "moderate": "मध्यम", "needs care": "सावधानी आवश्यक"}[verdict]
    return {
        "area": area, "title": A["hi"] if hi else A["en"], "house": h, "sign": SIGNS[sign], "lord": lord,
        "varga": f"D{D}", "karaka": k, "chara_karaka": ck, "score": round(score, 1),
        "verdict": verdict_hi if hi else verdict, "verdict_key": verdict,
        "points": points, "periods": windows,
        "source": "PVR Narasimha Rao, Lessons on Vedic Astrology (houses, vargas, arudhas, karakas); BPHS",
    }


def all_areas(chart, dasha, lang="en", now=None):
    return [analyse_area(chart, dasha, a, lang, now) for a in AREA_DEF]
