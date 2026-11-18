"""Question & answer: answer a user's question from their chart and the books.

Two answer modes:
  * offline (default): the question is matched to life areas, planets, houses, doshas and an
    intent (timing / remedy / general). The answer is assembled from the engine's own analysis
    (life areas, placements, dasha, remedies), with the book pages that discuss the topic.
  * AI (optional): if an Anthropic API key is saved (data/ai.json) or set in ANTHROPIC_API_KEY,
    Claude writes the answer from the chart facts, the offline findings and the matching book
    pages, citing the pages. If the call fails, the offline answer is returned with a note.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import tempfile
from datetime import datetime

import httpx

from . import books, doshas, i18n, lalkitab, placements, predictions, remedies, simple
from .afflictions import analyse as analyse_afflictions, describe as describe_affliction


def _default_config_path() -> pathlib.Path:
    if os.environ.get("VERCEL"):
        return pathlib.Path(tempfile.gettempdir()) / "jyotish" / "ai.json"
    return pathlib.Path(__file__).resolve().parent.parent / "data" / "ai.json"


CONFIG = _default_config_path()
DEFAULT_MODEL = "claude-sonnet-5-5"
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

AREA_WORDS = {  # life-area key (lifeareas.py) -> words in questions (en + hi)
    "marriage": "marriage marry married wedding wife husband spouse partner love relationship divorce "
                "विवाह शादी पत्नी पति जीवनसाथी प्रेम रिश्ता तलाक दाम्पत्य",
    "career": "career job work business profession promotion office boss employment "
              "करियर नौकरी कार्य व्यापार व्यवसाय पद तरक्की प्रमोशन रोजगार",
    "wealth": "money wealth finance savings rich financial धन पैसा संपत्ति बचत आर्थिक",
    "gains": "income gain gains profit earnings आय आमदनी लाभ कमाई मुनाफा",
    "children": "child children son daughter pregnancy baby kids संतान बच्चे पुत्र पुत्री गर्भ",
    "property": "property home land vehicle car flat मकान भूमि जमीन वाहन गाड़ी",
    "education": "education study studies exam college degree learning शिक्षा पढ़ाई परीक्षा विद्या डिग्री",
    "foreign": "foreign abroad visa overseas settle travel विदेश परदेस वीज़ा यात्रा",
    "health": "health disease illness sick surgery hospital स्वास्थ्य रोग बीमारी सेहत ऑपरेशन",
    "parents": "father mother parents पिता माता माँ माता-पिता",
    "siblings": "brother sister sibling siblings भाई बहन",
}
HOUSE_NUM_HI = {"प्रथम": 1, "पहले": 1, "द्वितीय": 2, "दूसरे": 2, "तृतीय": 3, "तीसरे": 3, "चतुर्थ": 4, "चौथे": 4,
                "पंचम": 5, "पाँचवें": 5, "पांचवें": 5, "षष्ठ": 6, "छठे": 6, "सप्तम": 7, "सातवें": 7, "अष्टम": 8,
                "आठवें": 8, "नवम": 9, "नौवें": 9, "दशम": 10, "दसवें": 10, "एकादश": 11, "ग्यारहवें": 11,
                "द्वादश": 12, "बारहवें": 12}
INTENT = {
    "when": r"\bwhen\b|\bwhich year\b|\bhow long\b|\btime\b|\btiming\b|\bby when\b|कब|किस साल|कितने समय|समय",
    "remedy": r"remed|\bupay|solution|what (should|can) i do|\bgem|\bmantra|\bpuja|\bpooja|\bdonat|\bfast\b|उपाय|टोटका|समाधान|रत्न|मंत्र|दान|पूजा|क्या करूँ|क्या करें",
    "why": r"\bwhy\b|\breason\b|क्यों|कारण",
    "tantra": r"tantra|mahavidya|sadhana|devi|goddess|\bkali\b|तंत्र|महाविद्या|साधना|देवी",
    "temple": r"temple|tirtha|pilgrim|मंदिर|तीर्थ",
}
DOSHA_WORDS = {
    "manglik": r"manglik|mangal dosh|kuja|मांगलिक|मंगल दोष",
    "kaal_sarp": r"kaal ?sarp|kalsarp|काल ?सर्प",
    "sade_sati": r"sade ?sati|sadesati|dhaiya|shani|साढ़े ?साती|साढ़ेसाती|ढैया",
    "gand_mool": r"gand ?mool|gandmool|gandanta|मूल नक्षत्र|गंड ?मूल|गंडांत",
}


DOSHA_DEF = {
    "manglik": ("Manglik (Kuja) dosha: Mars in house 1, 4, 7, 8 or 12 (from the Lagna, Moon or Venus); traditionally checked before marriage.",
                "मांगलिक (कुज) दोष: मंगल लग्न, चंद्र या शुक्र से 1, 4, 7, 8 या 12वें भाव में हो; विवाह से पहले परंपरा से देखा जाता है।"),
    "kaal_sarp": ("Kaal Sarp dosha: all seven planets hemmed between Rahu and Ketu; it is said to bring struggle and delays until the native puts in sustained effort.",
                  "कालसर्प दोष: सातों ग्रह राहु और केतु के बीच हों; माना जाता है कि यह संघर्ष व देरी देता है, जो लगातार प्रयास से कम होती है।"),
    "sade_sati": ("Sade Sati: the 7½ years when Saturn transits the 12th, 1st and 2nd signs from the natal Moon; Dhaiya is Saturn's 2½ years in the 4th or 8th from the Moon.",
                  "साढ़ेसाती: जन्म चंद्र से 12वीं, पहली और दूसरी राशि में शनि का साढ़े सात वर्ष का गोचर; ढैया चंद्र से चौथी या आठवीं राशि में शनि के ढाई वर्ष।"),
    "gand_mool": ("Gand-mool: birth in Ashwini, Ashlesha, Magha, Jyeshtha, Mula or Revati – the nakshatras at the junctions of water and fire signs; Mula-shanti is traditionally done for it.",
                  "गंडमूल: अश्विनी, आश्लेषा, मघा, ज्येष्ठा, मूल या रेवती नक्षत्र में जन्म – जल व अग्नि राशियों की संधि के नक्षत्र; इसके लिए परंपरा से मूल-शांति कराई जाती है।"),
}


# ---------------------------------------------------------------- config
def _cfg() -> dict:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ai_status() -> dict:
    c = _cfg()
    key = c.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
    return {"ai": bool(key), "model": c.get("model") or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL,
            "key_hint": (key[:7] + "…" + key[-4:]) if key else None, "books": books.status()}


def save_key(api_key: str, model: str | None = None) -> dict:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    c = _cfg()
    if api_key is not None:
        c["api_key"] = api_key.strip()
    if model:
        c["model"] = model.strip()
    CONFIG.write_text(json.dumps(c), encoding="utf-8")
    return ai_status()


# ---------------------------------------------------------------- parsing
def parse(question: str) -> dict:
    q = books.norm(question)
    hi_terms = i18n.load("hi")["terms"]
    areas = [a for a, w in AREA_WORDS.items() if any(re.search(rf"(^|[^\wऀ-ॿ]){re.escape(books.norm(x))}", q) for x in w.split())]
    planets = []
    for p in PLANETS:
        names = [p.lower(), books.norm(hi_terms.get(p, p))] + {"Moon": ["चन्द्र", "चंद्रमा"], "Jupiter": ["बृहस्पति", "guru"],
                                                                "Saturn": ["shani"], "Sun": ["surya"], "Mars": ["mangal"],
                                                                "Venus": ["shukra"], "Mercury": ["budh"]}.get(p, [])
        if any(re.search(rf"(^|[^\wऀ-ॿ]){re.escape(n)}", q) for n in names):
            planets.append(p)
    houses = [int(m.group(1) or m.group(3)) for m in
              re.finditer(r"\b(1[0-2]|[1-9])(?:st|nd|rd|th)?\s+(?:house|bhav)\b|\b(?:house|bhav|khana)\s+(1[0-2]|[1-9])\b()", q)]
    houses += [int(m.group(1)) for m in re.finditer(r"(1[0-2]|[1-9])\s*(?:वें|वे|वां|वा)?\s*(?:भाव|घर|खाने)", q)]
    houses += [n for w, n in HOUSE_NUM_HI.items() if re.search(rf"{w}\s*(भाव|घर|खाने)", q)]
    intents = [k for k, rx in INTENT.items() if re.search(rx, q)]
    dosh = [k for k, rx in DOSHA_WORDS.items() if re.search(rx, q)]
    if "Saturn" in planets and "sade_sati" in dosh and not re.search(DOSHA_WORDS["sade_sati"].replace("|shani", ""), q):
        dosh.remove("sade_sati")      # "shani" alone is a planet question, not a Sade Sati one
    return {"areas": list(dict.fromkeys(areas)), "planets": planets, "houses": sorted(set(houses)),
            "intents": intents, "doshas": dosh}


# ---------------------------------------------------------------- offline answer
def _period_span(p: dict, hi: bool) -> str:
    return f"{simple._d(p['start'], hi)} – {simple._d(p['end'], hi)}"


def answer_offline(question: str, chart: dict, dasha: dict, life: list[dict], lang: str, now: datetime,
                   tz: str, s, lk_houses: dict, sade_sati_status: dict, nak_doshas: list[dict]) -> dict:
    hi = lang == "hi"
    L = (lambda en, h: h if hi else en)
    T = (lambda x: i18n.term(lang, x))
    pq = parse(question)
    sections = []
    focus_planets: list[str] = list(pq["planets"])
    by_area = {a["area"]: a for a in life}

    # houses asked about -> treat like their areas / lords
    for h in pq["houses"]:
        info = placements.house_info(h, lang)
        occ = [p for p in PLANETS if chart["planets"][p]["house"] == h]
        sign = chart["houses"][h - 1]["sign"] if isinstance(chart.get("houses"), list) else None
        txt = L(f"Your {info['name']} (house {h}) is about {info['meaning']}. ",
                f"आपका {info['name']} ({placements.ord_hi(h)} भाव) {info['meaning']} से जुड़ा है। ")
        txt += (L("Planets in it: ", "इसमें ग्रह: ") + ", ".join(T(p) for p in occ) + ("।" if hi else ".")) if occ else L("No planet sits in it.", "इसमें कोई ग्रह नहीं है।")
        if sign:
            lord = chart["houses"][h - 1]["lord"]
            lh = chart["planets"][lord]["house"]
            txt += " " + L(f"Its sign is {sign}; its lord {lord} sits in house {lh} ({placements.house_info(lh, lang)['name']}).",
                           f"इसकी राशि {T(sign)} है; इसका स्वामी {T(lord)} {placements.ord_hi(lh)} भाव ({placements.house_info(lh, lang)['name']}) में है।")
            focus_planets.append(lord)
        sections.append({"kind": "house", "title": L(f"House {h}", f"{placements.ord_hi(h)} भाव"), "paras": [txt]})
        focus_planets += occ

    # life areas
    for a in pq["areas"]:
        ar = by_area.get(a)
        if not ar:
            continue
        verdict = {"strong": L("strong", "मज़बूत"), "moderate": L("moderate", "मध्यम"), "weak": L("weak", "कमज़ोर")}.get(ar["verdict_key"], ar["verdict"])
        paras = [L(f"{ar['title']} is read from your {placements.house_info(ar['house'], lang)['name']} (house {ar['house']}, sign {ar['sign']}), ruled by {ar['lord']}. "
                   f"Overall this area is {verdict} in your chart.",
                   f"{ar['title']} आपके {placements.house_info(ar['house'], lang)['name']} ({placements.ord_hi(ar['house'])} भाव, {T(ar['sign'])} राशि) से देखा जाता है, जिसका स्वामी {T(ar['lord'])} है। "
                   f"आपकी कुंडली में यह क्षेत्र कुल मिलाकर {verdict} है।")]
        pos = [p["text"] for p in ar["points"] if p["weight"] > 0][:2]
        neg = [p["text"] for p in ar["points"] if p["weight"] < 0][:2]
        if pos:
            paras.append(L("Helping: ", "सहायक: ") + "; ".join(pos) + ("।" if hi else "."))
        if neg:
            paras.append(L("Holding back: ", "बाधक: ") + "; ".join(neg) + ("।" if hi else "."))
        up = [p for p in ar.get("periods", []) if p["end"] >= now.date().isoformat()][:3]
        if up:
            cur = [p for p in up if p["start"] <= now.date().isoformat()]
            paras.append(L("Periods that activate it: ", "इसे सक्रिय करने वाली दशाएँ: ")
                         + "; ".join(f"{T(p['md'])}–{T(p['ad'])} ({_period_span(p, hi)})" for p in up)
                         + ("।" if hi else ".")
                         + (" " + L("One of them is running now.", "इनमें से एक अभी चल रही है।") if cur else ""))
        elif "when" in pq["intents"]:
            paras.append(L("No strongly supportive period for this area is found in the coming decades; effort and remedies matter more.",
                           "आने वाले दशकों में इस क्षेत्र के लिए कोई प्रबल सहायक दशा नहीं दिखती; प्रयास और उपाय अधिक महत्वपूर्ण हैं।"))
        sections.append({"kind": "area", "title": ar["title"], "paras": paras, "verdict": ar["verdict_key"]})
        focus_planets += [ar["lord"]]
        if ar.get("karaka"):
            focus_planets.append(ar["karaka"])

    # planets asked about
    for p in pq["planets"]:
        ex = placements.explain(chart, p, lang)
        sections.append({"kind": "planet", "title": T(p), "paras": [ex["text"]]})

    # doshas
    for d in pq["doshas"]:
        if d == "manglik":
            m = doshas.manglik(chart)
            txt = (L("Manglik dosha is present in your chart (Mars in a sensitive house).", "आपकी कुंडली में मांगलिक दोष है (मंगल संवेदनशील भाव में)।")
                   if m["present"] else L("Your chart is not Manglik: Mars is not in houses 1, 4, 7, 8 or 12 from the Lagna, Moon or Venus.",
                                          "आपकी कुंडली मांगलिक नहीं है: मंगल लग्न, चंद्र या शुक्र से 1, 4, 7, 8 या 12वें भाव में नहीं है।"))
            focus_planets.append("Mars")
        elif d == "kaal_sarp":
            k = doshas.kaal_sarp(chart)
            txt = (L("Kaal Sarp dosha is present: all seven planets lie on one side of the Rahu–Ketu axis.",
                     "कालसर्प दोष है: सातों ग्रह राहु–केतु अक्ष के एक ओर हैं।") if k["present"]
                   else L("There is no Kaal Sarp dosha in your chart.", "आपकी कुंडली में कालसर्प दोष नहीं है।"))
            focus_planets += ["Rahu", "Ketu"]
        elif d == "sade_sati":
            ss = sade_sati_status
            if ss.get("sade_sati"):
                txt = L(f"Sade Sati is running now ({ss.get('phase')} phase).", f"अभी साढ़ेसाती चल रही है ({ss.get('phase')} चरण)।")
            elif ss.get("dhaiya"):
                txt = L(f"Sade Sati is not running, but Saturn's Dhaiya ({ss['dhaiya']}) is.", f"साढ़ेसाती नहीं, पर शनि की ढैया ({ss['dhaiya']}) चल रही है।")
            else:
                txt = L("Neither Sade Sati nor Dhaiya is running now.", "अभी न साढ़ेसाती है, न ढैया।")
            focus_planets.append("Saturn")
        else:
            mn = chart["planets"]["Moon"]["nakshatra"]["name"]
            txt = (L(f"Your Moon is in {mn}. ", f"आपका चंद्र {T(mn)} नक्षत्र में है। ")
                   + ("; ".join(x.get("text") or x.get("name", "") for x in nak_doshas) if nak_doshas
                      else L("It is not a Gand-mool / gandanta position.", "यह गंडमूल / गंडांत स्थिति नहीं है।")))
        sections.append({"kind": "dosha", "title": L("Dosha", "दोष"), "paras": [DOSHA_DEF[d][1 if hi else 0], txt]})

    # nothing recognised: current period as context
    if not sections:
        r = predictions.period_reading(chart, *(_running(dasha, now)), lang) if _running(dasha, now)[0] else None
        md, ad = _running(dasha, now)
        if r:
            sections.append({"kind": "now", "title": L("Your current period", "आपका वर्तमान समय"), "paras": [
                L(f"You are running {md}–{ad} (main period and sub-period); it is a {r['rating_label']} time. "
                  "I could not tell which part of life your question is about – try naming it (career, marriage, health, money, a planet or a house).",
                  f"अभी {T(md)}–{T(ad)} (महादशा–अंतर्दशा) चल रही है; यह {r['rating_label']} समय है। "
                  "आपका प्रश्न जीवन के किस क्षेत्र के बारे में है, यह स्पष्ट नहीं हुआ – क्षेत्र (करियर, विवाह, स्वास्थ्य, धन, कोई ग्रह या भाव) लिखकर पूछें।")]})
            focus_planets += [md, ad]

    # nothing else but a tantra / temple question: use the running dasha lords
    if not focus_planets and ({"tantra", "temple"} & set(pq["intents"])):
        md, ad = _running(dasha, now)
        focus_planets += [x for x in (ad, md) if x]
    if "tantra" in pq["intents"]:
        from . import tantra
        for p in list(dict.fromkeys(focus_planets))[:2]:
            tn = tantra.for_planet(p, lang)
            sections.append({"kind": "tantra", "title": L(f"Tantra for {p}", f"{T(p)} के लिए तंत्र"), "paras": tn["items"]})
    if "temple" in pq["intents"]:
        from . import temples
        for p in list(dict.fromkeys(focus_planets))[:2]:
            tl = temples.for_planet(p, lang)[:3]
            if tl:
                sections.append({"kind": "temple", "title": L(f"Temples for {p}", f"{T(p)} के लिए मंदिर"),
                                 "paras": [f"{x['name']} ({x['state']}) – {x['what'][:220]}" for x in tl]})

    # remedies for the weakest focus planet(s)
    focus = list(dict.fromkeys(p for p in focus_planets if p in PLANETS))
    rem = []
    if focus and ({"remedy", "temple"} & set(pq["intents"]) or pq["areas"] or pq["doshas"]):
        ranked = sorted(focus, key=lambda p: predictions.planet_tone(chart, p)[0])[:2 if "remedy" in pq["intents"] else 1]
        for p in ranked:
            full = remedies.full_set(chart, p, lang, lk_house=lk_houses.get(p), house_for_arudha=chart["planets"][p]["house"])
            rem.append({"planet": T(p), "approach": full["approach_text"], "steps": simple.remedy_steps(full, p, lang)})

    # book references: exact pages for the focus planets, then free-text search
    refs = []
    for p in focus[:3]:
        h_lk = lk_houses.get(p)
        if h_lk:
            try:
                e = lalkitab.entry(p, h_lk, lang)
                refs.append({"book": "lalkitab", "title": books.BOOKS["lalkitab"]["title_hi" if hi else "title"],
                             "pdf_page": e["pdf_pages"][0], "page_label": books.page_label("lalkitab", e["pdf_pages"][0], lang),
                             "why": L(f"{p} in house {h_lk} (Lal Kitab chart)", f"{T(p)} खाना {h_lk} में (लाल किताब कुंडली)"),
                             "image": f"/books/lalkitab/p{e['pdf_pages'][0]:03d}.jpg"})
            except (KeyError, IndexError):
                pass
    try:
        from . import bhrigu
        rd = {x["planet"]: x for x in bhrigu.report(chart)["readings"]}
    except Exception:  # noqa: BLE001 – the Bhrigu index is optional
        rd = {}
    for p in focus[:3]:
        x = rd.get(p)
        if x and x.get("pdf_page"):
            refs.append({"book": "bhrigu", "title": books.BOOKS["bhrigu"]["title_hi" if hi else "title"],
                         "pdf_page": x["pdf_page"], "page_label": books.page_label("bhrigu", x["pdf_page"], lang),
                         "why": L(f"{chart['lagna']['sign']} lagna, {p} in house {x['house']}",
                                  f"{T(chart['lagna']['sign'])} लग्न, {T(p)} {placements.ord_hi(x['house'])} भाव में"),
                         "image": f"/books/bhrigu/p{x['pdf_page']:03d}.jpg"})
    extra = [i18n.term("hi", p) for p in focus[:3]] + [AREA_WORDS[a].split()[-1] for a in pq["areas"]]
    hits = books.search(question, extra=extra, k=6, lang=lang, books=["pvr", "lalkitab", "nakshatra", "tantra"])
    for h in hits:
        if not any(r["book"] == h["book"] and r["pdf_page"] == h["pdf_page"] for r in refs):
            refs.append({k: v for k, v in h.items() if k != "text"})
    return {"question": question, "parsed": pq, "sections": sections, "remedies": rem, "refs": refs,
            "focus_planets": focus, "_hits": hits, "mode": "offline",
            "note": L("Answer assembled from your chart by the engine's rules. Book snippets are OCR text of scanned pages and may contain errors – open the page to read the original.",
                      "उत्तर इंजन के नियमों से आपकी कुंडली के आधार पर बना है। पुस्तक के अंश स्कैन पृष्ठों के OCR से हैं और उनमें त्रुटियाँ हो सकती हैं – मूल पढ़ने के लिए पृष्ठ खोलें।")}


def _running(dasha: dict, now: datetime):
    md, ad, _ = simple._current(dasha, now)
    return (md["lord"], ad["lord"]) if md else (None, None)


# ---------------------------------------------------------------- AI answer
def _chart_brief(chart: dict, dasha: dict, now: datetime) -> str:
    lines = [f"Lagna: {chart['lagna']['sign']} {chart['lagna']['degree_in_sign']}, nakshatra {chart['lagna']['nakshatra']['name']}"]
    for p in PLANETS:
        x = chart["planets"][p]
        lines.append(f"{p}: {x['sign']} {x['degree_in_sign']}, house {x['house']}, {x.get('dignity', '')}"
                     f"{', retrograde' if x.get('retrograde') else ''}, nakshatra {x['nakshatra']['name']}")
    md, ad = _running(dasha, now)
    if md:
        lines.append(f"Running Vimshottari dasha on {now.date()}: {md} mahadasha / {ad} antardasha")
    return "\n".join(lines)


def answer_ai(question: str, offline: dict, chart: dict, dasha: dict, lang: str, now: datetime,
              afflictions: list[str], timeout: float = 90.0) -> dict:
    st = ai_status()
    key = _cfg().get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
    findings = []
    for s in offline["sections"]:
        findings.append(f"[{s['title']}] " + " ".join(s["paras"]))
    for r in offline["remedies"]:
        findings.append(f"[Remedies for {r['planet']}] {r['approach']} " + " | ".join(r["steps"]))
    pages = []
    for i, h in enumerate(offline["_hits"][:5], 1):
        pages.append(f"<page n=\"{i}\" book=\"{books.BOOKS[h['book']]['title']}\" ref=\"{h['page_label']}\">\n{h['text'][:1800]}\n</page>")
    system = (
        "You are a careful Vedic astrologer (Jyotish) answering a user's question about their own birth chart inside a "
        "private study app. Base the answer on (1) the chart facts and the engine's findings provided, and (2) the book pages "
        "provided, which are OCR text of scanned Hindi books (they contain OCR errors; read through them). Cite book pages "
        "inline as [Book, page]. Paraphrase the books in your own words – never copy more than a short phrase. If the pages do "
        "not address the question, say so and rely on the chart findings. Do not invent chart facts. Astrology describes "
        "tendencies, not certainties; for health, legal or money matters remind the user to consult a professional. "
        "Keep it clear and practical: a direct answer first, then the reasons from the chart, then what to do (remedies) if "
        "relevant. 150–350 words. Use simple Markdown (short paragraphs, a few bullets at most). "
        + ("Answer in Hindi (Devanagari)." if lang == "hi" else "Answer in English."))
    user = (f"Question: {question}\n\nChart:\n{_chart_brief(chart, dasha, now)}\n\nAfflictions found by the engine: "
            f"{'; '.join(afflictions) or 'none'}\n\nEngine findings:\n" + "\n".join(findings)
            + "\n\nBook pages:\n" + ("\n\n".join(pages) or "(no matching pages)"))
    try:
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=timeout,
                       headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                       json={"model": st["model"], "max_tokens": 1500, "system": system,
                             "messages": [{"role": "user", "content": user}]})
        r.raise_for_status()
        text = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text").strip()
        return {"ok": True, "text": text, "model": st["model"]}
    except httpx.HTTPStatusError as e:
        try:
            msg = e.response.json().get("error", {}).get("message", "")
        except ValueError:
            msg = e.response.text[:200]
        return {"ok": False, "error": f"{e.response.status_code}: {msg}"}
    except httpx.HTTPError as e:
        return {"ok": False, "error": str(e) or e.__class__.__name__}


def ask(question: str, chart: dict, dasha: dict, life: list[dict], lang: str, now: datetime, tz: str, s,
        lk_houses: dict, sade_sati_status: dict, nak_doshas: list[dict], use_ai: bool = True) -> dict:
    out = answer_offline(question, chart, dasha, life, lang, now, tz, s, lk_houses, sade_sati_status, nak_doshas)
    if use_ai and ai_status()["ai"]:
        affl = [describe_affliction(a, "en") for a in analyse_afflictions(chart)]
        ai = answer_ai(question, out, chart, dasha, lang, now, affl)
        if ai["ok"]:
            out["ai_text"], out["mode"], out["model"] = ai["text"], "ai", ai["model"]
        else:
            out["ai_error"] = ai["error"]
    out.pop("_hits", None)
    return out
