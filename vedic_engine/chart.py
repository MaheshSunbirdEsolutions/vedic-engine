"""Birth chart (kundli): planets, signs, nakshatras, houses, dignities, vargas."""
from __future__ import annotations

import math
from datetime import datetime

from . import ephemeris as eph
from .constants import (
    ENEMIES, EXALTATION, FRIENDS, MOOLATRIKONA, NAKSHATRA_SPAN, NAKSHATRAS, PADA_SPAN,
    SIGN_LORDS, SIGNS, SIGNS_SANSKRIT, DASHA_ORDER,
)


def sign_index(lon: float) -> int:
    return int(lon // 30) % 12


def nakshatra(lon: float) -> dict:
    i = int(lon // NAKSHATRA_SPAN) % 27
    pada = int((lon % NAKSHATRA_SPAN) // PADA_SPAN) + 1
    return {"index": i + 1, "name": NAKSHATRAS[i], "pada": pada, "lord": DASHA_ORDER[i % 9]}


def dms(deg: float) -> str:
    d = int(deg)
    m_f = (deg - d) * 60
    m = int(m_f)
    s = int(round((m_f - m) * 60))
    if s == 60:
        m, s = m + 1, 0
    if m == 60:
        d, m = d + 1, 0
    return f"{d}°{m:02d}′{s:02d}″"


# ---------- divisional charts (vargas) ----------

def varga_sign(lon: float, division: int) -> int:
    """Sign index (0-11) of a longitude in a Parashari divisional chart (Jagannatha Hora defaults)."""
    s = sign_index(lon)
    deg = lon % 30
    odd = s % 2 == 0          # Aries (index 0) is an odd sign
    mode = s % 3              # 0 movable, 1 fixed, 2 dual
    part = int(deg // (30 / division)) if division > 0 else 0
    if division == 1:
        return s
    if division == 2:   # Hora (Parashara): odd sign -> Leo then Cancer; even -> Cancer then Leo
        first = deg < 15
        return (4 if first else 3) if odd else (3 if first else 4)
    if division == 3:   # Drekkana: same, 5th, 9th
        return (s + 4 * part) % 12
    if division == 4:   # Chaturthamsa: same, 4th, 7th, 10th
        return (s + 3 * part) % 12
    if division == 6:   # Shashtamsa: odd from Aries, even from Libra
        return (part if odd else 6 + part) % 12
    if division == 7:   # Saptamsa: odd from same sign, even from 7th
        return (s + part) % 12 if odd else (s + 6 + part) % 12
    if division == 9:   # Navamsa: continuous from Aries
        return int(lon // (30 / 9)) % 12
    if division == 10:  # Dashamsa: odd from same sign, even from 9th
        return (s + part) % 12 if odd else (s + 8 + part) % 12
    if division == 12:  # Dwadashamsa: from same sign
        return (s + part) % 12
    if division == 16:  # Shodashamsa: movable Aries, fixed Leo, dual Sagittarius
        return ([0, 4, 8][mode] + part) % 12
    if division == 20:  # Vimsamsa: movable Aries, fixed Sagittarius, dual Leo
        return ([0, 8, 4][mode] + part) % 12
    if division == 24:  # Chaturvimsamsa: odd Leo, even Cancer
        return ((4 if odd else 3) + part) % 12
    if division == 27:  # Nakshatramsa: fiery Aries, earthy Cancer, airy Libra, watery Capricorn
        return ([0, 3, 6, 9][s % 4] + part) % 12
    if division == 30:  # Trimsamsa (unequal)
        if odd:
            bounds = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]    # Mars, Saturn, Jupiter, Mercury, Venus
        else:
            bounds = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]    # Venus, Mercury, Jupiter, Saturn, Mars
        return next(sg for lim, sg in bounds if deg < lim)
    if division == 40:  # Khavedamsa: odd Aries, even Libra
        return ((0 if odd else 6) + part) % 12
    if division == 45:  # Akshavedamsa: movable Aries, fixed Leo, dual Sagittarius
        return ([0, 4, 8][mode] + part) % 12
    if division == 60:  # Shashtiamsa: from same sign
        return (s + part) % 12
    raise ValueError(f"D{division} not implemented")


VARGA_MEANINGS = {
    1: "Rashi – body, physical existence", 2: "Hora – wealth", 3: "Drekkana – siblings, courage",
    4: "Chaturthamsa – property, residence, fortune", 6: "Shashtamsa – health, enemies",
    7: "Saptamsa – children", 9: "Navamsa – spouse, dharma, inner strength", 10: "Dashamsa – career, work in society",
    12: "Dwadashamsa – parents", 16: "Shodashamsa – vehicles, comforts", 20: "Vimsamsa – spiritual progress",
    24: "Chaturvimsamsa – education, learning", 27: "Nakshatramsa – strengths and weaknesses",
    30: "Trimsamsa – misfortunes, inner enemies", 40: "Khavedamsa – maternal legacy",
    45: "Akshavedamsa – paternal legacy, character", 60: "Shashtiamsa – past karma",
}

SUPPORTED_VARGAS = (1, 2, 3, 4, 6, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60)


def dignity(planet: str, lon: float) -> str:
    if planet not in EXALTATION:
        return "n/a"  # Rahu/Ketu dignity differs by school; configure later
    s = sign_index(lon)
    deg = lon % 30
    ex_sign, _ = EXALTATION[planet]
    if s == ex_sign:
        return "exalted"
    if s == (ex_sign + 6) % 12:
        return "debilitated"
    mt_sign, a, b = MOOLATRIKONA[planet]
    if s == mt_sign and a <= deg < b:
        return "moolatrikona"
    lord = SIGN_LORDS[s]
    if lord == planet:
        return "own"
    if lord in FRIENDS[planet]:
        return "friend"
    if lord in ENEMIES[planet]:
        return "enemy"
    return "neutral"


def build_chart(dt_local: datetime, tz: str, lat: float, lon: float,
                settings: eph.Settings = eph.Settings()) -> dict:
    jd = eph.local_to_jd(dt_local, tz)
    asc = eph.ascendant(jd, lat, lon, settings)
    asc_sign = sign_index(asc)
    positions = eph.planet_longitudes(jd, settings)

    def entry(name: str, L: float, speed: float | None) -> dict:
        s = sign_index(L)
        e = {
            "longitude": round(L, 6),
            "sign": SIGNS[s], "sign_sanskrit": SIGNS_SANSKRIT[s], "sign_index": s + 1,
            "degree_in_sign": dms(L % 30),
            "nakshatra": nakshatra(L),
            "house": (s - asc_sign) % 12 + 1,  # whole-sign houses
            "vargas": {f"D{d}": SIGNS[varga_sign(L, d)] for d in SUPPORTED_VARGAS},
        }
        if speed is not None:
            e["retrograde"] = speed < 0 if name not in ("Rahu", "Ketu") else True
            e["dignity"] = dignity(name, L)
        return e

    planets = {n: entry(n, p["lon"], p["speed"]) for n, p in positions.items()}
    houses = [
        {"house": h + 1, "sign": SIGNS[(asc_sign + h) % 12], "lord": SIGN_LORDS[(asc_sign + h) % 12],
         "planets": [n for n, p in planets.items() if p["house"] == h + 1]}
        for h in range(12)
    ]
    return {
        "input": {"datetime_local": dt_local.isoformat(), "tz": tz, "lat": lat, "lon": lon,
                  "settings": settings.__dict__},
        "julian_day_ut": jd,
        "ayanamsa": {"name": settings.ayanamsa, "value": round(eph.ayanamsa(jd, settings), 6),
                     "dms": dms(eph.ayanamsa(jd, settings))},
        "lagna": entry("Lagna", asc, None),
        "planets": planets,
        "houses": houses,
        "vargas": {
            f"D{d}": {"lagna": SIGNS[varga_sign(asc, d)],
                      "planets": {n: SIGNS[varga_sign(p["lon"], d)] for n, p in positions.items()}}
            for d in SUPPORTED_VARGAS
        },
    }
