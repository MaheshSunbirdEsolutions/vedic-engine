"""Vimshottari dasha: Mahadasha -> Antardasha -> Pratyantardasha."""
from __future__ import annotations

from datetime import datetime

from . import ephemeris as eph
from .constants import DASHA_ORDER, DASHA_YEARS, NAKSHATRA_SPAN


def _sequence_from(lord: str) -> list[str]:
    i = DASHA_ORDER.index(lord)
    return DASHA_ORDER[i:] + DASHA_ORDER[:i]


def birth_balance(moon_lon: float) -> dict:
    """Starting lord and the fraction of its Mahadasha already elapsed at birth."""
    idx = int(moon_lon // NAKSHATRA_SPAN) % 27
    lord = DASHA_ORDER[idx % 9]
    elapsed_frac = (moon_lon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    years = DASHA_YEARS[lord]
    return {"lord": lord, "elapsed_fraction": elapsed_frac,
            "balance_years": (1 - elapsed_frac) * years}


def _periods(start_jd: float, lord: str, total_years: float, year_days: float, depth: int,
             levels: int, tz: str) -> list[dict]:
    """Subdivide a period of `total_years` that belongs to `lord` into 9 sub-periods."""
    out = []
    t = start_jd
    for sub in _sequence_from(lord):
        yrs = total_years * DASHA_YEARS[sub] / 120
        end = t + yrs * year_days
        p = {"lord": sub, "start": eph.jd_to_datetime(t, tz).isoformat(),
             "end": eph.jd_to_datetime(end, tz).isoformat(), "_s": t, "_e": end}
        if depth + 1 < levels:
            p["sub"] = _periods(t, sub, yrs, year_days, depth + 1, levels, tz)
        out.append(p)
        t = end
    return out


def vimshottari(dt_local: datetime, tz: str, settings: eph.Settings = eph.Settings(),
                levels: int = 3, at: datetime | None = None) -> dict:
    """Full 120-year timeline. levels: 1=MD, 2=+AD, 3=+PD."""
    jd = eph.local_to_jd(dt_local, tz)
    moon = eph.body_longitude(jd, "Moon", settings)
    bal = birth_balance(moon)
    yd = settings.year_days
    # The first MD began before birth; anchor the whole cycle at its true start.
    t = jd - bal["elapsed_fraction"] * DASHA_YEARS[bal["lord"]] * yd
    mahadashas = []
    for lord in _sequence_from(bal["lord"]):
        yrs = DASHA_YEARS[lord]
        end = t + yrs * yd
        md = {"lord": lord, "start": eph.jd_to_datetime(t, tz).isoformat(),
              "end": eph.jd_to_datetime(end, tz).isoformat(), "_s": t, "_e": end}
        if levels > 1:
            md["sub"] = _periods(t, lord, yrs, yd, 1, levels, tz)
        mahadashas.append(md)
        t = end

    at_jd = eph.local_to_jd(at, tz) if at else None
    current = []
    if at_jd is not None:
        layer = mahadashas
        while layer:
            hit = next((p for p in layer if p["_s"] <= at_jd < p["_e"]), None)
            if not hit:
                break
            current.append(hit["lord"])
            layer = hit.get("sub")

    def clean(ps):
        for p in ps:
            p.pop("_s"), p.pop("_e")
            if "sub" in p:
                clean(p["sub"])
        return ps

    return {
        "moon_longitude": round(moon, 6),
        "birth_dasha": {"lord": bal["lord"], "balance_years": round(bal["balance_years"], 4)},
        "current": current,  # e.g. ["Saturn", "Mercury", "Venus"] = MD / AD / PD
        "mahadashas": clean(mahadashas),
    }
