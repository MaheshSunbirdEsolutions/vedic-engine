"""Nakshatra-based analysis and remedies, from Raghunandan Prasad Gaur, *Nakshatra Jyotish*
(Krishnamurti paddhati sahit), Manoj Pocket Books. Rules are paraphrased; page numbers are the
book's printed pages.

* Gand-mool / gandanta / abhukta mool births and when their shanti is done (pp. 83-85)
* Vishkanya and Jwalamukhi yogas at birth and their shanti (pp. 82, 178)
* Tara bala – the nine taras counted from the birth nakshatra (pp. 88-91, 179)
* Muhurta for STARTING a remedy: Guru-Pushya, Ravi-Pushya (recommended for mantra sadhana),
  Amrit-siddhi, Sarvartha-siddhi and Ravi yoga, rejecting dagdha nakshatra, ghat nakshatra,
  janma/anujanma/trijanma, vipat/pratyari/vadha taras and Yamaghanta (pp. 173-179)
* Body parts and health watch-points ruled by each nakshatra (ch. 9, pp. 184-196)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from . import ephemeris as eph, i18n
from .constants import NAKSHATRAS, SIGNS
from .panchang import element_index, panchang

SRC = "R. P. Gaur, Nakshatra Jyotish"
NAK = [n if isinstance(n, str) else n[0] for n in NAKSHATRAS]
IDX = {n: i for i, n in enumerate(NAK)}

# ---------------------------------------------------------------- taras
TARAS = [  # (name en, name hi, good?, meaning en, meaning hi)
    ("Janma", "जन्म", None, "birth star – avoid starting new work", "जन्म तारा – नए कार्य का आरंभ न करें"),
    ("Sampat", "सम्पत्", True, "wealth", "धन"),
    ("Vipat", "विपत्", False, "danger / obstacles", "विपत्ति"),
    ("Kshema", "क्षेम", True, "well-being", "कुशलता"),
    ("Pratyari", "प्रत्यरि", False, "opposition", "शत्रुता"),
    ("Sadhaka", "साधक", True, "accomplishment", "सिद्धि"),
    ("Vadha", "वध", False, "destruction", "नाश"),
    ("Mitra", "मित्र", True, "friend", "मित्र"),
    ("Param Mitra", "परम मित्र", True, "great friend", "परम मित्र"),
]


def tara(birth_nak: int, day_nak: int) -> int:
    """0..8 – Janma, Sampat, Vipat, Kshema, Pratyari, Sadhaka, Vadha, Mitra, Param Mitra."""
    return ((day_nak - birth_nak) % 27) % 9


# ---------------------------------------------------------------- muhurta tables (weekday 0 = Sunday)
AMRIT_SIDDHI = {0: ("Hasta", 5), 1: ("Mrigashira", 6), 2: ("Ashwini", 7), 3: ("Anuradha", 8),
                4: ("Pushya", 10), 5: ("Revati", 10), 6: ("Rohini", 11)}   # (nakshatra, spoiling tithi)
SARVARTHA = {
    0: (["Ashwini", "Pushya", "Uttara Phalguni", "Hasta", "Mula", "Uttara Ashadha", "Uttara Bhadrapada"], [1, 3]),
    1: (["Rohini", "Mrigashira", "Pushya", "Anuradha", "Shravana"], [2, 11]),
    2: (["Ashwini", "Krittika", "Ashlesha", "Uttara Bhadrapada"], [3, 9, 12]),
    3: (["Krittika", "Rohini", "Mrigashira", "Hasta", "Anuradha"], [7, 9, 11]),
    4: (["Ashwini", "Punarvasu", "Pushya", "Anuradha", "Revati"], []),
    5: (["Ashwini", "Punarvasu", "Anuradha", "Shravana", "Revati"], []),
    6: (["Rohini", "Swati", "Shravana"], [11, 13]),
}
DAGDHA = {0: "Bharani", 1: "Chitra", 2: "Uttara Ashadha", 3: "Dhanishta", 4: "Uttara Phalguni", 5: "Jyeshtha", 6: "Revati"}
YAMAGHANTA = {0: "Magha", 1: "Vishakha", 2: "Ardra", 3: "Mula", 4: "Krittika", 5: "Rohini", 6: "Hasta"}
GHAT = {0: "Magha", 1: "Hasta", 2: "Swati", 3: "Anuradha", 4: "Mula", 5: "Shravana", 6: "Shatabhisha",
        7: "Revati", 8: "Bharani", 9: "Rohini", 10: "Ardra", 11: "Ashlesha"}  # by Moon sign
VISHKANYA = [  # (nakshatras, weekday, tithis)
    (["Ashlesha", "Shatabhisha"], 0, [2]), (["Krittika", "Vishakha", "Shatabhisha"], 0, [12]),
    (["Ashlesha", "Vishakha", "Shatabhisha"], 2, [7]), (["Ashlesha"], 6, [2]),
    (["Shatabhisha"], 2, [12]), (["Krittika"], 6, [7, 12]),
]
JWALAMUKHI = {1: "Mula", 5: "Bharani", 6: "Krittika", 9: "Rohini", 10: "Ashlesha"}  # tithi -> nakshatra
DAY = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_HI = ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"]
PLANET_DAY = {"Sun": 0, "Moon": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4, "Venus": 5, "Saturn": 6, "Rahu": 6, "Ketu": 2}

# ---------------------------------------------------------------- ch. 9: body parts & health watch-points
HEALTH = {  # nakshatra: ((parts en, parts hi), (watch en, watch hi))
    "Ashwini": (("head, brain", "सिर, मस्तिष्क"), ("head injury, migraine, fainting, epilepsy, insomnia, fevers",
                                                    "सिर की चोट, आधासीसी, मूर्छा, मिर्गी, अनिद्रा, ज्वर")),
    "Bharani": (("head, forehead, eyes and eyesight", "सिर, मस्तक, नेत्र व दृष्टि"),
                ("injury near the eyes, skin trouble, chills and fever, sexual-health problems", "नेत्रों के पास चोट, चर्म रोग, ठंड-ज्वर, रतिरोग")),
    "Krittika": (("head, eyes; face, neck, tonsils, lower jaw", "सिर, नेत्र; चेहरा, गर्दन, टॉन्सिल, निचला जबड़ा"),
                 ("high fevers, burns and accidents, acne, eye inflammation, throat and tonsil trouble, stiff neck",
                  "तीव्र ज्वर, जलना व दुर्घटना, मुंहासे, आंखें आना, गले व टॉन्सिल के रोग, गर्दन की अकड़न")),
    "Rohini": (("face, mouth, tongue, tonsils, palate, neck", "चेहरा, मुंह, जीभ, टॉन्सिल, तालू, गर्दन"),
               ("throat swelling, goitre, colds and cough, headache, irregular menses", "गले में सूजन, घेंघा, सर्दी-खांसी, सिरदर्द, अनियमित मासिक धर्म")),
    "Mrigashira": (("face, chin, cheeks, throat; arms, shoulders, ears", "चेहरा, ठोड़ी, गाल, गला; भुजा, कंधे, कान"),
                   ("acne, throat swelling, nasal polyp, cough-cold, constipation; blood disorders, shoulder pain, sciatica",
                    "मुंहासे, गले में सूजन, नाक में पॉलिप, खांसी-जुकाम, कब्ज; रक्त दोष, कंधों में दर्द, साइटिका")),
    "Ardra": (("throat, arms, shoulders, ears", "गला, भुजाएँ, कंधे, कान"),
              ("throat infections, asthma, dry cough, breathing and ear problems", "गले के रोग, दमा, सूखी खांसी, श्वास व कान के रोग")),
    "Punarvasu": (("ears, throat, shoulders, lungs; chest, stomach", "कान, गला, कंधे, फेफड़े; छाती, आमाशय"),
                  ("pneumonia, pleurisy, bronchitis, TB, ear pain; gastritis, irregular appetite",
                   "निमोनिया, प्लूरिसी, ब्रोंकाइटिस, क्षय, कान दर्द; आमाशय में सूजन, अनियमित भूख")),
    "Pushya": (("lungs, stomach, ribs", "फेफड़े, आमाशय, पसलियाँ"),
               ("TB, jaundice, eczema, stomach ulcers, gallstones", "क्षय, पीलिया, एक्ज़िमा, आमाशय के छाले, पित्ताशय की पथरी")),
    "Ashlesha": (("lungs, stomach, food pipe, gall bladder, pancreas, liver", "फेफड़े, आमाशय, भोजन नली, पित्ताशय, अग्नाशय, यकृत"),
                 ("vata trouble, breathlessness, indigestion, jaundice, anxiety", "वात रोग, श्वास विकार, अपच, पीलिया, घबराहट")),
    "Magha": (("heart, back, spinal cord, spleen, aorta", "हृदय, पीठ, मेरुरज्जु, प्लीहा, महाधमनी"),
              ("heart attack, palpitations, back pain, fainting, kidney stones", "हृदयाघात, धड़कन, पीठ दर्द, मूर्छा, गुर्दे की पथरी")),
    "Purva Phalguni": (("heart, spine", "हृदय, मेरुदंड"),
                       ("heart disease and valve trouble, anaemia, blood pressure, leg and ankle swelling", "हृदय व वाल्व रोग, रक्ताल्पता, रक्तचाप, टांग व टखने में सूजन")),
    "Uttara Phalguni": (("spine; intestines, liver", "मेरुदंड; आंतें, यकृत"),
                        ("back and head pain, fevers; bowel inflammation or blockage, liver disorders",
                         "पीठ व सिर दर्द, ज्वर; आंतों में सूजन या रुकावट, यकृत विकार")),
    "Hasta": (("intestines, glands, digestive enzymes", "आंतें, स्रावी ग्रंथियाँ, एंज़ाइम"),
              ("gas, stomach ache, dysentery, worms, sluggish digestion", "गैस, पेट दर्द, पेचिश, कृमि, मंदाग्नि")),
    "Chitra": (("abdomen, womb; liver, hernia, appendix (Libra half)", "उदर, गर्भाशय; यकृत, हर्निया, अपेंडिक्स"),
               ("stomach ulcers, bites and stings, urinary trouble, stones; kidney and bladder inflammation",
                "पेट में घाव, कीड़ों-सर्पों का काटना, मूत्र विकार, पथरी; गुर्दे व मूत्राशय में सूजन")),
    "Swati": (("skin, kidneys, urinary tract, bladder", "चर्म, गुर्दे, मूत्रनली, मूत्राशय"),
              ("urinary infections, skin disease, leucoderma, kidney disease", "मूत्र रोग, चर्म रोग, श्वेत दाग, गुर्दे के रोग")),
    "Vishakha": (("lower abdomen, bladder, kidneys, pancreas; reproductive organs", "पेट का निचला भाग, मूत्राशय, गुर्दे, अग्नाशय; प्रजनन अंग"),
                 ("diabetes, giddiness, kidney trouble; uterine or prostate problems", "मधुमेह, चक्कर, गुर्दे के रोग; गर्भाशय या प्रोस्टेट के रोग")),
    "Anuradha": (("bladder, rectum, reproductive organs, pubic bones", "मूत्राशय, मलाशय, प्रजनन अंग, गुदा"),
                 ("menstrual trouble, constipation, piles, hip fracture, sore throat, catarrh", "मासिक धर्म में रुकावट, कब्ज़, बवासीर, कूल्हे की चोट, गला दर्द, नज़ला")),
    "Jyeshtha": (("ovaries, womb, colon, reproductive organs", "अंडाशय, गर्भाशय, बड़ी आंत, प्रजनन अंग"),
                 ("leucorrhoea, bleeding piles, reproductive-organ disease, arm and shoulder pain, tumours",
                  "श्वेत प्रदर, खूनी बवासीर, प्रजनन अंगों के रोग, भुजा व कंधों में दर्द, ट्यूमर")),
    "Mula": (("hips, thighs, femur, sciatic nerve", "कूल्हे, जांघें, जांघ की हड्डी, साइटिक तंत्रिका"),
             ("lumbago, arthritis, back pain, breathing trouble, low blood pressure", "कटिवात, गठिया, कमर दर्द, श्वास रोग, निम्न रक्तचाप")),
    "Purva Ashadha": (("thighs, hips", "जांघें, कूल्हे"),
                      ("sciatica, diabetes, flatulence, knee swelling, chest colds", "साइटिका, मधुमेह, अफारा, घुटनों में सूजन, शीत प्रकोप")),
    "Uttara Ashadha": (("thighs; skin, knees, kneecap", "जांघें; चर्म, घुटने, पटेला"),
                       ("sciatica, arthritis, paralysis; gas, eczema, skin disease, palpitations", "साइटिका, गठिया, पक्षाघात; गैस, एक्ज़िमा, चर्म रोग, धड़कन")),
    "Shravana": (("knees, skin", "घुटने, चर्म"),
                 ("eczema, boils, arthritis, TB, pleurisy, indigestion, filaria", "एक्ज़िमा, फोड़े, गठिया, क्षय, प्लूरिसी, अपच, फाइलेरिया")),
    "Dhanishta": (("kneecap, knee bones, legs; ankles, calves", "घुटने की हड्डियाँ, पैर; टखने, पिंडली"),
                  ("leg injuries, hiccups, dry cough; fractures, palpitations, high blood pressure, varicose veins",
                   "पैरों में चोट, हिचकी, सूखी खांसी; फ्रैक्चर, धड़कन, उच्च रक्तचाप, वेरिकोज़ नसें")),
    "Shatabhisha": (("calves and calf muscles", "पिंडली व उसकी मांसपेशियाँ"),
                    ("leg fractures, arthritis, heart disease, eczema, high blood pressure", "टांग में फ्रैक्चर, गठिया, हृदय रोग, एक्ज़िमा, उच्च रक्तचाप")),
    "Purva Bhadrapada": (("ankles; feet and toes", "टखने; पैर व अंगूठा"),
                         ("low blood pressure, ankle swelling, enlarged heart; swollen feet, liver enlargement, hernia, diarrhoea",
                          "निम्न रक्तचाप, टखनों में सूजन, हृदय का बढ़ना; पैरों में सूजन, यकृत वृद्धि, हर्निया, अतिसार")),
    "Uttara Bhadrapada": (("feet", "पैर"), ("arthritis, foot fracture, indigestion, constipation, hernia, flatulence",
                                            "गठिया, पैर में फ्रैक्चर, अपच, कब्ज़, हर्निया, उदरवात")),
    "Revati": (("feet and toes", "पैर व पंजे"), ("foot cramps and pain, intestinal ulcers, deafness, kidney swelling",
                                                "पैरों में ऐंठन व दर्द, आंतों में छाले, बहरापन, गुर्दे में सूजन")),
}


def _T(lang, v):
    return i18n.term(lang, v)


def health_for(chart: dict, lang: str = "en", planets: list[str] | None = None) -> list[dict]:
    """Body parts and health watch-points from the nakshatras of the Moon, the lagna and given planets."""
    k = 1 if lang == "hi" else 0
    rows = []
    lagna_nak = int(chart["lagna"]["longitude"] // (360 / 27))
    pts = [("Lagna", lagna_nak), ("Moon", chart["planets"]["Moon"]["nakshatra"]["index"] - 1)]
    for p in planets or []:
        if p in chart["planets"] and p != "Moon":
            pts.append((p, chart["planets"][p]["nakshatra"]["index"] - 1))
    for who, n in pts:
        name = NAK[n]
        h = HEALTH[name]
        rows.append({"point": who, "nakshatra": name, "parts": h[0][k], "watch": h[1][k],
                     "source": f"{SRC}, ch. 9 (pp. 184–196)"})
    return rows


# ---------------------------------------------------------------- birth doshas
def _birth_tithi_vara(dt_local: datetime, tz: str, lat: float, lon: float, s) -> tuple[int, int]:
    jd = eph.local_to_jd(dt_local, tz)
    tithi = element_index("tithi", jd, s) + 1                      # 1..30
    midnight = eph.local_to_jd(datetime.combine(dt_local.date(), datetime.min.time()), tz)
    sunrise, _ = eph.sunrise_sunset(midnight, lat, lon)
    wd = (dt_local.weekday() + 1) % 7                               # Python Mon=0 -> Sunday=0
    if jd < sunrise:
        wd = (wd - 1) % 7                                           # Hindu day starts at sunrise
    return tithi, wd


def birth_doshas(chart: dict, dt_local: datetime, tz: str, lat: float, lon: float, s, lang: str = "en") -> list[dict]:
    hi = lang == "hi"
    moon = chart["planets"]["Moon"]
    lon_m = moon["longitude"]
    n = moon["nakshatra"]["index"] - 1
    name = NAK[n]
    out = []
    span = 360 / 27
    # Gand-mool
    if name in ("Ashwini", "Ashlesha", "Magha", "Jyeshtha", "Mula", "Revati"):
        big = name in ("Ashlesha", "Jyeshtha", "Mula")
        anujanma, trijanma = NAK[(n + 9) % 27], NAK[(n + 18) % 27]
        if hi:
            text = (f"चंद्रमा {_T(lang, name)} में – गण्डमूल नक्षत्र ({'बड़ा मूल' if big else 'छोटा मूल'})। जल व अग्नि राशियों की संधि पर जन्म।")
            rem = ([f"मूल शांति उस दिन कराएँ जब चंद्रमा पुनः {_T(lang, name)} नक्षत्र में आए (जन्म के लगभग 27 दिन बाद; वयस्क के लिए हर माह यह दिन आता है)।"]
                   if big else
                   [f"छोटे मूल की शांति जन्म नक्षत्र के दिन या उसी स्वामी के अनुजन्म ({_T(lang, anujanma)}) या त्रिजन्म ({_T(lang, trijanma)}) नक्षत्र के दिन कराई जा सकती है।"])
            rem.append(f"नक्षत्र स्वामी {_T(lang, 'Mercury' if name in ('Ashlesha', 'Jyeshtha', 'Revati') else 'Ketu')} के मंत्र जप व दान से सहायता।")
        else:
            text = (f"Moon in {name} – a gand-mool nakshatra ({'major' if big else 'minor'} mool): birth at the junction of a water and a fire sign.")
            rem = ([f"Do mool shanti on a day the Moon is again in {name} (about 27 days after birth for a baby; for an adult the day recurs every month)."]
                   if big else
                   [f"Shanti for a minor mool can be done on the birth-nakshatra day or on its anujanma ({anujanma}) or trijanma ({trijanma}) day – the 10th and 19th nakshatras, which share the same lord."])
            rem.append(f"Japa and daana for the nakshatra lord ({'Mercury' if name in ('Ashlesha', 'Jyeshtha', 'Revati') else 'Ketu'}) also help.")
        sev = 2 if big else 1
        d = min(abs(lon_m - b) for b in (0, 120, 240, 360))
        if d <= 26 / 60 + 40 / 3600:
            sev = 3
            text += (" गण्डान्त मूल – संधि बिंदु के 26′40″ के भीतर, सबसे संवेदनशील।" if hi else
                     " Gandanta mool – within 26′40″ of the junction, the most sensitive zone.")
        if abs(lon_m - 240) <= 13 / 60 + 20 / 3600:
            text += (" अभुक्त मूल (ज्येष्ठा-मूल संधि)।" if hi else " Abhukta mool (Jyeshtha–Mula junction).")
        out.append({"id": "gand_mool", "severity": sev, "text": text, "remedies": rem, "source": f"{SRC}, pp. 83–85"})
    # Vishkanya & Jwalamukhi need the birth tithi and weekday
    tithi, wd = _birth_tithi_vara(dt_local, tz, lat, lon, s)
    t_in_paksha = (tithi - 1) % 15 + 1
    if t_in_paksha in JWALAMUKHI and JWALAMUKHI[t_in_paksha] == name:
        out.append({"id": "jwalamukhi", "severity": 2,
                    "text": ("जन्म ज्वालामुखी योग में (तिथि व नक्षत्र का अशुभ संयोग)।" if hi else
                             "Born in Jwalamukhi yoga (an inauspicious tithi–nakshatra combination)."),
                    "remedies": (["मूल शांति की भाँति शांति कराएँ।"] if hi else ["Have a shanti done in the same way as mool shanti."]),
                    "source": f"{SRC}, p. 178"})
    for naks, day, tithis in VISHKANYA:
        if name in naks and wd == day and t_in_paksha in tithis:
            out.append({"id": "vishkanya", "severity": 1,
                        "text": ("विषकन्या योग (परंपरागत रूप से कन्या की कुंडली में देखा जाता है)। यह एक पारंपरिक मान्यता है, व्यक्ति पर कोई निर्णय नहीं।" if hi else
                                 "Vishkanya yoga (traditionally looked at only in a girl's chart). A traditional belief, not a judgement of the person."),
                        "remedies": (["शांति कराएँ; विवाह मिलान में दीर्घायु योग वाली कुंडली देखी जाती है।"] if hi else
                                     ["Have a shanti done; in matching, a partner's chart with strong longevity is traditionally preferred."]),
                        "source": f"{SRC}, p. 82"})
            break
    return out


# ---------------------------------------------------------------- when to start remedies
def remedy_days(chart: dict, tz: str, lat: float, lon: float, s, start: date, days: int = 60,
                planets: list[str] | None = None, lang: str = "en", limit: int = 12) -> list[dict]:
    """Auspicious days to START a remedy (mantra, vrata, wearing a ratna/jadi), filtered by the
    native's tara bala, janma nakshatras, dagdha, ghat nakshatra and Yamaghanta."""
    hi = lang == "hi"
    birth = chart["planets"]["Moon"]["nakshatra"]["index"] - 1
    moon_sign = chart["planets"]["Moon"]["sign_index"] - 1
    ghat = GHAT[moon_sign]
    want_days = {PLANET_DAY[p] for p in planets or []}
    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        p = panchang(d, tz, lat, lon, s)
        nak = p["nakshatra"]["name"]
        n = IDX.get(nak)
        if n is None:
            continue
        wd = (d.weekday() + 1) % 7
        t15 = (p["tithi"]["number"] - 1) % 15 + 1
        tr = tara(birth, n)
        bad = []
        if tr in (0, 2, 4, 6):
            bad.append(TARAS[tr][1 if hi else 0] + (" तारा" if hi else " tara"))
        if DAGDHA[wd] == nak:
            bad.append("दग्ध नक्षत्र" if hi else "dagdha nakshatra")
        if YAMAGHANTA[wd] == nak:
            bad.append("यमघंट" if hi else "Yamaghanta")
        if nak == ghat:
            bad.append("घात नक्षत्र" if hi else "ghat nakshatra")
        good = []
        if wd == 4 and nak == "Pushya":
            good.append(("गुरु पुष्य योग" if hi else "Guru-Pushya yoga", 3))
        if wd == 0 and nak == "Pushya":
            good.append(("रवि पुष्य योग – मंत्र साधना हेतु श्रेष्ठ" if hi else "Ravi-Pushya yoga – best for starting mantra sadhana", 3))
        a = AMRIT_SIDDHI[wd]
        if a[0] == nak and t15 != a[1]:
            good.append(("अमृत सिद्धि योग" if hi else "Amrit-siddhi yoga", 2.5))
        sv = SARVARTHA[wd]
        if nak in sv[0] and t15 not in sv[1]:
            good.append(("सर्वार्थ सिद्धि योग" if hi else "Sarvartha-siddhi yoga", 2))
        sun_n = int(eph.body_longitude(eph.local_to_jd(datetime.combine(d, datetime.min.time()).replace(hour=7), tz), "Sun", s) // (360 / 27))
        if (n - sun_n) % 27 + 1 in (4, 6, 10, 13, 20):
            good.append(("रवि योग" if hi else "Ravi yoga", 1))
        if not good or bad:
            continue
        score = sum(g[1] for g in good) + (1 if tr in (1, 3, 5, 7, 8) else 0) + (1.5 if wd in want_days else 0)
        out.append({
            "date": d.isoformat(), "weekday": DAY_HI[wd] if hi else DAY[wd], "nakshatra": nak,
            "tithi": p["tithi"]["name"], "paksha": p["tithi"]["paksha"], "nakshatra_ends": p["nakshatra"]["ends"],
            "yogas": [g[0] for g in good], "tara": TARAS[tr][1 if hi else 0],
            "for_planets": [pl for pl in planets or [] if PLANET_DAY[pl] == wd],
            "score": round(score, 1),
        })
    out.sort(key=lambda x: (-x["score"], x["date"]))
    return sorted(out[:limit], key=lambda x: x["date"])


def next_days(nak: str, tz: str, lat: float, lon: float, s, start: date, n: int = 3, horizon: int = 120) -> list[dict]:
    """Next dates on which the given nakshatra prevails at sunrise (e.g. Ashlesha for Ashlesha Bali)."""
    out: list[dict] = []
    target = IDX[nak]
    last: date | None = None
    for i in range(horizon):
        d = start + timedelta(days=i)
        p = panchang(d, tz, lat, lon, s)
        cur = IDX.get(p["nakshatra"]["name"])
        rec = None
        if cur == target:
            rec = {"date": d.isoformat(), "from": "sunrise", "ends": p["nakshatra"]["ends"]}
        elif cur is not None and (cur + 1) % 27 == target and p["nakshatra"]["ends"][:10] == d.isoformat():
            rec = {"date": d.isoformat(), "from": p["nakshatra"]["ends"], "ends": None}
        if rec:
            if last is None or (d - last).days > 1:   # same occurrence spanning two days -> keep the first
                out.append(rec)
            last = d
            if len(out) >= n and (d - last).days == 0 and out[-1]["date"] != d.isoformat():
                break
        if len(out) >= n and last and (d - last).days > 1:
            break
    return out[:n]


def tara_table(chart: dict, lang: str = "en") -> list[dict]:
    hi = lang == "hi"
    b = chart["planets"]["Moon"]["nakshatra"]["index"] - 1
    rows = []
    for t in range(9):
        naks = [NAK[(b + t + 9 * k) % 27] for k in range(3)]
        name, name_hi, good, m_en, m_hi = TARAS[t]
        rows.append({"tara": name_hi if hi else name, "good": good, "meaning": m_hi if hi else m_en, "nakshatras": naks})
    return rows


def days_note(lang: str) -> str:
    if lang == "hi":
        return ("उपाय (मंत्र जप, व्रत, रत्न/जड़ी धारण) इन्हीं शुभ दिनों में आरंभ करें; ग्रह के अपने वार वाले दिन प्राथमिकता पाते हैं। "
                "जन्म/अनुजन्म/त्रिजन्म, विपत्, प्रत्यरि व वध तारा, दग्ध नक्षत्र, घात नक्षत्र व यमघंट वाले दिन हटा दिए गए हैं।")
    return ("Start a remedy (mantra japa, vrata, wearing a ratna or jadi) on one of these days; days on the planet's own weekday rank higher. "
            "Days on your janma/anujanma/trijanma, Vipat/Pratyari/Vadha taras, dagdha or ghat nakshatra and Yamaghanta are excluded.")


def report(chart: dict, dt_local: datetime, tz: str, lat: float, lon: float, s, lang: str = "en",
           start: date | None = None, planets: list[str] | None = None) -> dict:
    hi = lang == "hi"
    moon = chart["planets"]["Moon"]
    n = moon["nakshatra"]["index"] - 1
    return {
        "janma_nakshatra": NAK[n], "pada": moon["nakshatra"]["pada"], "lord": moon["nakshatra"]["lord"],
        "anujanma": NAK[(n + 9) % 27], "trijanma": NAK[(n + 18) % 27],
        "ghat_nakshatra": GHAT[moon["sign_index"] - 1], "moon_sign": SIGNS[moon["sign_index"] - 1],
        "birth_doshas": birth_doshas(chart, dt_local, tz, lat, lon, s, lang),
        "taras": tara_table(chart, lang),
        "health": health_for(chart, lang, planets),
        "remedy_days": remedy_days(chart, tz, lat, lon, s, start or date.today(), 75, planets, lang),
        "remedy_days_note": days_note(lang),
        "source": f"{SRC} (Manoj Pocket Books) – chapters 4, 8, 9",
    }
