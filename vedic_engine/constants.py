"""Reference data for Parashari Jyotish.

Everything here is classical reference data (BPHS / Laghu Parashari conventions).
Items where schools disagree are marked so they can be made configurable.
"""

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGNS_SANSKRIT = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_SPAN = 360.0 / 27  # 13°20'
PADA_SPAN = NAKSHATRA_SPAN / 4  # 3°20'

# Vimshottari: nakshatra lords repeat in this order; years sum to 120
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

# Exaltation: (sign index, deepest degree). Debilitation is the opposite sign, same degree.
EXALTATION = {
    "Sun": (0, 10), "Moon": (1, 3), "Mars": (9, 28), "Mercury": (5, 15),
    "Jupiter": (3, 5), "Venus": (11, 27), "Saturn": (6, 20),
}
# Moolatrikona: (sign index, start deg, end deg)
MOOLATRIKONA = {
    "Sun": (4, 0, 20), "Moon": (1, 3, 30), "Mars": (0, 0, 12), "Mercury": (5, 15, 20),
    "Jupiter": (8, 0, 10), "Venus": (6, 0, 15), "Saturn": (10, 0, 20),
}
# Natural (naisargika) relationships, BPHS
FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
    "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
]
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
    "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti",
]
MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
VARA_NAMES = ["Somavara", "Mangalavara", "Budhavara", "Guruvara", "Shukravara", "Shanivara", "Ravivara"]  # Mon..Sun
# Rahu Kaal: which eighth of the daytime (1-based), indexed Mon..Sun
RAHU_KAAL_SEGMENT = [2, 7, 5, 6, 4, 3, 8]
