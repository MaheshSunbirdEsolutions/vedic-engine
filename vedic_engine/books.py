"""Full-text search over the books the app is built on (Q&A section).

The index (vedic_engine/book_text/<id>.json.gz) holds one entry per PDF page: the OCR text of
the scanned Hindi books, and the extracted text of the PVR book. It was built from the user's
own copies of the PDFs, for private study. The books are copyrighted: do not publish this index
or show long passages in a public app.

Search is BM25 over normalised word tokens. English questions are expanded with Hindi keywords
(LEXICON + i18n planet/sign/nakshatra names) so they also find pages in the Hindi books.
"""
from __future__ import annotations

import gzip
import json
import math
import pathlib
import re
import unicodedata
from collections import Counter
from functools import lru_cache

from . import i18n

ROOT = pathlib.Path(__file__).parent / "book_text"

BOOKS = {  # id -> metadata; printed page = pdf page + offset (None = only the PDF page is known)
    "pvr": {"title": "PVR Narasimha Rao – Lessons on Vedic Astrology, Vol. I", "title_hi": "पी.वी.आर. नरसिंह राव – वैदिक ज्योतिष के पाठ, भाग 1",
            "lang": "en", "offset": None, "images": None},
    "lalkitab": {"title": "Lal Kitab (Arun Sanhita)", "title_hi": "लाल किताब (अरुण संहिता)", "lang": "hi",
                 "offset": -21, "images": "lalkitab"},
    "bhrigu": {"title": "Bhrigu Samhita", "title_hi": "भृगु संहिता", "lang": "hi", "offset": 8, "images": "bhrigu"},
    "nakshatra": {"title": "R. P. Gaur – Nakshatra Jyotish", "title_hi": "आर. पी. गौड़ – नक्षत्र ज्योतिष", "lang": "hi",
                  "offset": None, "images": None},
    "tantra": {"title": "S. K. Dwivedi – Bharatiya Tantra Shastra", "title_hi": "श्या. का. द्विवेदी – भारतीय तंत्र शास्त्र",
               "lang": "hi", "offset": None, "images": None},
}

# English keyword -> extra search words (Hindi and English synonyms)
LEXICON = {
    "marriage": "विवाह शादी पत्नी पति स्त्री दाम्पत्य सप्तम कलत्र जीवनसाथी spouse wife husband marriage",
    "wife": "पत्नी स्त्री विवाह सप्तम", "husband": "पति विवाह सप्तम", "spouse": "पति पत्नी विवाह सप्तम",
    "love": "प्रेम विवाह पंचम सप्तम", "divorce": "तलाक विच्छेद अलगाव विवाह",
    "career": "कार्य नौकरी व्यवसाय व्यापार राज्य दशम कर्म पद career profession",
    "job": "नौकरी कार्य सेवा दशम", "business": "व्यापार व्यवसाय लाभ सप्तम दशम", "promotion": "पद उन्नति राज्य दशम",
    "money": "धन पैसा आय आमदनी लाभ द्वितीय एकादश wealth", "wealth": "धन संपत्ति लाभ द्वितीय एकादश",
    "income": "आय आमदनी लाभ एकादश", "debt": "ऋण कर्ज षष्ठ", "loan": "ऋण कर्ज",
    "children": "संतान पुत्र पुत्री बच्चे पंचम", "child": "संतान पुत्र पंचम", "son": "पुत्र संतान", "daughter": "पुत्री कन्या संतान",
    "pregnancy": "गर्भ संतान", "health": "स्वास्थ्य रोग बीमारी आयु शरीर", "disease": "रोग बीमारी व्याधि",
    "illness": "रोग बीमारी", "longevity": "आयु अष्टम मृत्यु", "death": "मृत्यु आयु मारक",
    "education": "विद्या शिक्षा पढ़ाई बुद्धि", "study": "विद्या शिक्षा पढ़ाई", "exam": "परीक्षा विद्या",
    "house": "मकान घर भवन चतुर्थ", "property": "भूमि मकान संपत्ति चतुर्थ", "land": "भूमि जमीन", "vehicle": "वाहन सवारी चतुर्थ",
    "mother": "माता मां चतुर्थ", "father": "पिता नवम दशम", "brother": "भाई भ्राता तृतीय", "sister": "बहन भगिनी",
    "foreign": "विदेश परदेस यात्रा द्वादश", "abroad": "विदेश परदेस", "travel": "यात्रा प्रवास",
    "enemy": "शत्रु षष्ठ", "court": "मुकदमा अदालत न्यायालय", "legal": "मुकदमा अदालत",
    "remedy": "उपाय टोटका दान मंत्र पूजा", "remedies": "उपाय टोटका दान मंत्र", "upay": "उपाय टोटका",
    "gem": "रत्न नग", "gemstone": "रत्न नग", "mantra": "मंत्र जप", "donation": "दान", "charity": "दान",
    "fasting": "व्रत उपवास", "worship": "पूजा उपासना आराधना", "temple": "मंदिर तीर्थ",
    "dosha": "दोष", "manglik": "मांगलिक मंगल दोष", "kaal": "कालसर्प", "sarp": "कालसर्प सर्प",
    "sade": "साढ़ेसाती शनि", "sati": "साढ़ेसाती", "dhaiya": "ढैया शनि", "pitra": "पितृ ऋण", "pitri": "पितृ ऋण",
    "debt of ancestors": "पितृ ऋण", "gand": "गंडमूल मूल गंडांत", "mool": "मूल गंडमूल", "gandanta": "गंडांत",
    "tantra": "तंत्र साधना", "sadhana": "साधना उपासना", "meditation": "ध्यान", "kundalini": "कुण्डलिनी चक्र",
    "nakshatra": "नक्षत्र", "dasha": "दशा महादशा अंतर्दशा", "transit": "गोचर", "yoga": "योग",
    "lagna": "लग्न", "ascendant": "लग्न", "moon sign": "चंद्र राशि", "aspect": "दृष्टि",
    "anger": "क्रोध", "mind": "मन", "peace": "शांति", "fame": "यश कीर्ति", "luck": "भाग्य", "fortune": "भाग्य नवम",
    "spiritual": "आध्यात्म धर्म मोक्ष", "accident": "दुर्घटना चोट", "theft": "चोरी", "loss": "हानि नुकसान व्यय",
}
HOUSE_WORDS_HI = ["प्रथम लग्न", "द्वितीय दूसरे धन", "तृतीय तीसरे", "चतुर्थ चौथे", "पंचम पाँचवें", "षष्ठ छठे",
                  "सप्तम सातवें", "अष्टम आठवें", "नवम नौवें", "दशम दसवें", "एकादश ग्यारहवें", "द्वादश बारहवें"]

_DEV = re.compile(r"[ऀ-ॿ]+|[a-z]+|\d+")
STOP = set("the a an of and or in on is are am be to for my me i what when will which how does do did it this that with "
           "at by from as have has can should would about any your you was were there their".split()) | set(
    "का की के को में है हैं से और या पर भी तो यह वह क्या कब कैसे मेरा मेरी मेरे मुझे होगा होगी होंगे हो कि एक जो नहीं ने".split())


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s.lower())
    return s.replace("़", "").replace("ँ", "ं").replace("ॉ", "ो")   # nukta, chandrabindu, candra o


def tokens(s: str) -> list[str]:
    return [t for t in _DEV.findall(norm(s)) if len(t) > 1 and t not in STOP]


@lru_cache(maxsize=1)
def _index():
    docs = []
    for bid in BOOKS:
        f = ROOT / f"{bid}.json.gz"
        if not f.exists():
            continue
        for pg in json.loads(gzip.decompress(f.read_bytes()).decode("utf-8")):
            tf = Counter(tokens(pg["t"]))
            if sum(tf.values()) < 15:
                continue
            docs.append({"book": bid, "p": pg["p"], "t": pg["t"], "tf": tf, "len": sum(tf.values())})
    df = Counter()
    for d in docs:
        df.update(d["tf"].keys())
    avg = sum(d["len"] for d in docs) / max(1, len(docs))
    return docs, df, avg


def status() -> dict:
    docs, _, _ = _index()
    c = Counter(d["book"] for d in docs)
    return {b: c.get(b, 0) for b in BOOKS}


def expand(question: str, extra: list[str] | None = None) -> list[str]:
    q = norm(question)
    words = tokens(q)
    out = list(words)
    for k, v in LEXICON.items():
        if re.search(rf"\b{re.escape(k)}\b", q):
            out += tokens(v)
    hi = i18n.load("hi")["terms"]
    for en, h in hi.items():        # planet, sign, nakshatra names -> Hindi
        if isinstance(h, str) and re.search(rf"\b{re.escape(en.lower())}\b", q):
            out += tokens(h)
    m = re.search(r"\b(1[0-2]|[1-9])(st|nd|rd|th)?\s+house\b|\bhouse\s+(1[0-2]|[1-9])\b", q)
    if m:
        out += tokens(HOUSE_WORDS_HI[int(m.group(1) or m.group(3)) - 1])
    out += [t for e in (extra or []) for t in tokens(e)]
    return out


def page_label(book: str, p: int, lang: str = "en") -> str:
    off = BOOKS[book]["offset"]
    hi = lang == "hi"
    if off is None or p + off < 1:
        return f"PDF पृ. {p}" if hi else f"PDF p. {p}"
    return (f"पृ. {p + off} (PDF {p})" if hi else f"p. {p + off} (PDF {p})")


def _snippet(text: str, terms: set[str], n: int = 32) -> str:
    """A short window of the page around the densest run of query words (OCR text, may contain errors)."""
    words = text.split()
    if not words:
        return ""
    hits = [i for i, w in enumerate(words) if any(t in norm(w) for t in terms)]
    centre = hits[len(hits) // 2] if hits else 0
    a = max(0, centre - n // 2)
    return ("… " if a else "") + " ".join(words[a:a + n]) + (" …" if a + n < len(words) else "")


def search(question: str, extra: list[str] | None = None, k: int = 6, books: list[str] | None = None,
           lang: str = "en", per_book: int = 2) -> list[dict]:
    docs, df, avg = _index()
    if not docs:
        return []
    q = Counter(expand(question, extra))
    n = len(docs)
    k1, b = 1.4, 0.75
    scored = []
    for d in docs:
        if books and d["book"] not in books:
            continue
        s = 0.0
        for t, qn in q.items():
            f = d["tf"].get(t)
            if not f:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * d["len"] / avg)) * (1 + 0.3 * (qn - 1))
        if s > 0:
            scored.append((s, d))
    scored.sort(key=lambda x: -x[0])
    out, used = [], Counter()
    terms = set(q)
    top = scored[0][0] if scored else 0
    for s, d in scored:
        if s < 0.4 * top:
            break
        if used[d["book"]] >= per_book:
            continue
        used[d["book"]] += 1
        meta = BOOKS[d["book"]]
        out.append({"book": d["book"], "title": meta["title_hi"] if lang == "hi" else meta["title"], "pdf_page": d["p"],
                    "page_label": page_label(d["book"], d["p"], lang), "score": round(s, 2),
                    "image": f"/books/{meta['images']}/p{d['p']:03d}.jpg" if meta["images"] else None,
                    "snippet": _snippet(d["t"], terms), "text": d["t"]})
        if len(out) >= k:
            break
    return out
