"""Life story: the life-long prediction told as a narrative.

Built from the same analysis as predictions.lifelong (dasha lords' houses, karakatva, functional
nature, strength; milestones; life-area timing), but written as a prologue, one chapter per
mahadasha and an epilogue – in the past tense for chapters already lived, the present for the
running one and the future for those to come. English and Hindi.
"""
from __future__ import annotations

from datetime import datetime

from . import i18n
from .constants import SIGN_LORDS
from .placements import explain, ord_hi

LAGNA_TRAIT = {  # (en, hi)
    "Aries": ("quick to act, brave and direct, happiest when you are leading or starting something new",
              "तुरंत कर्म करने वाले, साहसी और स्पष्टवादी; नेतृत्व करने या कुछ नया शुरू करने में सबसे प्रसन्न"),
    "Taurus": ("steady, patient and loyal, with a love of beauty, comfort and things that last",
               "स्थिर, धैर्यवान और निष्ठावान; सौंदर्य, सुख और टिकाऊ चीज़ों से प्रेम"),
    "Gemini": ("curious, quick-witted and talkative, always learning and connecting people and ideas",
               "जिज्ञासु, तीक्ष्ण बुद्धि और बातूनी; सदा सीखते और लोगों व विचारों को जोड़ते"),
    "Cancer": ("caring and protective, deeply tied to home and family, guided by feeling and memory",
               "स्नेही और रक्षक; घर-परिवार से गहराई से जुड़े, भावना व स्मृति से संचालित"),
    "Leo": ("warm, proud and generous, born to shine, to lead and to be seen doing the right thing",
            "उदार, स्वाभिमानी और गरिमामय; चमकने, नेतृत्व करने और सही काम करते दिखने के लिए जन्मे"),
    "Virgo": ("careful, practical and helpful, with an eye for detail and a wish to make things work better",
              "सावधान, व्यावहारिक और सहायक; बारीकी पर नज़र और चीज़ों को बेहतर बनाने की इच्छा"),
    "Libra": ("fair-minded, graceful and diplomatic, at your best in partnership and balance",
              "न्यायप्रिय, शालीन और कूटनीतिक; साझेदारी व संतुलन में सर्वश्रेष्ठ"),
    "Scorpio": ("intense, private and determined, drawn to what is hidden and able to transform yourself",
                "गहन, गोपनीय और दृढ़निश्चयी; छिपी बातों की ओर आकर्षित और स्वयं को बदलने में सक्षम"),
    "Sagittarius": ("open, optimistic and principled, a seeker of wisdom, travel and higher meaning",
                    "खुले विचारों वाले, आशावादी और सिद्धांतवादी; ज्ञान, यात्रा और उच्च अर्थ के खोजी"),
    "Capricorn": ("disciplined, ambitious and responsible, building slowly and surely towards the top",
                  "अनुशासित, महत्वाकांक्षी और ज़िम्मेदार; धीरे-धीरे पर पक्के कदमों से शिखर की ओर"),
    "Aquarius": ("independent, humane and original, thinking of the wider world and the future",
                 "स्वतंत्र, मानवतावादी और मौलिक; व्यापक संसार और भविष्य के बारे में सोचने वाले"),
    "Pisces": ("gentle, imaginative and compassionate, sensitive to others and to the unseen",
               "कोमल, कल्पनाशील और करुणामय; दूसरों और अदृश्य के प्रति संवेदनशील"),
}
MOON_TRAIT = {  # how the mind feels (en, hi)
    "Aries": ("restless and eager", "उत्सुक और अधीर"), "Taurus": ("calm and contented", "शांत और संतुष्ट"),
    "Gemini": ("lively and changeable", "चंचल और जीवंत"), "Cancer": ("tender and intuitive", "कोमल और अंतर्ज्ञानी"),
    "Leo": ("proud and big-hearted", "स्वाभिमानी और बड़े दिल वाला"), "Virgo": ("analytical and a little anxious", "विश्लेषक और थोड़ा चिंतित"),
    "Libra": ("harmony-seeking", "सामंजस्य चाहने वाला"), "Scorpio": ("deep and guarded", "गहरा और सतर्क"),
    "Sagittarius": ("hopeful and free", "आशावान और स्वतंत्र"), "Capricorn": ("serious and dutiful", "गंभीर और कर्तव्यनिष्ठ"),
    "Aquarius": ("detached and inventive", "निर्लिप्त और आविष्कारशील"), "Pisces": ("dreamy and devotional", "स्वप्निल और भक्तिमय"),
}
HOUSE_STORY = {  # what a chapter touching this house is about (en, hi)
    1: ("your own body, health and sense of who you are", "आपका शरीर, स्वास्थ्य और अपनी पहचान"),
    2: ("money, family and the power of your words", "धन, परिवार और वाणी की शक्ति"),
    3: ("courage, effort, siblings and your own initiatives", "साहस, परिश्रम, भाई-बहन और अपनी पहल"),
    4: ("home, mother, property and peace of mind", "घर, माता, संपत्ति और मन की शांति"),
    5: ("children, learning, creativity and the merit of past lives", "संतान, विद्या, रचनात्मकता और पूर्व पुण्य"),
    6: ("work, service, rivals, debts and health battles", "सेवा, नौकरी, प्रतिद्वंद्वी, ऋण और स्वास्थ्य संघर्ष"),
    7: ("marriage, partners and dealings with others", "विवाह, साझेदार और दूसरों से व्यवहार"),
    8: ("sudden change, hidden matters, inheritance and inner transformation", "अचानक परिवर्तन, गुप्त बातें, विरासत और आंतरिक रूपांतरण"),
    9: ("luck, father, teachers, faith and long journeys", "भाग्य, पिता, गुरु, आस्था और लंबी यात्राएँ"),
    10: ("career, status and your work in the world", "करियर, पद-प्रतिष्ठा और संसार में आपका कर्म"),
    11: ("gains, income, friends and wishes fulfilled", "लाभ, आय, मित्र और पूरी होती इच्छाएँ"),
    12: ("expenses, distant lands, rest and the spiritual life", "व्यय, दूर देश, विश्राम और आध्यात्मिक जीवन"),
}
CHAPTER = {  # planet: (title en, title hi, flavour en, flavour hi)
    "Sun": ("The Sun years – stepping into the light", "सूर्य के वर्ष – प्रकाश में आना",
            "the Sun asks you to stand on your own, to be recognised and to take responsibility", "सूर्य आपसे अपने पैरों पर खड़े होने, पहचान पाने और ज़िम्मेदारी लेने को कहता है"),
    "Moon": ("The Moon years – the life of the heart", "चंद्र के वर्ष – हृदय का जीवन",
             "the Moon turns life towards feelings, family, mother and the people around you", "चंद्रमा जीवन को भावनाओं, परिवार, माता और आसपास के लोगों की ओर मोड़ता है"),
    "Mars": ("The Mars years – courage and building", "मंगल के वर्ष – साहस और निर्माण",
             "Mars brings energy, competition and the drive to build, fight for and own things", "मंगल ऊर्जा, प्रतिस्पर्धा और कुछ बनाने, उसके लिए लड़ने व उसे पाने की प्रेरणा लाता है"),
    "Mercury": ("The Mercury years – learning and connecting", "बुध के वर्ष – सीखना और जुड़ना",
                "Mercury brings study, trade, writing, talking and a widening circle of contacts", "बुध अध्ययन, व्यापार, लेखन, संवाद और बढ़ता संपर्क-क्षेत्र लाता है"),
    "Jupiter": ("The Jupiter years – growth and grace", "गुरु के वर्ष – विकास और कृपा",
                "Jupiter brings growth, teachers, children, wisdom and the sense of being guided", "गुरु विकास, शिक्षक, संतान, ज्ञान और मार्गदर्शन का अनुभव लाता है"),
    "Venus": ("The Venus years – love and comfort", "शुक्र के वर्ष – प्रेम और सुख",
              "Venus brings relationships, beauty, comfort, vehicles and the pleasures of life", "शुक्र संबंध, सौंदर्य, सुख, वाहन और जीवन के आनंद लाता है"),
    "Saturn": ("The Saturn years – the long work", "शनि के वर्ष – लंबा परिश्रम",
               "Saturn brings duty, hard work, patience and results that come slowly but last", "शनि कर्तव्य, कठोर परिश्रम, धैर्य और धीरे पर स्थायी फल लाता है"),
    "Rahu": ("The Rahu years – hunger and the unknown", "राहु के वर्ष – भूख और अज्ञात",
             "Rahu brings big ambitions, foreign or unusual paths, sudden rises and restless confusion", "राहु बड़ी महत्वाकांक्षाएँ, विदेशी या असामान्य राहें, अचानक उन्नति और बेचैन भ्रम लाता है"),
    "Ketu": ("The Ketu years – letting go", "केतु के वर्ष – छोड़ना",
             "Ketu loosens attachments and turns you inward, towards research, spirit and what truly matters", "केतु आसक्तियों को ढीला कर आपको भीतर – शोध, आत्मा और सच्चे मूल्यों – की ओर मोड़ता है"),
}
STAGE = [(12, "childhood", "बचपन"), (24, "youth and education", "युवावस्था और शिक्षा"), (36, "the building years", "निर्माण के वर्ष"),
         (48, "the years of establishment", "स्थापना के वर्ष"), (60, "maturity", "परिपक्वता"), (75, "the elder years", "वरिष्ठ वर्ष"),
         (200, "the years of wisdom", "ज्ञान के वर्ष")]
AREA_HOUSE = {"marriage": 7, "career": 10, "children": 5, "property": 4, "wealth": 2, "foreign": 12, "education": 4}
AREA_EVENT = {  # (en, hi)
    "marriage": ("marriage or a committed partnership", "विवाह या स्थायी साझेदारी के"),
    "career": ("a rise or turn in career", "करियर में उन्नति या नए मोड़ के"),
    "children": ("children or a creative birth", "संतान या किसी रचनात्मक सृजन के"),
    "property": ("home, land or a vehicle", "घर, भूमि या वाहन के"),
    "wealth": ("savings and family wealth growing", "बचत और पारिवारिक धन बढ़ने के"),
    "foreign": ("travel or settling abroad", "विदेश यात्रा या वहाँ बसने के"),
    "education": ("studies and qualifications", "पढ़ाई और नई योग्यताओं के"),
}


def _stage(age: float, hi: bool) -> str:
    for lim, en, h in STAGE:
        if age < lim:
            return h if hi else en
    return STAGE[-1][2] if hi else STAGE[-1][1]


def _tense(status: str, hi: bool) -> dict:
    """status: past / present / future"""
    if hi:
        return {"past": {"was": "था", "were": "थे", "came": "आया", "brought": "लाया", "asked": "माँगा", "will": "रहा"},
                "present": {"was": "है", "were": "हैं", "came": "आता है", "brought": "ला रहा है", "asked": "माँग रहा है", "will": "है"},
                "future": {"was": "होगा", "were": "होंगे", "came": "आएगा", "brought": "लाएगा", "asked": "माँगेगा", "will": "रहेगा"}}[status]
    return {"past": {"was": "was", "were": "were", "came": "came", "brought": "brought", "asked": "asked", "opens": "opened", "is": "was"},
            "present": {"was": "is", "were": "are", "came": "comes", "brought": "is bringing", "asked": "is asking", "opens": "opens", "is": "is"},
            "future": {"was": "will be", "were": "will be", "came": "will come", "brought": "will bring", "asked": "will ask", "opens": "will open", "is": "will be"}}[status]


def _ord_en(n: int) -> str:
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"


def _join(xs: list[str], hi: bool) -> str:
    if len(xs) <= 1:
        return "".join(xs)
    return ", ".join(xs[:-1]) + (" और " if hi else " and ") + xs[-1]


def _when(start: str, end: str | None, now: datetime) -> str:
    s = datetime.fromisoformat(start[:10])
    e = datetime.fromisoformat(end[:10]) if end else s
    return "past" if e < now else ("present" if s <= now else "future")


EV = {  # kind: {tense: (en, hi)}  {age} {span}
    "sade_sati": {"past": ("Saturn's Sade Sati, at age {age}, brought weight, responsibility and a demand to grow up.",
                           "आयु {age} में शनि की साढ़ेसाती ज़िम्मेदारियों का भार और परिपक्व होने की माँग लेकर आई।"),
                  "present": ("Saturn's Sade Sati is running now (age {age}) – a time of weight, responsibility and growing up.",
                              "शनि की साढ़ेसाती अभी चल रही है (आयु {age}) – ज़िम्मेदारी, भार और परिपक्वता का समय।"),
                  "future": ("Saturn's Sade Sati, at age {age}, will bring weight, responsibility and a demand to slow down and simplify.",
                             "आयु {age} में शनि की साढ़ेसाती ज़िम्मेदारी का भार लाएगी और जीवन को सरल व स्थिर करने को कहेगी।")},
    "saturn_return": {"past": ("Around {age}, Saturn returned to its birth position and asked you to rebuild the structure of your life.",
                               "लगभग {age} वर्ष की आयु में शनि अपनी जन्म-स्थिति पर लौटा और जीवन के ढाँचे को नए सिरे से गढ़ने को कहा।"),
                      "present": ("Saturn is returning to its birth position now – a time to rebuild life's structure.",
                                  "शनि अभी अपनी जन्म-स्थिति पर लौट रहा है – जीवन के ढाँचे को फिर से गढ़ने का समय।"),
                      "future": ("Around {age}, Saturn will return to its birth position and ask you to rebuild the structure of your life.",
                                 "लगभग {age} वर्ष की आयु में शनि अपनी जन्म-स्थिति पर लौटेगा और जीवन के ढाँचे को नए सिरे से गढ़ने को कहेगा।")},
    "jupiter_return": {"past": ("Around {age}, Jupiter's return opened a new twelve-year cycle of growth.",
                                "लगभग {age} वर्ष पर गुरु की वापसी विकास का नया बारह-वर्षीय चक्र लेकर आई।"),
                       "present": ("Jupiter is returning to its birth sign now – a new twelve-year cycle of growth begins.",
                                   "गुरु अभी अपनी जन्म-राशि में लौट रहा है – विकास का नया बारह-वर्षीय चक्र आरंभ।"),
                       "future": ("Around {age}, Jupiter's return will open a new twelve-year cycle of growth.",
                                  "लगभग {age} वर्ष पर गुरु की वापसी विकास का नया बारह-वर्षीय चक्र लेकर आएगी।")},
    "area": {"past": ("In {span} (the {lord} sub-period) the chart showed openings for {what}.",
                      "{span} ({lord} अंतर्दशा) में {what} योग बने।"),
             "present": ("Now, in {span} (the {lord} sub-period), the chart shows openings for {what}.",
                         "अभी {span} ({lord} अंतर्दशा) में {what} योग बन रहे हैं।"),
             "future": ("In {span} (the {lord} sub-period) the chart shows openings for {what}.",
                        "{span} ({lord} अंतर्दशा) में {what} योग बनेंगे।")},
}


def _T(lang, x):
    return i18n.term(lang, x)


def _yr(s: str) -> str:
    return s[:4]


def _span(a: str, b: str) -> str:
    return a[:4] if a[:4] == b[:4] else f"{a[:4]}–{b[:4]}"


AREA_AGES = {"marriage": (18, 60), "children": (20, 50), "career": (17, 70), "property": (18, 85),
             "wealth": (16, 90), "foreign": (14, 80), "education": (5, 35)}


def _area_windows(chart: dict, md: dict) -> list[tuple[str, dict]]:
    """Antardashas inside this mahadasha that strongly connect with an area's house (its lord, an occupant
    or the area's karaka acting as AD lord together with a favourable MD)."""
    lagna = chart["lagna"]["sign_index"] - 1
    out = []
    for area, h in AREA_HOUSE.items():
        lord = SIGN_LORDS[(lagna + h - 1) % 12]
        occ = {p for p, v in chart["planets"].items() if v["house"] == h}
        best = None
        for ad in md["antardashas"]:
            hit = (ad["lord"] == lord) + (ad["lord"] in occ) + (md["lord"] in (lord, *occ))
            if hit and ad["rating"] in ("excellent", "good", "mixed"):
                cand = (hit, ad["score"])
                if best is None or cand > best[0]:
                    best = (cand, ad)
        if best and (best[0][0] >= 2 or best[1]["rating"] in ("excellent", "good")):
            out.append((area, best[1]))
    return out


def tell(chart: dict, life: dict, birth: datetime, lang: str = "en", now: datetime | None = None, name: str = "") -> dict:
    """life = predictions.lifelong(...) output."""
    hi = lang == "hi"
    k = 1 if hi else 0
    now = now or datetime.now()
    lagna = chart["lagna"]["sign"]
    moon = chart["planets"]["Moon"]
    ll = explain(chart, SIGN_LORDS[chart["lagna"]["sign_index"] - 1], lang)
    ov = life["overview"]
    who = name or ("आप" if hi else "you")

    # ---------------- prologue ----------------
    if hi:
        pro = [
            f"{birth.strftime('%d-%m-%Y')} को जब {who} जन्मे, पूर्वी क्षितिज पर {_T(lang, lagna)} राशि उदित हो रही थी। यह लग्न आपको {LAGNA_TRAIT[lagna][1]} बनाता है।",
            f"चंद्रमा {_T(lang, moon['sign'])} राशि और {_T(lang, moon['nakshatra']['name'])} नक्षत्र में था – इसलिए आपका मन {MOON_TRAIT[moon['sign']][1]} है।",
            f"आपकी जीवन-कथा का सूत्रधार लग्नेश {_T(lang, ll['planet'])} है, जो {ord_hi(ll['house'])} भाव में बैठा है – जीवन बार-बार {HOUSE_STORY[ll['house']][1]} की ओर लौटता है।",
            f"जन्म से मिले वरदान {', '.join(_T(lang, p) for p in ov['strongest'])} से आते हैं; जीवन की सीख {', '.join(_T(lang, p) for p in ov['weakest'])} से।",
        ]
        if ov["yogas"]:
            pro.append(f"कुंडली में {', '.join(ov['yogas'][:4])} जैसे योग हैं – ये वे आशीर्वाद हैं जो सही दशा आने पर खुलते हैं।")
        if ov["doshas"]:
            pro.append(f"साथ ही कुछ कर्म-गाँठें भी हैं – {', '.join(a['text'] for a in ov['doshas'][:3])} – जिन्हें धैर्य और उपाय से खोला जाता है।")
    else:
        pro = [
            f"When {who} {'were' if who == 'you' else 'was'} born on {birth.strftime('%d %B %Y')}, {lagna} was rising on the eastern horizon. This ascendant makes you {LAGNA_TRAIT[lagna][0]}.",
            f"The Moon stood in {moon['sign']}, in the nakshatra {moon['nakshatra']['name']}, so your mind is {MOON_TRAIT[moon['sign']][0]}.",
            f"The thread that runs through your story is the ascendant's lord, {ll['planet']}, sitting in the {_ord_en(ll['house'])} house – again and again life returns to {HOUSE_STORY[ll['house']][0]}.",
            f"Your gifts come through {', '.join(ov['strongest'])}; your lessons through {', '.join(ov['weakest'])}.",
        ]
        if ov["yogas"]:
            pro.append(f"The chart carries {', '.join(ov['yogas'][:4])} – blessings that open when the right period arrives.")
        if ov["doshas"]:
            pro.append(f"It also carries a few karmic knots – {', '.join(a['text'] for a in ov['doshas'][:3])} – which are untied with patience and remedies.")

    # ---------------- chapters ----------------
    chapters = []
    stones = life["milestones"]
    for i, md in enumerate(life["journey"], 1):
        st, en = datetime.fromisoformat(md["start"]), datetime.fromisoformat(md["end"])
        status = "past" if en < now else ("present" if st <= now else "future")
        tv = _tense(status, hi)
        p = md["lord"]
        pl = explain(chart, p, lang)
        title = CHAPTER[p][k]
        stage = _stage((md["age_from"] + md["age_to"]) / 2, hi)
        houses = [pl["house"]] + [o for o in pl["owns"] if o != pl["house"]]
        hs = [HOUSE_STORY[h][k] for h in houses]
        paras = []
        if hi:
            paras.append(f"{_yr(md['start'])} से {_yr(md['end'])} तक (आयु {md['age_from']:.0f}–{md['age_to']:.0f}), {stage} में, {CHAPTER[p][3]}। "
                         f"{_T(lang, p)} आपकी कुंडली में {ord_hi(pl['house'])} भाव में बैठा है, इसलिए यह अध्याय मुख्यतः {hs[0]} के बारे में {tv['was']}"
                         + (f"; और क्योंकि यह {_join([ord_hi(h) for h in houses[1:]], True)} भाव का स्वामी है, {' तथा '.join(hs[1:])} भी इस कथा का हिस्सा {tv['were']}।" if len(hs) > 1 else "।"))
            tone = {"excellent": f"यह जीवन के सबसे उजले अध्यायों में से एक {tv['was']} – {_T(lang, p)} आपकी कुंडली में बलवान व शुभ है, इसलिए प्रयास फल देते हैं और द्वार खुलते हैं।",
                    "good": f"यह समग्र रूप से अनुकूल अध्याय {tv['was']} – प्रगति स्थिर रहती है और सहायता सही समय पर मिलती है।",
                    "mixed": f"यह मिश्रित अध्याय {tv['was']} – एक हाथ से जीवन देता है तो दूसरे से परीक्षा लेता है; विवेक और संतुलन ही कुंजी है।",
                    "challenging": f"यह परीक्षा का अध्याय {tv['was']} – {_T(lang, p)} कुंडली में कठिन स्थिति में है, इसलिए बाधाएँ, विलंब या अचानक बदलाव आते हैं; पर यही काल सबसे गहरी सीख और भीतर की शक्ति भी देता है।"}[md["rating"]]
            paras.append(tone)
            if md["best_ad"] and md["hardest_ad"] and md["best_ad"]["lord"] != md["hardest_ad"]["lord"]:
                paras.append(f"इस अध्याय का सबसे उजला समय {_span(md['best_ad']['start'], md['best_ad']['end'])} ({_T(lang, md['best_ad']['lord'])} अंतर्दशा) {tv['was']}, "
                             f"और सबसे कठिन मोड़ {_span(md['hardest_ad']['start'], md['hardest_ad']['end'])} ({_T(lang, md['hardest_ad']['lord'])} अंतर्दशा)।")
        else:
            paras.append(f"From {_yr(md['start'])} to {_yr(md['end'])} (age {md['age_from']:.0f}–{md['age_to']:.0f}), through {stage}, {CHAPTER[p][2]}. "
                         f"{p} sits in your {_ord_en(pl['house'])} house, so this chapter {tv['is']} above all about {hs[0]}"
                         + (f"; and because it rules your {_join([_ord_en(h) for h in houses[1:]], False)} house{'s' if len(houses) > 2 else ''}, {' as well as '.join(hs[1:])} {tv['were']} part of the story too." if len(hs) > 1 else "."))
            tone = {"excellent": f"It {tv['is']} one of the brightest chapters of your life – {p} is strong and well-placed for you, so effort pays and doors open.",
                    "good": f"On the whole it {tv['is']} a kind chapter – progress is steady and help arrives when it is needed.",
                    "mixed": f"It {tv['is']} a mixed chapter – life gives with one hand and tests with the other; judgement and balance are the key.",
                    "challenging": f"It {tv['is']} a testing chapter – {p} is under strain in your chart, so obstacles, delays or sudden change come; yet this is also when the deepest lessons and inner strength are earned."}[md["rating"]]
            paras.append(tone)
            if md["best_ad"] and md["hardest_ad"] and md["best_ad"]["lord"] != md["hardest_ad"]["lord"]:
                paras.append(f"The brightest stretch {tv['is']} {_span(md['best_ad']['start'], md['best_ad']['end'])}, in the {md['best_ad']['lord']} sub-period; "
                             f"the hardest turn {_span(md['hardest_ad']['start'], md['hardest_ad']['end'])}, in the {md['hardest_ad']['lord']} sub-period.")
        # events in this chapter: milestones + life-area windows, each in its own tense, in date order
        ev = []
        for m in stones:
            ms = datetime.fromisoformat(m["start"])
            if st <= ms < en:
                tn = _when(m["start"], m.get("end"), now)
                age = m["age"] if m["kind"] == "sade_sati" else f"{float(m['age']):.0f}"
                if m["kind"] == "sade_sati" and float(str(m["age"]).split("–")[0]) < 12:
                    ev.append((m["start"], ("आपके बचपन (आयु {age}) में शनि की साढ़ेसाती थी – उस समय परिवार ने अधिक भार और ज़िम्मेदारी उठाई।" if hi else
                                            "Saturn's Sade Sati fell in your early childhood (age {age}) – a time when the family carried extra weight and responsibility.").format(age=age)))
                    continue
                ev.append((m["start"], EV[m["kind"]][tn][k].format(age=age)))
        wins = sorted(_area_windows(chart, md), key=lambda x: x[1]["start"])
        grouped: dict[str, list] = {}
        for area, ad in wins:
            lo, hi_age = AREA_AGES[area]
            if not (lo <= ad["age_from"] <= hi_age):
                continue
            grouped.setdefault(ad["start"], [ad, []])[1].append(area)
        for start_, (ad, areas_) in list(grouped.items())[:3]:
            tn = _when(ad["start"], ad["end"], now)
            span = _span(ad["start"], ad["end"])
            if hi:
                what = _join([AREA_EVENT[a][1].removesuffix(" के") for a in areas_], True) + " के"
            else:
                what = _join([AREA_EVENT[a][0] for a in areas_], False)
            ev.append((ad["start"], EV["area"][tn][k].format(span=span, lord=_T(lang, ad["lord"]), what=what)))
        ev = [x[1] for x in sorted(ev)]
        if ev:
            paras.append(" ".join(ev))
        if status == "present":
            cur_ad = next((a for a in md["antardashas"] if a["start"] <= now.date().isoformat() <= a["end"]), None)
            if cur_ad:
                paras.append((f"आप अभी इस अध्याय के बीच में हैं – {_T(lang, cur_ad['lord'])} अंतर्दशा {cur_ad['end'][:7]} तक चल रही है, जो {cur_ad['themes'][0].split('–')[-1].strip() if cur_ad['themes'] else ''} पर ध्यान माँगती है।" if hi else
                              f"You are in the middle of this chapter now – the {cur_ad['lord']} sub-period runs until {cur_ad['end'][:7]}, asking attention for {cur_ad['themes'][0].split('–')[-1].strip() if cur_ad['themes'] else 'its themes'}."))
        chapters.append({"n": i, "title": title, "lord": p, "status": status, "rating": md["rating"], "rating_label": md["rating_label"],
                         "start": md["start"], "end": md["end"], "age_from": md["age_from"], "age_to": md["age_to"],
                         "stage": stage, "paragraphs": paras})

    # ---------------- epilogue ----------------
    bright = [c for c in chapters if c["rating"] in ("excellent", "good")]
    hard = [c for c in chapters if c["rating"] == "challenging"]
    nxt = next((c for c in chapters if c["status"] == "future" and c["rating"] in ("excellent", "good")), None)
    cur = next((c for c in chapters if c["status"] == "present"), None)
    if hi:
        epi = [f"आपकी कथा में सबसे उजले अध्याय {', '.join(_T(lang, c['lord']) for c in bright) or '—'} के हैं, और सबसे गहरी परीक्षाएँ {', '.join(_T(lang, c['lord']) for c in hard) or '—'} की।"]
        if cur:
            epi.append(f"अभी आप {_T(lang, cur['lord'])} के अध्याय में हैं ({cur['start'][:4]}–{cur['end'][:4]})।")
        if nxt:
            epi.append(f"आगे का अगला अनुकूल अध्याय {_T(lang, nxt['lord'])} का है, जो {nxt['start'][:4]} में आरंभ होगा।")
        epi.append("ग्रह दिशा दिखाते हैं, भाग्य नहीं लिखते – कर्म, विवेक और उपाय से हर अध्याय को बेहतर लिखा जा सकता है।")
    else:
        epi = [f"The brightest chapters of your story belong to {', '.join(c['lord'] for c in bright) or '—'}; the deepest tests to {', '.join(c['lord'] for c in hard) or '—'}."]
        if cur:
            epi.append(f"You are now in the {cur['lord']} chapter ({cur['start'][:4]}–{cur['end'][:4]}).")
        if nxt:
            epi.append(f"The next favourable chapter is {nxt['lord']}'s, beginning in {nxt['start'][:4]}.")
        epi.append("The planets show the weather, not the destination – effort, judgement and remedies let you write each chapter better.")
    return {"prologue": pro, "chapters": chapters, "epilogue": epi}
