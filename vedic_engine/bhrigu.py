"""Bhrigu Samhita (Hindi edition, 638 pp.): lagna-specific planet-in-house readings.

bhrigu_index.json was built by OCR from the scanned book: for each lagna (12) x planet (9) x
house (12) it keeps the OCR'd Hindi reading and the PDF page it is on. About 82% of the 1296
readings were split automatically; for the rest the app points to the planet's 4-page block.
OCR text can contain errors – the page image (tools/extract_book_pages.py) is the reference.
Printed page = PDF page + 8.
"""
from __future__ import annotations

import functools
import json
import pathlib

from .constants import SIGNS

INDEX = pathlib.Path(__file__).parent / "bhrigu_index.json"
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SUN_PRINTED = {"Taurus": 129, "Gemini": 172, "Cancer": 215, "Leo": 258, "Virgo": 300, "Libra": 342,
               "Scorpio": 384, "Sagittarius": 427, "Capricorn": 469, "Aquarius": 511, "Pisces": 554}
YUTI_PAGES = {"two": 593, "three": 598, "four": 607, "five": 616, "six": 621}  # printed pages, Part 3


@functools.lru_cache(maxsize=None)
def index() -> dict:
    return json.loads(INDEX.read_text(encoding="utf-8"))


def block_pdf_pages(lagna: str, planet: str) -> list[int]:
    base = 81 if lagna == "Aries" else SUN_PRINTED[lagna] - 8
    s = base + 4 * PLANETS.index(planet)
    return list(range(s, s + 5))


def reading(lagna: str, planet: str, house: int) -> dict:
    e = index().get(lagna, {}).get(planet, {}).get(str(house))
    pages = block_pdf_pages(lagna, planet)
    return {
        "lagna": lagna, "planet": planet, "house": house,
        "text_hi": e["text"] if e else None,
        "pdf_page": e["pdf_page"] if e else pages[0],
        "printed_page": (e["pdf_page"] if e else pages[0]) + 8,
        "block_pdf_pages": pages,
        "found": bool(e),
    }


def report(chart: dict) -> dict:
    lagna = chart["lagna"]["sign"]
    items = [reading(lagna, p, chart["planets"][p]["house"]) for p in PLANETS]
    return {"lagna": lagna, "readings": items,
            "coverage": sum(len(v) for L in index().values() for v in L.values()),
            "source": "Bhrigu Samhita (Hindi), Part 2 – lagna-wise results of planets in the 12 houses",
            "note": "Hindi text is from OCR of the scanned book and may contain errors; open the page image to read the original."}
