"""Life-long and year-wise predictions.

Method (Parashari, as taught in BPHS and PVR Narasimha Rao's *Lessons*; gochara per Phaladeepika):

* A planet's period gives the results of (a) the houses it RULES and OCCUPIES from the lagna,
  (b) its natural significations (karakatva), coloured by (c) its functional nature for the lagna,
  its dignity / strength, and (d) the relation of the antardasha lord to the mahadasha lord
  (6/8/12 from each other strains; 1/4/5/7/9/10 supports).
* Transits (gochara) of the slow planets – Jupiter, Saturn, Rahu, Ketu – are read from the natal
  Moon (classical good houses: Jupiter 2,5,7,9,11; Saturn/Rahu/Ketu 3,6,11), refined by the planet's
  own ashtakavarga bindus in the sign, and from the lagna for which life areas are touched.
* Sade Sati / Dhaiya, the Tithi Pravesha year chart and the Lal Kitab annual chart add colour.

Scores are heuristics that rank and phrase the reading; the text always shows the reasons, so a
Jyotishi can see why. Nothing here is certain – the report says so.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from . import ephemeris as eph, i18n
from .ashtakavarga import from_chart as _av
from .constants import SIGNS
from .placements import BHAV, explain, ord_hi, owned_houses

KARAKA = {  # natural significations (en, hi)
    "Sun": ("authority, father, government, vitality, reputation", "अधिकार, पिता, शासन, जीवनशक्ति, प्रतिष्ठा"),
    "Moon": ("mind, mother, emotions, the public, travel", "मन, माता, भावनाएँ, जनता, यात्रा"),
    "Mars": ("energy, courage, siblings, land & property, disputes, surgery", "ऊर्जा, साहस, भाई, भूमि-संपत्ति, विवाद, शल्य"),
    "Mercury": ("intellect, communication, trade, learning, friends", "बुद्धि, संवाद, व्यापार, विद्या, मित्र"),
    "Jupiter": ("wisdom, children, teachers, wealth, dharma, blessings", "ज्ञान, संतान, गुरु, धन, धर्म, आशीर्वाद"),
    "Venus": ("marriage & spouse, comforts, vehicles, arts, luxury", "विवाह व जीवनसाथी, सुख, वाहन, कला, वैभव"),
    "Saturn": ("work, discipline, delays, servants, longevity, hard lessons", "कर्म, अनुशासन, विलंब, सेवक, आयु, कठोर सीख"),
    "Rahu": ("ambition, foreign links, technology, the unconventional, confusion", "महत्वाकांक्षा, विदेश, तकनीक, असामान्य, भ्रम"),
    "Ketu": ("detachment, spirituality, research, sudden events, losses", "वैराग्य, आध्यात्म, शोध, अचानक घटनाएँ, हानि"),
}
NATURE_SCORE = {"yogakaraka": 2, "benefic": 1, "neutral": 0, "mixed": 0, "maraka": -0.5, "malefic": -1}
STRENGTH_SCORE = {"strong": 1, "average": 0, "weak": -1}
GOOD_FROM_MOON = {"Sun": {3, 6, 10, 11}, "Moon": {1, 3, 6, 7, 10, 11}, "Mars": {3, 6, 11},
                  "Mercury": {2, 4, 6, 8, 10, 11}, "Jupiter": {2, 5, 7, 9, 11},
                  "Venus": {1, 2, 3, 4, 5, 8, 9, 11, 12}, "Saturn": {3, 6, 11}, "Rahu": {3, 6, 11}, "Ketu": {3, 6, 11}}
ASPECT = {"Jupiter": (5, 7, 9), "Saturn": (3, 7, 10), "Rahu": (5, 7, 9), "Ketu": (5, 7, 9), "Mars": (4, 7, 8)}
AREAS = [  # key, houses, en, hi
    ("career", [10], "Career & status", "करियर व पद"), ("wealth", [2, 11], "Money & gains", "धन व लाभ"),
    ("marriage", [7], "Marriage & partnerships", "विवाह व साझेदारी"), ("health", [1, 6, 8], "Health", "स्वास्थ्य"),
    ("home", [4], "Home, mother & property", "घर, माता व संपत्ति"), ("children", [5], "Children, studies & creativity", "संतान, विद्या व रचनात्मकता"),
    ("fortune", [9], "Fortune, father & dharma", "भाग्य, पिता व धर्म"), ("expenses", [12], "Expenses, travel abroad & sleep", "व्यय, विदेश यात्रा व निद्रा"),
]
SLOW = ("Jupiter", "Saturn", "Rahu", "Ketu")
RATING = [(1.2, "excellent", "उत्तम"), (0.3, "good", "शुभ"), (-0.9, "mixed", "मिश्रित"), (-99, "challenging", "चुनौतीपूर्ण")]


def _rate(score: float, hi: bool) -> tuple[str, str]:
    for lim, en, h in RATING:
        if score >= lim:
            return en, (h if hi else en)
    return "challenging", "चुनौतीपूर्ण" if hi else "challenging"


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=None)


def _T(lang, x):
    return i18n.term(lang, x)


def _ord(n: int, hi: bool) -> str:
    return ord_hi(n) if hi else ({1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th"))


# ---------------------------------------------------------------- planet / period tone
def planet_tone(chart: dict, p: str) -> tuple[float, dict]:
    pl = explain(chart, p, "en")
    lagna = chart["lagna"]["sign_index"] - 1
    if p in ("Rahu", "Ketu"):
        disp = SIGNS.index(chart["planets"][p]["sign"])
        from .constants import SIGN_LORDS
        base = 0.5 * NATURE_SCORE.get(explain(chart, SIGN_LORDS[disp], "en")["nature"], 0)
        h = pl["house"]
        base += 0.75 if h in (3, 6, 10, 11) else (-0.75 if h in (8, 12) else 0)
    else:
        base = NATURE_SCORE.get(pl["nature"], 0)
        h = pl["house"]
        own_dus = any(o in (6, 8, 12) for o in owned_houses(p, lagna))
        if h in (6, 8, 12):
            base += 0.25 if own_dus else -0.75          # a dusthana lord in a dusthana: viparita hint
        elif h in (1, 4, 5, 7, 9, 10):
            base += 0.5
    base += STRENGTH_SCORE[pl["strength"]] * 0.75
    return round(base, 2), pl


def _relation(chart, a: str, b: str) -> float:
    ha, hb = chart["planets"][a]["house"], chart["planets"][b]["house"]
    d = (hb - ha) % 12 + 1
    return -0.5 if d in (6, 8, 12) else (0.4 if d in (1, 4, 5, 7, 9, 10) else 0)


def _themes(chart, pl: dict, hi: bool) -> list[str]:
    hs = [pl["house"]] + [o for o in pl["owns"] if o != pl["house"]]
    out = []
    for h in hs:
        m = BHAV[h][3 if hi else 2].split(",")
        out.append(f"{_ord(h, hi)} {'भाव' if hi else 'house'} – {', '.join(x.strip() for x in m[:3])}")
    return out


def period_reading(chart: dict, md: str, ad: str | None, lang: str) -> dict:
    hi = lang == "hi"
    t_md, pl_md = planet_tone(chart, md)
    score = t_md
    reasons = []
    nat = {"yogakaraka": "योगकारक", "benefic": "शुभ", "mixed": "मिश्रित", "malefic": "अशुभ", "maraka": "मारक",
           "neutral": "सम", "shadow": "छाया ग्रह"}
    reasons.append((f"{_T(lang, md)}: {ord_hi(pl_md['house'])} भाव में, {nat[pl_md['nature']]}, {('बलवान' if pl_md['strength'] == 'strong' else 'दुर्बल' if pl_md['strength'] == 'weak' else 'सामान्य बल')}"
                    if hi else f"{md}: in the {_ord(pl_md['house'], False)} house, {pl_md['nature']}, {pl_md['strength']}"))
    if ad and ad != md:
        t_ad, pl_ad = planet_tone(chart, ad)
        rel = _relation(chart, md, ad)
        score = t_md * 0.55 + t_ad * 0.6 + rel
        reasons.append((f"{_T(lang, ad)}: {ord_hi(pl_ad['house'])} भाव में, {nat[pl_ad['nature']]}" if hi
                        else f"{ad}: in the {_ord(pl_ad['house'], False)} house, {pl_ad['nature']}"))
        if rel < 0:
            reasons.append("दशा व अंतर्दशा स्वामी परस्पर 6/8/12 – तालमेल की कमी" if hi else "MD and AD lords are 6/8/12 from each other – friction")
        elif rel > 0:
            reasons.append("दशा व अंतर्दशा स्वामी परस्पर केंद्र/त्रिकोण – सहयोग" if hi else "MD and AD lords are in kendra/trikona to each other – support")
        themes = _themes(chart, pl_ad, hi)[:2] + _themes(chart, pl_md, hi)[:1]
        kar = KARAKA[ad][1 if hi else 0]
    else:
        themes = _themes(chart, pl_md, hi)
        kar = KARAKA[md][1 if hi else 0]
    key, label = _rate(score, hi)
    return {"score": round(score, 2), "rating": key, "rating_label": label, "themes": themes, "karaka": kar, "reasons": reasons}


def _md_text(chart, md: str, r: dict, lang: str) -> str:
    hi = lang == "hi"
    pl = explain(chart, md, lang)
    good = r["rating"] in ("excellent", "good")
    th = "; ".join(r["themes"])
    if hi:
        return (f"{_T(lang, md)} की महादशा {th} को सक्रिय करती है और {KARAKA[md][1]} के विषय आगे लाती है। "
                + ("यह काल समग्र रूप से सहायक है – इन क्षेत्रों में प्रगति और अवसर की संभावना।" if good else
                   "यह काल प्रयास व धैर्य माँगता है – इन क्षेत्रों में रुकावट या बदलाव संभव; उपाय सहायक रहेंगे."
                   if r["rating"] == "challenging" else "मिश्रित फल – कुछ क्षेत्र आगे बढ़ेंगे, कुछ में सावधानी।"))
    return (f"{md} mahadasha activates {th}, and brings {KARAKA[md][0]} to the fore. "
            + ("Overall a supportive period – progress and openings in these areas are likely." if good else
               "A period that asks for effort and patience – blocks or change in these areas are possible; remedies help."
               if r["rating"] == "challenging" else "Mixed results – some of these areas move forward, others need care."))


# ---------------------------------------------------------------- transits
def _lons(jd: float, s) -> dict[str, float]:
    return {p: v["lon"] for p, v in eph.planet_longitudes(jd, s).items()}


def transit_segments(tz: str, s, start: date, end: date, planets=SLOW) -> dict[str, list[dict]]:
    """Sign occupied by each slow planet from start to end, with ingress dates (to the day)."""
    out = {p: [] for p in planets}
    d = start
    prev = None
    while d <= end:
        jd = eph.local_to_jd(datetime(d.year, d.month, d.day, 12), tz)
        L = _lons(jd, s)
        signs = {p: int(L[p] // 30) for p in planets}
        for p in planets:
            if prev is None or prev[p] != signs[p]:
                out[p].append({"sign": SIGNS[signs[p]], "sign_index": signs[p], "from": d.isoformat()})
        prev = signs
        d += timedelta(days=1)
    for p in planets:
        for i, seg in enumerate(out[p]):
            seg["to"] = out[p][i + 1]["from"] if i + 1 < len(out[p]) else end.isoformat()
    return out


def _transit_read(chart: dict, p: str, sign_i: int, av: dict, lang: str) -> dict:
    hi = lang == "hi"
    moon = chart["planets"]["Moon"]["sign_index"] - 1
    lagna = chart["lagna"]["sign_index"] - 1
    hm = (sign_i - moon) % 12 + 1
    hl = (sign_i - lagna) % 12 + 1
    good = hm in GOOD_FROM_MOON[p]
    bindus = av["bav"][p][sign_i] if p in av["bav"] else None
    sc = (1.5 if good else -0.6) if p == "Jupiter" else (1 if good else -0.8) if p == "Saturn" else (0.5 if good else -0.4)
    if bindus is not None:
        sc += 0.4 if bindus >= 5 else (-0.4 if bindus <= 2 else 0)
    asp = sorted({(hl - 1 + a - 1) % 12 + 1 for a in ASPECT.get(p, ())})
    mean = BHAV[hl][3 if hi else 2].split(",")
    text = ((f"{_T(lang, p)} चंद्र से {ord_hi(hm)} ({'शुभ' if good else 'अशुभ'}), लग्न से {ord_hi(hl)} भाव में – {', '.join(x.strip() for x in mean[:3])}"
             + (f"; अष्टकवर्ग बिंदु {bindus}" if bindus is not None else "") + (f"; दृष्टि भाव {', '.join(map(str, asp))} पर" if asp else ""))
            if hi else
            (f"{p} in the {_ord(hm, False)} from the Moon ({'favourable' if good else 'unfavourable'}), the {_ord(hl, False)} from the lagna – "
             f"{', '.join(x.strip() for x in mean[:3])}" + (f"; {bindus} ashtakavarga bindus" if bindus is not None else "")
             + (f"; aspects houses {', '.join(map(str, asp))}" if asp else "")))
    return {"house_from_moon": hm, "house_from_lagna": hl, "good": good, "bindus": bindus, "aspects": asp,
            "score": round(sc, 2), "text": text}


# ---------------------------------------------------------------- milestones
def _returns(chart, tz, s, birth: datetime, planet: str, years: int, min_gap_days: int) -> list[dict]:
    natal = chart["planets"][planet]["sign_index"] - 1
    out, d, prev = [], (birth + timedelta(days=200)).date(), None
    end = (birth + timedelta(days=365.25 * years)).date()
    step = 5
    while d <= end:
        jd = eph.local_to_jd(datetime(d.year, d.month, d.day, 12), tz)
        sg = int(_lons(jd, s)[planet] // 30)
        if sg == natal and prev is not None and prev != natal:
            if not out or (d - date.fromisoformat(out[-1]["date"])).days > min_gap_days:
                out.append({"date": d.isoformat(), "age": round((d - birth.date()).days / 365.25, 1)})
        prev = sg
        d += timedelta(days=step)
    return out


# ---------------------------------------------------------------- life-long
def lifelong(chart: dict, dasha: dict, birth: datetime, tz: str, s, lang: str = "en",
             life_areas: list | None = None, interpretation: list | None = None, sade_sati: list | None = None,
             afflictions: list | None = None, now: datetime | None = None) -> dict:
    hi = lang == "hi"
    now = now or datetime.now()
    tones = {p: planet_tone(chart, p)[0] for p in chart["planets"]}
    order = sorted(tones, key=lambda p: -tones[p])
    lagna_lord = explain(chart, __import__("vedic_engine.constants", fromlist=["SIGN_LORDS"]).SIGN_LORDS[chart["lagna"]["sign_index"] - 1], lang)
    moon = chart["planets"]["Moon"]
    yogas = [f["name"] for f in (interpretation or []) if f.get("nature") == "benefic"]
    overview = {
        "lagna": chart["lagna"]["sign"], "moon_sign": moon["sign"], "nakshatra": moon["nakshatra"]["name"],
        "lagna_lord": lagna_lord, "strongest": order[:3], "weakest": order[-3:][::-1], "yogas": yogas,
        "doshas": [a for a in (afflictions or []) if a["severity"] >= 2][:6],
        "text": (f"{_T(lang, chart['lagna']['sign'])} लग्न, चंद्रमा {_T(lang, moon['sign'])} राशि व {_T(lang, moon['nakshatra']['name'])} नक्षत्र में। "
                 f"लग्नेश {_T(lang, lagna_lord['planet'])} {ord_hi(lagna_lord['house'])} भाव में – जीवन की दिशा इस भाव के विषयों ({lagna_lord['house_meaning']}) से जुड़ती है। "
                 f"सबसे सहायक ग्रह: {', '.join(_T(lang, p) for p in order[:3])}; जिन ग्रहों पर ध्यान चाहिए: {', '.join(_T(lang, p) for p in order[-3:][::-1])}।"
                 if hi else
                 f"{chart['lagna']['sign']} ascendant, Moon in {moon['sign']} in {moon['nakshatra']['name']} nakshatra. "
                 f"The lagna lord {lagna_lord['planet']} sits in the {_ord(lagna_lord['house'], False)} house, so life's direction is tied to {lagna_lord['house_meaning']}. "
                 f"Most supportive planets: {', '.join(order[:3])}; planets that need care: {', '.join(order[-3:][::-1])}."),
    }
    journey = []
    end_life = birth + timedelta(days=365.25 * 100)
    for md in dasha["mahadashas"]:
        st, en = _dt(md["start"]), _dt(md["end"])
        if en < birth or st > end_life:
            continue
        r = period_reading(chart, md["lord"], None, lang)
        ads = []
        for ad in md.get("sub", []):
            a_st, a_en = _dt(ad["start"]), _dt(ad["end"])
            if a_en < birth:
                continue
            ar = period_reading(chart, md["lord"], ad["lord"], lang)
            ads.append({"lord": ad["lord"], "start": max(a_st, birth).date().isoformat(), "end": ad["end"][:10],
                        "age_from": max(0, round((a_st - birth).days / 365.25, 1)), "rating": ar["rating"],
                        "rating_label": ar["rating_label"], "score": ar["score"], "themes": ar["themes"][:2], "reasons": ar["reasons"]})
        best = max(ads, key=lambda x: x["score"]) if ads else None
        worst = min(ads, key=lambda x: x["score"]) if ads else None
        journey.append({
            "lord": md["lord"], "start": max(st, birth).date().isoformat(), "end": en.date().isoformat(),
            "age_from": max(0, round((st - birth).days / 365.25, 1)), "age_to": round((en - birth).days / 365.25, 1),
            "current": st <= now <= en, "rating": r["rating"], "rating_label": r["rating_label"], "score": r["score"],
            "themes": r["themes"], "karaka": r["karaka"], "reasons": r["reasons"], "text": _md_text(chart, md["lord"], r, lang),
            "best_ad": best and {"lord": best["lord"], "start": best["start"], "end": best["end"]},
            "hardest_ad": worst and {"lord": worst["lord"], "start": worst["start"], "end": worst["end"]},
            "antardashas": ads,
        })
    milestones = []
    for p in (sade_sati or []):
        if not p.get("start"):
            continue
        p_end = p.get("end") or end_life.date().isoformat()   # still running at the end of the window
        a0 = round((_dt(p["start"]) - birth).days / 365.25, 1)
        a1 = round((_dt(p_end) - birth).days / 365.25, 1)
        milestones.append({"kind": "sade_sati", "start": p["start"], "end": p_end, "age": f"{max(0, a0)}–{a1}",
                           "text": ("शनि की साढ़ेसाती – दबाव, ज़िम्मेदारी व परिपक्वता का समय" if hi else
                                    "Saturn's Sade Sati – a time of pressure, responsibility and maturing")})
    for r in _returns(chart, tz, s, birth, "Saturn", 95, 3000):
        milestones.append({"kind": "saturn_return", "start": r["date"], "end": None, "age": str(r["age"]),
                           "text": ("शनि की वापसी – जीवन के ढाँचे (कार्य, संबंध) की पुनर्रचना" if hi else
                                    "Saturn return – life's structures (work, commitments) are rebuilt")})
    for r in _returns(chart, tz, s, birth, "Jupiter", 90, 3000):
        milestones.append({"kind": "jupiter_return", "start": r["date"], "end": None, "age": str(r["age"]),
                           "text": ("गुरु की वापसी – विस्तार, शिक्षा, आस्था व अवसर का नया चक्र" if hi else
                                    "Jupiter return – a new 12-year cycle of growth, learning and opportunity")})
    milestones.sort(key=lambda m: m["start"])
    areas = [{"area": a["area"], "title": a["title"], "verdict": a["verdict"], "verdict_key": a["verdict_key"],
              "points": [p["text"] for p in a["points"][:3]], "periods": a["periods"][:4]} for a in (life_areas or [])]
    return {"overview": overview, "life_areas": areas, "journey": journey, "milestones": milestones,
            "method": ("दशा स्वामी के भाव-स्वामित्व, स्थिति, कारकत्व, कार्यात्मक स्वभाव व बल से (BPHS, PVR); गोचर चंद्र से (फलदीपिका)।"
                       if hi else "From each dasha lord's houses owned and occupied, karakatva, functional nature and strength (BPHS, PVR); transits from the Moon (Phaladeepika)."),
            "disclaimer": ("ज्योतिषीय फल संभावनाएँ हैं, निश्चितता नहीं; निर्णय अपने विवेक व विशेषज्ञ सलाह से लें।" if hi else
                           "Astrological readings describe tendencies, not certainties; make decisions with your own judgement and expert advice.")}


# ---------------------------------------------------------------- year-wise
def _periods_in(dasha: dict, start: datetime, end: datetime, level: int = 2) -> list[dict]:
    out = []
    for md in dasha["mahadashas"]:
        if _dt(md["end"]) < start or _dt(md["start"]) > end:
            continue
        for ad in md.get("sub", []):
            if _dt(ad["end"]) < start or _dt(ad["start"]) > end:
                continue
            if level == 2:
                out.append({"md": md["lord"], "ad": ad["lord"], "start": ad["start"][:10], "end": ad["end"][:10]})
            else:
                for pd in ad.get("sub", []):
                    if _dt(pd["end"]) < start or _dt(pd["start"]) > end:
                        continue
                    out.append({"md": md["lord"], "ad": ad["lord"], "pd": pd["lord"], "start": pd["start"][:10], "end": pd["end"][:10]})
    return out


def _overlap_days(a0, a1, b0, b1) -> int:
    return max(0, (min(a1, b1) - max(a0, b0)).days)


def year_score(chart: dict, dasha: dict, year: int, tz: str, s, av: dict, ss_status) -> tuple[float, dict]:
    y0, y1 = datetime(year, 1, 1), datetime(year, 12, 31)
    pers = _periods_in(dasha, y0, y1)
    tot = 0.0
    for p in pers:
        w = _overlap_days(_dt(p["start"]), _dt(p["end"]), y0, y1) / 365
        tot += w * period_reading(chart, p["md"], p["ad"], "en")["score"]
    jd = eph.local_to_jd(datetime(year, 7, 1, 12), tz)
    L = _lons(jd, s)
    tr = {p: _transit_read(chart, p, int(L[p] // 30), av, "en")["score"] for p in SLOW}
    tsc = tr["Jupiter"] + tr["Saturn"] + 0.5 * (tr["Rahu"] + tr["Ketu"])
    ss = ss_status(datetime(year, 7, 1))
    ssp = -1.2 if ss.get("sade_sati") and "peak" in (ss.get("phase") or "") else (-0.8 if ss.get("sade_sati") else (-0.6 if ss.get("dhaiya") else 0))
    return round(tot + 0.5 * tsc + ssp, 2), {"periods": pers, "transit": tr, "sade_sati": ss}


def _area_outlook(chart: dict, pers: list[dict], segs: dict, av: dict, lang: str, y0: date, y1: date) -> list[dict]:
    hi = lang == "hi"
    lagna = chart["lagna"]["sign_index"] - 1
    out = []
    for key, houses, en, h_ in AREAS:
        sc, why = 0.0, []
        for p in pers:
            w = _overlap_days(_dt(p["start"]), _dt(p["end"]), datetime.combine(y0, datetime.min.time()),
                              datetime.combine(y1, datetime.min.time())) / 365
            if w <= 0:
                continue
            for lord in dict.fromkeys([p["md"], p["ad"]]):
                pl = explain(chart, lord, "en")
                links = [hh for hh in houses if hh == pl["house"] or hh in pl["owns"]]
                if links:
                    t = planet_tone(chart, lord)[0]
                    sc += w * (0.8 if t > 0.3 else (-0.8 if t < -0.3 else 0.2))
                    why.append((f"{_T(lang, lord)} दशा भाव {'/'.join(map(str, links))} से जुड़ी" if hi else
                                f"{lord} period linked to house {'/'.join(map(str, links))}"))
        for planet, segl in segs.items():
            for seg in segl:
                hl = (seg["sign_index"] - lagna) % 12 + 1
                asp = {(hl - 1 + a - 1) % 12 + 1 for a in ASPECT.get(planet, ())}
                frac = max(1, (date.fromisoformat(seg["to"]) - date.fromisoformat(seg["from"])).days) / 365
                period = f"{seg['from'][5:]}→{seg['to'][5:]}"
                for hh in houses:
                    if planet == "Jupiter" and (hh == hl or hh in asp):
                        sc += 0.9 * frac
                        why.append((f"गुरु का भाव {hh} पर {'गोचर' if hh == hl else 'दृष्टि'} ({period})" if hi else
                                    f"Jupiter {'transits' if hh == hl else 'aspects'} house {hh} ({period})"))
                    if planet == "Saturn" and hh == hl:
                        sc += (-0.4 if hh not in (3, 6, 11) else 0.4) * frac
                        why.append((f"शनि भाव {hh} में ({period}) – धीमी, स्थिर प्रगति/दबाव" if hi else
                                    f"Saturn in house {hh} ({period}) – slow, steady progress or pressure"))
                    if planet == "Saturn" and hh in asp and hh != hl:
                        sc -= 0.2 * frac
                    if planet in ("Rahu", "Ketu") and hh == hl:
                        sc += (0.3 if hh in (3, 6, 11) else -0.35) * frac
                        why.append((f"{_T(lang, planet)} भाव {hh} में ({period})" if hi else f"{planet} in house {hh} ({period})"))
        rk, rl = _rate(sc, hi)
        why = list(dict.fromkeys(why))[:5] or ["इस वर्ष कोई प्रबल दशा/गोचर संकेत नहीं – सामान्य प्रवाह" if hi else
                                               "No strong dasha or transit trigger this year – ordinary flow"]
        out.append({"area": key, "title": h_ if hi else en, "score": round(sc, 2), "rating": rk, "rating_label": rl,
                    "reasons": why})
    return out


def _month_table(chart, dasha, year: int, tz: str, s, lang: str) -> list[dict]:
    hi = lang == "hi"
    moon = chart["planets"]["Moon"]["sign_index"] - 1
    months_hi = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
    months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    out = []
    for m in range(1, 13):
        mid = datetime(year, m, 15)
        cur = [p for p in _periods_in(dasha, mid, mid, level=3)]
        pd = cur[0] if cur else None
        jd = eph.local_to_jd(datetime(year, m, 15, 12), tz)
        L = _lons(jd, s)
        sc = 0.0
        notes = []
        if pd:
            r = period_reading(chart, pd["ad"], pd["pd"], lang)
            sc += r["score"] * 0.8
            notes.append((f"प्रत्यंतर {_T(lang, pd['pd'])}" if hi else f"PD {pd['pd']}"))
        for p in ("Sun", "Mars", "Venus", "Mercury"):
            hm = (int(L[p] // 30) - moon) % 12 + 1
            good = hm in GOOD_FROM_MOON[p]
            sc += {"Sun": 0.35, "Mars": 0.35, "Venus": 0.2, "Mercury": 0.15}[p] * (1 if good else -1)
            if p in ("Sun", "Mars"):
                notes.append((f"{_T(lang, p)} चंद्र से {hm}" if hi else f"{p} {hm} from Moon") + (" ✓" if good else ""))
        rk, rl = _rate(sc, hi)
        out.append({"month": (months_hi if hi else months_en)[m - 1], "rating": rk, "rating_label": rl,
                    "score": round(sc, 2), "notes": notes, "pd": pd})
    return out


def yearly(chart: dict, dasha3: dict, birth: datetime, tz: str, lat: float, lon: float, s, year: int,
           lang: str = "en", ss_status=None, tp=None, lk=None) -> dict:
    hi = lang == "hi"
    av = _av(chart)
    y0, y1 = date(year, 1, 1), date(year, 12, 31)
    pers = _periods_in(dasha3, datetime(year, 1, 1), datetime(year, 12, 31))
    periods = []
    for p in pers:
        r = period_reading(chart, p["md"], p["ad"], lang)
        periods.append({**p, **{k: r[k] for k in ("rating", "rating_label", "themes", "reasons", "score")}})
    segs = transit_segments(tz, s, y0, y1)
    transits = []
    for p, segl in segs.items():
        for seg in segl:
            tr = _transit_read(chart, p, seg["sign_index"], av, lang)
            transits.append({"planet": p, "sign": seg["sign"], "from": seg["from"], "to": seg["to"], **tr})
    score, parts = year_score(chart, dasha3, year, tz, s, av, ss_status)
    rk, rl = _rate(score, hi)
    ss_mid = parts["sade_sati"]
    areas = _area_outlook(chart, pers, segs, av, lang, y0, y1)
    best = sorted(areas, key=lambda a: -a["score"])[:2]
    weak = sorted(areas, key=lambda a: a["score"])[:2]
    main = periods[0] if periods else None
    summary = (
        (f"{year}: समग्र रूप से {rl} वर्ष। " + (f"{_T(lang, main['md'])} महादशा में {' → '.join(dict.fromkeys(_T(lang, p['ad']) for p in periods))} की अंतर्दशा। " if main else "")
         + f"सबसे अनुकूल: {', '.join(a['title'] for a in best)}। ध्यान दें: {', '.join(a['title'] for a in weak)}।"
         + (" शनि की साढ़ेसाती चल रही है।" if ss_mid.get("sade_sati") else (f" शनि की ढैया ({_T(lang, ss_mid['dhaiya'])})।" if ss_mid.get("dhaiya") else "")))
        if hi else
        (f"{year}: overall a {rl} year. " + (f"{main['md']} mahadasha, {' → '.join(dict.fromkeys(p['ad'] for p in periods))} antardasha. " if main else "")
         + f"Most favourable: {', '.join(a['title'] for a in best)}. Needs care: {', '.join(a['title'] for a in weak)}."
         + (" Saturn's Sade Sati is running." if ss_mid.get("sade_sati") else (f" Saturn's Dhaiya ({ss_mid['dhaiya']})." if ss_mid.get("dhaiya") else "")))
    )
    return {"year": year, "age": year - birth.year, "score": score, "rating": rk, "rating_label": rl, "summary": summary,
            "periods": periods, "transits": transits, "areas": areas, "months": _month_table(chart, dasha3, year, tz, s, lang),
            "sade_sati": ss_mid, "tithi_pravesha": tp, "lal_kitab": lk}


def years_table(chart: dict, dasha: dict, birth: datetime, tz: str, s, start_year: int, n: int, lang: str, ss_status) -> list[dict]:
    hi = lang == "hi"
    av = _av(chart)
    out = []
    for y in range(start_year, start_year + n):
        sc, parts = year_score(chart, dasha, y, tz, s, av, ss_status)
        rk, rl = _rate(sc, hi)
        main = max(parts["periods"], key=lambda p: _overlap_days(_dt(p["start"]), _dt(p["end"]), datetime(y, 1, 1), datetime(y, 12, 31))) if parts["periods"] else None
        jd = eph.local_to_jd(datetime(y, 7, 1, 12), tz)
        L = _lons(jd, s)
        out.append({"year": y, "age": y - birth.year, "score": sc, "rating": rk, "rating_label": rl,
                    "dasha": f"{_T(lang, main['md'])}–{_T(lang, main['ad'])}" if main else "",
                    "jupiter": SIGNS[int(L['Jupiter'] // 30)], "saturn": SIGNS[int(L['Saturn'] // 30)],
                    "sade_sati": bool(parts["sade_sati"].get("sade_sati")), "dhaiya": parts["sade_sati"].get("dhaiya")})
    return out
