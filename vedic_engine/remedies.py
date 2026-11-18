"""Remedy catalogue, side by side by system:

* parashari  – navagraha beeja mantra (japa count = Vimshottari years x 1000), daana, vrata (weekday)
* pvr        – P.V.R. Narasimha Rao's methods from 'Lessons on Vedic Astrology':
               - deity of each planet via the Dashavatara mapping (Lesson 2) and the deities he names
               - arudha-based remedy (Lesson 9): for a weak house, fast on the weekday of the lord of
                 its arudha, and worship the deity of the lord of the 2nd house from that arudha
* lal_kitab  – planet-in-house upay from the Lal Kitab dataset (vedic_engine/lalkitab/data)

Principles kept from the sources: satvik remedies (prayer, mantra, service, fasting) come first;
gems are rajasik and need a full chart reading (Lesson 24, 43). No remedy promises an outcome.
"""
from __future__ import annotations

from .constants import SIGN_LORDS

WEEKDAY = {"Sun": "Sunday", "Moon": "Monday", "Mars": "Tuesday", "Mercury": "Wednesday",
           "Jupiter": "Thursday", "Venus": "Friday", "Saturn": "Saturday", "Rahu": "Saturday", "Ketu": "Tuesday"}
WEEKDAY_HI = {"Sunday": "रविवार", "Monday": "सोमवार", "Tuesday": "मंगलवार", "Wednesday": "बुधवार",
              "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार"}

PLANET = {
    "Sun": {
        "avatar": ("Rama", "श्रीराम"), "deity": ("Surya / Shiva", "सूर्य देव / शिव"),
        "mantra": "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः", "mantra_en": "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "daana": ("wheat, jaggery, copper vessel", "गेहूँ, गुड़, तांबे का पात्र"),
        "practice": ("Offer water to the rising Sun (Surya arghya); respect your father", "उगते सूर्य को अर्घ्य दें; पिता का सम्मान करें"),
    },
    "Moon": {
        "avatar": ("Krishna", "श्रीकृष्ण"), "deity": ("Gauri / Shiva", "गौरी / शिव"),
        "mantra": "ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः", "mantra_en": "Om Shraam Shreem Shraum Sah Chandraya Namah",
        "daana": ("rice, milk, white cloth, silver", "चावल, दूध, सफेद वस्त्र, चाँदी"),
        "practice": ("Serve your mother; offer water/milk on a Shivalinga on Mondays", "माता की सेवा करें; सोमवार को शिवलिंग पर जल/दूध चढ़ाएँ"),
    },
    "Mars": {
        "avatar": ("Narasimha", "नृसिंह"), "deity": ("Hanuman / Subrahmanya", "हनुमान / कार्तिकेय"),
        "mantra": "ॐ क्रां क्रीं क्रौं सः भौमाय नमः", "mantra_en": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
        "daana": ("red lentils (masoor), jaggery, red cloth", "मसूर दाल, गुड़, लाल वस्त्र"),
        "practice": ("Recite Hanuman Chalisa on Tuesdays; support brothers", "मंगलवार को हनुमान चालीसा पढ़ें; भाइयों का साथ दें"),
    },
    "Mercury": {
        "avatar": ("Buddha (Vishnu)", "बुद्ध (विष्णु)"), "deity": ("Vishnu", "विष्णु"),
        "mantra": "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः", "mantra_en": "Om Braam Breem Braum Sah Budhaya Namah",
        "daana": ("green moong, green cloth", "हरी मूँग, हरा वस्त्र"),
        "practice": ("Recite Vishnu Sahasranama (PVR, Lesson 12: on Wednesdays)", "विष्णु सहस्रनाम का पाठ करें (बुधवार)"),
    },
    "Jupiter": {
        "avatar": ("Vamana", "वामन"), "deity": ("Dakshinamurthy / Brihaspati", "दक्षिणामूर्ति / बृहस्पति"),
        "mantra": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः", "mantra_en": "Om Graam Greem Graum Sah Gurave Namah",
        "daana": ("chana dal, turmeric, yellow cloth, books to students", "चने की दाल, हल्दी, पीला वस्त्र, विद्यार्थियों को पुस्तकें"),
        "practice": ("Respect teachers and elders; practise humility (the Vamana lesson)", "गुरु और बड़ों का सम्मान; विनम्रता अपनाएँ"),
    },
    "Venus": {
        "avatar": ("Parashurama", "परशुराम"), "deity": ("Lakshmi", "लक्ष्मी"),
        "mantra": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः", "mantra_en": "Om Draam Dreem Draum Sah Shukraya Namah",
        "daana": ("white rice, curd, sugar, white clothes", "सफेद चावल, दही, चीनी, सफेद वस्त्र"),
        "practice": ("Respect women and your spouse; keep yourself and home clean", "स्त्रियों और जीवनसाथी का सम्मान; स्वच्छता रखें"),
    },
    "Saturn": {
        "avatar": ("Kurma", "कूर्म"), "deity": ("Venkateshwara / Hanuman", "वेंकटेश्वर / हनुमान"),
        "mantra": "ॐ प्रां प्रीं प्रौं सः शनये नमः", "mantra_en": "Om Praam Preem Praum Sah Shanaye Namah",
        "daana": ("black sesame, mustard oil, iron, black blanket", "काले तिल, सरसों का तेल, लोहा, काला कंबल"),
        "practice": ("Serve workers, the elderly and the disabled; be disciplined and honest", "श्रमिकों, वृद्धों व दिव्यांगों की सेवा; अनुशासन और ईमानदारी"),
    },
    "Rahu": {
        "avatar": ("Varaha", "वराह"), "deity": ("Durga", "दुर्गा"),
        "mantra": "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः", "mantra_en": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
        "daana": ("black urad, coconut, blanket", "काली उड़द, नारियल, कंबल"),
        "practice": ("Recite Durga Saptashati / Durga Chalisa; avoid intoxicants and shortcuts", "दुर्गा सप्तशती/चालीसा; नशे और गलत रास्तों से बचें"),
    },
    "Ketu": {
        "avatar": ("Matsya", "मत्स्य"), "deity": ("Ganesha", "गणेश"),
        "mantra": "ॐ स्रां स्रीं स्रौं सः केतवे नमः", "mantra_en": "Om Sraam Sreem Sraum Sah Ketave Namah",
        "daana": ("blanket, sesame; feed stray dogs", "कंबल, तिल; कुत्तों को भोजन"),
        "practice": ("Worship Ganesha; keep up a spiritual practice in a lineage", "गणेश पूजा; परंपरा से साधना"),
    },
}
JAPA_COUNT = {"Sun": 6000, "Moon": 10000, "Mars": 7000, "Mercury": 17000, "Jupiter": 16000,
              "Venus": 20000, "Saturn": 19000, "Rahu": 18000, "Ketu": 7000}


def parashari(planet: str, lang: str = "en") -> dict:
    d, hi = PLANET[planet], lang == "hi"
    day = WEEKDAY[planet]
    return {
        "system": "parashari",
        "planet": planet,
        "mantra": d["mantra"] if hi else d["mantra_en"],
        "japa": JAPA_COUNT[planet],
        "daana": d["daana"][1 if hi else 0],
        "day": WEEKDAY_HI[day] if hi else day,
        "practice": d["practice"][1 if hi else 0],
        "source": "BPHS – Graha shanti; navagraha beeja mantras",
    }


def pvr_deity(planet: str, lang: str = "en") -> dict:
    d, hi = PLANET[planet], lang == "hi"
    return {"system": "pvr", "planet": planet, "avatar": d["avatar"][1 if hi else 0],
            "deity": d["deity"][1 if hi else 0],
            "source": "PVR Narasimha Rao, Lessons on Vedic Astrology – Lesson 2 (avatars), 9, 12"}


def pvr_arudha_remedy(planets: dict, lagna_sign: int, house: int, lang: str = "en") -> dict:
    """Lesson 9: strengthen a house through its arudha – fast on the weekday of the arudha's
    lord and propitiate the deity of the lord of the 2nd from the arudha (house of sustenance)."""
    from .jaimini import arudha_of_sign, lord_of_sign
    sign = (lagna_sign + house - 1) % 12
    ar = arudha_of_sign(planets, sign)
    ar_lord = lord_of_sign(planets, ar)
    second_lord = lord_of_sign(planets, (ar + 1) % 12)
    hi = lang == "hi"
    day = WEEKDAY[ar_lord]
    d = PLANET[second_lord]
    return {
        "system": "pvr_arudha", "house": house, "arudha_sign": ar, "arudha_lord": ar_lord,
        "fast_day": WEEKDAY_HI[day] if hi else day,
        "deity_planet": second_lord, "deity": d["deity"][1 if hi else 0], "avatar": d["avatar"][1 if hi else 0],
        "source": "PVR Narasimha Rao, Lessons on Vedic Astrology – Lesson 9 (remedies through arudha padas)",
    }


# =====================================================================================
# Extended catalogue (traditional Parashari / popular Jyotish practice).
# Each entry is (english, hindi). Shlokas are from the Navagraha Stotra attributed to Vyasa.
# =====================================================================================
SHLOKA = {
    "Sun": "जपाकुसुमसङ्काशं काश्यपेयं महाद्युतिम्। तमोऽरिं सर्वपापघ्नं प्रणतोऽस्मि दिवाकरम्॥",
    "Moon": "दधिशङ्खतुषाराभं क्षीरोदार्णवसम्भवम्। नमामि शशिनं सोमं शम्भोर्मुकुटभूषणम्॥",
    "Mars": "धरणीगर्भसम्भूतं विद्युत्कान्तिसमप्रभम्। कुमारं शक्तिहस्तं तं मङ्गलं प्रणमाम्यहम्॥",
    "Mercury": "प्रियङ्गुकलिकाश्यामं रूपेणाप्रतिमं बुधम्। सौम्यं सौम्यगुणोपेतं तं बुधं प्रणमाम्यहम्॥",
    "Jupiter": "देवानां च ऋषीणां च गुरुं काञ्चनसन्निभम्। बुद्धिभूतं त्रिलोकेशं तं नमामि बृहस्पतिम्॥",
    "Venus": "हिमकुन्दमृणालाभं दैत्यानां परमं गुरुम्। सर्वशास्त्रप्रवक्तारं भार्गवं प्रणमाम्यहम्॥",
    "Saturn": "नीलाञ्जनसमाभासं रविपुत्रं यमाग्रजम्। छायामार्तण्डसम्भूतं तं नमामि शनैश्चरम्॥",
    "Rahu": "अर्धकायं महावीर्यं चन्द्रादित्यविमर्दनम्। सिंहिकागर्भसम्भूतं तं राहुं प्रणमाम्यहम्॥",
    "Ketu": "पलाशपुष्पसङ्काशं तारकाग्रहमस्तकम्। रौद्रं रौद्रात्मकं घोरं तं केतुं प्रणमाम्यहम्॥",
}
PATH = {
    "Sun": ("Aditya Hridayam at sunrise (Valmiki Ramayana, Yuddha Kanda); Surya Ashtakam",
            "सूर्योदय के समय आदित्य हृदय स्तोत्र (वाल्मीकि रामायण); सूर्याष्टक"),
    "Moon": ("Shiva Panchakshara Stotra and 'Om Namah Shivaya' 108 times on Mondays; Chandra Kavacham",
             "सोमवार को शिव पंचाक्षर स्तोत्र व 'ॐ नमः शिवाय' 108 बार; चंद्र कवच"),
    "Mars": ("Hanuman Chalisa or Sundarkand on Tuesdays; Rina-Mochana Mangala Stotra for debts",
             "मंगलवार को हनुमान चालीसा या सुंदरकांड; ऋण के लिए ऋणमोचन मंगल स्तोत्र"),
    "Mercury": ("Vishnu Sahasranama on Wednesdays; Budha Kavacham", "बुधवार को विष्णु सहस्रनाम; बुध कवच"),
    "Jupiter": ("Vishnu Sahasranama or Guru Stotra on Thursdays; Dakshinamurthy Stotram",
                "गुरुवार को विष्णु सहस्रनाम या गुरु स्तोत्र; दक्षिणामूर्ति स्तोत्र"),
    "Venus": ("Shri Suktam / Lakshmi Ashtottara on Fridays", "शुक्रवार को श्री सूक्त / लक्ष्मी अष्टोत्तर"),
    "Saturn": ("Dasharatha's Shani Stotra and Hanuman Chalisa on Saturdays", "शनिवार को दशरथकृत शनि स्तोत्र व हनुमान चालीसा"),
    "Rahu": ("Durga Saptashati (at least Devi Kavach, Argala, Kilak) or Durga Chalisa; Rahu Kavacham",
             "दुर्गा सप्तशती (कम से कम देवी कवच, अर्गला, कीलक) या दुर्गा चालीसा; राहु कवच"),
    "Ketu": ("Ganapati Atharvashirsha; Sankat-Nashana Ganesha Stotra", "गणपति अथर्वशीर्ष; संकटनाशन गणेश स्तोत्र"),
}
DAANA_WHEN = {  # whom to give, when
    "Sun": ("Sunday morning, to a father figure, a temple or a needy person", "रविवार प्रातः, पिता-तुल्य व्यक्ति, मंदिर या ज़रूरतमंद को"),
    "Moon": ("Monday evening, to mother figures or elderly women", "सोमवार संध्या, माता-तुल्य या वृद्ध महिलाओं को"),
    "Mars": ("Tuesday around noon, to young men, soldiers or at a Hanuman temple", "मंगलवार दोपहर, युवकों, सैनिकों या हनुमान मंदिर में"),
    "Mercury": ("Wednesday morning, to students or young girls (kanya)", "बुधवार प्रातः, विद्यार्थियों या कन्याओं को"),
    "Jupiter": ("Thursday morning, to teachers, priests or scholars", "गुरुवार प्रातः, शिक्षकों, पुरोहितों या विद्वानों को"),
    "Venus": ("Friday, to young women or for a girl's education/marriage", "शुक्रवार, युवतियों को या कन्या की शिक्षा/विवाह हेतु"),
    "Saturn": ("Saturday evening, to labourers, the elderly, the disabled or the poor", "शनिवार संध्या, श्रमिकों, वृद्धों, दिव्यांगों या निर्धनों को"),
    "Rahu": ("Saturday evening, to sanitation workers or the very poor", "शनिवार संध्या, सफ़ाई कर्मियों या अति निर्धनों को"),
    "Ketu": ("Tuesday or Saturday, to sadhus, or feed stray dogs", "मंगलवार या शनिवार, साधुओं को, या आवारा कुत्तों को भोजन"),
}
VRATA = {  # fast: how, count
    "Sun": (12, "one meal before sunset, no salt; offer arghya first", "सूर्यास्त से पहले एक बार भोजन, बिना नमक; पहले अर्घ्य"),
    "Moon": (16, "milk, fruit or one sattvic meal; Shiva puja (Solah Somvar)", "दूध, फल या एक सात्विक भोजन; शिव पूजा (सोलह सोमवार)"),
    "Mars": (21, "one meal with jaggery/sweet, no salt; Hanuman puja", "गुड़/मीठे के साथ एक बार भोजन, बिना नमक; हनुमान पूजा"),
    "Mercury": (21, "one meal with green moong; Vishnu/Ganesha puja", "हरी मूँग के साथ एक भोजन; विष्णु/गणेश पूजा"),
    "Jupiter": (16, "one yellow meal (chana dal, besan), no salt; banana-tree puja", "एक पीला भोजन (चने की दाल, बेसन), बिना नमक; केले के वृक्ष की पूजा"),
    "Venus": (21, "one meal of white food (kheer, rice); Lakshmi puja", "सफेद भोजन (खीर, चावल) एक बार; लक्ष्मी पूजा"),
    "Saturn": (19, "one meal with black urad / sesame after sunset; lamp of mustard oil under a peepal", "सूर्यास्त बाद काली उड़द/तिल के साथ भोजन; पीपल के नीचे सरसों तेल का दीपक"),
    "Rahu": (18, "Saturday fast, one meal; Durga puja", "शनिवार व्रत, एक भोजन; दुर्गा पूजा"),
    "Ketu": (18, "Tuesday fast, one meal; Ganesha puja", "मंगलवार व्रत, एक भोजन; गणेश पूजा"),
}
RUDRAKSHA = {"Sun": "1 / 12", "Moon": "2", "Mars": "3", "Mercury": "4", "Jupiter": "5", "Venus": "6",
             "Saturn": "7", "Rahu": "8", "Ketu": "9"}
GEM = {  # primary, upratna (substitute), metal, finger, day, weight
    "Sun": (("Ruby (Manik)", "माणिक्य"), ("red garnet / red spinel", "गार्नेट / लाल स्पिनेल"), ("gold or copper", "सोना या तांबा"),
            ("ring finger", "अनामिका"), "3–5 ct"),
    "Moon": (("Pearl (Moti)", "मोती"), ("moonstone", "चंद्रकांत मणि"), ("silver", "चाँदी"), ("little finger", "कनिष्ठा"), "4–6 ct"),
    "Mars": (("Red coral (Moonga)", "मूँगा"), ("carnelian", "कार्नेलियन"), ("gold or copper", "सोना या तांबा"), ("ring finger", "अनामिका"), "6–9 ct"),
    "Mercury": (("Emerald (Panna)", "पन्ना"), ("peridot / green tourmaline", "पेरिडॉट / हरा टूमलाइन"), ("gold", "सोना"),
                ("little finger", "कनिष्ठा"), "3–6 ct"),
    "Jupiter": (("Yellow sapphire (Pukhraj)", "पुखराज"), ("citrine / yellow topaz", "सुनैला / पीला टोपाज़"), ("gold", "सोना"),
                ("index finger", "तर्जनी"), "3–5 ct"),
    "Venus": (("Diamond (Heera) or white sapphire", "हीरा या सफ़ेद पुखराज"), ("opal / white zircon", "ओपल / सफ़ेद ज़रकन"),
              ("silver or platinum", "चाँदी या प्लैटिनम"), ("middle finger", "मध्यमा"), "diamond 0.5–1 ct"),
    "Saturn": (("Blue sapphire (Neelam)", "नीलम"), ("amethyst / blue spinel", "जामुनिया / नीला स्पिनेल"), ("silver or panchdhatu", "चाँदी या पंचधातु"),
               ("middle finger", "मध्यमा"), "3–5 ct"),
    "Rahu": (("Hessonite (Gomed)", "गोमेद"), ("orange zircon", "नारंगी ज़रकन"), ("silver or ashtadhatu", "चाँदी या अष्टधातु"),
             ("middle finger", "मध्यमा"), "5–8 ct"),
    "Ketu": (("Cat's eye (Lehsunia)", "लहसुनिया"), ("tiger's eye", "टाइगर आई"), ("silver or panchdhatu", "चाँदी या पंचधातु"),
             ("little or middle finger", "कनिष्ठा या मध्यमा"), "3–5 ct"),
}
JADI = {  # herb root worn in place of a gem
    "Sun": ("Bel (bilva) root", "बेल की जड़"), "Moon": ("Khirni root", "खिरनी की जड़"),
    "Mars": ("Anantmool root", "अनंतमूल की जड़"), "Mercury": ("Vidhara root", "विधारा की जड़"),
    "Jupiter": ("Banana (kela) root or turmeric root", "केले की जड़ या हल्दी की गाँठ"),
    "Venus": ("Sarpankha root", "सरपंखा की जड़"), "Saturn": ("Shami root (or bichhu booti)", "शमी की जड़ (या बिच्छू बूटी)"),
    "Rahu": ("White sandalwood / nagarmotha root", "सफ़ेद चंदन / नागरमोथा की जड़"), "Ketu": ("Ashwagandha root", "अश्वगंधा की जड़"),
}
COLOUR = {
    "Sun": (("red, saffron, orange", "लाल, केसरिया, नारंगी"), ("copper", "तांबा")),
    "Moon": (("white, cream, silver", "सफ़ेद, क्रीम, चाँदी"), ("silver", "चाँदी")),
    "Mars": (("red, coral", "लाल, मूँगिया"), ("copper", "तांबा")),
    "Mercury": (("green", "हरा"), ("bronze (kansa)", "काँसा")),
    "Jupiter": (("yellow, gold", "पीला, सुनहरा"), ("gold / brass", "सोना / पीतल")),
    "Venus": (("white, pastel, light pink", "सफ़ेद, हल्के रंग, गुलाबी"), ("silver", "चाँदी")),
    "Saturn": (("black, dark blue", "काला, गहरा नीला"), ("iron", "लोहा")),
    "Rahu": (("smoky grey, dark blue", "धूसर, गहरा नीला"), ("lead / ashtadhatu", "सीसा / अष्टधातु")),
    "Ketu": (("grey, brown, mixed colours", "धूसर, भूरा, चितकबरा"), ("iron / panchdhatu", "लोहा / पंचधातु")),
}
KARMA = {  # behaviour – the remedy that costs nothing
    "Sun": ("Wake before sunrise; respect your father and those in authority; be truthful; never take bribes or favours from officials.",
            "सूर्योदय से पहले उठें; पिता व अधिकारियों का सम्मान करें; सत्य बोलें; रिश्वत या अनुचित लाभ न लें।"),
    "Moon": ("Serve your mother; keep regular sleep; avoid brooding at night; drink water from a silver glass; meditate near water.",
             "माता की सेवा करें; नियमित नींद लें; रात में चिंता न पालें; चाँदी के गिलास में पानी पिएँ; जल के पास ध्यान करें।"),
    "Mars": ("Turn anger into exercise or sport; stand by your brothers; settle disputes quickly; avoid rash driving.",
             "क्रोध को व्यायाम/खेल में लगाएँ; भाइयों का साथ दें; विवाद जल्दी सुलझाएँ; तेज़ गाड़ी न चलाएँ।"),
    "Mercury": ("Keep your word in writing and speech; avoid gossip and half-truths; respect sisters, daughters and aunts; keep accounts clean.",
                "लिखित व मौखिक वचन निभाएँ; चुगली और आधा-सच न बोलें; बहन, बेटी, बुआ का सम्मान करें; हिसाब साफ़ रखें।"),
    "Jupiter": ("Respect teachers, priests and elders; teach what you know; avoid arrogance; apply a saffron or turmeric tilak.",
                "गुरु, पुरोहित व बड़ों का सम्मान करें; जो जानते हैं वह सिखाएँ; अहंकार से बचें; केसर/हल्दी का तिलक लगाएँ।"),
    "Venus": ("Honour your spouse and women in general; keep body, clothes and home clean and fragrant; avoid indulgence outside marriage.",
              "जीवनसाथी व स्त्रियों का सम्मान करें; शरीर, वस्त्र व घर स्वच्छ व सुगंधित रखें; विवाहेतर भोग से बचें।"),
    "Saturn": ("Be punctual, honest and patient; treat servants and workers fairly; avoid alcohol and meat (at least on Saturdays).",
               "समयनिष्ठ, ईमानदार व धैर्यवान रहें; सेवकों और श्रमिकों से न्याय करें; मद्य व मांस से बचें (कम से कम शनिवार)।"),
    "Rahu": ("Stay away from intoxicants, gambling and shortcuts; keep the home's south-west and stairs clean; don't hoard broken electronics.",
             "नशे, जुए और शॉर्टकट से दूर रहें; घर का दक्षिण-पश्चिम व सीढ़ियाँ साफ़ रखें; टूटा इलेक्ट्रॉनिक सामान न रखें।"),
    "Ketu": ("Feed stray dogs; keep a regular meditation practice; stay humble; support your children and nephews.",
             "आवारा कुत्तों को भोजन दें; नियमित ध्यान करें; विनम्र रहें; संतान व भतीजे-भांजों का साथ दें।"),
}
GOOD_NATURES = ("yogakaraka", "benefic")


def gem_advice(planet: str, nature: str, dignity: str | None, hi: bool) -> tuple[str, str]:
    """(verdict, reason). Gems strengthen a planet – right only if the planet does good for this lagna."""
    if planet in ("Rahu", "Ketu"):
        return ("caution", "छाया ग्रह का रत्न केवल अनुभवी ज्योतिषी की जाँच और 3 दिन के परीक्षण के बाद।" if hi else
                "A node's gem only after an experienced astrologer checks the chart, and a 3-day trial.")
    if nature in GOOD_NATURES:
        return ("suitable", "यह ग्रह आपके लग्न के लिए शुभ है, अतः इसका रत्न बल दे सकता है – फिर भी ज्योतिषी से पुष्टि करें।" if hi else
                "This planet does good for your ascendant, so strengthening it with its gem can help – still confirm with an astrologer.")
    if nature in ("malefic", "maraka"):
        return ("avoid", "यह ग्रह आपके लग्न के लिए कठिन भावों का स्वामी है; रत्न उसे और बलवान करेगा। इसके बजाय मंत्र, दान व सेवा करें।" if hi else
                "This planet rules difficult houses for your ascendant; a gem would make it stronger. Pacify it with mantra, daana and service instead.")
    return ("caution", "मिश्रित फल वाला ग्रह – रत्न से पहले पूरी कुंडली की जाँच आवश्यक।" if hi else
            "Mixed planet for your ascendant – needs a full chart check before any gem.")


def full_set(chart: dict, planet: str, lang: str = "en", lk_house: int | None = None,
             lk_annual_house: int | None = None, house_for_arudha: int | None = None) -> dict:
    """Every remedy system for one planet, ordered from satvik (free, safe) to rajasik (gems),
    with the planet's placement explained and the approach (strengthen vs pacify) worked out."""
    from . import lalkitab, placements
    hi = lang == "hi"
    k = 1 if hi else 0
    pl = placements.explain(chart, planet, lang)
    nature, dig = pl["nature"], pl["dignity"]
    weak = pl["strength"] == "weak" or pl["combust"] or dig in ("debilitated", "enemy")
    if nature in GOOD_NATURES:
        approach = "strengthen"
        why = ("ग्रह शुभ है पर दुर्बल/पीड़ित है – उसे बल दें: मंत्र, स्तोत्र, पूजा; रत्न पर विचार किया जा सकता है।" if weak and hi else
               "The planet is good for you but weak or afflicted – strengthen it: mantra, stotra, worship; a gem may be considered." if weak else
               "ग्रह शुभ है – उसके कारकत्व बढ़ाने हेतु मंत्र व पूजा; उसकी वस्तुओं का दान कम करें।" if hi else
               "The planet is good for you – support it with mantra and worship; go light on donating its items.")
    elif nature == "shadow":
        approach = "pacify"
        why = ("राहु/केतु को शांत किया जाता है, बल नहीं दिया जाता – जप, दान, देवी/गणेश उपासना।" if hi else
               "Rahu and Ketu are pacified, not strengthened – japa, daana, Durga / Ganesha worship.")
    else:
        approach = "pacify"
        why = ("ग्रह आपके लग्न के लिए कठिन भावों का स्वामी है – उसे शांत करें: दान, सेवा, जप, व्रत; रत्न न पहनें।" if hi else
               "The planet rules difficult houses for your ascendant – pacify it: daana, service, japa, fasting; do not wear its gem.")
    d = PLANET[planet]
    day = WEEKDAY[planet]
    dayn = WEEKDAY_HI[day] if hi else day
    gv, greason = gem_advice(planet, nature, dig, hi)
    g = GEM[planet]
    vr = VRATA[planet]
    col, metal = COLOUR[planet]
    systems = []

    def add(id_, items, source, note=None, tone=None):
        systems.append({"id": id_, "items": [x for x in items if x], "source": source, "note": note, "tone": tone})

    # 1. Lal Kitab
    lk_items, lk_src = [], []
    for kind, h in (("annual", lk_annual_house), ("natal", lk_house if lk_house else pl["house"])):
        if not h:
            continue
        e = lalkitab.entry(planet, h, lang)
        for u in e["upay"]:
            lk_items.append(("(इस वर्ष) " if hi else "(this year) ") + u if kind == "annual" else u)
        if e["upay"]:
            lk_src.append(f"p. {e['book_page']}")
        if kind == "annual" and lk_annual_house == lk_house:
            break
    q = lalkitab.quick_upay(planet, lang, weak)
    if q:
        lk_items.append(("शीघ्र उपाय: " if hi else "Quick remedy: ") + q["text"])
    hp = lalkitab.planet_help(planet, lang)
    if hp:
        lk_items.append(("दैनिक सहायता: " if hi else "Everyday help: ") + hp["text"])
    add("lal_kitab", lk_items, "Lal Kitab (Arun Sanhita) " + ", ".join(lk_src + ["pp. 43–44"]),
        note=None if lk_src else ("इस भाव का विस्तृत उपाय अभी जोड़ा जाना है।" if hi else "The detailed upay for this house is still being added."))
    # 2. Mantra
    add("mantra", [
        f"{'बीज मंत्र' if hi else 'Beeja mantra'}: {d['mantra'] if hi else d['mantra_en']}",
        None if hi else f"Devanagari: {d['mantra']}",
        (f"कुल जप {JAPA_COUNT[planet]:,} (40 दिनों में बाँटें, प्रतिदिन ~{-(-JAPA_COUNT[planet] // 40)}); आरंभ शुक्ल पक्ष के {dayn} को"
         if hi else f"Total japa {JAPA_COUNT[planet]:,} (spread over 40 days, ~{-(-JAPA_COUNT[planet] // 40)} a day); begin on a {day} in the bright fortnight"),
        f"{'नवग्रह स्तोत्र श्लोक' if hi else 'Navagraha Stotra verse'}: {SHLOKA[planet]}",
    ], "BPHS (graha shanti); Navagraha Stotra (Vyasa)")
    # 3. Stotra / path
    add("path", [PATH[planet][k]], "Traditional stotras")
    # 4. Daana
    add("daana", [f"{'वस्तुएँ' if hi else 'Items'}: {d['daana'][k]}", f"{'कब/किसे' if hi else 'When / to whom'}: {DAANA_WHEN[planet][k]}",
                  ("शुभ ग्रह की वस्तुओं का दान कम मात्रा में करें।" if hi else "For a planet that is good for you, keep its daana small.")
                  if approach == "strengthen" else None], "BPHS (graha shanti) – daana")
    # 5. Vrata
    add("vrata", [f"{vr[0]} {dayn}{'' if hi else 's'}: {vr[2] if hi else vr[1]}"], "Traditional vrata practice")
    # 6. Karma
    add("karma", [KARMA[planet][k]], "Lal Kitab & Parashari behavioural remedies")
    # 7. Deity (PVR)
    add("deity", [f"{'देवता' if hi else 'Deity'}: {d['deity'][k]}", f"{'अवतार' if hi else 'Avatar'}: {d['avatar'][k]}"],
        "PVR Narasimha Rao, Lessons on Vedic Astrology – Lesson 2, 12")
    # 8. Arudha (house-based) remedy
    if house_for_arudha:
        a = pvr_arudha_remedy(chart["planets"], chart["lagna"]["sign_index"] - 1, house_for_arudha, lang)
        add("arudha", [
            (f"भाव {house_for_arudha} का आरूढ़ {i18n_term(lang, SIGNS_[a['arudha_sign']])} में; उसके स्वामी {i18n_term(lang, a['arudha_lord'])} के दिन ({a['fast_day']}) व्रत"
             if hi else f"Arudha of house {house_for_arudha} falls in {SIGNS_[a['arudha_sign']]}; fast on its lord {a['arudha_lord']}'s day ({a['fast_day']})"),
            f"{'उपासना' if hi else 'Worship'}: {a['deity']} ({a['avatar']})"], a["source"])
    # 9. Rudraksha
    add("rudraksha", [(f"{RUDRAKSHA[planet]} मुखी रुद्राक्ष, लाल या {col[1].split(',')[0]} रंग के धागे में, {dayn} को अभिमंत्रित करके"
                       if hi else f"{RUDRAKSHA[planet]} mukhi rudraksha on a red or {col[0].split(',')[0]} thread, energised on a {day}")],
        "Shiva Purana / Padma Purana (rudraksha mukhi); popular practice")
    # 10. Jadi (herb root)
    add("jadi", [(f"{JADI[planet][1]} – {col[1].split(',')[0]} रंग के कपड़े में बाँधकर {dayn} को भुजा या गले में" if hi
                  else f"{JADI[planet][0]} – tied in {col[0].split(',')[0]} cloth, worn on the arm or neck from a {day}"),
                 ("रत्न का सस्ता व सुरक्षित विकल्प।" if hi else "A cheaper, gentler substitute for the gem.")],
        "Traditional (mool / jadi)")
    # 11. Gemstone (with chart-based advice)
    add("gem", [
        f"{g[0][k]}; {'उपरत्न' if hi else 'substitute'}: {g[1][k]}",
        f"{'धातु' if hi else 'Metal'}: {g[2][k]} · {'उँगली' if hi else 'Finger'}: {g[3][k]} · {dayn} · {g[4]}",
        greason,
    ], "Traditional; PVR Lessons 24, 43: gems are rajasik, use only with a full reading",
        tone={"suitable": "good", "avoid": "bad", "caution": "mixed"}[gv])
    # 12. Yantra & colour
    add("yantra", [
        (f"{i18n_term(lang, planet)} यंत्र ({metal[1]} धातु का), {dayn} को स्थापित करें; प्रतिदिन दीप जलाकर बीज मंत्र 108 बार" if hi
         else f"{planet} yantra (on {metal[0]}), installed on a {day}; daily lamp and 108 beeja mantra"),
        (f"शुभ रंग: {col[1]}" if hi else f"Helpful colours: {col[0]}") if approach == "strengthen" else
        (f"इस ग्रह के रंग ({col[1]}) का अधिक प्रयोग न करें" if hi else f"Avoid overusing its colours ({col[0]})"),
    ], "Traditional yantra practice")

    # 13. Tantra (Mahavidya) – principles from Dwivedi's Bharatiya Tantra Shastra; mapping from tradition
    from . import tantra, temples
    tn = tantra.for_planet(planet, lang)
    add("tantra", tn["items"], tn["source"])
    # 14. Temples / tirthas for this planet
    tl = temples.for_planet(planet, lang)
    add("temple", [f"{t['name']} ({t['state']}) – {t['when']}" for t in tl],
        "Temple research, Nov 2026 – confirm timings with the temple", )
    return {"planet": planet, "placement": pl, "approach": approach, "approach_text": why,
            "gem_verdict": gv, "systems": systems, "temples": tl}


def i18n_term(lang, v):
    from . import i18n
    return i18n.term(lang, v)


from .constants import SIGNS as SIGNS_  # noqa: E402
