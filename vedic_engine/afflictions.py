"""'What's wrong' summary: afflicted positions, harmful yutis (conjunctions) and doshas,
each with a severity (1 mild … 3 strong), the houses / life areas it touches, and remedy tags.

Definitions are the common Parashari / popular ones; cancellation rules are only partly
applied (noted per item), so wording stays tentative.
"""
from __future__ import annotations

from .constants import ENEMIES, SIGN_LORDS, SIGNS
from .rules.engine import NATURAL_BENEFICS

# Combustion orbs from the Sun (degrees); (direct, retrograde)
COMBUST_ORB = {"Moon": (12, 12), "Mars": (17, 17), "Mercury": (14, 12), "Jupiter": (11, 11),
               "Venus": (10, 8), "Saturn": (15, 15)}

HOUSE_AREAS = {
    1: ["health", "self"], 2: ["finance", "family"], 3: ["courage", "siblings"], 4: ["home", "mind", "mother"],
    5: ["children", "education"], 6: ["health", "enemies", "debts"], 7: ["marriage", "partnership"],
    8: ["health", "sudden_events"], 9: ["fortune", "father"], 10: ["career"], 11: ["finance", "gains"],
    12: ["expenses", "sleep", "foreign"],
}
PLANET_AREAS = {
    "Sun": ["self", "father", "career"], "Moon": ["mind", "mother"], "Mars": ["courage", "siblings", "property"],
    "Mercury": ["education", "business"], "Jupiter": ["fortune", "children", "wisdom"],
    "Venus": ["marriage", "comforts"], "Saturn": ["career", "delays"], "Rahu": ["confusion", "foreign"],
    "Ketu": ["detachment", "spiritual"],
}

YUTI_RULES = [  # (id, planets, severity, remedy tags)
    ("guru_chandal", ("Jupiter", "Rahu"), 3, ["jupiter", "rahu"]),
    ("guru_ketu", ("Jupiter", "Ketu"), 1, ["jupiter", "ketu"]),
    ("surya_grahan", ("Sun", "Rahu"), 3, ["sun", "rahu"]),
    ("surya_ketu", ("Sun", "Ketu"), 2, ["sun", "ketu"]),
    ("chandra_grahan", ("Moon", "Rahu"), 3, ["moon", "rahu"]),
    ("chandra_ketu", ("Moon", "Ketu"), 2, ["moon", "ketu"]),
    ("angarak", ("Mars", "Rahu"), 3, ["mars", "rahu"]),
    ("shrapit", ("Saturn", "Rahu"), 3, ["saturn", "rahu"]),
    ("vish", ("Moon", "Saturn"), 2, ["moon", "saturn"]),
    ("surya_shani", ("Sun", "Saturn"), 2, ["sun", "saturn"]),
    ("mangal_shani", ("Mars", "Saturn"), 2, ["mars", "saturn"]),
    ("shukra_rahu", ("Venus", "Rahu"), 1, ["venus", "rahu"]),
]


def _sep(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def analyse(chart: dict, extra_flags: dict | None = None) -> list[dict]:
    P = chart["planets"]
    lagna = chart["lagna"]["sign_index"] - 1
    sun = P["Sun"]["longitude"]
    out: list[dict] = []

    def house_lords(planet):
        return [h for h in range(1, 13) if SIGN_LORDS[(lagna + h - 1) % 12] == planet]

    def add(id_, cat, planets, severity, houses, tags, data=None):
        areas = sorted({a for h in houses for a in HOUSE_AREAS[h]} |
                       {a for p in planets for a in PLANET_AREAS.get(p, [])})
        out.append({"id": id_, "category": cat, "planets": list(planets), "severity": severity,
                    "houses": sorted(set(houses)), "areas": areas, "remedy_tags": tags, "data": data or {}})

    for p, v in P.items():
        h, dig, lon = v["house"], v.get("dignity"), v["longitude"]
        involved_houses = [h] + house_lords(p)
        if dig == "debilitated":
            add("debilitated", "position", [p], 3, involved_houses, [p.lower()])
        if dig == "enemy":
            add("enemy_sign", "position", [p], 1, involved_houses, [p.lower()])
        if p in COMBUST_ORB:
            orb = COMBUST_ORB[p][1 if v.get("retrograde") else 0]
            if _sep(lon, sun) <= orb:
                add("combust", "position", [p], 2, involved_houses, [p.lower(), "sun"],
                    {"distance": round(_sep(lon, sun), 2)})
        if h in (6, 8, 12) and (p in NATURAL_BENEFICS or 1 in house_lords(p)):
            add("dusthana", "position", [p], 1, involved_houses, [p.lower()], {"house": h})

    ll = SIGN_LORDS[lagna]
    if P[ll]["house"] in (6, 8, 12):
        add("lagna_lord_dusthana", "position", [ll], 2, [1, P[ll]["house"]], [ll.lower()],
            {"house": P[ll]["house"]})

    # Gandanta: water-fire sign junctions (last / first 3°20')
    for name, lon in [("Moon", P["Moon"]["longitude"]), ("Lagna", chart["lagna"]["longitude"])]:
        s, d = int(lon // 30), lon % 30
        if (s in (3, 7, 11) and d >= 30 - 10 / 3) or (s in (0, 4, 8) and d < 10 / 3):
            add("gandanta", "position", [name] if name != "Lagna" else [], 2,
                [1] if name == "Lagna" else [P["Moon"]["house"]], ["moon" if name == "Moon" else "lagna", "ketu"],
                {"point": name})

    # Weak Moon (near new moon)
    if _sep(P["Moon"]["longitude"], sun) < 72:
        add("weak_moon", "position", ["Moon"], 1, [P["Moon"]["house"]], ["moon"],
            {"distance_from_sun": round(_sep(P["Moon"]["longitude"], sun), 1)})

    # Graha yuddha (planetary war): two of Mars..Saturn within 1°
    war = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    for i, a in enumerate(war):
        for b in war[i + 1:]:
            if _sep(P[a]["longitude"], P[b]["longitude"]) < 1:
                add("graha_yuddha", "position", [a, b], 2, [P[a]["house"]], [a.lower(), b.lower()])

    # Yutis (same sign)
    for id_, pair, sev, tags in YUTI_RULES:
        a, b = pair
        if P[a]["sign_index"] == P[b]["sign_index"]:
            close = _sep(P[a]["longitude"], P[b]["longitude"])
            add(id_, "yuti", list(pair), sev + (1 if close < 5 and sev < 3 else 0),
                [P[a]["house"]] + house_lords(a) + house_lords(b), tags, {"orb": round(close, 1)})

    # Doshas
    flags = dict(extra_flags or {})
    if flags.get("manglik"):
        add("manglik", "dosha", ["Mars"], 2, [P["Mars"]["house"], 7], ["mars", "manglik"])
    if flags.get("kaal_sarp"):
        add("kaal_sarp", "dosha", ["Rahu", "Ketu"], 2, [P["Rahu"]["house"], P["Ketu"]["house"]],
            ["rahu", "ketu", "kaal_sarp"])
    ninth = (lagna + 8) % 12
    pitra = (P["Rahu"]["sign_index"] - 1 == ninth or P["Sun"]["sign_index"] == P["Rahu"]["sign_index"]
             or P["Sun"]["sign_index"] == P["Saturn"]["sign_index"] and P["Sun"]["house"] == 9)
    if pitra:
        add("pitra", "dosha", ["Sun", "Rahu"], 2, [9], ["sun", "rahu", "pitra"])
    moon_s = P["Moon"]["sign_index"] - 1
    around = [p for p, v in P.items() if p not in ("Moon", "Sun", "Rahu", "Ketu")
              and (v["sign_index"] - 1) in ((moon_s + 1) % 12, (moon_s - 1) % 12, moon_s)]
    kendra_from_lagna = [p for p, v in P.items() if p not in ("Sun", "Rahu", "Ketu", "Moon") and v["house"] in (1, 4, 7, 10)]
    if not around and not kendra_from_lagna:
        add("kemadruma", "dosha", ["Moon"], 2, [P["Moon"]["house"]], ["moon", "kemadruma"])

    order = {"dosha": 0, "yuti": 1, "position": 2}
    out.sort(key=lambda x: (-x["severity"], order[x["category"]]))
    return out


TEXT = {
    "debilitated": ("{p} is debilitated", "{p} नीच राशि में है"),
    "enemy_sign": ("{p} is in an enemy's sign", "{p} शत्रु राशि में है"),
    "combust": ("{p} is combust (too close to the Sun)", "{p} अस्त है (सूर्य के बहुत निकट)"),
    "dusthana": ("{p} sits in a dusthana (6th/8th/12th house)", "{p} दुःस्थान (6/8/12 भाव) में है"),
    "lagna_lord_dusthana": ("Ascendant lord {p} is in a dusthana", "लग्नेश {p} दुःस्थान में है"),
    "gandanta": ("Gandanta: a sensitive water–fire sign junction", "गण्डान्त: जल-अग्नि राशि की संधि"),
    "weak_moon": ("The Moon is weak (close to the Sun)", "चंद्रमा क्षीण है (सूर्य के निकट)"),
    "graha_yuddha": ("Planetary war between {p}", "{p} के बीच ग्रह युद्ध"),
    "guru_chandal": ("Guru-Chandal yoga ({p})", "गुरु-चांडाल योग ({p})"),
    "guru_ketu": ("Jupiter with Ketu", "गुरु-केतु युति"),
    "surya_grahan": ("Grahan dosha: Sun with Rahu", "ग्रहण दोष: सूर्य-राहु युति"),
    "surya_ketu": ("Sun with Ketu (partial grahan)", "सूर्य-केतु युति (आंशिक ग्रहण)"),
    "chandra_grahan": ("Grahan dosha: Moon with Rahu", "ग्रहण दोष: चंद्र-राहु युति"),
    "chandra_ketu": ("Moon with Ketu (partial grahan)", "चंद्र-केतु युति (आंशिक ग्रहण)"),
    "angarak": ("Angarak yoga: Mars with Rahu", "अंगारक योग: मंगल-राहु युति"),
    "shrapit": ("Shrapit yoga: Saturn with Rahu", "शापित योग: शनि-राहु युति"),
    "vish": ("Vish yoga: Moon with Saturn", "विष योग: चंद्र-शनि युति"),
    "surya_shani": ("Sun with Saturn (father–son friction)", "सूर्य-शनि युति (पिता-पुत्र मतभेद)"),
    "mangal_shani": ("Mars with Saturn (conflict, accidents)", "मंगल-शनि युति (संघर्ष, दुर्घटना)"),
    "shukra_rahu": ("Venus with Rahu (relationship confusion)", "शुक्र-राहु युति (संबंधों में भ्रम)"),
    "manglik": ("Manglik dosha", "मांगलिक दोष"),
    "kaal_sarp": ("Kaal Sarp dosha", "कालसर्प दोष"),
    "pitra": ("Pitra dosha (ancestral karma)", "पितृ दोष"),
    "kemadruma": ("Kemadruma dosha (unsupported Moon)", "केमद्रुम दोष"),
}


def describe(item: dict, lang: str = "en") -> str:
    from . import i18n
    en, hi = TEXT[item["id"]]
    tpl = hi if lang == "hi" else en
    names = [i18n.term(lang, p) for p in item["planets"]]
    return tpl.format(p=(" + " if len(names) > 1 else "").join(names) if names else "")
