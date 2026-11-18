"""Thin wrapper over Swiss Ephemeris.

All astronomy goes through this module so the backend can be swapped
(e.g. for an MIT-licensed library) without touching the rest of the engine.

LICENSE NOTE: pyswisseph / Swiss Ephemeris is AGPL-3.0 or a paid Professional
License from Astrodienst. A closed-source hosted product needs the paid license.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

_EPHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ephe")
swe.set_ephe_path(_EPHE_DIR if os.path.isdir(_EPHE_DIR) else None)

AYANAMSAS = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
    "true_chitra": swe.SIDM_TRUE_CITRA,
}
_BODIES = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}


@dataclass(frozen=True)
class Settings:
    ayanamsa: str = "lahiri"
    node: str = "mean"  # "mean" or "true" Rahu/Ketu
    year_days: float = 365.25  # dasha year length


def local_to_jd(dt_local: datetime, tz: str) -> float:
    """Local civil time + IANA zone (handles historical offsets/DST) -> Julian Day (UT)."""
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=ZoneInfo(tz))
    u = dt_local.astimezone(timezone.utc)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600 + u.microsecond / 3.6e9)


def jd_to_datetime(jd: float, tz: str = "UTC") -> datetime:
    y, m, d, h = swe.revjul(jd)
    secs = round(h * 3600)
    base = datetime(y, m, d, tzinfo=timezone.utc)
    from datetime import timedelta
    return (base + timedelta(seconds=secs)).astimezone(ZoneInfo(tz))


def _flags(settings: Settings) -> int:
    swe.set_sid_mode(AYANAMSAS[settings.ayanamsa])
    return swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED


def ayanamsa(jd: float, settings: Settings = Settings()) -> float:
    swe.set_sid_mode(AYANAMSAS[settings.ayanamsa])
    return swe.get_ayanamsa_ut(jd)


def planet_longitudes(jd: float, settings: Settings = Settings()) -> dict[str, dict]:
    """Sidereal longitude and speed (deg/day) of the 9 grahas."""
    fl = _flags(settings)
    out = {}
    for name, body in _BODIES.items():
        xx = swe.calc_ut(jd, body, fl)[0]
        out[name] = {"lon": xx[0] % 360, "speed": xx[3]}
    node = swe.MEAN_NODE if settings.node == "mean" else swe.TRUE_NODE
    xx = swe.calc_ut(jd, node, fl)[0]
    out["Rahu"] = {"lon": xx[0] % 360, "speed": xx[3]}
    out["Ketu"] = {"lon": (xx[0] + 180) % 360, "speed": xx[3]}
    return out


def body_longitude(jd: float, name: str, settings: Settings = Settings()) -> float:
    fl = _flags(settings)
    xx = swe.calc_ut(jd, _BODIES[name], fl)[0]
    return xx[0] % 360


def ascendant(jd: float, lat: float, lon: float, settings: Settings = Settings()) -> float:
    fl = _flags(settings)
    _, ascmc = swe.houses_ex(jd, lat, lon, b"W", fl)
    return ascmc[0] % 360


def sunrise_sunset(jd_start: float, lat: float, lon: float) -> tuple[float, float]:
    """Next sunrise after jd_start and the sunset after that (upper limb, refraction)."""
    geo = (lon, lat, 0)
    _, rise = swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, geo)
    _, sett = swe.rise_trans(rise[0], swe.SUN, swe.CALC_SET, geo)
    return rise[0], sett[0]
