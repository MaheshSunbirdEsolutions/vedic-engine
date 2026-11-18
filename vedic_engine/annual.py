"""Annual charts: Tithi Pravesha (PVR) and Lal Kitab Varshphal.

Tithi Pravesha (TP): the moment in a given year when the Sun is back in its natal sign
and the Moon-Sun angle (the tithi) is exactly what it was at birth. The year's vara lord
(weekday lord at the TP moment, Vedic day from sunrise) and hora lord are key indicators
(Lessons 13, 14, 24, 30). The TP chart is cast for the place of residence.

Lal Kitab varshphal: each natal house moves to a fixed house for each year of age (1-120),
per the table on book pp. 71-73.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from . import ephemeris as eph
from .chart import build_chart, sign_index
from .constants import SIGNS
from .lalkitab.varshphal_table import VARSHPHAL

VARA_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]  # Mon..Sun
HORA_ORDER = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]


def _angle(jd, s):
    return (eph.body_longitude(jd, "Moon", s) - eph.body_longitude(jd, "Sun", s)) % 360


def _find_root(jd_a: float, jd_b: float, target: float, s) -> float:
    f = lambda jd: ((_angle(jd, s) - target + 180) % 360) - 180  # signed distance
    lo, hi = jd_a, jd_b
    for _ in range(50):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def tithi_pravesha_jd(birth_jd: float, year: int, tz: str, s: eph.Settings = eph.Settings()) -> float:
    natal_angle = _angle(birth_jd, s)
    natal_sun_sign = sign_index(eph.body_longitude(birth_jd, "Sun", s))
    b = eph.jd_to_datetime(birth_jd, tz)
    try:
        anniv = b.replace(year=year)
    except ValueError:                      # 29 Feb
        anniv = b.replace(year=year, day=28)
    start = eph.local_to_jd(anniv.replace(tzinfo=None), tz) - 45
    f = lambda jd: ((_angle(jd, s) - natal_angle + 180) % 360) - 180
    jd, step = start, 0.25
    roots = []
    while jd < start + 90:
        a, c = f(jd), f(jd + step)
        if a <= 0 < c or (a < 0 and c >= 0):
            if abs(a - c) < 30:             # ignore the wrap-around jump
                roots.append(_find_root(jd, jd + step, natal_angle, s))
        jd += step
    for r in roots:
        if sign_index(eph.body_longitude(r, "Sun", s)) == natal_sun_sign:
            return r
    raise RuntimeError("no Tithi Pravesha found in the search window")


def hora_lord(jd: float, lat: float, lon: float, tz: str) -> dict:
    """Vara lord (Vedic day from sunrise) and planetary hora lord at a moment."""
    local = eph.jd_to_datetime(jd, tz)
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    rise, sett = eph.sunrise_sunset(eph.local_to_jd(midnight.replace(tzinfo=None), tz), lat, lon)
    if jd < rise:   # before today's sunrise -> belongs to the previous Vedic day (night part)
        prev = midnight - timedelta(days=1)
        rise, sett = eph.sunrise_sunset(eph.local_to_jd(prev.replace(tzinfo=None), tz), lat, lon)
    vara_day = eph.jd_to_datetime(rise, tz).weekday()
    vara_lord = VARA_LORDS[vara_day]
    if jd < sett:
        idx = int((jd - rise) / ((sett - rise) / 12))
    else:
        next_rise, _ = eph.sunrise_sunset(sett, lat, lon)
        idx = 12 + int((jd - sett) / ((next_rise - sett) / 12))
    start = HORA_ORDER.index(vara_lord)
    return {"vara_lord": vara_lord, "hora_lord": HORA_ORDER[(start + idx) % 7], "hora_number": idx + 1}


def tithi_pravesha(dt_birth: datetime, tz: str, lat: float, lon: float, year: int,
                   res_lat: float | None = None, res_lon: float | None = None, res_tz: str | None = None,
                   s: eph.Settings = eph.Settings()) -> dict:
    birth_jd = eph.local_to_jd(dt_birth, tz)
    rtz, rlat, rlon = res_tz or tz, res_lat if res_lat is not None else lat, res_lon if res_lon is not None else lon
    jd = tithi_pravesha_jd(birth_jd, year, rtz, s)
    moment = eph.jd_to_datetime(jd, rtz).replace(tzinfo=None, microsecond=0)
    chart = build_chart(moment, rtz, rlat, rlon, s)
    lords = hora_lord(jd, rlat, rlon, rtz)
    next_jd = tithi_pravesha_jd(birth_jd, year + 1, rtz, s)
    return {"year": year, "moment": eph.jd_to_datetime(jd, rtz).isoformat(timespec="minutes"),
            "valid_until": eph.jd_to_datetime(next_jd, rtz).isoformat(timespec="minutes"),
            **lords, "chart": chart}


# ---------------- Lal Kitab ----------------

def lal_kitab_houses(chart: dict) -> dict[str, int]:
    """Lal Kitab uses the birth chart's house positions (lagna = house 1, signs ignored)."""
    return {p: v["house"] for p, v in chart["planets"].items()}


def age_running(dt_birth: datetime, on: datetime) -> int:
    """Lal Kitab year of life: 1 from birth to the first birthday, etc."""
    years = on.year - dt_birth.year - ((on.month, on.day) < (dt_birth.month, dt_birth.day))
    return years + 1


def lal_kitab_varshphal(chart: dict, age: int) -> dict:
    if not 1 <= age <= 120:
        raise ValueError("Lal Kitab varshphal covers ages 1-120")
    natal = lal_kitab_houses(chart)
    row = VARSHPHAL[age]
    annual = {p: row[h - 1] for p, h in natal.items()}
    houses = {h: [p for p, x in annual.items() if x == h] for h in range(1, 13)}
    return {"age": age, "natal_houses": natal, "annual_houses": annual, "houses": houses,
            "source": "Lal Kitab (Arun Sanhita) varshphal table, book pp. 71-73"}
