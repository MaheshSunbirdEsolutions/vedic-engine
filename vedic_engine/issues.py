"""Current-issues report: what is troubling the native *now*, ranked, with remedies.

Evidence layers (each adds weighted points to a life area):
  1. Running Vimshottari MD / AD / PD lords (weights 3 / 2 / 1) – functional malefics,
     dusthana lords, natal afflictions of the lord, the house the lord occupies.
  2. Transits today – Sade Sati / Dhaiya, Saturn-Rahu-Ketu over natal Moon / Lagna, weak
     transit houses by ashtakavarga (Lessons 37-39).
  3. Tithi Pravesha chart of the running year (PVR) – year lords, TP lagna lord, TP dusthanas.
  4. Lal Kitab varshphal of the running year of age – malefics in sensitive annual houses.
Remedies are attached side by side: Lal Kitab (annual-house upay for this year), PVR arudha
remedy for the area's house, PVR deity, Parashari mantra / daana.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from . import annual, ashtakavarga, doshas, ephemeris as eph, remedies
from .afflictions import analyse as analyse_afflictions, describe
from .chart import build_chart, sign_index
from .constants import SIGN_LORDS
from .dasha import vimshottari

AREAS = {  # area -> houses (from lagna)
    "career": [10], "finance": [2, 11], "marriage": [7], "health": [1, 6, 8], "mind": [4],
    "home": [4], "children": [5], "education": [4, 5], "fortune": [9], "expenses": [12],
    "enemies_debts": [6], "siblings": [3],
}
AREA_NAMES = {
    "career": ("Career & work", "करियर और कार्य"), "finance": ("Money & income", "धन और आय"),
    "marriage": ("Marriage & partnership", "विवाह और साझेदारी"), "health": ("Health & vitality", "स्वास्थ्य"),
    "mind": ("Mind & peace", "मन और शांति"), "home": ("Home, property & mother", "घर, संपत्ति और माता"),
    "children": ("Children", "संतान"), "education": ("Education", "शिक्षा"),
    "fortune": ("Fortune, father & dharma", "भाग्य, पिता और धर्म"), "expenses": ("Expenses & losses", "व्यय और हानि"),
    "enemies_debts": ("Disputes, debts & enemies", "विवाद, ऋण और शत्रु"), "siblings": ("Siblings & courage", "भाई-बहन और साहस"),
}
HOUSE_TO_AREAS = defaultdict(list)
for a, hs in AREAS.items():
    for h in hs:
        HOUSE_TO_AREAS[h].append(a)


def functional_nature(planet: str, lagna: int) -> str:
    """Laghu Parashari functional nature for a lagna (simplified)."""
    if planet in ("Rahu", "Ketu"):
        return "shadow"
    owned = [h for h in range(1, 13) if SIGN_LORDS[(lagna + h - 1) % 12] == planet]
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


def _owned(planet, lagna):
    return [h for h in range(1, 13) if SIGN_LORDS[(lagna + h - 1) % 12] == planet]


def report(dt_birth: datetime, tz: str, lat: float, lon: float, now: datetime | None = None,
           lang: str = "en", s: eph.Settings = eph.Settings(), top: int = 6,
           lk_upay=None) -> dict:
    now = now or datetime.now()
    hi = lang == "hi"
    natal = build_chart(dt_birth, tz, lat, lon, s)
    natal["doshas"] = {"manglik": doshas.manglik(natal), "kaal_sarp": doshas.kaal_sarp(natal)}
    lagna = natal["lagna"]["sign_index"] - 1
    moon_sign = natal["planets"]["Moon"]["sign_index"] - 1
    affl = analyse_afflictions(natal, {k: v["present"] for k, v in natal["doshas"].items()})

    score = defaultdict(float)
    evidence = defaultdict(list)
    planet_weight = defaultdict(lambda: defaultdict(float))

    def add(areas, w, text_en, text_hi, planets=(), source=""):
        for a in areas:
            score[a] += w
            evidence[a].append({"weight": w, "text": text_hi if hi else text_en, "source": source})
            for p in planets:
                planet_weight[a][p] += w

    def tr(x):
        from . import i18n
        return i18n.term(lang, x)

    NAT_HI = {"malefic": "अशुभ", "maraka": "मारक", "mixed": "मिश्रित", "benefic": "शुभ", "neutral": "सम",
              "yogakaraka": "योगकारक", "shadow": "छाया ग्रह"}

    # ---- 1. dasha lords ----
    d = vimshottari(dt_birth, tz, s, levels=3, at=now)
    cur = d["current"]
    labels = [("Mahadasha", "महादशा", 3), ("Antardasha", "अंतर्दशा", 2), ("Pratyantardasha", "प्रत्यंतर दशा", 1)]
    for (en_l, hi_l, w), lord in zip(labels, cur):
        nature = functional_nature(lord, lagna)
        owned = _owned(lord, lagna)
        house = natal["planets"][lord]["house"]
        bad_owned = [h for h in owned if h in (6, 8, 12)]
        if nature in ("malefic", "maraka") or bad_owned:
            hs = sorted(set(bad_owned + [house]))
            areas = sorted({a for h in hs for a in HOUSE_TO_AREAS[h]})
            add(areas, w, f"{en_l} of {lord} – lord of houses {owned}, placed in house {house} ({nature})",
                f"{tr(lord)} की {hi_l} – भाव {owned} का स्वामी, भाव {house} में ({NAT_HI[nature]})", [lord], "Vimshottari")
        if house in (6, 8, 12):
            areas = sorted({a for h in owned for a in HOUSE_TO_AREAS[h]})
            add(areas, w * 0.7, f"{en_l} lord {lord} sits in house {house}: matters of houses {owned} strain",
                f"{hi_l} स्वामी {tr(lord)} भाव {house} में: भाव {owned} के विषयों पर दबाव", [lord], "Vimshottari")
        if lord in ("Rahu", "Ketu"):
            disp = SIGN_LORDS[natal["planets"][lord]["sign_index"] - 1]
            add(HOUSE_TO_AREAS[house], w * 0.8, f"{en_l} of {lord} in house {house} (dispositor {disp})",
                f"{tr(lord)} की {hi_l}, भाव {house} में (राशि स्वामी {tr(disp)})", [lord], "Vimshottari")
        for a_ in affl:
            if lord in a_["planets"]:
                add(a_["areas"] and [x for x in a_["areas"] if x in AREAS] or HOUSE_TO_AREAS[house],
                    w * a_["severity"] / 3, f"{en_l} lord is involved in: {describe(a_, 'en')}",
                    f"{hi_l} स्वामी इसमें शामिल: {describe(a_, 'hi')}", [lord], "Natal affliction")

    # ---- 2. transits ----
    tnow = build_chart(now, tz, lat, lon, s)
    tp_ = {p: v["sign_index"] - 1 for p, v in tnow["planets"].items()}
    ss = doshas.sade_sati_status(moon_sign, now, tz, s)
    if ss["sade_sati"]:
        add(["mind", "health", "career"], 3, f"Sade Sati is running ({ss['phase']})",
            f"साढ़ेसाती चल रही है ({tr(ss['phase'])})", ["Saturn"], "Transit")
    if ss["dhaiya"]:
        areas = ["home", "mind"] if "4th" in ss["dhaiya"] else ["health", "mind"]
        add(areas, 2, f"Saturn's Dhaiya: {ss['dhaiya']}", f"शनि की ढैया: {tr(ss['dhaiya'])}", ["Saturn"], "Transit")
    av = ashtakavarga.from_chart(natal)
    sat_house = (tp_["Saturn"] - lagna) % 12 + 1
    sat_bindus = av["bav"]["Saturn"][tp_["Saturn"]]
    if sat_bindus <= 3 and sat_house in (1, 4, 7, 8, 10, 12, 2):
        add(HOUSE_TO_AREAS[sat_house], 1.5, f"Saturn transits house {sat_house} with only {sat_bindus} ashtakavarga bindus",
            f"शनि भाव {sat_house} से गोचर, केवल {sat_bindus} अष्टकवर्ग बिंदु", ["Saturn"], "Transit + Ashtakavarga")
    for node in ("Rahu", "Ketu"):
        for target, nm_en, nm_hi, areas in [(moon_sign, "natal Moon", "जन्म चंद्र", ["mind"]),
                                            (lagna, "Lagna", "लग्न", ["health"])]:
            if tp_[node] == target:
                add(areas, 1.5, f"Transit {node} over the {nm_en}", f"गोचर {tr(node)} {nm_hi} पर", [node], "Transit")
    jup_from_moon = (tp_["Jupiter"] - moon_sign) % 12 + 1
    if jup_from_moon in (6, 8, 12):
        add(["fortune"], 1, f"Jupiter transits the {jup_from_moon}th from the Moon (less support)",
            f"गुरु चंद्र से {jup_from_moon}वें भाव में गोचर (सहयोग कम)", ["Jupiter"], "Transit")

    # ---- 3. Tithi Pravesha of the running year ----
    tp = None
    for y in (now.year, now.year - 1):
        try:
            cand = annual.tithi_pravesha(dt_birth, tz, lat, lon, y, s=s)
        except RuntimeError:
            continue
        if cand["moment"][:16] <= now.isoformat()[:16]:
            tp = cand
            break
    if tp:
        tc = tp["chart"]
        tl = tc["lagna"]["sign_index"] - 1
        tll = SIGN_LORDS[tl]
        tll_house = tc["planets"][tll]["house"]
        if tll_house in (6, 8, 12):
            add(["health"], 1.5, f"Year chart (Tithi Pravesha): its lagna lord {tll} is in house {tll_house}",
                f"वर्ष कुंडली (तिथि प्रवेश): लग्नेश {tr(tll)} भाव {tll_house} में", [tll], "Tithi Pravesha")
        for key, w in (("vara_lord", 1.5), ("hora_lord", 1)):
            p = tp[key]
            nat = functional_nature(p, lagna)
            if nat in ("malefic", "maraka"):
                hs = [h for h in _owned(p, lagna) if h in (2, 3, 6, 7, 8, 11, 12)]
                add(sorted({a for h in hs for a in HOUSE_TO_AREAS[h]}), w,
                    f"Year's {key.replace('_', ' ')} is {p}, a functional {nat} for your lagna",
                    f"वर्ष का {'वार स्वामी' if key == 'vara_lord' else 'होरा स्वामी'} {tr(p)} है, जो आपके लग्न के लिए {NAT_HI[nat]} है",
                    [p], "Tithi Pravesha")
        for h in (8, 12, 6, 7, 10):
            mal = [p for p, v in tc["planets"].items() if v["house"] == h and p in ("Saturn", "Mars", "Rahu", "Ketu")]
            if mal:
                add(HOUSE_TO_AREAS[h], 1, f"Year chart: malefics {mal} in house {h}",
                    f"वर्ष कुंडली: भाव {h} में पाप ग्रह {', '.join(tr(m) for m in mal)}", mal, "Tithi Pravesha")

    # ---- 4. Lal Kitab varshphal ----
    age = annual.age_running(dt_birth, now)
    vp = annual.lal_kitab_varshphal(natal, age)
    LK_SENSITIVE = {1: ["health"], 4: ["mind", "home"], 7: ["marriage"], 8: ["health"], 10: ["career"], 12: ["expenses"]}
    for p in ("Saturn", "Rahu", "Ketu", "Mars"):
        h = vp["annual_houses"][p]
        if h in LK_SENSITIVE:
            add(LK_SENSITIVE[h], 1, f"Lal Kitab varshphal (year {age}): {p} moves to house {h}",
                f"लाल किताब वर्षफल (वर्ष {age}): {tr(p)} भाव {h} में", [p], "Lal Kitab varshphal")

    # ---- rank & attach remedies ----
    ranked = sorted(score.items(), key=lambda x: -x[1])[:top]
    issues = []
    for rank, (area, sc) in enumerate(ranked, 1):
        key_planets = sorted(planet_weight[area].items(), key=lambda x: -x[1])
        kp = key_planets[0][0] if key_planets else SIGN_LORDS[(lagna + AREAS[area][0] - 1) % 12]
        from . import lalkitab as _lk
        afflicted = any(kp in a_["planets"] and a_["severity"] >= 2 for a_ in affl)
        rem = {
            "lal_kitab": (lk_upay(kp, vp["annual_houses"][kp], natal["planets"][kp]["house"], lang)
                          if lk_upay else []),
            "lal_kitab_quick": _lk.quick_upay(kp, lang, afflicted),
            "lal_kitab_help": _lk.planet_help(kp, lang),
            "pvr_arudha": remedies.pvr_arudha_remedy(natal["planets"], lagna, AREAS[area][0], lang),
            "pvr_deity": remedies.pvr_deity(kp, lang),
            "parashari": remedies.parashari(kp, lang),
            "full": remedies.full_set(natal, kp, lang, lk_house=natal["planets"][kp]["house"],
                                      lk_annual_house=vp["annual_houses"][kp], house_for_arudha=AREAS[area][0]),
        }
        level = "high" if sc >= 5 else ("medium" if sc >= 2.5 else "low")
        issues.append({
            "rank": rank, "area": area, "area_name": AREA_NAMES[area][1 if hi else 0],
            "house_info": __import__("vedic_engine.placements", fromlist=["house_info"]).house_info(AREAS[area][0], lang),
            "other_planets": [__import__("vedic_engine.placements", fromlist=["explain"]).explain(natal, p_, lang)
                              for p_, _w in key_planets[1:3]],
            "score": round(sc, 1), "priority": level, "key_planet": kp,
            "evidence": sorted(evidence[area], key=lambda e: -e["weight"]),
            "remedies": rem,
        })
    return {
        "as_of": now.isoformat(timespec="minutes"),
        "dasha_now": cur,
        "age_running": age,
        "tithi_pravesha": {k: tp[k] for k in ("moment", "valid_until", "vara_lord", "hora_lord")} if tp else None,
        "sade_sati": ss,
        "natal_afflictions": [{**a_, "text": describe(a_, lang)} for a_ in affl],
        "rin": __import__("vedic_engine.lalkitab", fromlist=["detect_rin"]).detect_rin(natal, lang),
        "upay_rules": __import__("vedic_engine.lalkitab", fromlist=["upay_rules"]).upay_rules(lang),
        "issues": issues,
        "disclaimer": ("Traditional astrological guidance, not medical, legal or financial advice. Remedies are spiritual practices; no outcome is guaranteed."
                       if not hi else "यह पारंपरिक ज्योतिषीय मार्गदर्शन है, चिकित्सा, कानूनी या वित्तीय सलाह नहीं। उपाय आध्यात्मिक साधन हैं; किसी परिणाम की गारंटी नहीं है।"),
    }
