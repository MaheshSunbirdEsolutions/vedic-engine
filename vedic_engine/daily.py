"""Daily horoscope (Dainik Rashifal / Gochara Phal) – both personalized (for a natal chart)
and general (12 Moon signs / Rashis).

Classical basis:
* Chandrabala – Moon transit from natal Moon (1, 3, 6, 7, 10, 11 favourable; 8th = Chandrashtama),
  refined by Moon's Ashtakavarga bindus in the transit sign (Phaladeepika).
* Tarabala – nine-fold tara from the birth nakshatra (R. P. Gaur, Nakshatra Jyotish, pp. 88–91)
  plus ghat nakshatra, dagdha/yamaghanta cautions and Siddhi yogas (pp. 173–179).
* Gochara of fast & slow planets from natal Moon (Phaladeepika) and Lagna houses for daily areas.
* Running Vimshottari MD / AD / PD backdrop (BPHS, PVR).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from . import ephemeris as eph, i18n, nakshatra as _nak
from .ashtakavarga import from_chart as _av
from .constants import NAKSHATRA_SPAN, PLANETS, SIGNS, SIGNS_SANSKRIT, SIGN_LORDS
from .panchang import panchang
from .placements import BHAV, explain, ord_hi
from .predictions import (
    AREAS, ASPECT, GOOD_FROM_MOON, _lons, _periods_in, _rate, planet_tone, period_reading,
)
from .remedies import PLANET as REM_PLANET

VARA_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]  # Mon=0 .. Sun=6
VARA_COLOUR = {
    "Sun": ("copper / saffron", "तांबा / केसरिया"),
    "Moon": ("white / pearl", "सफ़ेद / मोती"),
    "Mars": ("red / coral", "लाल / मूंगा"),
    "Mercury": ("green", "हरा"),
    "Jupiter": ("yellow / gold", "पीला / सुनहरा"),
    "Venus": ("cream / pastel", "क्रीम / हल्का गुलाबी"),
    "Saturn": ("navy / dark blue", "गहरा नीला"),
}
LUCKY_NUMBERS = {
    "Sun": [1, 3, 9], "Moon": [2, 7, 9], "Mars": [1, 3, 9],
    "Mercury": [3, 5, 6], "Jupiter": [3, 5, 9], "Venus": [2, 6, 8], "Saturn": [4, 5, 8],
}
FAST = ("Sun", "Moon", "Mars", "Mercury", "Venus")
FAST_WEIGHT = {"Moon": 0.9, "Sun": 0.35, "Mars": 0.35, "Venus": 0.25, "Mercury": 0.25}
SLOW_WEIGHT = {"Jupiter": 0.45, "Saturn": 0.4, "Rahu": 0.2, "Ketu": 0.2}

RASHI_AREAS = [
    ("career", [10, 6, 11], "Career & Work", "करियर व कार्य"),
    ("finance", [2, 11, 9], "Money & Gains", "धन व लाभ"),
    ("love", [7, 4, 2, 5], "Love, Marriage & Family", "प्रेम, विवाह व परिवार"),
    ("health", [1, 6, 8, 12], "Health, Mind & Energy", "स्वास्थ्य, मन व ऊर्जा"),
    ("learning", [5, 9, 3], "Studies, Decisions & Travel", "अध्ययन, निर्णय व यात्रा"),
]

MOON_HOUSE_NOTE = {
    1: ("Moon over natal Moon – heightened feelings, focus on self and personal plans.",
        "जन्म चंद्र पर चंद्र गोचर – भावनाएँ प्रबल, स्वयं व व्यक्तिगत योजनाओं पर ध्यान।"),
    2: ("Moon in 2nd – attention on family, speech, food and finances; keep words gentle.",
        "चंद्र दूसरे भाव में – परिवार, वाणी, भोजन व धन पर ध्यान; वाणी मधुर रखें।"),
    3: ("Moon in 3rd – courage, initiative, short trips and productive conversations.",
        "चंद्र तीसरे भाव में – साहस, पहल, छोटी यात्रा व सार्थक संवाद के लिए अच्छा दिन।"),
    4: ("Moon in 4th – emotional sensitivity, domestic chores; protect peace of mind.",
        "चंद्र चौथे भाव में – मन संवेदनशील, घरेलू कार्य; मानसिक शांति बनाए रखें।"),
    5: ("Moon in 5th – creative thinking, study and children, though moods may fluctuate.",
        "चंद्र पाँचवें भाव में – रचनात्मकता, अध्ययन व संतान से जुड़े विषय; मन थोड़ा चंचल।"),
    6: ("Moon in 6th – good for clearing pending tasks, overcoming hurdles and health routines.",
        "चंद्र छठे भाव में – रुके काम निपटाने, बाधाओं पर विजय और स्वास्थ्य नियम के लिए शुभ।"),
    7: ("Moon in 7th – favourable for partnerships, meetings, public dealings and harmony.",
        "चंद्र सातवें भाव में – साझेदारी, मुलाक़ात, जनसंपर्क और तालमेल के लिए अनुकूल।"),
    8: ("Chandrashtama (Moon in 8th) – low energy or sudden hiccups possible; avoid big risks and new launches.",
        "चंद्राष्टम (चंद्र आठवें भाव में) – ऊर्जा में कमी या अचानक अड़चन संभव; बड़े जोखिम व नए आरंभ टालें।"),
    9: ("Moon in 9th – longing for meaning, travel or elders' advice; patience pays.",
        "चंद्र नौवें भाव में – धर्म, यात्रा या बड़ों की सलाह से लाभ; धैर्य रखें।"),
    10: ("Moon in 10th – strong focus on work, responsibility and recognition.",
         "चंद्र दसवें भाव में – कार्य, ज़िम्मेदारी और सम्मान पर अच्छा ध्यान।"),
    11: ("Moon in 11th – gains, helpful friends, networking and fulfilment of small goals.",
         "चंद्र ग्यारहवें भाव में – लाभ, मित्रों का सहयोग, संपर्क व इच्छापूर्ति के संकेत।"),
    12: ("Moon in 12th – higher expenses, fatigue or need for quiet rest; avoid impulse spending.",
         "चंद्र बारहवें भाव में – खर्च, थकान या एकांत की आवश्यकता; अनावश्यक खर्च से बचें।"),
}


def _T(lang: str, x: str) -> str:
    return i18n.term(lang, x)


def _ord(n: int, hi: bool) -> str:
    return ord_hi(n) if hi else ({1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th"))


def _nak_name(lon: float) -> tuple[int, str]:
    idx = int((lon % 360) // NAKSHATRA_SPAN) % 27
    return idx, _nak.NAK[idx]


def _day_yogas(day: date, p: dict, sun_lon: float, moon_nak_idx: int, birth_nak: int | None,
               natal_moon_sign: int | None, lang: str) -> dict:
    """Auspicious yogas & cautions for `day` from Nakshatra Jyotish (pp. 173–179)."""
    hi = lang == "hi"
    nak = p["nakshatra"]["name"]
    wd = (day.weekday() + 1) % 7  # Sun=0 .. Sat=6
    t15 = (p["tithi"]["number"] - 1) % 15 + 1
    good: list[str] = []
    caution: list[str] = []

    if wd == 4 and nak == "Pushya":
        good.append("गुरु पुष्य योग" if hi else "Guru-Pushya yoga")
    if wd == 0 and nak == "Pushya":
        good.append("रवि पुष्य योग" if hi else "Ravi-Pushya yoga")
    amrit = _nak.AMRIT_SIDDHI[wd]
    if amrit[0] == nak and t15 != amrit[1]:
        good.append("अमृत सिद्धि योग" if hi else "Amrit-siddhi yoga")
    sv = _nak.SARVARTHA[wd]
    if nak in sv[0] and t15 not in sv[1]:
        good.append("सर्वार्थ सिद्धि योग" if hi else "Sarvartha-siddhi yoga")
    sun_n = int((sun_lon % 360) // NAKSHATRA_SPAN) % 27
    if (moon_nak_idx - sun_n) % 27 + 1 in (4, 6, 10, 13, 20):
        good.append("रवि योग" if hi else "Ravi yoga")

    if _nak.DAGDHA[wd] == nak:
        caution.append("दग्ध नक्षत्र" if hi else "Dagdha nakshatra")
    if _nak.YAMAGHANTA[wd] == nak:
        caution.append("यमघंट योग" if hi else "Yamaghanta")
    if natal_moon_sign is not None and _nak.GHAT[natal_moon_sign] == nak:
        caution.append("घात नक्षत्र (नए कार्य टालें)" if hi else "Ghat nakshatra (avoid new starts)")

    tara_info = None
    if birth_nak is not None:
        tr = _nak.tara(birth_nak, moon_nak_idx)
        t_en, t_hi, t_good, m_en, m_hi = _nak.TARAS[tr]
        tara_info = {
            "index": tr + 1,
            "name": t_hi if hi else t_en,
            "good": t_good,
            "meaning": m_hi if hi else m_en,
        }
        if t_good is False:
            caution.append(f"{tara_info['name']} {'तारा' if hi else 'tara'} ({tara_info['meaning']})")

    return {"good_yogas": good, "cautions": caution, "tara": tara_info}


def _transit_score(p: str, hm: int, bindus: int | None) -> float:
    good = hm in GOOD_FROM_MOON[p]
    if p == "Moon":
        sc = 1.1 if good else (-1.3 if hm == 8 else (-0.75 if hm in (4, 12) else -0.45))
    elif p in FAST_WEIGHT:
        sc = FAST_WEIGHT[p] if good else -FAST_WEIGHT[p] * 0.7
    else:
        sc = SLOW_WEIGHT[p] if good else -SLOW_WEIGHT[p] * 0.65
    if bindus is not None:
        sc += 0.25 if bindus >= 5 else (-0.25 if bindus <= 2 else 0.0)
    return sc


def _daily_areas(chart: dict, L: dict[str, float], dasha_lords: list[str], lang: str) -> list[dict]:
    hi = lang == "hi"
    L_fn = (lambda en, h: h if hi else en)
    lagna = chart["lagna"]["sign_index"] - 1
    moon = chart["planets"]["Moon"]["sign_index"] - 1
    out = []
    for key, houses, en, h_ in AREAS:
        sc = 0.0
        why: list[str] = []
        for p in ("Moon", "Sun", "Mars", "Mercury", "Venus", "Jupiter", "Saturn"):
            si = int(L[p] // 30)
            hl = (si - lagna) % 12 + 1
            hm = (si - moon) % 12 + 1
            good = hm in GOOD_FROM_MOON[p]
            asp = {(hl - 1 + a - 1) % 12 + 1 for a in ASPECT.get(p, (7,))}
            if hl in houses or (p in ("Moon", "Jupiter", "Saturn", "Mars") and any(hh in asp for hh in houses)):
                touched = hl if hl in houses else next(hh for hh in houses if hh in asp)
                w = 0.75 if p == "Moon" else (0.45 if p in FAST else 0.35)
                sc += w if (good or p == "Jupiter") else -w * 0.8
                verb = ("गोचर" if hl == touched else "दृष्टि") if hi else ("transits" if hl == touched else "aspects")
                why.append(f"{_T(lang, p)} का भाव {touched} पर {verb} ({'शुभ' if good else 'सावधान'})" if hi
                           else f"{p} {verb} house {touched} ({'favourable' if good else 'mixed/care'})")
        for lord in dict.fromkeys(dasha_lords):
            pl = explain(chart, lord, "en")
            links = [hh for hh in houses if hh == pl["house"] or hh in pl["owns"]]
            if links:
                t = planet_tone(chart, lord)[0]
                sc += 0.35 if t > 0.3 else (-0.35 if t < -0.3 else 0.1)
                why.append(f"दशा स्वामी {_T(lang, lord)} भाव {'/'.join(map(str, links))} से जुड़ा" if hi
                           else f"Dasha lord {lord} linked to house {'/'.join(map(str, links))}")
        rk, rl = _rate(sc, hi)
        if not why:
            why = ["आज कोई विशेष गोचर दबाव नहीं – सामान्य दिन" if hi else "No strong transit trigger today – steady day"]
        text = (
            L_fn("Supportive planetary alignment today – good momentum for progress here.",
                 "आज इस क्षेत्र में ग्रहों का अच्छा सहयोग है – आगे बढ़ने के लिए अनुकूल समय।")
            if rk in ("excellent", "good") else
            L_fn("Mixed influences today – proceed steadily and double-check important details.",
                 "आज इस क्षेत्र में मिला-जुला प्रभाव है – सोच-समझकर और धैर्य से कदम बढ़ाएँ।")
            if rk == "mixed" else
            L_fn("Sensitive area today – avoid rushing, conflict, or unnecessary risks.",
                 "आज इस क्षेत्र में सावधानी रखें – जल्दबाज़ी, विवाद या अनावश्यक जोखिम से बचें।")
        )
        out.append({"area": key, "title": h_ if hi else en, "score": round(sc, 2),
                    "rating": rk, "rating_label": rl, "text": text, "reasons": why[:3]})
    return out


def _daily_day_core(chart: dict, dasha3: dict, tz: str, lat: float, lon: float, s: eph.Settings,
                    day: date, av: dict, ss_status, lang: str) -> dict:
    hi = lang == "hi"
    p = panchang(day, tz, lat, lon, s)
    jd = eph.local_to_jd(datetime(day.year, day.month, day.day, 12), tz)
    L = _lons(jd, s)
    natal_moon = chart["planets"]["Moon"]["sign_index"] - 1
    birth_nak = chart["planets"]["Moon"]["nakshatra"]["index"] - 1
    lagna = chart["lagna"]["sign_index"] - 1

    moon_sign = int(L["Moon"] // 30)
    hm_moon = (moon_sign - natal_moon) % 12 + 1
    hl_moon = (moon_sign - lagna) % 12 + 1
    day_nak_idx = _nak.IDX.get(p["nakshatra"]["name"])
    if day_nak_idx is None:
        day_nak_idx, _ = _nak_name(L["Moon"])

    yogas = _day_yogas(day, p, L["Sun"], day_nak_idx, birth_nak, natal_moon, lang)
    tara_info = yogas["tara"]

    # Dasha at noon on `day`
    mid = datetime(day.year, day.month, day.day, 12)
    pers = _periods_in(dasha3, mid, mid, level=3)
    pd_now = pers[0] if pers else None
    dasha_score = 0.0
    if pd_now:
        pr = period_reading(chart, pd_now["md"], pd_now["ad"], lang)
        pdr = period_reading(chart, pd_now["ad"], pd_now["pd"], lang)
        dasha_score = 0.25 * pr["score"] + 0.3 * pdr["score"]
    else:
        pr = pdr = None

    # All 9 transits today
    transits = []
    sc_transits = 0.0
    for pl_name in PLANETS:
        si = int(L[pl_name] // 30)
        _, nak_nm = _nak_name(L[pl_name])
        hm = (si - natal_moon) % 12 + 1
        hl = (si - lagna) % 12 + 1
        good = hm in GOOD_FROM_MOON[pl_name]
        bindus = av["bav"][pl_name][si] if pl_name in av["bav"] else None
        pts = _transit_score(pl_name, hm, bindus)
        sc_transits += pts
        mean = BHAV[hl][3 if hi else 2].split(",")[0].strip()
        note = (f"{_T(lang, pl_name)} {_T(lang, SIGNS[si])} में (चंद्र से {ord_hi(hm)}, लग्न से {ord_hi(hl)} – {mean})"
                if hi else
                f"{pl_name} in {SIGNS[si]} ({_ord(hm, False)} from Moon, {_ord(hl, False)} from Lagna – {mean})")
        transits.append({
            "planet": pl_name, "sign": SIGNS[si], "nakshatra": nak_nm,
            "house_from_moon": hm, "house_from_lagna": hl, "good": good,
            "bindus": bindus, "score": round(pts, 2), "text": note,
        })

    # Tara & yoga adjustment + Sade Sati backdrop
    tara_adj = 0.45 if tara_info and tara_info["good"] is True else (-0.55 if tara_info and tara_info["good"] is False else 0.0)
    yoga_adj = 0.25 if yogas["good_yogas"] else 0.0
    caution_adj = -0.2 * len([c for c in yogas["cautions"] if "तारा" not in c and "tara" not in c])
    ss = ss_status(mid) if ss_status else {}
    ss_adj = -0.35 if ss.get("sade_sati") else (-0.2 if ss.get("dhaiya") else 0.0)

    total = round(sc_transits * 0.65 + dasha_score + tara_adj + yoga_adj + caution_adj + ss_adj, 2)
    rk, rl = _rate(total, hi)

    return {
        "panchang": p, "L": L, "moon_sign": moon_sign, "hm_moon": hm_moon, "hl_moon": hl_moon,
        "yogas": yogas, "tara": tara_info, "pd_now": pd_now, "pr": pr, "pdr": pdr,
        "transits": transits, "sade_sati": ss, "score": total, "rating": rk, "rating_label": rl,
    }


def for_chart(chart: dict, dasha3: dict, birth: datetime, tz: str, lat: float, lon: float, s: eph.Settings,
              day: date, lang: str = "en", ss_status=None) -> dict:
    """Personalized daily horoscope for `chart` on `day`, plus a 7-day outlook strip."""
    hi = lang == "hi"
    L_fn = (lambda en, h: h if hi else en)
    av = _av(chart)
    core = _daily_day_core(chart, dasha3, tz, lat, lon, s, day, av, ss_status, lang)
    p = core["panchang"]
    hm = core["hm_moon"]
    hl = core["hl_moon"]
    moon_sign_name = SIGNS[core["moon_sign"]]
    moon_bindus = av["bav"]["Moon"][core["moon_sign"]]
    sav_sign = av["sav"][core["moon_sign"]]
    chandrashtama = hm == 8
    moon_good = hm in GOOD_FROM_MOON["Moon"]

    vara_lord = VARA_LORDS[day.weekday()]
    pd_now = core["pd_now"]
    dasha_lords = [pd_now["md"], pd_now["ad"], pd_now["pd"]] if pd_now else []
    areas = _daily_areas(chart, core["L"], dasha_lords, lang)
    best_areas = [a["title"] for a in sorted(areas, key=lambda x: -x["score"])[:2]]
    care_areas = [a["title"] for a in sorted(areas, key=lambda x: x["score"])[:2] if a["score"] < 0.2]

    # Chandrabala summary
    chandra_note = MOON_HOUSE_NOTE[hm][1 if hi else 0]
    chandra_status = "chandrashtama" if chandrashtama else ("good" if moon_good else "mixed")
    chandra_label = (L_fn("Chandrashtama (caution)", "चंद्राष्टम (सावधानी)") if chandrashtama else
                     L_fn("Favourable", "शुभ चंद्रबल") if moon_good else L_fn("Average / Restful", "सामान्य / मध्यम"))

    # Overall summary paragraph
    natal_rashi_i = chart["planets"]["Moon"]["sign_index"] - 1
    natal_rashi = SIGNS[natal_rashi_i]
    natal_rashi_sa = SIGNS_SANSKRIT[natal_rashi_i]
    summary_parts = [
        L_fn(f"For your {natal_rashi} ({natal_rashi_sa}) Rashi — {day.strftime('%A, %d %B %Y')} is overall a {core['rating_label']} day.",
             f"आपकी {_T(lang, natal_rashi)} ({natal_rashi_sa}) राशि के लिए {day.isoformat()} ({_T(lang, p['vara'])}) कुल मिलाकर {core['rating_label']} दिन है।"),
        L_fn(f"Transit Moon is in {moon_sign_name} ({_ord(hm, False)} from your natal Moon, {_ord(hl, False)} from Lagna) with {moon_bindus} Ashtakavarga bindus.",
             f"गोचर चंद्र {_T(lang, moon_sign_name)} में है (जन्म चंद्र से {ord_hi(hm)}, लग्न से {ord_hi(hl)}) – अष्टकवर्ग बिंदु {moon_bindus}।"),
        chandra_note,
    ]
    if core["tara"]:
        summary_parts.append(L_fn(
            f"Tarabala: {core['tara']['name']} tara ({core['tara']['meaning']}).",
            f"तारा बल: {core['tara']['name']} तारा ({core['tara']['meaning']})।"))
    if best_areas:
        summary_parts.append(L_fn("Supportive areas: ", "सहयोगी क्षेत्र: ") + "; ".join(best_areas) + ("।" if hi else "."))
    if care_areas:
        summary_parts.append(L_fn("Take extra care with: ", "सावधानी रखें: ") + "; ".join(care_areas) + ("।" if hi else "."))

    # Guidance: favourable vs avoid
    favour = []
    avoid = []
    if moon_good:
        favour.append(L_fn("Good Chandrabala supports routine initiatives and meetings.", "शुभ चंद्रबल दैनिक कार्यों और मुलाक़ातों में सहायक है।"))
    if core["yogas"]["good_yogas"]:
        favour.append(L_fn("Auspicious muhurta: ", "शुभ योग: ") + ", ".join(core["yogas"]["good_yogas"]) + ("।" if hi else "."))
    if best_areas:
        favour.append(L_fn("Focus on: ", "प्राथमिकता दें: ") + ", ".join(best_areas) + ("।" if hi else "."))
    if not favour:
        favour.append(L_fn("Steady routine work, planning and reflection.", "नियमित कार्य, योजना और शांत मन से काम करना।"))

    if chandrashtama:
        avoid.append(L_fn("Chandrashtama: avoid major financial decisions, arguments or new beginnings.",
                          "चंद्राष्टम: बड़े आर्थिक फ़ैसले, विवाद या नए काम की शुरुआत टालें।"))
    if core["yogas"]["cautions"]:
        avoid.extend(core["yogas"]["cautions"])
    avoid.append(L_fn(f"Avoid important starts during Rahu Kaal ({p['rahu_kaal']['start'][11:16]}–{p['rahu_kaal']['end'][11:16]}).",
                      f"राहु काल ({p['rahu_kaal']['start'][11:16]}–{p['rahu_kaal']['end'][11:16]}) में शुभ कार्य आरंभ न करें।"))

    # Simple daily tip / remedy (weekday lord + Moon if Chandrashtama)
    tip_planet = "Moon" if chandrashtama else vara_lord
    rem = REM_PLANET[tip_planet]
    moon_lord = SIGN_LORDS[chart["planets"]["Moon"]["sign_index"] - 1]
    nums = list(dict.fromkeys(LUCKY_NUMBERS[vara_lord] + LUCKY_NUMBERS[moon_lord]))[:4]
    daily_tip = {
        "planet": tip_planet,
        "colour": VARA_COLOUR[vara_lord][1 if hi else 0],
        "lucky_numbers": nums,
        "deity": f"{rem['deity'][1 if hi else 0]} ({rem['avatar'][1 if hi else 0]})",
        "mantra": rem["mantra"] if hi else rem["mantra_en"],
        "practice": rem["practice"][1 if hi else 0],
        "daana": rem["daana"][1 if hi else 0],
    }

    # Abhijit muhurta (8th of 15 daytime muhurtas, centred around solar noon)
    rise_dt = datetime.fromisoformat(p["sunrise"])
    set_dt = datetime.fromisoformat(p["sunset"])
    muh = (set_dt - rise_dt) / 15
    ab_start = rise_dt + muh * 7
    ab_end = rise_dt + muh * 8

    # Health watch (birth nakshatra + today's transit nakshatra)
    birth_nak_name = chart["planets"]["Moon"]["nakshatra"]["name"]
    day_nak_name = p["nakshatra"]["name"]
    health_watch = []
    for kind, nm in (("birth", birth_nak_name), ("today", day_nak_name)):
        hw = _nak.HEALTH.get(nm)
        if hw:
            health_watch.append({
                "kind": kind,
                "nakshatra": nm,
                "parts": hw[0][1 if hi else 0],
                "watch": hw[1][1 if hi else 0],
            })

    # 7-day strip (today + next 6 days)
    week = []
    for offset in range(7):
        d_i = day + timedelta(days=offset)
        c_i = core if offset == 0 else _daily_day_core(chart, dasha3, tz, lat, lon, s, d_i, av, ss_status, lang)
        week.append({
            "date": d_i.isoformat(),
            "weekday": _nak.DAY_HI[(d_i.weekday() + 1) % 7] if hi else _nak.DAY[(d_i.weekday() + 1) % 7],
            "vara": c_i["panchang"]["vara"],
            "nakshatra": c_i["panchang"]["nakshatra"]["name"],
            "moon_sign": SIGNS[c_i["moon_sign"]],
            "house_from_moon": c_i["hm_moon"],
            "chandrashtama": c_i["hm_moon"] == 8,
            "tara": c_i["tara"]["name"] if c_i["tara"] else "",
            "tara_good": c_i["tara"]["good"] if c_i["tara"] else None,
            "score": c_i["score"],
            "rating": c_i["rating"],
            "rating_label": c_i["rating_label"],
        })

    return {
        "date": day.isoformat(),
        "tz": tz,
        "score": core["score"],
        "rating": core["rating"],
        "rating_label": core["rating_label"],
        "summary": " ".join(summary_parts),
        "natal": {
            "lagna": chart["lagna"]["sign"],
            "lagna_sanskrit": SIGNS_SANSKRIT[chart["lagna"]["sign_index"] - 1],
            "moon_sign": chart["planets"]["Moon"]["sign"],
            "moon_rashi_sanskrit": SIGNS_SANSKRIT[natal_rashi_i],
            "moon_lord": SIGN_LORDS[natal_rashi_i],
            "nakshatra": birth_nak_name,
            "pada": chart["planets"]["Moon"]["nakshatra"]["pada"],
            "ghat_nakshatra": _nak.GHAT[natal_rashi_i],
        },
        "panchang": {
            "vara": p["vara"],
            "vara_lord": vara_lord,
            "tithi": p["tithi"],
            "nakshatra": p["nakshatra"],
            "yoga": p["yoga"],
            "karana": p["karana"],
            "sunrise": p["sunrise"],
            "sunset": p["sunset"],
            "rahu_kaal": p["rahu_kaal"],
            "abhijit": {
                "start": ab_start.isoformat(timespec="minutes"),
                "end": ab_end.isoformat(timespec="minutes"),
            },
        },
        "chandrabala": {
            "moon_sign": moon_sign_name,
            "house_from_moon": hm,
            "house_from_lagna": hl,
            "favourable": moon_good,
            "chandrashtama": chandrashtama,
            "status": chandra_status,
            "label": chandra_label,
            "bindus": moon_bindus,
            "sav": sav_sign,
            "note": chandra_note,
        },
        "tarabala": core["tara"],
        "yogas": core["yogas"]["good_yogas"],
        "cautions": core["yogas"]["cautions"],
        "dasha_now": dasha_lords,
        "dasha_period": pd_now,
        "dasha_reading": core["pdr"] or core["pr"],
        "sade_sati": core["sade_sati"],
        "areas": areas,
        "transits": core["transits"],
        "health_watch": health_watch,
        "guidance": {"favour": favour, "avoid": avoid},
        "daily_tip": daily_tip,
        "week": week,
        "method": L_fn(
            "Chandrabala (Moon from natal Moon) + Tarabala + Ashtakavarga bindus + daily Gochara + running Vimshottari dasha.",
            "चंद्रबल (जन्म चंद्र से गोचर चंद्र) + तारा बल + अष्टकवर्ग बिंदु + दैनिक गोचर + वर्तमान विंशोत्तरी दशा।"),
        "disclaimer": L_fn(
            "Daily readings show general tendencies, not fixed fate; use your own judgement.",
            "दैनिक राशिफल सामान्य प्रवृत्तियाँ बताता है, निश्चित भविष्य नहीं; अपने विवेक से निर्णय लें।"),
    }


def _rashi_areas(L: dict[str, float], rashi_idx: int, day_nak_name: str, lang: str) -> list[dict]:
    hi = lang == "hi"
    L_fn = (lambda en, h: h if hi else en)
    hm_of = {p: (int(L[p] // 30) - rashi_idx) % 12 + 1 for p in PLANETS}
    karaka = {
        "career": ("Sun", "Saturn"),
        "finance": ("Jupiter", "Venus"),
        "love": ("Venus", "Moon"),
        "health": ("Moon", "Mars"),
        "learning": ("Mercury", "Jupiter"),
    }
    out = []
    for key, houses, en, h_ in RASHI_AREAS:
        sc = 0.0
        why: list[str] = []
        for p in ("Moon", "Sun", "Mars", "Mercury", "Venus", "Jupiter", "Saturn"):
            hm = hm_of[p]
            good = hm in GOOD_FROM_MOON[p]
            asp = {(hm - 1 + a - 1) % 12 + 1 for a in ASPECT.get(p, (7,))}
            if hm in houses or (p in ("Moon", "Jupiter", "Saturn", "Mars") and any(hh in asp for hh in houses)):
                touched = hm if hm in houses else next(hh for hh in houses if hh in asp)
                w = 0.7 if p == "Moon" else (0.45 if p in FAST else 0.35)
                sc += w if (good or p == "Jupiter") else -w * 0.75
                verb = ("गोचर" if hm == touched else "दृष्टि") if hi else ("transits" if hm == touched else "aspects")
                why.append(L_fn(
                    f"{p} {verb} {_ord(touched, False)} house ({'supportive' if good else 'asks care'})",
                    f"{_T(lang, p)} की {ord_hi(touched)} भाव पर {verb} ({'शुभ' if good else 'सावधानी'})"))
        for kp in karaka[key]:
            khm = hm_of[kp]
            if khm in GOOD_FROM_MOON[kp]:
                sc += 0.25
                why.append(L_fn(
                    f"{kp} is well placed in {_ord(khm, False)} from your Moon",
                    f"{_T(lang, kp)} चंद्र से {ord_hi(khm)} भाव में अनुकूल है"))
        if key == "health" and day_nak_name in _nak.HEALTH:
            parts = _nak.HEALTH[day_nak_name][0][1 if hi else 0]
            why.append(L_fn(f"Today's star ({day_nak_name}) governs: {parts}",
                            f"आज का नक्षत्र ({_T(lang, day_nak_name)}) इन अंगों से जुड़ा है: {parts}"))
        rk, rl = _rate(round(sc, 2), hi)
        if not why:
            why = [L_fn("Steady planetary flow today – normal routine goes smoothly.",
                        "आज ग्रहों का प्रवाह सामान्य है – दैनिक कार्य सहज रहेंगे।")]
        summary = (
            L_fn("Favourable energy here today – good for taking constructive steps.",
                 "आज इस क्षेत्र में अच्छा सहयोग मिलेगा – सकारात्मक कदम बढ़ाएँ।")
            if rk in ("excellent", "good") else
            L_fn("Mixed influences – move step by step and double-check details.",
                 "मिला-जुला प्रभाव – सोच-समझकर और धैर्य से आगे बढ़ें।")
            if rk == "mixed" else
            L_fn("Sensitive area today – avoid rushing or unnecessary strain.",
                 "आज इस क्षेत्र में सावधानी रखें – जल्दबाज़ी व तनाव से बचें।")
        )
        out.append({"area": key, "title": h_ if hi else en, "score": round(sc, 2),
                    "rating": rk, "rating_label": rl, "text": summary, "reasons": why[:3]})
    return out


def by_signs(day: date, tz: str = "Asia/Kolkata", lat: float = 28.6139, lon: float = 77.2090,
             s: eph.Settings = eph.Settings(), lang: str = "en") -> dict:
    """12-Rashi (Moon sign) daily horoscope for `day` based on Moon & planetary gochara."""
    hi = lang == "hi"
    L_fn = (lambda en, h: h if hi else en)

    # Precompute 7 days of Panchang + planetary longitudes once for all 12 Rashis
    day_snapshots = []
    for offset in range(7):
        d_i = day + timedelta(days=offset)
        p_i = panchang(d_i, tz, lat, lon, s)
        jd_i = eph.local_to_jd(datetime(d_i.year, d_i.month, d_i.day, 12), tz)
        L_i = _lons(jd_i, s)
        day_snapshots.append((d_i, p_i, L_i))

    _, p, L = day_snapshots[0]
    moon_sign = int(L["Moon"] // 30)
    saturn_sign = int(L["Saturn"] // 30)
    vara_lord = VARA_LORDS[day.weekday()]
    day_nak_idx = _nak.IDX.get(p["nakshatra"]["name"])
    if day_nak_idx is None:
        day_nak_idx, _ = _nak_name(L["Moon"])
    day_nak_name = _nak.NAK[day_nak_idx]
    day_yogas = _day_yogas(day, p, L["Sun"], day_nak_idx, None, None, lang)
    health_watch = _nak.HEALTH.get(day_nak_name)

    signs_out = []
    for rashi_idx, rashi_name in enumerate(SIGNS):
        rashi_lord = SIGN_LORDS[rashi_idx]
        hm_moon = (moon_sign - rashi_idx) % 12 + 1
        moon_good = hm_moon in GOOD_FROM_MOON["Moon"]
        chandrashtama = hm_moon == 8

        # Saturn phase (Sade Sati / Dhaiya) relative to this Rashi
        hm_sat = (saturn_sign - rashi_idx) % 12 + 1
        saturn_phase = {12: "rising (12th)", 1: "peak (1st)", 2: "setting (2nd)",
                        4: "Kantaka/Ardhashtama (4th)", 8: "Ashtama (8th)"}.get(hm_sat)

        sc = 0.0
        good_planets = []
        care_planets = []
        transits = []
        for pl_name in PLANETS:
            si = int(L[pl_name] // 30)
            _, pl_nak = _nak_name(L[pl_name])
            hm = (si - rashi_idx) % 12 + 1
            good = hm in GOOD_FROM_MOON[pl_name]
            pts = _transit_score(pl_name, hm, None)
            sc += pts * (0.85 if pl_name == "Moon" else 0.55)
            if good:
                good_planets.append(pl_name)
            elif pl_name in ("Moon", "Sun", "Mars", "Saturn"):
                care_planets.append(pl_name)
            mean = BHAV[hm][3 if hi else 2].split(",")[0].strip()
            tr_txt = (f"{_T(lang, pl_name)} {_T(lang, SIGNS[si])} में – चंद्र राशि से {ord_hi(hm)} भाव ({mean}) {'[शुभ]' if good else '[सामान्य/सावधान]'}"
                      if hi else
                      f"{pl_name} in {SIGNS[si]} – {_ord(hm, False)} from {rashi_name} ({mean}) [{'favourable' if good else 'mixed/care'}]")
            transits.append({
                "planet": pl_name, "sign": SIGNS[si], "nakshatra": pl_nak,
                "house_from_moon": hm, "good": good, "score": round(pts, 2), "text": tr_txt,
            })

        ghat_nak = _nak.GHAT[rashi_idx]
        is_ghat = ghat_nak == p["nakshatra"]["name"]
        if is_ghat:
            sc -= 0.25
        rk, rl = _rate(round(sc, 2), hi)

        chandra_note = MOON_HOUSE_NOTE[hm_moon][1 if hi else 0]
        areas = _rashi_areas(L, rashi_idx, day_nak_name, lang)
        best_areas = [a["title"] for a in sorted(areas, key=lambda x: -x["score"])[:2]]
        care_areas = [a["title"] for a in sorted(areas, key=lambda x: x["score"])[:2] if a["score"] < 0.2]

        # Rich multi-sentence overview
        overview_parts = [
            L_fn(f"For {rashi_name} (ruled by {rashi_lord}), today's Moon transits your {_ord(hm_moon, False)} house in {SIGNS[moon_sign]} ({day_nak_name} nakshatra).",
                 f"{_T(lang, rashi_name)} राशि (स्वामी {_T(lang, rashi_lord)}) के लिए आज चंद्र {_T(lang, SIGNS[moon_sign])} में {_T(lang, day_nak_name)} नक्षत्र के साथ आपकी राशि से {ord_hi(hm_moon)} भाव में गोचर कर रहा है।"),
            chandra_note,
        ]
        fast_good = [gp for gp in ("Sun", "Mars", "Mercury", "Venus") if gp in good_planets]
        if fast_good:
            overview_parts.append(L_fn(
                f"Supportive transits from {', '.join(fast_good)} boost confidence, communication and daily flow.",
                f"{', '.join(_T(lang, x) for x in fast_good)} का शुभ गोचर आत्मविश्वास, संवाद और कार्यक्षमता को बल दे रहा है।"))
        jup_hm = (int(L["Jupiter"] // 30) - rashi_idx) % 12 + 1
        if jup_hm in GOOD_FROM_MOON["Jupiter"]:
            overview_parts.append(L_fn(
                f"Jupiter in your {_ord(jup_hm, False)} house offers wisdom, guidance and steady growth.",
                f"{ord_hi(jup_hm)} भाव में गुरु का गोचर मार्गदर्शन, सौभाग्य और स्थिर प्रगति दे रहा है।"))
        if saturn_phase:
            overview_parts.append(L_fn(
                f"With Saturn in {_T(lang, saturn_phase)}, patience, discipline and steady effort pay off best.",
                f"शनि के {_T(lang, saturn_phase)} प्रभाव में धैर्य, अनुशासन और निरंतर प्रयास श्रेष्ठ फल देंगे।"))
        if is_ghat:
            overview_parts.append(L_fn(
                f"Caution: {ghat_nak} is a Ghat nakshatra for {rashi_name} – avoid major new launches.",
                f"सावधानी: {_T(lang, ghat_nak)} {_T(lang, rashi_name)} के लिए घात नक्षत्र है – बड़े नए कार्य आज आरंभ न करें।"))

        # Short highlights for the 12-sign summary grid
        jupiter_hm = jup_hm
        venus_hm = (int(L["Venus"] // 30) - rashi_idx) % 12 + 1
        saturn_hm = hm_sat
        highlights = [
            L_fn(f"Work & finance: {'supportive momentum' if hm_moon in (3, 6, 10, 11) or jupiter_hm in (2, 5, 9, 11) else 'steady pace; plan carefully'}.",
                 f"कार्य व धन: {'अच्छी गति और सहयोग' if hm_moon in (3, 6, 10, 11) or jupiter_hm in (2, 5, 9, 11) else 'सामान्य गति; सोच-समझकर कदम बढ़ाएँ'}।"),
            L_fn(f"Relationships: {'warm & cooperative' if hm_moon in (1, 3, 7, 11) or venus_hm in (1, 2, 4, 5, 9, 11) else 'listen patiently'}.",
                 f"संबंध: {'मधुर और सहयोगपूर्ण' if hm_moon in (1, 3, 7, 11) or venus_hm in (1, 2, 4, 5, 9, 11) else 'धैर्य से संवाद करें'}।"),
            L_fn(f"Health & mood: {'take extra rest (Chandrashtama)' if chandrashtama else 'avoid fatigue' if hm_moon == 12 or saturn_hm in (1, 8, 12) else 'balanced energy'}.",
                 f"स्वास्थ्य व मन: {'विश्राम व सावधानी रखें (चंद्राष्टम)' if chandrashtama else 'थकान से बचें' if hm_moon == 12 or saturn_hm in (1, 8, 12) else 'संतुलित ऊर्जा'}।"),
        ]

        # Guidance (Do's & Don'ts)
        favour = []
        if moon_good:
            favour.append(L_fn("Favourable Chandrabala supports meetings, decisions and visible progress.",
                               "शुभ चंद्रबल मुलाक़ातों, निर्णयों और प्रगति में सहायक है।"))
        if day_yogas["good_yogas"]:
            favour.append(L_fn("Auspicious yogas today: ", "आज के शुभ योग: ") + ", ".join(day_yogas["good_yogas"]) + ("।" if hi else "."))
        if best_areas:
            favour.append(L_fn("Best focus areas: ", "प्रमुख अनुकूल क्षेत्र: ") + ", ".join(best_areas) + ("।" if hi else "."))
        if not favour:
            favour.append(L_fn("Complete pending routine tasks, organize plans and stay calm.",
                               "लंबित नियमित कार्य पूरे करें, योजना बनाएँ और शांत रहें।"))

        avoid = []
        if chandrashtama:
            avoid.append(L_fn("Chandrashtama (Moon in 8th): avoid big financial risks, arguments or new ventures.",
                              "चंद्राष्टम (आठवाँ चंद्र): बड़े आर्थिक जोखिम, विवाद या नए आरंभ से बचें।"))
        if is_ghat:
            avoid.append(L_fn(f"Ghat nakshatra ({ghat_nak}): postpone auspicious ceremonies or major starts.",
                              f"घात नक्षत्र ({_T(lang, ghat_nak)}): बड़े शुभ कार्य या नई शुरुआत टालें।"))
        if care_areas:
            avoid.append(L_fn("Needs patience: ", "इन विषयों में धैर्य रखें: ") + ", ".join(care_areas) + ("।" if hi else "."))
        avoid.append(L_fn(f"Avoid new starts during Rahu Kaal ({p['rahu_kaal']['start'][11:16]}–{p['rahu_kaal']['end'][11:16]}).",
                          f"राहु काल ({p['rahu_kaal']['start'][11:16]}–{p['rahu_kaal']['end'][11:16]}) में नए कार्य शुरू न करें।"))

        rem_planet = "Moon" if chandrashtama else rashi_lord
        rem = REM_PLANET[rem_planet]
        tip = L_fn(
            f"{rem['practice'][0]}. Lucky colour: {VARA_COLOUR[rashi_lord][0]}.",
            f"{rem['practice'][1]}। शुभ रंग: {VARA_COLOUR[rashi_lord][1]}।")
        if is_ghat:
            tip += L_fn(f" Note: {ghat_nak} is Ghat nakshatra for {rashi_name} – avoid major new starts.",
                        f" ध्यान दें: {_T(lang, ghat_nak)} {_T(lang, rashi_name)} के लिए घात नक्षत्र है – बड़े नए कार्य टालें।")

        # 7-day outlook for this Rashi
        week = []
        for d_i, p_i, L_i in day_snapshots:
            ms_i = int(L_i["Moon"] // 30)
            hm_i = (ms_i - rashi_idx) % 12 + 1
            sc_i = sum(_transit_score(pl_n, (int(L_i[pl_n] // 30) - rashi_idx) % 12 + 1, None)
                       * (0.85 if pl_n == "Moon" else 0.55) for pl_n in PLANETS)
            if _nak.GHAT[rashi_idx] == p_i["nakshatra"]["name"]:
                sc_i -= 0.25
            rk_i, rl_i = _rate(round(sc_i, 2), hi)
            week.append({
                "date": d_i.isoformat(),
                "weekday": _nak.DAY_HI[(d_i.weekday() + 1) % 7] if hi else _nak.DAY[(d_i.weekday() + 1) % 7],
                "moon_sign": SIGNS[ms_i],
                "nakshatra": p_i["nakshatra"]["name"],
                "moon_house": hm_i,
                "chandrashtama": hm_i == 8,
                "score": round(sc_i, 2),
                "rating": rk_i,
                "rating_label": rl_i,
            })

        signs_out.append({
            "sign": rashi_name,
            "sanskrit": SIGNS_SANSKRIT[rashi_idx],
            "sign_index": rashi_idx + 1,
            "lord": rashi_lord,
            "score": round(sc, 2),
            "rating": rk,
            "rating_label": rl,
            "moon_house": hm_moon,
            "moon_good": moon_good,
            "chandrashtama": chandrashtama,
            "ghat_nakshatra": is_ghat,
            "ghat_nakshatra_name": ghat_nak,
            "saturn_phase": saturn_phase,
            "summary": chandra_note,
            "overview": " ".join(overview_parts),
            "highlights": highlights,
            "areas": areas,
            "guidance": {"favour": favour, "avoid": avoid},
            "transits": transits,
            "week": week,
            "colour": VARA_COLOUR[rashi_lord][1 if hi else 0],
            "lucky_numbers": LUCKY_NUMBERS[rashi_lord],
            "deity": f"{rem['deity'][1 if hi else 0]} ({rem['avatar'][1 if hi else 0]})",
            "daana": rem["daana"][1 if hi else 0],
            "tip": tip,
            "mantra": rem["mantra"] if hi else rem["mantra_en"],
            "favorable_transits": good_planets,
            "care_transits": care_planets,
            "health_watch": {"parts": health_watch[0][1 if hi else 0], "watch": health_watch[1][1 if hi else 0]} if health_watch else None,
        })

    return {
        "date": day.isoformat(),
        "tz": tz,
        "panchang": {
            "vara": p["vara"],
            "vara_lord": vara_lord,
            "tithi": p["tithi"],
            "nakshatra": p["nakshatra"],
            "yoga": p["yoga"],
            "karana": p["karana"],
            "sunrise": p["sunrise"],
            "sunset": p["sunset"],
            "rahu_kaal": p["rahu_kaal"],
        },
        "moon_sign": SIGNS[moon_sign],
        "yogas": day_yogas["good_yogas"],
        "cautions": day_yogas["cautions"],
        "signs": signs_out,
        "disclaimer": L_fn(
            "Rashi-based predictions use the Moon sign gochara; open a Kundli for a personalized reading.",
            "राशिफल चंद्र राशि के गोचर पर आधारित है; व्यक्तिगत फल के लिए अपनी कुंडली खोलें।"),
    }
