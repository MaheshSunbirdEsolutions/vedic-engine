"""Popular dosha checks: Manglik, Kaal Sarp, Sade Sati.

These implement the common textbook definitions. Cancellation (parihara) rules
vary between schools and are deliberately NOT applied here; they belong in the
rules engine, reviewed by a Jyotishi.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from . import ephemeris as eph
from .chart import sign_index
from .constants import SIGNS

MANGLIK_HOUSES = {1, 2, 4, 7, 8, 12}


def manglik(chart: dict) -> dict:
    mars_sign = chart["planets"]["Mars"]["sign_index"] - 1
    refs = {
        "lagna": chart["lagna"]["sign_index"] - 1,
        "moon": chart["planets"]["Moon"]["sign_index"] - 1,
        "venus": chart["planets"]["Venus"]["sign_index"] - 1,
    }
    result = {}
    for ref, s in refs.items():
        h = (mars_sign - s) % 12 + 1
        result[ref] = {"mars_house": h, "manglik": h in MANGLIK_HOUSES}
    return {"present": result["lagna"]["manglik"], "from": result,
            "note": "Counted from Lagna (primary), Moon and Venus. Cancellation rules not applied."}


def kaal_sarp(chart: dict) -> dict:
    rahu = chart["planets"]["Rahu"]["longitude"]
    rel = [(chart["planets"][p]["longitude"] - rahu) % 360
           for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")]
    one_side = all(0 < r < 180 for r in rel) or all(180 < r < 360 for r in rel)
    return {"present": one_side,
            "note": "All seven planets hemmed on one side of the Rahu-Ketu axis (strict longitude test)."}


def sade_sati_periods(dt_birth: datetime, tz: str, moon_sign: int, years: int = 100,
                      settings: eph.Settings = eph.Settings()) -> list[dict]:
    """Saturn's transits through the 12th, 1st and 2nd signs from natal Moon (day resolution)."""
    target = {(moon_sign - 1) % 12, moon_sign, (moon_sign + 1) % 12}
    phase_name = {(moon_sign - 1) % 12: "rising (12th)", moon_sign: "peak (1st)", (moon_sign + 1) % 12: "setting (2nd)"}
    jd0 = eph.local_to_jd(dt_birth, tz)
    periods, cur = [], None
    for d in range(int(years * 365.25) + 1):
        jd = jd0 + d
        s = sign_index(eph.body_longitude(jd, "Saturn", settings))
        inside = s in target
        if inside and cur is None:
            cur = {"start": jd, "phases": []}
        if inside:
            if not cur["phases"] or cur["phases"][-1]["sign"] != SIGNS[s]:
                cur["phases"].append({"sign": SIGNS[s], "phase": phase_name[s], "from": jd})
        if not inside and cur is not None:
            cur["end"] = jd
            periods.append(cur)
            cur = None
    if cur is not None:
        cur["end"] = None
        periods.append(cur)

    # Merge brief exits caused by retrograde motion (gaps < 1 year) into one period.
    merged = []
    for p in periods:
        if merged and merged[-1]["end"] is not None and p["start"] - merged[-1]["end"] < 365:
            merged[-1]["end"] = p["end"]
            for ph in p["phases"]:
                if merged[-1]["phases"][-1]["sign"] != ph["sign"]:
                    merged[-1]["phases"].append(ph)
        else:
            merged.append(p)
    fmt = lambda jd: None if jd is None else eph.jd_to_datetime(jd, tz).date().isoformat()
    return [{"start": fmt(p["start"]), "end": fmt(p["end"]),
             "phases": [{"sign": ph["sign"], "phase": ph["phase"], "from": fmt(ph["from"])} for ph in p["phases"]]}
            for p in merged]


def sade_sati_status(moon_sign: int, at: datetime, tz: str, settings: eph.Settings = eph.Settings()) -> dict:
    s = sign_index(eph.body_longitude(eph.local_to_jd(at, tz), "Saturn", settings))
    rel = (s - moon_sign) % 12
    phase = {11: "rising (12th)", 0: "peak (1st)", 1: "setting (2nd)"}.get(rel)
    dhaiya = {3: "Kantaka/Ardhashtama (4th)", 7: "Ashtama (8th)"}.get(rel)
    return {"saturn_sign": SIGNS[s], "sade_sati": phase is not None, "phase": phase, "dhaiya": dhaiya}
