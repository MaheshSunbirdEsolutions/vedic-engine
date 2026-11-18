"""Simple summary report: the current period and what to do about it, in plain words.

Nothing new is calculated here. The module takes the outputs of the issues report, the
year-wise prediction and the running dasha, and rewrites them as short sentences without
tables or technical terms, plus a short list of remedies a beginner can actually follow.
"""
from __future__ import annotations

from datetime import date, datetime

from . import i18n

DAY = {"Sun": ("Sunday", "रविवार"), "Moon": ("Monday", "सोमवार"), "Mars": ("Tuesday", "मंगलवार"),
       "Mercury": ("Wednesday", "बुधवार"), "Jupiter": ("Thursday", "गुरुवार"), "Venus": ("Friday", "शुक्रवार"),
       "Saturn": ("Saturday", "शनिवार"), "Rahu": ("Saturday", "शनिवार"), "Ketu": ("Tuesday", "मंगलवार")}

PLAIN = {  # what a planet stands for, in everyday words
    "Sun": ("confidence, father, government and reputation", "आत्मविश्वास, पिता, सरकार और मान-सम्मान"),
    "Moon": ("mind, mother, emotions and peace", "मन, माता, भावनाएँ और शांति"),
    "Mars": ("energy, courage, land, siblings and anger", "ऊर्जा, साहस, भूमि, भाई-बहन और क्रोध"),
    "Mercury": ("speech, business, learning and nerves", "वाणी, व्यापार, पढ़ाई और नसें"),
    "Jupiter": ("wisdom, children, teachers, wealth and faith", "ज्ञान, संतान, गुरु, धन और आस्था"),
    "Venus": ("marriage, comfort, art, vehicles and luxury", "विवाह, सुख-सुविधा, कला, वाहन और विलासिता"),
    "Saturn": ("hard work, delays, discipline, servants and old age", "परिश्रम, देरी, अनुशासन, सेवक और वृद्धावस्था"),
    "Rahu": ("sudden events, confusion, foreign links and ambition", "अचानक घटनाएँ, भ्रम, विदेश और महत्वाकांक्षा"),
    "Ketu": ("detachment, spirituality, hidden troubles and loss", "वैराग्य, आध्यात्म, छिपी परेशानियाँ और हानि"),
}

TONE = {  # rating key -> (en, hi) plain sentence about the period
    "excellent": ("This is a strong, supportive time. Use it to start important things.",
                  "यह मज़बूत और सहयोगी समय है। महत्वपूर्ण काम इसी समय शुरू करें।"),
    "good": ("This is a good time overall. Steady effort brings results.",
             "कुल मिलाकर यह अच्छा समय है। लगातार मेहनत का फल मिलेगा।"),
    "mixed": ("This is a mixed time: some things move, some get stuck. Go step by step.",
              "यह मिला-जुला समय है: कुछ काम बनेंगे, कुछ अटकेंगे। एक-एक कदम आगे बढ़ें।"),
    "challenging": ("This is a testing time. Results come slowly; patience and remedies help a lot.",
                    "यह परीक्षा का समय है। फल धीरे मिलेंगे; धैर्य और उपाय बहुत मदद करेंगे।"),
}

PRIORITY = {"high": ("needs attention now", "अभी ध्यान दें"), "medium": ("keep an eye on it", "नज़र रखें"),
            "low": ("minor", "मामूली")}


def _T(lang, x):
    return i18n.term(lang, x)


def _d(s: str | None, hi: bool) -> str:
    if not s:
        return ""
    d = date.fromisoformat(s[:10])
    if hi:
        m = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"][d.month - 1]
        return f"{d.day} {m} {d.year}"
    return f"{d.day} {d.strftime('%B %Y')}"   # no %-d: it fails on Windows


_date = _d


def _items(full: dict, sid: str) -> list[str]:
    for s in full.get("systems", []):
        if s["id"] == sid:
            return s.get("items", [])
    return []


def _current(dasha: dict, now: datetime) -> tuple[dict | None, dict | None, dict | None]:
    """Running mahadasha, antardasha, and the next antardasha."""
    key = now.isoformat()
    flat = []
    md_now = ad_now = None
    for md in dasha["mahadashas"]:
        for ad in md.get("sub", []):
            flat.append((md, ad))
    for i, (md, ad) in enumerate(flat):
        if ad["start"][:19] <= key <= ad["end"][:19]:
            md_now, ad_now = md, ad
            nxt = flat[i + 1] if i + 1 < len(flat) else None
            return md_now, ad_now, nxt
    return None, None, None


def remedy_steps(full: dict, p: str, lang: str, lk_quick: dict | None = None) -> list[str]:
    """Short, plain remedy steps for one planet, from remedies.full_set()."""
    hi = lang == "hi"
    L = (lambda en, h: h if hi else en)
    mantra = _items(full, "mantra")
    steps = []
    beeja = next((m for m in mantra if m.startswith(("Beeja mantra", "बीज मंत्र"))), None)
    if beeja:
        name = beeja.split(":", 1)[-1].strip()
        dev = next((m.split(":", 1)[-1].strip() for m in mantra if m.startswith("Devanagari")), "")
        dev = "" if dev == name else dev
        steps.append(L(f"Mantra: every day, or at least every {DAY[p][0]}, say “{name}” 108 times"
                       + (f" ({dev})" if dev else "") + ".",
                       f"मंत्र: रोज़, या कम से कम हर {DAY[p][1]}, “{dev or name}” का 108 बार जाप करें।"))
    path = _items(full, "path")
    if path:
        steps.append(L("Prayer: ", "पाठ: ") + path[0])
    daana = _items(full, "daana")
    if daana:
        steps.append(L("Give (daana): ", "दान: ") + " · ".join(x.split(":", 1)[-1].strip() for x in daana[:2]))
    lk = lk_quick
    if lk and lk.get("text"):
        steps.append(L("Lal Kitab quick remedy: ", "लाल किताब का त्वरित उपाय: ") + lk["text"])
    karma = _items(full, "karma")
    if karma:
        steps.append(L("Daily habit: ", "रोज़ की आदत: ") + karma[0])
    temples = full.get("temples") or []
    if temples:
        t = temples[0]
        steps.append(L(f"Temple visit (when possible): {t['name']}, {t['state']} – best on {t.get('when', '')}.",
                       f"मंदिर दर्शन (जब संभव हो): {t.get('name_hi') or t['name']}, {t['state']} – {t.get('when_hi') or t.get('when', '')}।"))
    gem = full.get("gem_verdict")
    gem_items = _items(full, "gem")
    gem_name = gem_items[0].split(";")[0] if gem_items else ""
    if gem == "avoid" and gem_name:
        steps.append(L(f"Do NOT wear this planet's gem ({gem_name}) – it would make the problem stronger.",
                       f"इस ग्रह का रत्न ({gem_name}) न पहनें – इससे समस्या बढ़ सकती है।"))
    elif gem == "suitable" and gem_name:
        steps.append(L(f"Gem: {gem_name} can help – but show your chart to an astrologer before wearing it.",
                       f"रत्न: {gem_name} मदद कर सकता है – पर पहनने से पहले किसी ज्योतिषी को कुंडली दिखा लें।"))
    return steps


def summary(chart: dict, dasha: dict, issues: dict, year: dict, next_months: list[dict],
            reading_now, reading_next, lang: str, now: datetime) -> dict:
    hi = lang == "hi"
    L = (lambda en, h: h if hi else en)
    sections = []

    # 1. where you are now
    md, ad, nxt = _current(dasha, now)
    now_par = []
    if md and ad:
        r = reading_now
        now_par.append(L(
            f"You are now in the period of {md['lord']} (main period, {_date(md['start'], False)} – {_date(md['end'], False)}) "
            f"and inside it the sub-period of {ad['lord']}, which lasts until {_date(ad['end'], False)}.",
            f"अभी आप पर {_T(lang, md['lord'])} की महादशा ({_date(md['start'], True)} – {_date(md['end'], True)}) चल रही है, "
            f"और उसके भीतर {_T(lang, ad['lord'])} की अंतर्दशा, जो {_date(ad['end'], True)} तक रहेगी।"))
        now_par.append(L(
            f"{md['lord']} stands for {PLAIN[md['lord']][0]}; {ad['lord']} stands for {PLAIN[ad['lord']][0]}. "
            f"So these are the matters that come up most in your life right now.",
            f"{_T(lang, md['lord'])} का संबंध {PLAIN[md['lord']][1]} से है; {_T(lang, ad['lord'])} का संबंध {PLAIN[ad['lord']][1]} से है। "
            f"इसलिए अभी जीवन में यही विषय सबसे ज़्यादा सामने आते हैं।"))
        if r["themes"]:
            now_par.append(L("In your chart these planets touch: ", "आपकी कुंडली में ये ग्रह इन बातों से जुड़े हैं: ")
                           + "; ".join(dict.fromkeys(t.split("–", 1)[-1].strip() for t in r["themes"][:3])) + ("।" if hi else "."))
        now_par.append(TONE[r["rating"]][1 if hi else 0])
        if nxt:
            n_md, n_ad = nxt
            rn = reading_next
            better = rn["score"] > r["score"] + 0.3
            worse = rn["score"] < r["score"] - 0.3
            now_par.append(L(
                f"On {_date(n_ad['start'], False)} the sub-period changes to {n_ad['lord']}"
                + (" – things should get easier then." if better else " – be a little more careful then." if worse else " – the overall feel stays much the same.")
                + (f" (The main period also changes, to {n_md['lord']}.)" if n_md is not md else ""),
                f"{_date(n_ad['start'], True)} से अंतर्दशा {_T(lang, n_ad['lord'])} की होगी"
                + (" – तब हालात आसान होने चाहिए।" if better else " – तब थोड़ी अधिक सावधानी रखें।" if worse else " – तब भी माहौल लगभग ऐसा ही रहेगा।")
                + (f" (महादशा भी बदलकर {_T(lang, n_md['lord'])} की होगी।)" if n_md is not md else "")))
    sections.append({"id": "now", "title": L("Where you are now", "अभी आप कहाँ हैं"), "paras": now_par})

    # 2. this year
    yr = []
    yr.append(L(f"{year['year']} is, overall, a {year['rating_label']} year for you.",
                f"{year['year']} आपके लिए कुल मिलाकर {year['rating_label']} वर्ष है।"))
    good = [a["title"] for a in year.get("areas", []) if a["rating"] in ("excellent", "good")]
    care = [a["title"] for a in year.get("areas", []) if a["rating"] == "challenging"]
    if good:
        yr.append(L("Going well: ", "अच्छा चल रहा है: ") + "; ".join(good) + ("।" if hi else "."))
    if care:
        yr.append(L("Needs care: ", "सावधानी चाहिए: ") + "; ".join(care) + ("।" if hi else "."))
    ss = issues.get("sade_sati") or {}
    if ss.get("sade_sati"):
        yr.append(L("Saturn's Sade Sati is running. It is a slow, heavy period that asks for patience, honesty and hard work; "
                    "it ends well for those who stay disciplined. Saturn remedies are especially useful now.",
                    "शनि की साढ़ेसाती चल रही है। यह धीमा और भारी समय है जो धैर्य, ईमानदारी और मेहनत माँगता है; "
                    "अनुशासन रखने वालों के लिए इसका अंत अच्छा होता है। अभी शनि के उपाय विशेष रूप से उपयोगी हैं।"))
    elif ss.get("dhaiya"):
        dh_hi = {"Ashtama (8th)": "अष्टम", "Kantaka/Ardhashtama (4th)": "कंटक/अर्धाष्टम"}.get(ss["dhaiya"], ss["dhaiya"])
        dh_en = {"Ashtama (8th)": "Ashtama – 8th from the Moon", "Kantaka/Ardhashtama (4th)": "Kantaka – 4th from the Moon"}.get(ss["dhaiya"], ss["dhaiya"])
        yr.append(L(f"Saturn's Dhaiya ({dh_en}) is running: about two and a half years of extra pressure – "
                    "slower progress, more responsibility, and the need to look after health. Saturn remedies help.",
                    f"शनि की ढैया ({dh_hi}) चल रही है: लगभग ढाई साल का अतिरिक्त दबाव – "
                    "धीमी प्रगति, ज़्यादा ज़िम्मेदारी और स्वास्थ्य का ध्यान। शनि के उपाय मदद करेंगे।"))
    sections.append({"id": "year", "title": L(f"This year ({year['year']})", f"यह वर्ष ({year['year']})"), "paras": yr})

    # 3. coming months
    if next_months:
        good_m = [m["label"] for m in next_months if m["rating"] in ("excellent", "good")]
        hard_m = [m["label"] for m in next_months if m["rating"] == "challenging"]
        mp = []
        if good_m:
            mp.append(L("Better months for new starts and important work: ", "नए काम और ज़रूरी फ़ैसलों के लिए बेहतर महीने: ")
                      + ", ".join(good_m) + ("।" if hi else "."))
        if hard_m:
            mp.append(L("Go slow and avoid big risks in: ", "इन महीनों में धीरे चलें और बड़ा जोखिम न लें: ")
                      + ", ".join(hard_m) + ("।" if hi else "."))
        if not good_m and not hard_m:
            mp.append(L("The coming months are fairly even – no sharp highs or lows.",
                        "आने वाले महीने लगभग एक-से हैं – न बहुत ऊँचाई, न बहुत गिरावट।"))
        sections.append({"id": "months", "title": L("The next six months", "अगले छह महीने"), "paras": mp,
                         "months": next_months})

    # 4. what needs attention
    att = []
    for i in issues.get("issues", [])[:3]:
        hinfo = i.get("house_info") or {}
        att.append({
            "area": i["area_name"], "priority": i["priority"], "priority_label": PRIORITY[i["priority"]][1 if hi else 0],
            "planet": _T(lang, i["key_planet"]),
            "text": L(f"{i['area_name']} – {PRIORITY[i['priority']][0]}. The main planet behind it is {i['key_planet']}"
                      + (f", which sits in your {hinfo.get('name', '')} ({hinfo.get('meaning', '')})" if hinfo.get("name") else "") + ".",
                      f"{i['area_name']} – {PRIORITY[i['priority']][1]}। इसके पीछे मुख्य ग्रह {_T(lang, i['key_planet'])} है"
                      + (f", जो आपके {hinfo.get('name', '')} ({hinfo.get('meaning', '')}) में बैठा है" if hinfo.get("name") else "") + "।"),
        })
    sections.append({"id": "attention", "title": L("What needs attention", "किन बातों पर ध्यान दें"), "items": att})

    # 5. simple remedies, one block per key planet (max 2)
    plans = []
    seen = []
    for i in issues.get("issues", []):
        p = i["key_planet"]
        if p in seen or len(seen) >= 2:
            continue
        seen.append(p)
        full = i["remedies"].get("full") or {}
        steps = remedy_steps(full, p, lang, i["remedies"].get("lal_kitab_quick"))
        why = L(f"Why {p}: it is linked to “{i['area_name']}” right now. "
                + ("Its remedies aim to calm it down." if full.get("approach") == "pacify" else "Its remedies aim to make it stronger."),
                f"{_T(lang, p)} क्यों: अभी यह “{i['area_name']}” से जुड़ा है। "
                + ("इसके उपाय इसे शांत करने के लिए हैं।" if full.get("approach") == "pacify" else "इसके उपाय इसे मज़बूत करने के लिए हैं।"))
        plans.append({"planet": _T(lang, p), "day": DAY[p][1 if hi else 0], "why": why, "steps": steps})
    sections.append({"id": "remedies", "title": L("What to do – simple remedies", "क्या करें – सरल उपाय"), "plans": plans,
                     "paras": [L("Pick one or two of these and do them regularly for 40 days. Doing a little every day works better than doing a lot once.",
                                 "इनमें से एक-दो उपाय चुनें और 40 दिन तक नियमित करें। एक बार बहुत करने से अच्छा है रोज़ थोड़ा करना।")]})

    # 6. good days to begin
    days = issues.get("remedy_days", [])[:3]
    if days:
        sections.append({"id": "days", "title": L("Good days to begin", "शुरू करने के शुभ दिन"),
                         "paras": [L("Start your remedies on one of these days: ", "उपाय इनमें से किसी दिन शुरू करें: ")
                                   + ", ".join(f"{_date(d['date'], hi)} ({d['weekday']})" for d in days) + ("।" if hi else ".")]})

    # 7. health
    hw = issues.get("health_watch") or []
    if hw:
        parts = ", ".join(dict.fromkeys(h["parts"] for h in hw[:2]))
        sections.append({"id": "health", "title": L("Health tip", "स्वास्थ्य सुझाव"),
                         "paras": [L(f"By tradition, your chart asks you to take extra care of: {parts}. "
                                     "Regular check-ups are a good idea – this is not a medical diagnosis.",
                                     f"परंपरा के अनुसार आपकी कुंडली इन अंगों का विशेष ध्यान रखने को कहती है: {parts}। "
                                     "नियमित जाँच करवाते रहें – यह चिकित्सा निदान नहीं है।")]})

    closing = L("Astrology shows tendencies, not fixed fate. Your own effort, good conduct and sensible decisions matter most. "
                "For the full detail behind this summary, open the other reports.",
                "ज्योतिष प्रवृत्तियाँ बताता है, अटल भाग्य नहीं। आपकी मेहनत, अच्छा आचरण और समझदारी भरे फ़ैसले सबसे ज़्यादा मायने रखते हैं। "
                "इस सार का पूरा विवरण अन्य रिपोर्टों में देखें।")
    return {"as_of": now.date().isoformat(), "rating": reading_now["rating"] if md else None,
            "rating_label": reading_now["rating_label"] if md else None, "sections": sections, "closing": closing}
