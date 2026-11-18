"""Build the Q&A search index (vedic_engine/book_text/<id>.json.gz) from page texts.

    # scanned books: a folder of per-page OCR text files named p030.txt / 030.txt (PDF page number)
    python tools/build_book_index.py --book lalkitab --dir path/to/ocr_pages
    # text PDFs (PVR):
    python tools/build_book_index.py --book pvr --pdf path/to/book1-for-CD.pdf

OCR for the scanned Hindi books was made with:  tesseract page.png out -l hin --psm 4  (PDF page at 200-220 dpi).
The books are copyrighted: keep the index for private study; do not publish it.
"""
import argparse
import gzip
import json
import pathlib
import re

OUT = pathlib.Path(__file__).resolve().parent.parent / "vedic_engine" / "book_text"


def clean(t: str) -> str:
    lines = []
    for ln in t.splitlines():
        ln = ln.strip()
        letters = len(re.findall(r"[ऀ-ॿA-Za-z]", ln))
        if len(ln) < 3 or letters < 0.5 * len(ln.replace(" ", "")):
            continue
        lines.append(re.sub(r"\s+", " ", ln))
    return "\n".join(lines)


def from_dirs(dirs):
    pages = {}
    for d in dirs:
        for f in sorted(pathlib.Path(d).glob("*.txt")):
            m = re.search(r"(\d+)", f.stem)
            if m and int(m.group(1)) not in pages:
                pages[int(m.group(1))] = clean(f.read_text(encoding="utf-8", errors="ignore"))
    return [{"p": p, "t": t} for p, t in sorted(pages.items()) if t]


def from_pdf(pdf):
    import pymupdf
    doc = pymupdf.open(pdf)
    return [{"p": i + 1, "t": clean(pg.get_text())} for i, pg in enumerate(doc) if pg.get_text().strip()]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True, choices=["pvr", "lalkitab", "bhrigu", "nakshatra", "tantra"])
    ap.add_argument("--dir", action="append", default=[])
    ap.add_argument("--pdf")
    a = ap.parse_args()
    pages = from_pdf(a.pdf) if a.pdf else from_dirs(a.dir)
    OUT.mkdir(exist_ok=True)
    (OUT / f"{a.book}.json.gz").write_bytes(gzip.compress(json.dumps(pages, ensure_ascii=False).encode("utf-8")))
    print(a.book, len(pages), "pages")
