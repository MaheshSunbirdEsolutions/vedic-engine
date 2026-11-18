"""Render the book pages the app links to, from YOUR copies of the PDFs, into the local web app.

    python tools/extract_book_pages.py --lalkitab "path/to/006_Arun_Sanhita_Lal_Kitab_Hare_Krishna_Trashta.pdf" \
                                       --bhrigu   "path/to/bhrigu-samhita-hindi1.pdf"

Writes JPEGs to vedic_engine/static/books/lalkitab/p###.jpg and .../bhrigu/p###.jpg
(### = PDF page number). Pages stay on your machine; they are not part of the code package.
The books are copyrighted – use the images for personal study / review, not in a public app.
"""
import argparse
import pathlib

import pymupdf as fitz  # PyMuPDF

ROOT = pathlib.Path(__file__).resolve().parent.parent / "vedic_engine" / "static" / "books"
RANGES = {"lalkitab": range(30, 281), "bhrigu": range(70, 601)}   # PDF pages used by the app
WIDTH = {"lalkitab": 1100, "bhrigu": 1000}


def render(pdf: str, kind: str):
    out = ROOT / kind
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    n = 0
    for p in RANGES[kind]:
        if p > doc.page_count:
            break
        target = out / f"p{p:03d}.jpg"
        if target.exists():
            continue
        page = doc[p - 1]
        zoom = WIDTH[kind] / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
        pix.save(str(target), jpg_quality=72)
        n += 1
    print(f"{kind}: {n} new pages -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lalkitab")
    ap.add_argument("--bhrigu")
    a = ap.parse_args()
    if not (a.lalkitab or a.bhrigu):
        ap.error("give --lalkitab and/or --bhrigu")
    if a.lalkitab:
        render(a.lalkitab, "lalkitab")
    if a.bhrigu:
        render(a.bhrigu, "bhrigu")
