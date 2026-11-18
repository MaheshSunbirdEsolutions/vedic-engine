"""Daily panchang: tithi, vara, nakshatra, yoga, karana at local sunrise, with end times."""
from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from . import ephemeris as eph
from .constants import (
    MOVABLE_KARANAS, NAKSHATRA_SPAN, NAKSHATRAS, RAHU_KAAL_SEGMENT, TITHI_NAMES, VARA_NAMES,
    YOGA_NAMES,
)


def _sun_moon(jd, s):
    return eph.body_longitude(jd, "Sun", s), eph.body_longitude(jd, "Moon", s)


# Each element is a monotonically increasing angle; elements change every `span` degrees.
def _angle(kind: str, jd: float, s: eph.Settings) -> float:
    sun, moon = _sun_moon(jd, s)
    if kind in ("tithi", "karana"):
        return (moon - sun) % 360
    if kind == "nakshatra":
        return moon
    if kind == "yoga":
        return (sun + moon) % 360
    raise ValueError(kind)


SPANS = {"tithi": 12.0, "karana": 6.0, "nakshatra": NAKSHATRA_SPAN, "yoga": NAKSHATRA_SPAN}


def element_index(kind: str, jd: float, s: eph.Settings = eph.Settings()) -> int:
    return int(_angle(kind, jd, s) // SPANS[kind])  # 0-based


def element_end(kind: str, jd: float, s: eph.Settings = eph.Settings()) -> float:
    """JD when the element current at `jd` ends (bisection on the angle)."""
    span = SPANS[kind]
    start_idx = element_index(kind, jd, s)
    lo, hi = jd, jd
    while element_index(kind, hi, s) == start_idx:  # step until it changes
        lo, hi = hi, hi + 0.1
    for _ in range(40):  # ~1e-12 day precision
        mid = (lo + hi) / 2
        if element_index(kind, mid, s) == start_idx:
            lo = mid
        else:
            hi = mid
    return hi


def tithi_name(i: int) -> dict:
    paksha = "Shukla" if i < 15 else "Krishna"
    n = i % 15
    name = TITHI_NAMES[n] if n < 14 else ("Purnima" if i == 14 else "Amavasya")
    return {"number": i + 1, "name": name, "paksha": paksha}


def karana_name(k: int) -> str:
    if k == 0:
        return "Kimstughna"
    if k >= 57:
        return ["Shakuni", "Chatushpada", "Naga"][k - 57]
    return MOVABLE_KARANAS[(k - 1) % 7]


def panchang(day: date, tz: str, lat: float, lon: float, settings: eph.Settings = eph.Settings()) -> dict:
    midnight = datetime.combine(day, time(0, 0), tzinfo=ZoneInfo(tz))
    rise, sett = eph.sunrise_sunset(eph.local_to_jd(midnight, tz), lat, lon)
    fmt = lambda jd: eph.jd_to_datetime(jd, tz).isoformat(timespec="minutes")

    t = element_index("tithi", rise, settings)
    n = element_index("nakshatra", rise, settings)
    y = element_index("yoga", rise, settings)
    k = element_index("karana", rise, settings)
    weekday = day.weekday()  # Mon=0
    seg = (sett - rise) / 8
    rk_start = rise + (RAHU_KAAL_SEGMENT[weekday] - 1) * seg
    return {
        "date": day.isoformat(), "tz": tz, "lat": lat, "lon": lon,
        "sunrise": fmt(rise), "sunset": fmt(sett),
        "vara": VARA_NAMES[weekday],
        "tithi": {**tithi_name(t), "ends": fmt(element_end("tithi", rise, settings))},
        "nakshatra": {"number": n + 1, "name": NAKSHATRAS[n], "ends": fmt(element_end("nakshatra", rise, settings))},
        "yoga": {"number": y + 1, "name": YOGA_NAMES[y], "ends": fmt(element_end("yoga", rise, settings))},
        "karana": {"name": karana_name(k), "ends": fmt(element_end("karana", rise, settings))},
        "rahu_kaal": {"start": fmt(rk_start), "end": fmt(rk_start + seg)},
        "note": "Elements are those prevailing at local sunrise; 'ends' is when each changes.",
    }
