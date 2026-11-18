"""HTTP API.  Run:  uvicorn vedic_engine.api:app --reload"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

import pathlib

import geonamescache
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import doshas, i18n, matching, predictions as _pred, nakshatra as _nak, placements as _pl, remedies as _rem, tantra as _tantra, temples as _tmp
from .chart import build_chart
from .dasha import vimshottari
from .ephemeris import Settings
from .panchang import panchang
from .rules import facts_from_chart, interpret

app = FastAPI(title="Vedic Engine", version="1.1.0")

from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
import os as _os  # noqa: E402
app.add_middleware(CORSMiddleware, allow_origins=_os.environ.get("JYOTISH_CORS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
                   allow_methods=["*"], allow_headers=["*"])


class SettingsIn(BaseModel):
    ayanamsa: Literal["lahiri", "raman", "krishnamurti", "true_chitra"] = "lahiri"
    node: Literal["mean", "true"] = "mean"
    year_days: float = 365.25

    def to(self) -> Settings:
        return Settings(**self.model_dump())


class BirthIn(BaseModel):
    datetime_local: datetime = Field(..., examples=["1990-05-14T06:30:00"])
    tz: str = Field(..., examples=["Asia/Kolkata"])
    lat: float
    lon: float
    settings: SettingsIn = SettingsIn()


@app.post("/chart")
def chart(b: BirthIn):
    c = build_chart(b.datetime_local.replace(tzinfo=None), b.tz, b.lat, b.lon, b.settings.to())
    c["doshas"] = {"manglik": doshas.manglik(c), "kaal_sarp": doshas.kaal_sarp(c)}
    return c


class DashaIn(BirthIn):
    levels: int = Field(3, ge=1, le=3)
    at: datetime | None = None


@app.post("/dasha")
def dasha(b: DashaIn):
    at = (b.at or datetime.now()).replace(tzinfo=None)
    return vimshottari(b.datetime_local.replace(tzinfo=None), b.tz, b.settings.to(), b.levels, at)


@app.post("/sade-sati")
def sade_sati(b: BirthIn):
    s = b.settings.to()
    c = build_chart(b.datetime_local.replace(tzinfo=None), b.tz, b.lat, b.lon, s)
    moon_sign = c["planets"]["Moon"]["sign_index"] - 1
    return {
        "moon_sign": c["planets"]["Moon"]["sign"],
        "now": doshas.sade_sati_status(moon_sign, datetime.now(), b.tz, s),
        "periods": doshas.sade_sati_periods(b.datetime_local.replace(tzinfo=None), b.tz, moon_sign, 100, s),
    }


class PanchangIn(BaseModel):
    day: date
    tz: str
    lat: float
    lon: float
    settings: SettingsIn = SettingsIn()


@app.post("/panchang")
def panchang_ep(p: PanchangIn):
    return panchang(p.day, p.tz, p.lat, p.lon, p.settings.to())


class MatchIn(BaseModel):
    groom: BirthIn
    bride: BirthIn


@app.post("/match")
def match(m: MatchIn):
    g = build_chart(m.groom.datetime_local.replace(tzinfo=None), m.groom.tz, m.groom.lat, m.groom.lon, m.groom.settings.to())
    b = build_chart(m.bride.datetime_local.replace(tzinfo=None), m.bride.tz, m.bride.lat, m.bride.lon, m.bride.settings.to())
    res = matching.ashtakoota(g["planets"]["Moon"]["longitude"], b["planets"]["Moon"]["longitude"])
    res["manglik"] = {"groom": doshas.manglik(g)["present"], "bride": doshas.manglik(b)["present"]}
    return res


class InterpretIn(BirthIn):
    include_draft: bool = True  # set False in production: only Jyotishi-reviewed rules
    lang: Literal["en", "hi"] = "en"


@app.post("/interpret")
def interpret_ep(b: InterpretIn):
    c = chart(b)
    hits = interpret(facts_from_chart(c), include_draft=b.include_draft, lang=b.lang)
    return {
        "lagna": c["lagna"]["sign"], "moon_sign": c["planets"]["Moon"]["sign"],
        "moon_nakshatra": c["planets"]["Moon"]["nakshatra"]["name"],
        "findings": hits,
        "remedy_tags": sorted({t for h in hits for t in h["remedy_tags"]}),
    }


@app.get("/i18n/{lang}")
def i18n_bundle(lang: Literal["en", "hi"]):
    """UI strings, term map and chart abbreviations for the web app."""
    d = i18n.load(lang)
    return {"lang": lang, "ui": d["ui"], "terms": d["terms"], "abbr": d["abbr"]}


@app.get("/health")
def health():
    return {"ok": True}


# ---------- reports ----------
from . import afflictions as _aff, annual as _annual, ashtakavarga as _av, issues as _issues, jaimini as _jai, lifeareas as _life, lalkitab as _lk  # noqa: E402
from .constants import SIGNS as _SIGNS  # noqa: E402


class ReportIn(BirthIn):
    lang: Literal["en", "hi"] = "en"
    year: int | None = None
    at: datetime | None = None


def _birth(b):
    return b.datetime_local.replace(tzinfo=None)


def _remedy_plan(c: dict, affl: list[dict], age: int, lang: str) -> list[dict]:
    """Full remedy set for every planet named in an affliction, worst first."""
    vp = _annual.lal_kitab_varshphal(c, max(1, min(120, age)))
    worst: dict[str, dict] = {}
    for a in affl:
        for p in a["planets"]:
            if p in c["planets"] and (p not in worst or a["severity"] > worst[p]["severity"]):
                worst[p] = {"severity": a["severity"], "reasons": []}
            if p in worst:
                worst[p]["reasons"].append(_aff.describe(a, lang))
    out = []
    for p, w in sorted(worst.items(), key=lambda x: -x[1]["severity"]):
        fs = _rem.full_set(c, p, lang, lk_house=vp["natal_houses"][p], lk_annual_house=vp["annual_houses"][p],
                           house_for_arudha=c["planets"][p]["house"])
        out.append({**fs, "severity": w["severity"], "reasons": list(dict.fromkeys(w["reasons"]))})
    return out


@app.post("/report/full")
def report_full(b: ReportIn):
    s = b.settings.to()
    c = chart(b)
    d = vimshottari(_birth(b), b.tz, s, levels=2, at=(b.at or datetime.now()).replace(tzinfo=None))
    av = _av.from_chart(c)
    affl = _aff.analyse(c, {k: v["present"] for k, v in c["doshas"].items()})
    now = (b.at or datetime.now()).replace(tzinfo=None)
    return {
        "chart": c, "dasha": d, "jaimini": _jai.summary(c),
        "placements": _pl.all_planets(c, b.lang), "bhavas": _pl.houses(c, b.lang),
        "nakshatra_doshas": _nak.birth_doshas(c, _birth(b), b.tz, b.lat, b.lon, s, b.lang),
        "remedy_plan": _remedy_plan(c, affl, _annual.age_running(_birth(b), now), b.lang),
        "ashtakavarga": {"bav": av["bav"], "sav": av["sav"], "signs": _SIGNS},
        "afflictions": [{**a, "text": _aff.describe(a, b.lang)} for a in affl],
        "interpretation": interpret(facts_from_chart(c), lang=b.lang),
    }


@app.post("/report/life-areas")
def report_life(b: ReportIn):
    s = b.settings.to()
    c = build_chart(_birth(b), b.tz, b.lat, b.lon, s)
    now = (b.at or datetime.now()).replace(tzinfo=None)
    d = vimshottari(_birth(b), b.tz, s, levels=2, at=now)
    areas = _life.all_areas(c, d, b.lang, now)
    vp = _annual.lal_kitab_varshphal(c, max(1, min(120, _annual.age_running(_birth(b), now))))
    for a in areas:
        a["house_info"] = _pl.house_info(a["house"], b.lang)
        a["lord_placement"] = _pl.explain(c, a["lord"], b.lang)
        a["occupants"] = [_pl.explain(c, p, b.lang) for p, v in c["planets"].items() if v["house"] == a["house"]]
        if a["verdict_key"] != "strong":
            a["remedy"] = _rem.full_set(c, a["lord"], b.lang, lk_house=vp["natal_houses"][a["lord"]],
                                        lk_annual_house=vp["annual_houses"][a["lord"]], house_for_arudha=a["house"])
    return {"areas": areas, "dasha_now": d["current"]}


@app.post("/report/varshphal")
def report_varshphal(b: ReportIn):
    s = b.settings.to()
    now = (b.at or datetime.now()).replace(tzinfo=None)
    year = b.year or now.year
    c = build_chart(_birth(b), b.tz, b.lat, b.lon, s)
    tp = _annual.tithi_pravesha(_birth(b), b.tz, b.lat, b.lon, year, s=s)
    age = year - _birth(b).year + 1   # Lal Kitab year of life that starts on the birthday in `year`
    lk = _lk.report(c, max(1, min(120, age)), b.lang)
    tp["placements"] = _pl.all_planets(tp["chart"], b.lang)
    _add_vedic(c, lk, b.lang, annual=True)
    return {"year": year, "tithi_pravesha": tp, "lal_kitab": lk, "age": age,
            "bhav_names": {h: _pl.house_info(h, b.lang) for h in range(1, 13)}}


def _add_vedic(c: dict, lk: dict, lang: str, annual: bool = False) -> None:
    """Attach the Vedic placement explanation and the other systems' remedies to each Lal Kitab row."""
    for e in lk["planets"]:
        p = e["planet"]
        e["vedic"] = _pl.explain(c, p, lang)
        e["house_info"] = _pl.house_info(e["house"], lang)
        if annual:
            e["annual"]["house_info"] = _pl.house_info(e["annual"]["house"], lang)
        e["other_remedies"] = _rem.full_set(c, p, lang, lk_house=e["house"],
                                            lk_annual_house=e.get("annual_house"), house_for_arudha=c["planets"][p]["house"])


@app.post("/report/lal-kitab")
def report_lal_kitab(b: ReportIn):
    s = b.settings.to()
    now = (b.at or datetime.now()).replace(tzinfo=None)
    c = build_chart(_birth(b), b.tz, b.lat, b.lon, s)
    age = _annual.age_running(_birth(b), now)
    lk = _lk.report(c, age, b.lang)
    _add_vedic(c, lk, b.lang)
    return {"age": age, **lk, "bhav_names": {h: _pl.house_info(h, b.lang) for h in range(1, 13)}}


@app.post("/report/issues")
def report_issues(b: ReportIn):
    now = (b.at or datetime.now()).replace(tzinfo=None)
    s = b.settings.to()
    r = _issues.report(_birth(b), b.tz, b.lat, b.lon, now=now, lang=b.lang, s=s, lk_upay=_lk.upay_for)
    c = build_chart(_birth(b), b.tz, b.lat, b.lon, s)
    keys = list(dict.fromkeys(i["key_planet"] for i in r["issues"][:4]))
    r["remedy_days"] = _nak.remedy_days(c, b.tz, b.lat, b.lon, s, now.date(), 60, keys, b.lang, limit=8)
    r["remedy_days_note"] = _nak.days_note(b.lang)
    r["nakshatra_doshas"] = _nak.birth_doshas(c, _birth(b), b.tz, b.lat, b.lon, s, b.lang)
    r["health_watch"] = _nak.health_for(c, b.lang, keys)
    return r


@app.post("/report/lifelong")
def report_lifelong(b: ReportIn):
    s = b.settings.to()
    now = (b.at or datetime.now()).replace(tzinfo=None)
    c = chart(b)
    birth = _birth(b)
    d = vimshottari(birth, b.tz, s, levels=2, at=now)
    affl = _aff.analyse(c, {k: v["present"] for k, v in c["doshas"].items()})
    moon_sign = c["planets"]["Moon"]["sign_index"] - 1
    r = _pred.lifelong(c, d, birth, b.tz, s, b.lang,
                       life_areas=_life.all_areas(c, d, b.lang, now),
                       interpretation=interpret(facts_from_chart(c), lang=b.lang),
                       sade_sati=doshas.sade_sati_periods(birth, b.tz, moon_sign, 100, s),
                       afflictions=[{**a, "text": _aff.describe(a, b.lang)} for a in affl], now=now)
    from . import story as _story
    r["story"] = _story.tell(c, r, birth, b.lang, now)
    return r


@app.post("/report/yearly")
def report_yearly(b: ReportIn):
    s = b.settings.to()
    now = (b.at or datetime.now()).replace(tzinfo=None)
    year = b.year or now.year
    c = chart(b)
    birth = _birth(b)
    d3 = vimshottari(birth, b.tz, s, levels=3, at=now)
    moon_sign = c["planets"]["Moon"]["sign_index"] - 1
    ss = lambda at: doshas.sade_sati_status(moon_sign, at, b.tz, s)  # noqa: E731
    try:
        tp = _annual.tithi_pravesha(birth, b.tz, b.lat, b.lon, year, s=s)
        tp_out = {k: tp[k] for k in ("moment", "valid_until", "vara_lord", "hora_lord")}
        tp_out["lagna"] = tp["chart"]["lagna"]["sign"]
        tp_out["vara_nature"] = _pl.explain(c, tp["vara_lord"], b.lang)["nature"]
        tp_out["hora_nature"] = _pl.explain(c, tp["hora_lord"], b.lang)["nature"]
    except Exception:  # noqa: BLE001
        tp_out = None
    age = year - birth.year + 1
    vp = _annual.lal_kitab_varshphal(c, max(1, min(120, age)))
    r = _pred.yearly(c, d3, birth, b.tz, b.lat, b.lon, s, year, b.lang, ss, tp_out,
                     {"age": age, "houses": vp["annual_houses"]})
    r["years"] = _pred.years_table(c, d3, birth, b.tz, s, now.year - 1, 12, b.lang, ss)
    return r


@app.post("/report/simple")
def report_simple(b: ReportIn):
    """Plain-language summary of the current period and the remedies to follow."""
    from . import simple as _simple
    s = b.settings.to()
    now = (b.at or datetime.now()).replace(tzinfo=None)
    b_now = b.model_copy(update={"year": now.year, "at": now})
    iss = report_issues(b_now)
    yr = report_yearly(b_now)
    c = chart(b)
    d3 = vimshottari(_birth(b), b.tz, s, levels=3, at=now)
    md, ad, nxt = _simple._current(d3, now)
    r_now = _pred.period_reading(c, md["lord"], ad["lord"], b.lang) if md else None
    r_next = _pred.period_reading(c, nxt[0]["lord"], nxt[1]["lord"], b.lang) if nxt else None
    months = [{**m, "label": f"{m['month']} {now.year}"} for m in yr["months"]][now.month - 1:]
    if len(months) < 6:
        nm = _pred._month_table(c, d3, now.year + 1, b.tz, s, b.lang)
        months += [{**m, "label": f"{m['month']} {now.year + 1}"} for m in nm]
    months = [{k: m[k] for k in ("label", "rating", "rating_label")} for m in months[:6]]
    return _simple.summary(c, d3, iss, yr, months, r_now, r_next, b.lang, now)


@app.post("/report/tirtha")
def report_tirtha(b: ReportIn):
    """Temples & tantra: temples ranked for this chart, the full directory, and the tantra layer."""
    s = b.settings.to()
    now = (b.at or datetime.now()).replace(tzinfo=None)
    c = chart(b)
    affl = _aff.analyse(c, {k: v["present"] for k, v in c["doshas"].items()})
    ss = doshas.sade_sati_status(c["planets"]["Moon"]["sign_index"] - 1, now, b.tz, s)
    d = vimshottari(_birth(b), b.tz, s, levels=2, at=now)
    cur = list(d.get("current") or [])[:2]
    life = _life.all_areas(c, d, b.lang, now)
    weak = [{"area": a["area"], "title": a["title"]} for a in life if a["verdict_key"] == "needs care"]
    planets = list(dict.fromkeys(cur + [p for a in affl if a["severity"] >= 2 for p in a["planets"] if p in c["planets"]]))
    ashlesha = _nak.next_days("Ashlesha", b.tz, b.lat, b.lon, s, now.date(), 3)
    return {
        "suggested": _tmp.suggest(c, affl, b.lang, ss, weak, cur),
        "directory": _tmp.directory(b.lang),
        "tantra": _tantra.report(planets, b.lang),
        "planets_considered": planets, "weak_areas": weak,
        "next_ashlesha": ashlesha,
        "note": ("समय, शुल्क व नियम बदलते रहते हैं – यात्रा से पहले मंदिर से पुष्टि करें। कोई उपाय परिणाम की गारंटी नहीं देता।"
                 if b.lang == "hi" else
                 "Timings, fees and rules change – confirm with the temple before travelling. No remedy guarantees an outcome."),
    }


@app.post("/report/nakshatra")
def report_nakshatra(b: ReportIn):
    s = b.settings.to()
    now = (b.at or datetime.now()).replace(tzinfo=None)
    c = chart(b)
    affl = _aff.analyse(c, {k: v["present"] for k, v in c["doshas"].items()})
    d = vimshottari(_birth(b), b.tz, s, levels=2, at=now)
    cur = list(d.get("current") or [])[:2]
    planets = list(dict.fromkeys(cur + [p for a in affl if a["severity"] >= 2 for p in a["planets"] if p in c["planets"]]))
    r = _nak.report(c, _birth(b), b.tz, b.lat, b.lon, s, b.lang, now.date(), planets)
    r["planets_considered"] = planets
    r["placements"] = [_pl.explain(c, p, b.lang) for p in planets]
    return r


@app.post("/report/bhrigu")
def report_bhrigu(b: ReportIn):
    from . import bhrigu
    c = build_chart(_birth(b), b.tz, b.lat, b.lon, b.settings.to())
    return bhrigu.report(c)


# ---------- questions & answers ----------
class AskIn(ReportIn):
    question: str = Field(..., min_length=2, max_length=1000)
    use_ai: bool = True


class AiKeyIn(BaseModel):
    api_key: str = ""
    model: str | None = None


@app.get("/ask/status")
def ask_status():
    from . import ask as _ask
    return _ask.ai_status()


@app.post("/ask/key")
def ask_key(k: AiKeyIn):
    """Save (or clear, with an empty key) the Anthropic API key in data/ai.json on this computer."""
    from . import ask as _ask
    return _ask.save_key(k.api_key, k.model)


@app.post("/ask")
def ask_question(b: AskIn):
    from . import ask as _ask
    s = b.settings.to()
    now = (b.at or datetime.now()).replace(tzinfo=None)
    c = build_chart(_birth(b), b.tz, b.lat, b.lon, s)
    d = vimshottari(_birth(b), b.tz, s, levels=2, at=now)
    age = now.year - _birth(b).year + 1
    vp = _annual.lal_kitab_varshphal(c, max(1, min(120, age)))
    moon_sign = c["planets"]["Moon"]["sign_index"] - 1
    return _ask.ask(b.question, c, d, _life.all_areas(c, d, b.lang, now), b.lang, now, b.tz, s,
                    vp["natal_houses"], doshas.sade_sati_status(moon_sign, now, b.tz, s),
                    _nak.birth_doshas(c, _birth(b), b.tz, b.lat, b.lon, s, b.lang), use_ai=b.use_ai)


@app.get("/books/status")
def books_status():
    """Which book page images have been generated locally by tools/extract_book_pages.py."""
    root = pathlib.Path(__file__).parent / "static" / "books"
    return {k: len(list((root / k).glob("*.jpg"))) if (root / k).exists() else 0 for k in ("lalkitab", "bhrigu")}


# ---------- saved kundlis ----------
from fastapi import HTTPException  # noqa: E402
from . import store  # noqa: E402


class KundliIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    gender: Literal["male", "female", "other", ""] | None = ""
    datetime_local: datetime
    tz: str
    lat: float
    lon: float
    place: str | None = ""
    settings: SettingsIn = SettingsIn()
    notes: str | None = ""
    tags: str | None = ""

    def record(self) -> dict:
        d = self.model_dump()
        d["datetime_local"] = self.datetime_local.replace(tzinfo=None).isoformat(timespec="seconds")
        return d


@app.get("/kundlis")
def kundlis_list(q: str = ""):
    return store.list_kundlis(q)


@app.post("/kundlis", status_code=201)
def kundlis_create(k: KundliIn):
    return store.create(k.record())


@app.get("/kundlis/export")
def kundlis_export():
    return {"format": "jyotish-lab-kundlis", "version": 1, "kundlis": store.list_kundlis(limit=100000)}


@app.post("/kundlis/import")
def kundlis_import(payload: dict):
    items = payload.get("kundlis", payload if isinstance(payload, list) else [])
    return {"imported": store.import_many(items)}


@app.get("/kundlis/{kid}")
def kundlis_get(kid: str):
    k = store.get(kid)
    if not k:
        raise HTTPException(404, "kundli not found")
    return k


@app.put("/kundlis/{kid}")
def kundlis_update(kid: str, k: KundliIn):
    r = store.update(kid, k.record())
    if not r:
        raise HTTPException(404, "kundli not found")
    return r


@app.delete("/kundlis/{kid}")
def kundlis_delete(kid: str):
    if not store.delete(kid):
        raise HTTPException(404, "kundli not found")
    return {"deleted": kid}


# ---------- offline place search (GeoNames, cities with population > 15,000) ----------
_PLACES: list[dict] | None = None


def _places() -> list[dict]:
    global _PLACES
    if _PLACES is None:
        gc = geonamescache.GeonamesCache()
        countries = {c["iso"]: c["name"] for c in gc.get_countries().values()}
        _PLACES = sorted(
            ({"name": c["name"], "country": countries.get(c["countrycode"], c["countrycode"]),
              "lat": c["latitude"], "lon": c["longitude"], "tz": c["timezone"],
              "population": c["population"],
              "_keys": {c["name"].lower(), *(a.lower() for a in c.get("alternatenames", []) if a.isascii())}}
             for c in gc.get_cities().values()),
            key=lambda x: -x["population"])
    return _PLACES


@app.get("/places")
def places(q: str, limit: int = 10):
    q = q.strip().lower()
    if len(q) < 2:
        return []
    # tiers: 0 name exact, 1 name prefix, 2 alternate-name exact, 3 alternate-name prefix
    tiers: list[list[dict]] = [[], [], [], []]
    for p in _places():  # already sorted by population
        name = p["name"].lower()
        if name == q:
            tiers[0].append(p)
        elif name.startswith(q):
            tiers[1].append(p)
        elif q in p["_keys"]:
            tiers[2].append(p)
        elif any(k.startswith(q) for k in p["_keys"]):
            tiers[3].append(p)
    ranked = [p for t in tiers for p in t][:limit]
    return [{k: v for k, v in p.items() if k != "_keys"} for p in ranked]


# The web UI (must be mounted last so API routes take priority)
app.mount("/", StaticFiles(directory=pathlib.Path(__file__).parent / "static", html=True), name="ui")
