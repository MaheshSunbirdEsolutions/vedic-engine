"""Lal Kitab (Arun Sanhita, Hare Krishna Trust edition) data: planet-in-house titles, themes and upay.

data/titles.yaml – the book's own one-line title for each of the 108 planet-house sections (exact,
                   from the table of contents) with the book page.
data/upay.yaml   – per planet-house: short theme (en/hi) and the book's upay, paraphrased in our own
                   words (en/hi), each with its book page so a reviewer can check it.
"""
from __future__ import annotations

import functools
import pathlib

import yaml

DATA = pathlib.Path(__file__).parent / "data"
PAKKA_GHAR = {"Sun": [1], "Moon": [4], "Mars": [3, 8], "Mercury": [7], "Jupiter": [2],
              "Venus": [7], "Saturn": [8], "Rahu": [12], "Ketu": [6]}
TITLE_EN_HINT = "Book title of this placement (Hindi, from the table of contents)"


@functools.lru_cache(maxsize=None)
def titles() -> dict:
    try:
        p = DATA / "titles.yaml"
        return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        return {}


@functools.lru_cache(maxsize=None)
def upay_data() -> dict:
    try:
        p = DATA / "upay.yaml"
        return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        return {}


@functools.lru_cache(maxsize=None)
def section_pages() -> dict:
    import json
    try:
        p = DATA / "section_pages.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        return {}


def entry(planet: str, house: int, lang: str = "en") -> dict:
    t = titles().get(planet, {}).get(house, {})
    u = upay_data().get(planet, {}).get(house, {})
    hi = lang == "hi"
    sec = section_pages().get(planet, {}).get(str(house), [])
    return {
        "planet": planet, "house": house, "title_hi": t.get("title_hi", ""), "book_page": t.get("book_page", 0),
        "theme": (u.get("theme_hi") if hi else u.get("theme_en")) or "",
        "upay": [x["hi" if hi else "en"] for x in u.get("upay", []) if isinstance(x, dict) and ("hi" in x or "en" in x)],
        "pakka_ghar": house in PAKKA_GHAR.get(planet, []),
        "status": u.get("status", "pending" if not u else "draft"),
        "pdf_pages": sec,
    }


def upay_for(planet: str, annual_house: int, natal_house: int, lang: str = "en") -> list[dict]:
    """Remedies for an issue's key planet: this year's annual-house upay first, then natal-house upay."""
    out = []
    for kind, h in (("annual", annual_house), ("natal", natal_house)):
        e = entry(planet, h, lang)
        if e["upay"]:
            out.append({"system": "lal_kitab", "kind": kind, "planet": planet, "house": h,
                        "title_hi": e["title_hi"], "upay": e["upay"],
                        "source": f"Lal Kitab (Arun Sanhita), book p. {e['book_page']}"})
        if kind == "annual" and annual_house == natal_house:
            break
    return out


def report(chart: dict, age: int, lang: str = "en") -> dict:
    from ..annual import lal_kitab_varshphal
    vp = lal_kitab_varshphal(chart, age)
    planets = []
    for p, h in vp["natal_houses"].items():
        e = entry(p, h, lang)
        e["annual_house"] = vp["annual_houses"][p]
        e["annual"] = entry(p, vp["annual_houses"][p], lang)
        planets.append(e)
    # sleeping houses: houses with no planet (Lal Kitab treats empty houses as "asleep")
    occupied = set(vp["natal_houses"].values())
    return {"planets": planets, "varshphal": vp, "empty_houses": [h for h in range(1, 13) if h not in occupied],
            "rin": detect_rin(chart, lang), "quick": [quick_upay(p, lang) for p in vp["natal_houses"]],
            "rules": upay_rules(lang),
            "source": "Lal Kitab (Arun Sanhita), Hare Krishna Trust edition"}


# ---------------- remedies from the general chapters ----------------

@functools.lru_cache(maxsize=None)
def general() -> dict:
    try:
        p = DATA / "remedies.yaml"
        return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {"rules": [], "quick": {}, "planet": {}, "rin": {}}
    except Exception:
        return {"rules": [], "quick": {}, "planet": {}, "rin": {}}


def detect_rin(chart: dict, lang: str = "en") -> list[dict]:
    """Karmic debts (rin pitri) from the birth chart (book pp. 33-38)."""
    houses = {p: v["house"] for p, v in chart["planets"].items()}
    k = "hi" if lang == "hi" else "en"
    out = []
    for planet, r in general()["rin"].items():
        hits = [p for p in r["when"]["planets"] if houses.get(p) in r["when"]["houses"]]
        if hits:
            out.append({"rin_of": planet, "name": r["name"][k], "trigger": hits,
                        "houses": r["when"]["houses"], "sign": r["sign"][k], "upay": r["upay"][k],
                        "source": f"Lal Kitab (Arun Sanhita), book p. {r['page']}"})
    return out


def quick_upay(planet: str, lang: str = "en", afflicted: bool = False) -> dict | None:
    q = general()["quick"]
    key = "Mars_bad" if planet == "Mars" and afflicted else planet
    if key not in q:
        return None
    k = "hi" if lang == "hi" else "en"
    return {"planet": planet, "text": q[key][k], "source": "Lal Kitab (Arun Sanhita), book p. 44 – remedies that act within hours"}


def planet_help(planet: str, lang: str = "en") -> dict | None:
    p = general()["planet"].get(planet)
    if not p:
        return None
    return {"planet": planet, "text": p["hi" if lang == "hi" else "en"], "source": f"Lal Kitab (Arun Sanhita), book p. {p['page']}"}


def upay_rules(lang: str = "en") -> list[dict]:
    k = "hi" if lang == "hi" else "en"
    return [{"text": r[k], "source": f"Lal Kitab (Arun Sanhita), book p. {r['page']}"} for r in general()["rules"]]
