"""Tantra layer for remedies.

Two sources, kept apart and labelled:

1. Dr. Shyama Kant Dwivedi 'Anand', *Bharatiya Tantra Shastra – Siddhanta aur Sadhana*
   (Chowkhamba, Krishnadas Prachya Vidya Series 33). A philosophical work (Trika / Shakta).
   Used for the PRINCIPLES of sadhana: tadatmya with the mantra-devata, unbroken practice,
   sankalpa, giving up glani, inner (manasi) puja as the highest worship and the "ten flowers"
   of Tara Rahasya (ch. 8, printed pp. 365-391), and the list of the ten Mahavidyas (p. 388).
   Paraphrased; the Sanskrit verse quoted is from Tara Rahasya (ancient, public domain).

2. The planet → Mahavidya correspondence is NOT in the book. It is the common tantra-jyotish
   association (Kali–Saturn, Tara–Jupiter, Shodashi–Mercury, Bhuvaneshwari–Moon, Bhairavi–Lagna,
   Chhinnamasta–Rahu, Dhumavati–Ketu, Bagalamukhi–Mars, Matangi–Sun, Kamala–Venus); some lineages
   differ (e.g. Bhuvaneshwari for Venus).

Deliberately excluded: beeja / tantric mantras of the Mahavidyas (tradition gives them only with
diksha from a guru) and every abhichara / shatkarma practice aimed at other people
(vashikaran, uchchatan, maran, stambhan of others). The book itself contains none of these.
"""
from __future__ import annotations

BOOK = "Dr. S. K. Dwivedi 'Anand', Bharatiya Tantra Shastra – Siddhanta aur Sadhana (Chowkhamba)"
TRAD = "Tantra-jyotish tradition (planet–Mahavidya correspondence; varies by lineage)"

MAHAVIDYA = {  # planet: (name en, name hi, essence en, essence hi, open practice en, open practice hi, days)
    "Saturn": ("Kali", "काली", "time and transformation; removes fear and long-standing karmic weight",
               "काल व रूपांतरण; भय व पुराने कर्म-भार का नाश",
               "Kali's 108 names or Kali Chalisa; lamp of sesame oil on Saturdays and Amavasya",
               "काली के 108 नाम या काली चालीसा; शनिवार व अमावस्या को तिल के तेल का दीपक",
               "Saturday, Amavasya"),
    "Jupiter": ("Tara", "तारा", "the saviour who carries across; wisdom and speech",
                "तारने वाली; ज्ञान व वाणी",
                "Tara's 108 names / Tara stotra; honour teachers; study of scripture",
                "तारा के 108 नाम / तारा स्तोत्र; गुरुओं का सम्मान; शास्त्र-स्वाध्याय",
                "Thursday, Navami"),
    "Mercury": ("Shodashi (Tripura Sundari / Lalita)", "षोडशी (त्रिपुरसुंदरी / ललिता)",
                "beauty, harmony and the integrated intellect (Sri Vidya)", "सौंदर्य, सामंजस्य व एकीकृत बुद्धि (श्रीविद्या)",
                "Lalita Sahasranama or Lalita Trishati; Saundarya Lahari", "ललिता सहस्रनाम या ललिता त्रिशती; सौंदर्य लहरी",
                "Wednesday, Friday, Purnima"),
    "Moon": ("Bhuvaneshwari", "भुवनेश्वरी", "the space that holds the worlds; peace of mind and nurturing",
             "लोकों को धारण करने वाला आकाश; मन की शांति व पोषण",
             "Bhuvaneshwari stotra / 108 names; white flowers on Mondays and Purnima",
             "भुवनेश्वरी स्तोत्र / 108 नाम; सोमवार व पूर्णिमा को श्वेत पुष्प", "Monday, Purnima"),
    "Rahu": ("Chhinnamasta", "छिन्नमस्ता", "self-sacrifice and mastery over the restless mind and appetites",
             "आत्म-त्याग; चंचल मन व वासनाओं पर विजय",
             "Chhinnamasta's 108 names / stotra only; her sadhana proper needs a guru",
             "केवल छिन्नमस्ता के 108 नाम / स्तोत्र; उनकी साधना गुरु से ही", "Saturday, Chaturdashi"),
    "Ketu": ("Dhumavati", "धूमावती", "the smoke that remains – detachment, letting go of loss",
             "शेष धुआँ – वैराग्य, हानि को छोड़ना",
             "Dhumavati stotra / 108 names; charity to widows and the destitute",
             "धूमावती स्तोत्र / 108 नाम; विधवाओं व निराश्रितों को दान", "Tuesday, Saturday"),
    "Mars": ("Bagalamukhi", "बगलामुखी", "the power that stills harmful speech and conflict – protection",
             "हानिकारक वाणी व संघर्ष को शांत करने वाली शक्ति – रक्षा",
             "Bagalamukhi's 108 names / Pitambara stotra; yellow flowers and turmeric on Tuesdays",
             "बगलामुखी के 108 नाम / पीतांबरा स्तोत्र; मंगलवार को पीले पुष्प व हल्दी", "Tuesday, Ashtami"),
    "Sun": ("Matangi", "मातंगी", "inner speech, learning and the arts; the outcaste made sacred",
            "अंतर्वाणी, विद्या व कला",
            "Matangi stotra / 108 names; support music, learning and those on society's margins",
            "मातंगी स्तोत्र / 108 नाम; संगीत, विद्या व वंचितों की सहायता", "Sunday, Tritiya"),
    "Venus": ("Kamala (Kamalatmika)", "कमला (कमलात्मिका)", "abundance, grace and lotus-like purity (tantric Lakshmi)",
              "समृद्धि, लावण्य व कमल-सी पवित्रता (तांत्रिक लक्ष्मी)",
              "Shri Suktam / Kanakadhara stotra; lotus or white flowers on Fridays",
              "श्री सूक्त / कनकधारा स्तोत्र; शुक्रवार को कमल या श्वेत पुष्प", "Friday, Purnima"),
    "Lagna": ("Tripura Bhairavi", "त्रिपुर भैरवी", "tapas and inner fire; strength of the whole self",
              "तप व आंतरिक अग्नि; संपूर्ण व्यक्तित्व का बल",
              "Bhairavi stotra / 108 names", "भैरवी स्तोत्र / 108 नाम", "Navratri"),
}

# "Ten flowers" offered in inner worship (Tara Rahasya, cited in the book, p. 391)
TEN_FLOWERS_VERSE = ("दयापुष्पं क्षमापुष्पं पुष्पमिन्द्रियनिग्रहम्। ज्ञानपुष्पं पुण्यपुष्पमहिंसापुष्पमुत्तमम्॥ "
                     "आचारपुष्पं मे देवि स्वयंभूपुष्पमुत्तमम्। आनन्दपुष्पं दातव्यं पुष्पञ्च साधकार्चनम्॥")
FLOWERS = [  # key, en, hi
    ("daya", "compassion", "दया"), ("kshama", "forgiveness", "क्षमा"), ("indriya", "restraint of the senses", "इन्द्रिय-निग्रह"),
    ("jnana", "knowledge", "ज्ञान"), ("punya", "good deeds", "पुण्य"), ("ahimsa", "non-harming", "अहिंसा"),
    ("achara", "right conduct", "आचार"), ("svayambhu", "the self-born inner flower (the Self)", "स्वयंभू (आत्म-पुष्प)"),
    ("ananda", "joy", "आनन्द"), ("sadhaka", "honouring fellow seekers", "साधकार्चन"),
]
# Which inner flowers best answer a planet's difficult side – an app suggestion, not the book's
PLANET_FLOWERS = {"Sun": ["kshama", "achara"], "Moon": ["ananda", "daya"], "Mars": ["kshama", "ahimsa"],
                  "Mercury": ["jnana", "achara"], "Jupiter": ["jnana", "sadhaka"], "Venus": ["indriya", "ananda"],
                  "Saturn": ["daya", "punya"], "Rahu": ["indriya", "achara"], "Ketu": ["svayambhu", "daya"]}

PRINCIPLES = [  # (en, hi, printed page)
    ("Identification (tadatmya): a mantra works when the practitioner becomes one with its devata – recite with that feeling, not mechanically.",
     "तादात्म्य: मंत्र तब फल देता है जब साधक मंत्र-देवता से एकरूप हो – यांत्रिक रूप से नहीं, भाव से जप करें।", 366),
    ("Unbroken practice (abhyasa-nairantarya): once begun, keep the daily count without a break; a broken practice loses its momentum.",
     "अभ्यास-नैरन्तर्य: आरंभ के बाद प्रतिदिन की संख्या बिना टूटे बनाए रखें; टूटा अभ्यास गति खो देता है।", 368),
    ("Sankalpa and single-minded devotion: take a clear resolve before starting and hold to one deity and one mantra.",
     "संकल्प व अनन्य निष्ठा: आरंभ से पहले स्पष्ट संकल्प लें; एक देवता व एक मंत्र पर टिके रहें।", 373),
    ("Give up glani (despondency): dejection drains all capacity; it is overcome by fresh inner awakening (unmesha), not by force.",
     "ग्लानि का त्याग: निराशा सारी क्षमता नष्ट करती है; इसे आंतरिक उन्मेष से जीतें, ज़ोर से नहीं।", 372),
    ("Inner worship is the highest: tantra's ideal is manasi (mental) and symbolic puja – outer ritual is a support, not the goal.",
     "मानसी पूजा सर्वोच्च: तंत्र का आदर्श मानसिक व प्रतीकात्मक पूजा है – बाह्य कर्मकांड सहायक है, लक्ष्य नहीं।", 390),
    ("Offer the ten flowers: compassion, forgiveness, sense-restraint, knowledge, good deeds, non-harming, conduct, the Self, joy and honouring fellow seekers – these are the real offerings.",
     "दस पुष्प अर्पित करें: दया, क्षमा, इन्द्रिय-निग्रह, ज्ञान, पुण्य, अहिंसा, आचार, स्वयंभू, आनन्द व साधकार्चन – यही वास्तविक अर्पण हैं।", 391),
    ("Diksha from a guru is central to mantra sadhana in the book; so this app lists only a Mahavidya's names, stotras and inner worship – take her mantra from a guru.",
     "ग्रंथ में मंत्र साधना हेतु गुरु-दीक्षा केंद्रीय है; अतः यह ऐप महाविद्या के केवल नाम, स्तोत्र व मानसी पूजा देता है – मंत्र गुरु से लें।", 367),
]


def for_planet(planet: str, lang: str = "en") -> dict:
    hi = lang == "hi"
    m = MAHAVIDYA[planet]
    fl = {k: (en, h) for k, en, h in FLOWERS}
    flowers = [fl[k][1 if hi else 0] for k in PLANET_FLOWERS.get(planet, [])]
    return {
        "planet": planet, "mahavidya": m[1] if hi else m[0], "essence": m[3] if hi else m[2],
        "practice": m[5] if hi else m[4], "days": m[6], "inner_flowers": flowers,
        "items": [
            (f"महाविद्या: {m[1]} – {m[3]}" if hi else f"Mahavidya: {m[0]} – {m[2]}"),
            (f"सबके लिए खुला अभ्यास: {m[5]} ({m[6]})" if hi else f"Open to all: {m[4]} ({m[6]})"),
            (f"मानसी पूजा में अर्पित करें: {', '.join(flowers)}" if hi else f"In inner worship offer the flowers of {', '.join(flowers)}"),
            ("बीज/तांत्रिक मंत्र केवल गुरु-दीक्षा से।" if hi else "Beeja / tantric mantras only with a guru's diksha."),
        ],
        "source": f"{TRAD}; principles from {BOOK}, ch. 8",
    }


def report(planets: list[str], lang: str = "en") -> dict:
    hi = lang == "hi"
    return {
        "principles": [{"text": p[1] if hi else p[0], "page": p[2]} for p in PRINCIPLES],
        "ten_flowers": {"verse": TEN_FLOWERS_VERSE, "source": "Tara Rahasya, quoted in the book p. 391",
                        "flowers": [{"key": k, "name": h if hi else en} for k, en, h in FLOWERS]},
        "mahavidyas": [for_planet(p, lang) for p in ["Lagna", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]],
        "for_you": [for_planet(p, lang) for p in planets if p in MAHAVIDYA],
        "excluded_note": ("अभिचार/षट्कर्म (वशीकरण, उच्चाटन, मारण, दूसरों का स्तंभन) शामिल नहीं – ये दूसरों को हानि पहुँचाते हैं और इस ग्रंथ में भी नहीं हैं।"
                          if hi else "Abhichara / shatkarma aimed at others (vashikaran, uchchatan, maran, stambhan of others) is not included – it harms others and is not in this book either."),
        "book": BOOK, "mapping_source": TRAD,
    }
