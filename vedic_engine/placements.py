"""Plain-language explanation of where each planet sits: bhav (house) with its name and meaning,
sign and dignity, houses it rules, nakshatra, conjunctions (yuti), aspects (drishti) given and
received, combustion / retrogression, and its functional nature for the ascendant.

Used by every report so a reader sees *why* a planet matters before reading its remedies.
House significations follow BPHS / PVR Lessons on Vedic Astrology (Lesson 3, houses).
"""
from __future__ import annotations

from . import i18n
from .constants import SIGN_LORDS, SIGNS
from .rules.engine import ASPECTS

BHAV = {  # house: (sanskrit name, hindi name, english meaning, hindi meaning)
    1: ("Tanu", "तनु भाव", "self, body, health, personality, overall direction of life",
        "स्वयं, शरीर, स्वास्थ्य, व्यक्तित्व, जीवन की दिशा"),
    2: ("Dhana", "धन भाव", "wealth, savings, family, speech, food, early education",
        "धन, संचय, कुटुंब, वाणी, भोजन, प्रारंभिक शिक्षा"),
    3: ("Sahaja", "सहज/पराक्रम भाव", "courage, effort, younger siblings, communication, short travel, skills with the hands",
        "साहस, पराक्रम, छोटे भाई-बहन, संवाद, छोटी यात्राएँ, हस्त-कौशल"),
    4: ("Sukha", "सुख भाव", "mother, home, property, vehicles, inner peace, schooling",
        "माता, घर, भूमि-भवन, वाहन, मन की शांति, शिक्षा"),
    5: ("Putra", "पुत्र/विद्या भाव", "children, intelligence, learning, mantra, creativity, past-life merit, speculation",
        "संतान, बुद्धि, विद्या, मंत्र, रचनात्मकता, पूर्व पुण्य, सट्टा"),
    6: ("Ripu", "रिपु/शत्रु भाव", "enemies, disease, debts, disputes, litigation, service, daily work",
        "शत्रु, रोग, ऋण, विवाद, मुकदमे, सेवा, दैनिक कार्य"),
    7: ("Kalatra", "कलत्र/जाया भाव", "marriage, spouse, partnerships, business dealings, public",
        "विवाह, जीवनसाथी, साझेदारी, व्यापारिक लेन-देन, जनता"),
    8: ("Ayu", "आयु/रंध्र भाव", "longevity, sudden events, hidden matters, inheritance, research, chronic illness, the occult",
        "आयु, अचानक घटनाएँ, गुप्त बातें, विरासत, शोध, दीर्घ रोग, गूढ़ विद्या"),
    9: ("Dharma", "धर्म/भाग्य भाव", "fortune, father, guru, dharma, higher learning, long journeys, blessings",
        "भाग्य, पिता, गुरु, धर्म, उच्च शिक्षा, लंबी यात्राएँ, आशीर्वाद"),
    10: ("Karma", "कर्म भाव", "career, status, authority, actions in the world, reputation",
         "कर्म, व्यवसाय, पद-प्रतिष्ठा, अधिकार, समाज में कार्य"),
    11: ("Labha", "लाभ भाव", "gains, income, fulfilment of desires, elder siblings, friends, networks",
         "लाभ, आय, इच्छापूर्ति, बड़े भाई-बहन, मित्र, संपर्क"),
    12: ("Vyaya", "व्यय भाव", "expenses, losses, sleep, foreign lands, hospitals, isolation, moksha",
         "व्यय, हानि, निद्रा, विदेश, अस्पताल, एकांत, मोक्ष"),
}
HOUSE_GROUP = {  # (en, hi)
    "kendra": ("a kendra (angle: 1/4/7/10) – planets here act strongly and visibly",
               "केंद्र (1/4/7/10) – यहाँ ग्रह प्रबल और प्रत्यक्ष फल देते हैं"),
    "trikona": ("a trikona (trine: 1/5/9) – the most auspicious houses, of merit and luck",
                "त्रिकोण (1/5/9) – सबसे शुभ भाव, पुण्य व भाग्य के"),
    "dusthana": ("a dusthana (6/8/12) – houses of struggle; planets here face obstacles or turn their energy to fighting problems",
                 "दुःस्थान (6/8/12) – संघर्ष के भाव; यहाँ ग्रह बाधा पाते हैं या समस्याओं से लड़ते हैं"),
    "upachaya": ("an upachaya (3/6/10/11) – houses of growth; malefics improve here with time and effort",
                 "उपचय (3/6/10/11) – वृद्धि के भाव; पाप ग्रह यहाँ समय व प्रयास से सुधरते हैं"),
    "maraka": ("a maraka house (2/7) – houses that can bring health strain in difficult periods",
               "मारक भाव (2/7) – कठिन दशा में स्वास्थ्य पर दबाव ला सकते हैं"),
}
DIGNITY = {
    "exalted": ("exalted – at its strongest, gives its best results", "उच्च – सबसे बलवान, श्रेष्ठ फल देता है"),
    "moolatrikona": ("in moolatrikona – very strong, works like an office-holder", "मूलत्रिकोण में – बहुत बलवान"),
    "own": ("in its own sign – comfortable and strong", "स्वराशि में – सहज और बलवान"),
    "friend": ("in a friend's sign – supported, gives fair results", "मित्र राशि में – सहयोग मिलता है, अच्छा फल"),
    "neutral": ("in a neutral sign – average results", "सम राशि में – सामान्य फल"),
    "enemy": ("in an enemy's sign – uncomfortable, results come with friction", "शत्रु राशि में – असहज, फल में रुकावट"),
    "debilitated": ("debilitated – at its weakest; its themes need conscious effort and remedies",
                    "नीच – सबसे दुर्बल; इसके विषयों में प्रयास व उपाय आवश्यक"),
}
NATURE = {
    "yogakaraka": ("yogakaraka (rules both an angle and a trine) – the best planet for this ascendant",
                   "योगकारक (केंद्र व त्रिकोण दोनों का स्वामी) – इस लग्न के लिए सर्वश्रेष्ठ ग्रह"),
    "benefic": ("a functional benefic for this ascendant", "इस लग्न के लिए कार्यात्मक शुभ"),
    "mixed": ("mixed for this ascendant (rules good and difficult houses)", "इस लग्न के लिए मिश्रित (शुभ व कठिन भावों का स्वामी)"),
    "malefic": ("a functional malefic for this ascendant (rules 3/6/8/11)", "इस लग्न के लिए कार्यात्मक अशुभ (3/6/8/11 का स्वामी)"),
    "maraka": ("a maraka for this ascendant (rules 2/7)", "इस लग्न के लिए मारक (2/7 का स्वामी)"),
    "neutral": ("neutral for this ascendant", "इस लग्न के लिए सम"),
    "shadow": ("a shadow planet – gives the results of its sign lord and companions",
               "छाया ग्रह – अपनी राशि के स्वामी व साथी ग्रहों जैसा फल देता है"),
}
COMBUST_ORB = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}
ORD = {1: "1st", 2: "2nd", 3: "3rd"}


HI_ORD = {1: "पहले", 2: "दूसरे", 3: "तीसरे", 4: "चौथे", 5: "पाँचवें", 6: "छठे", 7: "सातवें", 8: "आठवें", 9: "नौवें", 10: "दसवें", 11: "ग्यारहवें", 12: "बारहवें"}


def ord_hi(n: int) -> str:
    return HI_ORD.get(n, f"{n}वें")


def ordinal(n: int) -> str:
    return ORD.get(n, f"{n}th")


def functional_nature(planet: str, lagna: int) -> str:
    """Laghu Parashari functional nature for a lagna (simplified)."""
    if planet in ("Rahu", "Ketu"):
        return "shadow"
    owned = owned_houses(planet, lagna)
    if any(h in (4, 7, 10) for h in owned) and any(h in (5, 9) for h in owned):
        return "yogakaraka"
    if 1 in owned:
        return "benefic"
    if any(h in (5, 9) for h in owned):
        return "benefic" if not any(h in (6, 8, 11, 3) for h in owned) else "mixed"
    if any(h in (3, 6, 11, 8) for h in owned):
        return "malefic"
    if any(h in (2, 7) for h in owned):
        return "maraka"
    return "neutral"


def owned_houses(planet: str, lagna: int) -> list[int]:
    return [h for h in range(1, 13) if SIGN_LORDS[(lagna + h - 1) % 12] == planet]


def _groups(h: int) -> list[str]:
    g = []
    if h in (1, 4, 7, 10):
        g.append("kendra")
    if h in (1, 5, 9):
        g.append("trikona")
    if h in (6, 8, 12):
        g.append("dusthana")
    if h in (3, 6, 10, 11):
        g.append("upachaya")
    if h in (2, 7):
        g.append("maraka")
    return g


def _sep(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def house_info(h: int, lang: str = "en") -> dict:
    sa, hi_name, en, hi = BHAV[h]
    return {"house": h, "name": hi_name if lang == "hi" else f"{sa} bhav", "meaning": hi if lang == "hi" else en}


def strength(v: dict, combust: bool) -> str:
    """Rough tag for the UI: strong / average / weak."""
    dig = v.get("dignity")
    s = {"exalted": 2, "moolatrikona": 2, "own": 1.5, "friend": 0.5, "neutral": 0, "enemy": -1,
         "debilitated": -2}.get(dig, 0)
    s += {1: 1, 4: 0.5, 5: 1, 7: 0.5, 9: 1, 10: 1, 11: 0.5, 6: -0.5, 8: -1, 12: -1}.get(v["house"], 0)
    if combust:
        s -= 1
    return "strong" if s >= 1.5 else ("weak" if s <= -1 else "average")


def explain(chart: dict, planet: str, lang: str = "en") -> dict:
    P = chart["planets"]
    v = P[planet]
    lagna = chart["lagna"]["sign_index"] - 1
    hi = lang == "hi"
    T = lambda x: i18n.term(lang, x)  # noqa: E731
    h = v["house"]
    sign_i = v["sign_index"] - 1
    owned = owned_houses(planet, lagna)
    nature = functional_nature(planet, lagna)
    with_ = [p for p, w in P.items() if p != planet and w["sign_index"] == v["sign_index"]]
    asp_set = ASPECTS.get(planet, {7}) if planet not in ("Sun", "Moon", "Mercury", "Venus") else {7}
    aspects_houses = sorted(((h - 1 + n - 1) % 12) + 1 for n in asp_set)
    aspected_by = []
    for p, w in P.items():
        if p == planet:
            continue
        a_set = ASPECTS.get(p, {7})
        if any(((w["sign_index"] - 1 + n - 1) % 12) == sign_i for n in a_set):
            aspected_by.append(p)
    combust = planet in COMBUST_ORB and _sep(v["longitude"], P["Sun"]["longitude"]) <= COMBUST_ORB[planet]
    dig = v.get("dignity")
    sa, hname, hmean_en, hmean_hi = BHAV[h]
    groups = _groups(h)

    # ---------- the plain-language paragraph ----------
    if hi:
        parts = [f"{T(planet)} {ord_hi(h)} भाव ({hname}) में {T(v['sign'])} राशि में है। यह भाव {hmean_hi} से जुड़ा है।"]
        if groups:
            parts.append("यह भाव " + "; साथ ही ".join(HOUSE_GROUP[g][1] for g in groups) + "।")
        if dig and dig in DIGNITY:
            parts.append(f"{T(planet)} यहाँ {DIGNITY[dig][1]}।".replace(" – ", " है – ", 1))
        if owned:
            parts.append(f"आपके {T(SIGNS[lagna])} लग्न के लिए यह ग्रह भाव {', '.join(map(str, owned))} का स्वामी है ("
                         + "; ".join(BHAV[o][3].split(',')[0] for o in owned) + "), अतः इन विषयों का फल "
                         + f"{ord_hi(h)} भाव के विषयों से जुड़ता है।")
        parts.append(f"स्वभाव: {NATURE[nature][1]}।")
        if with_:
            parts.append(f"युति: {', '.join(T(x) for x in with_)} के साथ।")
        if aspected_by:
            parts.append(f"दृष्टि पाता है: {', '.join(T(x) for x in aspected_by)}।")
        parts.append(f"इसकी दृष्टि भाव {', '.join(map(str, aspects_houses))} पर।")
        if v.get("retrograde") and planet not in ("Rahu", "Ketu"):
            parts.append("वक्री है – फल भीतर की ओर मुड़ता है, पुराने विषय दोहराए जाते हैं।")
        if combust:
            parts.append("अस्त है – सूर्य के तेज से दबा, इसके कारकत्व कमज़ोर।")
        nk = v["nakshatra"]
        parts.append(f"नक्षत्र {T(nk['name'])} (पाद {nk['pada']}, स्वामी {T(nk['lord'])})।")
    else:
        parts = [f"{planet} is in the {ordinal(h)} house ({sa} bhav) in {v['sign']}. "
                 f"This house covers {hmean_en}."]
        if groups:
            parts.append("It is " + "; also ".join(HOUSE_GROUP[g][0] for g in groups) + ".")
        if dig and dig in DIGNITY:
            parts.append(f"{planet} is {DIGNITY[dig][0]}.")
        if owned:
            parts.append(f"For your {SIGNS[lagna]} ascendant it rules house{'s' if len(owned) > 1 else ''} "
                         f"{' & '.join(map(str, owned))} ("
                         + "; ".join(BHAV[o][2].split(',')[0] for o in owned)
                         + f"), so those matters are carried into the {ordinal(h)} house.")
        parts.append(f"It is {NATURE[nature][0]}.")
        if with_:
            parts.append(f"Conjunct (yuti) with {', '.join(with_)}.")
        if aspected_by:
            parts.append(f"Aspected by {', '.join(aspected_by)}.")
        parts.append(f"It aspects house{'s' if len(aspects_houses) > 1 else ''} {', '.join(map(str, aspects_houses))}.")
        if v.get("retrograde") and planet not in ("Rahu", "Ketu"):
            parts.append("Retrograde – its results turn inward and old matters return for review.")
        if combust:
            parts.append("Combust – overpowered by the Sun, so its significations are weakened.")
        nk = v["nakshatra"]
        parts.append(f"Nakshatra {nk['name']} (pada {nk['pada']}, ruled by {nk['lord']}).")

    return {
        "planet": planet, "house": h, "bhav": hname if hi else f"{sa} bhav",
        "house_meaning": hmean_hi if hi else hmean_en, "sign": v["sign"], "degree": v["degree_in_sign"],
        "dignity": dig, "owns": owned, "owns_meaning": [house_info(o, lang) for o in owned],
        "nature": nature, "with": with_, "aspected_by": aspected_by, "aspects": aspects_houses,
        "retrograde": bool(v.get("retrograde")) and planet not in ("Rahu", "Ketu"), "combust": combust,
        "nakshatra": v["nakshatra"], "groups": groups, "strength": strength(v, combust),
        "text": " ".join(parts),
    }


def all_planets(chart: dict, lang: str = "en") -> list[dict]:
    return [explain(chart, p, lang) for p in chart["planets"]]


def houses(chart: dict, lang: str = "en") -> list[dict]:
    """Bhav-by-bhav table: sign on the cusp, its lord and where that lord sits, occupants."""
    P = chart["planets"]
    lagna = chart["lagna"]["sign_index"] - 1
    out = []
    for h in range(1, 13):
        s = (lagna + h - 1) % 12
        lord = SIGN_LORDS[s]
        out.append({**house_info(h, lang), "sign": SIGNS[s], "lord": lord, "lord_in": P[lord]["house"],
                    "occupants": [p for p, v in P.items() if v["house"] == h]})
    return out
