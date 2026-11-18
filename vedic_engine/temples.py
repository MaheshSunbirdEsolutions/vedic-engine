"""Temples and tirthas traditionally visited for a planet, a dosha or a life problem.

Facts were gathered from public sources in Nov 2026 (temple / government / encyclopaedia pages,
listed per entry). Timings, fees and rules change – the app always tells the user to confirm with
the temple before travelling. Nothing here promises a result.
"""
from __future__ import annotations

T = list[str]


def _e(id_, name, name_hi, place, state, planets, doshas, areas, deity, what, what_hi, when, when_hi, sources, lat=None, lon=None):
    return {"id": id_, "name": name, "name_hi": name_hi, "place": place, "state": state, "planets": planets,
            "doshas": doshas, "areas": areas, "deity": deity, "what": what, "what_hi": what_hi,
            "when": when, "when_hi": when_hi, "sources": sources, "lat": lat, "lon": lon}


NAV_SRC = "https://en.wikipedia.org/wiki/Navagraha_temples_in_Tamil_Nadu"

TEMPLES = [
    # ---------------- Navagraha circuit around Kumbakonam (Tamil Nadu) ----------------
    _e("suryanar", "Suryanar Kovil", "सूर्यनार कोविल", "near Aduthurai, Kumbakonam", "Tamil Nadu", ["Sun"], [], ["career", "health"],
       "Surya", "The Sun temple of the Navagraha circuit; the only one where Surya is the main deity, with shrines for all nine grahas. Good first stop of the circuit.",
       "नवग्रह परिक्रमा का सूर्य मंदिर; यहाँ सूर्य ही मुख्य देवता हैं और नौ ग्रहों के अलग-अलग मंदिर हैं।",
       "Sunday", "रविवार", [NAV_SRC]),
    _e("thingalur", "Kailasanathar Temple, Thingalur", "कैलासनाथर मंदिर, तिंगलूर", "Thingalur, ~35 km from Kumbakonam", "Tamil Nadu", ["Moon"], ["vish", "kemadruma", "chandra_grahan", "weak_moon"], ["mind"],
       "Shiva with Chandra", "Moon (Chandra) shrine of the Navagraha circuit, for an afflicted or weak Moon and peace of mind.",
       "नवग्रह परिक्रमा का चंद्र स्थान – पीड़ित/क्षीण चंद्रमा व मानसिक शांति हेतु।",
       "Monday", "सोमवार", [NAV_SRC]),
    _e("vaitheeswaran", "Vaitheeswaran Koil", "वैदीश्वरन कोविल", "near Mayiladuthurai", "Tamil Nadu", ["Mars"], ["manglik", "angarak"], ["health"],
       "Shiva as Vaidyanathar (the divine physician)", "Mars (Angaraka) shrine. Shiva here is the 'God of healing'; a dip in the Siddhamirtham tank is believed to cure disease. Also known for Nadi palm-leaf astrology.",
       "मंगल (अंगारक) स्थान। यहाँ शिव वैद्यनाथ ('चिकित्सक') हैं; सिद्धामृत कुंड में स्नान रोग-निवारक माना जाता है। नाड़ी ज्योतिष के लिए भी प्रसिद्ध।",
       "Tuesday", "मंगलवार", ["https://en.wikipedia.org/wiki/Vaitheeswaran_Koil", "https://www.incredibleindia.gov.in/en/tamil-nadu/thanjavur/vaitheeswaran-koil"]),
    _e("thiruvenkadu", "Swetharanyeswarar Temple, Thiruvenkadu", "श्वेतारण्येश्वर मंदिर, तिरुवेंकाडु", "~13 km east of Vaitheeswaran Koil", "Tamil Nadu", ["Mercury"], [], ["education", "business"],
       "Shiva with Budha", "Mercury (Budha) shrine of the Navagraha circuit – for learning, speech and trade.",
       "बुध स्थान – विद्या, वाणी और व्यापार हेतु।", "Wednesday", "बुधवार", [NAV_SRC]),
    _e("alangudi", "Apatsahayesvarar Temple, Alangudi", "आपत्सहायेश्वर मंदिर, आलंगुडी", "18 km south of Kumbakonam", "Tamil Nadu", ["Jupiter"], ["guru_chandal", "guru_ketu"], ["children", "education", "marriage", "fortune"],
       "Shiva; Dakshinamurthy worshipped as Guru", "Jupiter (Guru) shrine. Thursdays are crowded; huge gatherings at Guru Peyarchi (Jupiter's sign change). Tradition asks devotees to stay at least one lagna (about 2½ hours).",
       "गुरु स्थान; दक्षिणामूर्ति की गुरु रूप में पूजा। गुरुवार व गुरु पेयर्ची (गुरु का राशि परिवर्तन) पर भारी भीड़। परंपरा: कम से कम एक लग्न (~2½ घंटे) रुकें।",
       "Thursday; Guru Peyarchi", "गुरुवार; गुरु राशि परिवर्तन", [NAV_SRC, "https://shivatemples.com/sofc/sc098.html"]),
    _e("kanjanur", "Agniswarar Temple, Kanjanur", "अग्नीश्वर मंदिर, कंजनूर", "3 km from Suryanar Kovil", "Tamil Nadu", ["Venus"], ["shukra_rahu"], ["marriage", "comforts"],
       "Shiva with Shukra", "Venus (Shukra) shrine – for marriage, comforts and relationships.", "शुक्र स्थान – विवाह, सुख-सुविधा व संबंधों हेतु।",
       "Friday", "शुक्रवार", [NAV_SRC]),
    _e("thirunallar", "Darbaranyeswarar (Saneeswaran) Temple, Thirunallar", "दर्भारण्येश्वर (शनीश्वर) मंदिर, तिरुनल्लार", "near Karaikal", "Puducherry",
       ["Saturn"], ["sade_sati", "dhaiya", "shrapit", "vish", "surya_shani", "mangal_shani"], ["career", "delays", "health"],
       "Shani (Saneeswaran) within the Shiva temple", "The most important Saturn temple. King Nala was freed from Saturn's affliction here; devotees apply sesame oil and bathe in Nala Theertham before darshan. Very crowded on Saturdays and at Shani Peyarchi (Saturn's sign change; the latest was 6 March 2026, Aquarius → Pisces).",
       "शनि का प्रमुख मंदिर। राजा नल यहीं शनि-पीड़ा से मुक्त हुए; दर्शन से पहले तिल का तेल लगाकर नल तीर्थ में स्नान। शनिवार व शनि पेयर्ची पर भारी भीड़ (पिछला परिवर्तन 6 मार्च 2026, कुंभ → मीन)।",
       "Saturday; Shani Peyarchi", "शनिवार; शनि राशि परिवर्तन",
       ["https://www.shivatemples.com/sofc/sc052.php", "https://karaikal.gov.in/sanipeyarchi-festival-2026/"]),
    _e("thirunageswaram", "Naganathaswamy Temple, Thirunageswaram", "नागनाथस्वामी मंदिर, तिरुनागेश्वरम", "~6 km from Kumbakonam", "Tamil Nadu",
       ["Rahu"], ["kaal_sarp", "surya_grahan", "chandra_grahan", "guru_chandal", "shrapit", "angarak", "shukra_rahu"], ["marriage", "children"],
       "Shiva as Naganatha; Rahu with his two consorts", "Rahu shrine. Milk abhishekam to Rahu during Rahu Kalam – the milk is seen turning bluish as it flows over the idol. Sundays are special. Offerings: urad dal and blue cloth. Sought for Kaal Sarp / sarpa dosha, marriage obstacles and childlessness.",
       "राहु स्थान। राहु काल में राहु का दुग्धाभिषेक – दूध मूर्ति पर नीला दिखता है। रविवार विशेष। अर्पण: उड़द दाल, नीला वस्त्र। कालसर्प/सर्प दोष, विवाह बाधा व संतान हेतु।",
       "Rahu Kalam, especially Sunday", "राहु काल, विशेषकर रविवार", ["https://shivatemples.com/sofc/sc029.html", "https://www.wikipedia.org/wiki/Rahu_Stalam"]),
    _e("keezhaperumpallam", "Naganathaswamy Temple, Keezhaperumpallam", "नागनाथस्वामी मंदिर, कीळपेरुम्पल्लम", "near Poompuhar", "Tamil Nadu",
       ["Ketu"], ["surya_ketu", "chandra_ketu", "guru_ketu", "kaal_sarp"], ["spiritual"],
       "Shiva; Ketu shrine", "Ketu shrine of the Navagraha circuit.", "नवग्रह परिक्रमा का केतु स्थान।", "Tuesday", "मंगलवार", [NAV_SRC]),
    # ---------------- all nine grahas ----------------
    _e("guwahati_navagraha", "Navagraha Mandir, Chitrachal Hill", "नवग्रह मंदिर, चित्राचल पहाड़ी", "Guwahati", "Assam",
       ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"], [], [],
       "Nine graha-lingas", "Built in 1752 by Ahom king Rajeshwar Singha. Nine Shiva-lingas, one per graha, each draped in its colour, with the Sun at the centre – worship of all nine together.",
       "1752 में अहोम राजा राजेश्वर सिंह द्वारा निर्मित। नौ ग्रहों के नौ लिंग, प्रत्येक अपने रंग के वस्त्र में – सभी ग्रहों की एक साथ पूजा।",
       "any day", "कोई भी दिन", ["https://en.wikipedia.org/wiki/Navagraha_Mandir,_Guwahati"]),
    # ---------------- Mars / Manglik ----------------
    _e("mangalnath", "Mangalnath Temple", "मंगलनाथ मंदिर", "Ujjain, on the Kshipra", "Madhya Pradesh", ["Mars"], ["manglik", "angarak"], ["marriage"],
       "Shiva as Mangalnath", "Held to be the birthplace of Mars (Matsya Purana). Known for Bhat Puja (offering of cooked rice) for Manglik / Kuja dosha, usually before marriage; also Angarak dosha shanti.",
       "मत्स्य पुराण अनुसार मंगल का जन्म स्थान। मांगलिक/कुज दोष के लिए भात पूजा (चावल अर्पण), प्रायः विवाह से पहले; अंगारक दोष शांति भी।",
       "Tuesday (puja hours ~7 am–3 pm)", "मंगलवार (पूजा ~प्रातः 7 – दोपहर 3)", ["https://en.wikipedia.org/wiki/Mangalnath_Temple", "https://www.ujjaindarshan.com/mangalnath-temple-ujjain/"]),
    _e("amalner", "Shree Mangal Graha Mandir", "श्री मंगल ग्रह मंदिर", "Amalner, Jalgaon district", "Maharashtra", ["Mars"], ["manglik"], ["marriage", "property"],
       "Mangal Dev", "One of the rare temples dedicated to Mars itself; red lentils are the main offering.",
       "मंगल देव को समर्पित दुर्लभ मंदिरों में एक; मसूर दाल मुख्य अर्पण।", "Tuesday", "मंगलवार",
       ["https://jalgaon.gov.in/?p=29853", "https://www.incredibleindia.gov.in/en/maharashtra/jalgaon/shree-mangal-graha-mandir"]),
    # ---------------- Rahu–Ketu / Kaal Sarp / Naga ----------------
    _e("trimbakeshwar", "Trimbakeshwar Jyotirlinga", "त्र्यंबकेश्वर ज्योतिर्लिंग", "near Nashik", "Maharashtra",
       ["Rahu", "Ketu", "Sun"], ["kaal_sarp", "pitra"], ["family"],
       "Shiva (Jyotirlinga)", "The best-known place for Kaal Sarp shanti and for Narayan Nagbali (a 3-day rite for pitra dosha) and Tripindi shraddha. These are done by Trimbak's priests in the town; only Rudrabhishek is done inside the temple.",
       "कालसर्प शांति, नारायण नागबलि (पितृ दोष हेतु 3 दिन का अनुष्ठान) व त्रिपिंडी श्राद्ध के लिए सबसे प्रसिद्ध। ये नगर के पुरोहित करते हैं; मंदिर के भीतर केवल रुद्राभिषेक।",
       "dates fixed by nakshatra – book with a priest", "नक्षत्र अनुसार तिथि – पुरोहित से तय करें", ["https://trimbakeshwar-temple.teachable.com/"]),
    _e("kalahasti", "Srikalahasti Temple", "श्रीकालहस्ती मंदिर", "~36 km from Tirupati", "Andhra Pradesh",
       ["Rahu", "Ketu"], ["kaal_sarp", "surya_grahan", "chandra_grahan", "shrapit"], ["marriage", "children"],
       "Shiva as Kalahasteeswara (Vayu linga)", "Famous Rahu–Ketu Sarpa Dosha Nivarana Puja, held daily; doing it in Rahu Kalam is preferred. Also sought for marriage delay and progeny.",
       "प्रसिद्ध राहु-केतु सर्प दोष निवारण पूजा, प्रतिदिन; राहु काल में करना श्रेष्ठ। विवाह विलंब व संतान हेतु भी।",
       "daily; Rahu Kalam preferred", "प्रतिदिन; राहु काल श्रेष्ठ", ["https://srikalahastitemple.org.in/srikalahasti-temple-sarpa-dosha-pooja", "https://hindupad.com/rahu-ketu-sarpa-dosha-nivarana-puja-at-sri-kalahasti-temple/"]),
    _e("kukke", "Kukke Subramanya Temple", "कुक्के सुब्रह्मण्य मंदिर", "Dakshina Kannada", "Karnataka",
       ["Rahu", "Ketu", "Mars"], ["kaal_sarp", "manglik"], ["children", "health"],
       "Subramanya with Vasuki (Nagaraja)", "India's foremost temple for sarpa / naga dosha. Sarpa Samskara is a 2-day rite (₹4,200 on the temple's site); Ashlesha Bali is done on Ashlesha nakshatra days. Also sought by childless couples.",
       "सर्प/नाग दोष के लिए प्रमुख मंदिर। सर्प संस्कार 2 दिन का (मंदिर साइट पर ₹4,200); आश्लेषा बलि आश्लेषा नक्षत्र के दिन। निःसंतान दंपति भी आते हैं।",
       "Ashlesha nakshatra days (Ashlesha Bali)", "आश्लेषा नक्षत्र (आश्लेषा बलि)", ["https://kukkedevasthanam.org.in/", "https://karnatakatourism.org/en/attractions/kukke-subramanya-temple"]),
    # ---------------- Saturn ----------------
    _e("shingnapur", "Shani Shingnapur", "शनि शिंगणापुर", "Ahilyanagar (Ahmednagar) district", "Maharashtra",
       ["Saturn"], ["sade_sati", "dhaiya", "shrapit"], ["career"],
       "Shani as a self-manifested black stone, open to the sky", "Devotees do tail-abhishek (oil poured over the stone) to ease Sade Sati and Dhaiya. Shani Amavasya (new moon on a Saturday) is the biggest day. Since 2025 the trust accepts only branded oil.",
       "खुले आकाश में स्वयंभू काली शिला। साढ़ेसाती/ढैया हेतु तैलाभिषेक। शनि अमावस्या सबसे बड़ा दिन। 2025 से केवल ब्रांडेड तेल स्वीकार।",
       "Saturday; Shani Amavasya", "शनिवार; शनि अमावस्या", ["https://etvbharat.com/en/!state/shanishinganapur-only-branded-oil-can-be-offered-at-shani-temple-enn25021504135"]),
    # ---------------- Moon ----------------
    _e("somnath", "Somnath Jyotirlinga", "सोमनाथ ज्योतिर्लिंग", "Prabhas Patan, Veraval", "Gujarat", ["Moon"], ["vish", "kemadruma", "chandra_grahan", "weak_moon"], ["mind", "health"],
       "Shiva as Somnatha, 'Lord of the Moon'", "Tradition holds that the Moon was freed from Daksha's curse here by worshipping Shiva (with the Mahamrityunjaya mantra) – the classic tirtha for a weak or afflicted Moon.",
       "परंपरा: चंद्रमा ने यहाँ शिव (महामृत्युंजय मंत्र) की आराधना कर दक्ष के शाप से मुक्ति पाई – क्षीण/पीड़ित चंद्र हेतु प्रमुख तीर्थ।",
       "Monday; Purnima", "सोमवार; पूर्णिमा", ["https://www.utsav.gov.in/view-darshan/somnath-live-darshan"]),
    # ---------------- Pitra dosha ----------------
    _e("gaya", "Vishnupad Temple & Phalgu river, Gaya", "विष्णुपद मंदिर व फल्गु नदी, गया", "Gaya", "Bihar", ["Sun", "Rahu"], ["pitra"], ["family"],
       "Vishnu's footprint", "The foremost place for pind daan and shraddha; Pitru Paksha mela every Ashwin. Rites begin on the Phalgu and continue at Vishnupad and the other vedis.",
       "पिंडदान व श्राद्ध का सर्वप्रमुख स्थान; हर आश्विन में पितृपक्ष मेला। फल्गु तट से आरंभ, विष्णुपद व अन्य वेदियों पर।",
       "Pitru Paksha (Sep–Oct) or any Amavasya", "पितृपक्ष (सितंबर–अक्टूबर) या अमावस्या", ["https://utsav.gov.in/view-event/pitra-paksha-1", "https://www.hindu-blog.com/2009/09/pitru-paksh-shradh-and-pinda-daan-at.html"]),
    _e("brahmakapal", "Brahma Kapal, Badrinath", "ब्रह्मकपाल, बद्रीनाथ", "Badrinath, on the Alaknanda", "Uttarakhand", ["Sun", "Rahu"], ["pitra"], ["family"],
       "—", "Pind daan on the ghat behind the Badrinath temple; open only in the Char Dham season.",
       "बद्रीनाथ मंदिर के पीछे अलकनंदा तट पर पिंडदान; केवल चारधाम यात्रा काल में।",
       "Badrinath season (May–Nov)", "बद्रीनाथ यात्रा काल (मई–नवंबर)", ["https://www.chardhamtour.in/pind-daan-in-badrinath.html"]),
    _e("pehowa", "Prithudak Tirtha, Pehowa", "पृथूदक तीर्थ, पिहोवा", "Kurukshetra district", "Haryana", ["Sun", "Rahu"], ["pitra"], ["family"],
       "Saraswati tirtha", "A major place for pind daan for ancestors on the Saraswati; family genealogy registers are kept here. Closest of these to Himachal.",
       "सरस्वती तट पर पिंडदान का प्रमुख स्थान; यहाँ वंशावली रजिस्टर रखे जाते हैं। हिमाचल से सबसे निकट।",
       "Amavasya; Chaitra Chaudas mela", "अमावस्या; चैत्र चौदस मेला", ["https://en.wikipedia.org/wiki/Pehowa"]),
    _e("ujjain_siddhavat", "Siddhavat & Ram Ghat", "सिद्धवट व रामघाट", "Ujjain, on the Kshipra", "Madhya Pradesh", ["Rahu", "Ketu", "Sun"], ["pitra", "kaal_sarp"], ["family"],
       "Sacred banyan (Siddhavat)", "Pitra dosh pind daan and tarpan, and Kaal Sarp shanti, on the Kshipra banks (not inside Mahakaleshwar's sanctum). Combines well with Mangalnath.",
       "क्षिप्रा तट पर पितृ दोष पिंडदान/तर्पण व कालसर्प शांति (महाकाल गर्भगृह में नहीं)। मंगलनाथ के साथ किया जा सकता है।",
       "Amavasya; Naga Panchami", "अमावस्या; नाग पंचमी", ["https://www.ujjaindarshan.com/the-sacred-banyan-tree/"]),
    # ---------------- life-area temples ----------------
    _e("thirumanancheri", "Kalyana Sundareswarar Temple, Thirumanancheri", "कल्याणसुंदरेश्वर मंदिर, तिरुमणंचेरी", "near Kuthalam, Mayiladuthurai", "Tamil Nadu",
       ["Venus", "Jupiter"], ["manglik"], ["marriage"],
       "Shiva and Parvati in their wedding form", "Where Shiva married Parvati – the 'marriage temple' for delayed marriage. Devotees offer garlands; the garland received back is kept at home and returned to the temple by the couple after the wedding.",
       "जहाँ शिव-पार्वती का विवाह हुआ – विवाह विलंब का मंदिर। माला अर्पित की जाती है; मिली माला घर में रखी जाती है और विवाह के बाद दंपति लौटाते हैं।",
       "any day", "कोई भी दिन", ["https://shivatemples.com/nofc/nc25.php"]),
    _e("garbharakshambigai", "Garbharakshambigai Temple, Thirukarukavur", "गर्भरक्षाम्बिका मंदिर, तिरुकरुकावूर", "near Papanasam, Thanjavur", "Tamil Nadu",
       ["Jupiter", "Moon"], [], ["children"],
       "Parvati as protector of the womb", "Visited by couples praying for a child and for safe pregnancy: ghee blessed at the goddess's feet is taken for 48 days; castor oil is given for a safe delivery.",
       "संतान व सुरक्षित गर्भ हेतु। देवी के चरणों में अभिमंत्रित घी 48 दिन लिया जाता है; सुरक्षित प्रसव हेतु अरंडी का तेल।",
       "any day", "कोई भी दिन", ["https://en.wikipedia.org/wiki/Garbharakshambigai_Temple"]),
    _e("baglamukhi", "Maa Baglamukhi Temple, Bankhandi", "माँ बगलामुखी मंदिर, बनखंडी", "near Dehra, Kangra (~35–40 km from Kangra)", "Himachal Pradesh",
       ["Mars"], ["manglik", "angarak"], ["enemies", "legal"],
       "Bagalamukhi, the 8th Mahavidya", "A siddha-peetha of Bagalamukhi, the Mahavidya linked to Mars in tantra-jyotish. Havans here are sought for protection, disputes and court cases. Near Jwalamukhi and Chintpurni – the closest of these temples to Mandi.",
       "बगलामुखी का सिद्ध पीठ – तंत्र-ज्योतिष में मंगल से संबद्ध महाविद्या। रक्षा, विवाद व मुकदमों हेतु हवन। ज्वालामुखी व चिंतपूर्णी के निकट – मंडी से सबसे पास।",
       "Tuesday; Navratri", "मंगलवार; नवरात्रि", ["https://hpkangra.nic.in/tourist-place/shri-bagalamukhi-mata-temple/", "https://en.wikipedia.org/wiki/Bagalamukhi_Temple,_Bankhandi,_HP"]),
]
BY_ID = {t["id"]: t for t in TEMPLES}
AREA_ALIASES = {"marriage": "marriage", "children": "children", "health": "health", "career": "career",
                "wealth": "fortune", "parents": "family", "enemies": "enemies"}


def view(t: dict, lang: str = "en", reasons: list[str] | None = None) -> dict:
    hi = lang == "hi"
    return {"id": t["id"], "name": t["name_hi"] if hi else t["name"], "place": t["place"], "state": t["state"],
            "deity": t["deity"], "planets": t["planets"], "doshas": t["doshas"],
            "what": t["what_hi"] if hi else t["what"], "when": t["when_hi"] if hi else t["when"],
            "sources": t["sources"], "reasons": reasons or []}


def for_planet(planet: str, lang: str = "en", limit: int = 3) -> list[dict]:
    """Temples for one planet: dedicated shrines first, the all-graha temple last."""
    ts = [t for t in TEMPLES if planet in t["planets"]]
    ts.sort(key=lambda t: (len(t["planets"]) > 3, len(t["planets"])))
    return [view(t, lang) for t in ts[:limit]]


def suggest(chart: dict, afflictions: list[dict], lang: str = "en", sade_sati: dict | None = None,
            areas: list[str] | None = None, dasha_lords: list[str] | None = None, limit: int = 10) -> list[dict]:
    """Rank temples for this chart: doshas present > afflicted planets > running dasha lords > weak life areas."""
    hi = lang == "hi"
    from . import i18n
    tr = lambda x: i18n.term(lang, x)  # noqa: E731
    from .afflictions import describe
    score: dict[str, float] = {}
    why: dict[str, list[str]] = {}

    def hit(tid, s, reason):
        score[tid] = score.get(tid, 0) + s
        why.setdefault(tid, [])
        if reason not in why[tid]:
            why[tid].append(reason)

    for a in afflictions:
        for t in TEMPLES:
            if a["id"] in t["doshas"]:
                hit(t["id"], 2 + a["severity"], describe(a, lang))
            elif a["category"] != "position" and any(p in t["planets"] for p in a["planets"]) and len(t["planets"]) <= 3:
                hit(t["id"], 0.5 * a["severity"], describe(a, lang))
        if a["category"] == "position" and a["severity"] >= 2:
            for p in a["planets"]:
                for t in TEMPLES:
                    if p in t["planets"] and len(t["planets"]) <= 3:
                        hit(t["id"], 1 + 0.5 * a["severity"], describe(a, lang))
    if sade_sati and (sade_sati.get("sade_sati") or sade_sati.get("dhaiya")):
        key = "sade_sati" if sade_sati.get("sade_sati") else "dhaiya"
        label = ("शनि की साढ़ेसाती चल रही है" if key == "sade_sati" else "शनि की ढैया चल रही है") if hi else \
                ("Saturn's Sade Sati is running" if key == "sade_sati" else "Saturn's Dhaiya is running")
        for t in TEMPLES:
            if key in t["doshas"]:
                hit(t["id"], 4, label)
    for p in dasha_lords or []:
        for t in TEMPLES:
            if p in t["planets"] and len(t["planets"]) <= 3:
                hit(t["id"], 1, (f"{tr(p)} की दशा चल रही है" if hi else f"{p} dasha is running"))
    for ar in areas or []:
        key, title = (ar["area"], ar["title"]) if isinstance(ar, dict) else (ar, ar)
        k = AREA_ALIASES.get(key, key)
        for t in TEMPLES:
            if k in t["areas"]:
                hit(t["id"], 1.5, (f"सावधानी वाला क्षेत्र: {title}" if hi else f"area needing care: {title}"))
    ranked = sorted(score.items(), key=lambda x: -x[1])[:limit]
    return [{**view(BY_ID[tid], lang, why[tid]), "score": round(s, 1)} for tid, s in ranked]


def directory(lang: str = "en") -> list[dict]:
    return [view(t, lang) for t in TEMPLES]
