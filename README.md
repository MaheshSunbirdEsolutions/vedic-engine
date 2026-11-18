# Jyotish Lab / Vedic Engine

**To run it, see [RUN.md](RUN.md)** (Windows: double-click `start.bat`; Mac/Linux: `./start.sh`).

## Ask (questions & answers)

The **Ask** tab of a kundli answers a typed question (English or Hindi) about a life area, a planet, a house, a dosha, timing, remedies, tantra or temples.

* **Offline (default):** `vedic_engine/ask.py` recognises the life area / planet / house / dosha and the intent (when / remedy / tantra / temple), then assembles the answer from the engine's own analysis: life-area verdict with reasons, dasha windows that activate it, placement explanation, simple remedies. It lists the exact Lal Kitab and Bhrigu Samhita pages for the planets involved, plus the best-matching pages from a full-text search of all five books.
* **AI (optional):** add an Anthropic API key under *AI settings* (saved only in `data/ai.json`, or set `ANTHROPIC_API_KEY`). Claude then writes the answer from the chart facts, the offline findings and the matching book pages, citing the pages. If the call fails, the offline answer is shown with the error. Each question is a paid API call.
* **Book search index:** `vedic_engine/book_text/*.json.gz` (OCR of the scanned Hindi books with tesseract `hin`, and the PVR book's text), built with `tools/build_book_index.py`. OCR text has errors – the app shows only short snippets and links the page images where they exist. The books are copyrighted: keep the index for private study and do not publish it.

## Simple summary report

`POST /report/simple` (first tab under Reports) – the current dasha period, this year, the next six months, the top three issues and two short remedy plans (mantra, prayer, daana, Lal Kitab quick remedy, habit, temple, gem do/don't) in plain sentences, plus good start days and a health tip. It reuses the issues, year-wise and dasha analysis; nothing new is calculated.

## Structure

```
vedic-engine/
├─ vedic_engine/        Python engine (FastAPI): calculations, reports, rules, i18n, kundli store
├─ web/                 Next.js 16 app (React + TypeScript): Kundlis (save/open/search/export/import),
│                       kundli view (chart, dasha, interpretation, Sade Sati, 7 reports), Panchang, Matching
├─ data/kundlis.db      saved kundlis (SQLite, created on first save; back it up or use Export)
├─ tools/               extract_book_pages.py
├─ tests/               63 pytest tests
├─ start.bat / start.sh               engine + web app
└─ start-engine.bat / start-engine.sh engine only (API on :8000, classic UI)
```

The web app calls the engine through the Next.js rewrite `/engine/*` → `ENGINE_URL` (default `http://127.0.0.1:8000`, see `web/.env.example`).

Kundli API: `GET /kundlis?q=`, `POST /kundlis`, `GET|PUT|DELETE /kundlis/{id}`, `GET /kundlis/export`, `POST /kundlis/import`. A saved kundli stores only the birth data and settings; charts are always recomputed.

## Overview

A Python/FastAPI service that computes a Vedic (sidereal, Parashari) chart and the core MVP features:

| Feature | Module | Endpoint |
|---|---|---|
| Kundli: Lagna and 9 grahas with sign, degree, nakshatra/pada, whole-sign house, dignity, retrograde | `chart.py` | `POST /chart` |
| Divisional charts D1, D3, D7, D9, D10, D12 | `chart.py` | in `/chart` |
| Vimshottari dasha: MD / AD / PD, current period | `dasha.py` | `POST /dasha` |
| Panchang: tithi, vara, nakshatra, yoga, karana at sunrise with end times; sunrise/sunset; Rahu Kaal | `panchang.py` | `POST /panchang` |
| Manglik (from Lagna/Moon/Venus), Kaal Sarp | `doshas.py` | in `/chart` |
| Sade Sati: lifetime periods with phases, current status, Dhaiya | `doshas.py` | `POST /sade-sati` |
| Ashtakoota matching (36 gunas) | `matching.py` | `POST /match` |

| Interpretations: yogas, doshas, placements, with sources and remedy tags | `rules/` | `POST /interpret` |

Settings on every request: `ayanamsa` (`lahiri` default, `raman`, `krishnamurti`, `true_chitra`), `node` (`mean`/`true`), `year_days` (dasha year, default 365.25).

## Book page images

`tools/extract_book_pages.py` renders the Lal Kitab and Bhrigu Samhita pages that the reports link to, from your own PDFs, into `vedic_engine/static/books/`. They are not part of the code package. The `GET /books/status` endpoint reports how many pages are available.

## Run the web app (local testing)

**Windows:** double-click `start.bat`. **Mac/Linux:** run `./start.sh`.

The first run creates a virtual environment and installs dependencies, which takes about a minute. After that it opens **http://127.0.0.1:8000** in your browser. Requires Python 3.10 or newer (3.11 or 3.12 recommended on Windows, so that pyswisseph installs from a prebuilt wheel).

The web app ("Jyotish Lab") has these tabs:
- **Chart**: D1 and D9 in North or South Indian style, planet table (nakshatra, pada, house, dignity, D9, D10), houses.
- **Dasha**: Vimshottari MD, AD and PD; click to expand. The running period is highlighted.
- **Interpretation**: yogas, doshas and placements from the rules engine, with sources and remedy tags.
- **Sade Sati**: whether it is running now, Dhaiya, and all lifetime periods with phases.
- **Panchang**: any date and place; tithi, nakshatra, yoga and karana with end times; sunrise and sunset; Rahu Kaal.
- **Matching**: Ashtakoota for two charts, plus Manglik for both.
- **Raw JSON**: everything the API returned, for debugging.

Place search works offline (GeoNames: about 34,000 cities with population over 15,000, including their time zones). For a village that isn't listed, open **Advanced** and type the latitude, longitude and time zone. Charts you generate are saved in the browser's list for one-click re-runs.

## Run (API only)

```bash
pip install -r requirements.txt
uvicorn vedic_engine.api:app --reload      # docs at http://127.0.0.1:8000/docs
pytest -q
```

Example request:

```bash
curl -X POST localhost:8000/chart -H 'content-type: application/json' -d '{
  "datetime_local": "1990-05-14T06:30:00", "tz": "Asia/Kolkata", "lat": 28.6139, "lon": 77.2090 }'
```

Birth time is **local civil time + an IANA zone** (e.g. `Asia/Kolkata`). The engine converts it to UT using historical offsets, which matters for pre-1947 Indian births and for foreign births with DST. The app front-end must geocode the place to lat/lon and a time zone.

## Verified so far

- Lahiri ayanamsa at J2000 = 23.857° (23°51′25″) ✔
- Diwali 2024, New Delhi: Amavasya ends 18:17, Swati ends 03:31 (2 Nov), Priti ends 10:40, sunrise 06:33. These match published panchangs to within a minute ✔
- Kartik Purnima 2024 ends 02:58 on 16 Nov ✔
- June 2024 transits: Saturn in Aquarius, Jupiter in Taurus, Rahu in Pisces, Ketu in Virgo (sidereal) ✔
- Dasha timeline is contiguous, totals 120 years, and each AD starts with its MD lord ✔

## Next: parity with Jagannatha Hora

1. Generate 50–100 charts in Jagannatha Hora (Lahiri, mean node), covering a range of years, places and times near sign or nakshatra boundaries.
2. For each, copy `tests/fixture_template.json` to `tests/fixtures/<name>.json` and enter the longitudes and Mahadasha start dates.
3. Run `pytest`. Tolerances are 1 arcminute and 2 days by default.

## Reports (Reports tab → print / save as PDF, English or हिन्दी)

| Report | What it does | Sources |
|---|---|---|
| **Current issues & remedies** | Ranks the life areas under pressure *now* by combining running MD/AD/PD lords (functional nature, dusthana lordship, natal afflictions), transits (Sade Sati/Dhaiya, Rahu–Ketu over Moon/Lagna, Saturn's ashtakavarga bindus), the running **Tithi Pravesha** year chart (vara & hora lords, TP lagna lord, malefics in TP dusthanas) and the **Lal Kitab varshphal** of the running year. Each issue lists its evidence and remedies from four systems, side by side. Also lists karmic debts (rin) and the Lal Kitab upay rules. | PVR lessons; BPHS; Lal Kitab |
| **What's wrong** | Afflictions with a severity of 1–3: positions (debilitated, combust, dusthana, enemy sign, gandanta, weak Moon, planetary war), yutis (Guru-Chandal, Grahan, Angarak, Shrapit, Vish, Sun–Saturn, Mars–Saturn…), doshas (Manglik, Kaal Sarp, Pitra, Kemadruma). | Parashari/popular |
| **Full Kundli** | D1, D9, D10, D2, D4, D7, D12, D24, D60 charts; a table of all 16 Parashari vargas plus D6; chara karakas (8, incl. Rahu); arudha padas A1–A12 (PVR exceptions); SAV; MD/AD; yogas; afflictions. | BPHS, PVR |
| **Life areas** | Career, marriage, wealth, gains, children, property, education, foreign, health, parents, siblings. Each is read from its house, divisional chart, arudha, natural and chara karaka, with the dasha periods that activate it. | PVR lessons 6–27, 42 |
| **Varshphal** | The Tithi Pravesha chart for the chosen year (moment, validity, vara/hora lords) plus the Lal Kitab annual chart from the 120-year table. | PVR; Lal Kitab pp. 71–73 |
| **Lal Kitab** | House chart, annual chart, the book's own title for each placement, pakka ghar, empty houses, fast-acting upay, karmic debts with family remedies. Each placement also shows its Vedic view (bhav, sign, lordship) and the other systems' remedies. | Lal Kitab |
| **Nakshatra & remedy timing** | Janma / anujanma / trijanma and ghat nakshatra; gand-mool, gandanta, abhukta mool, Jwalamukhi and Vishkanya births with their shanti; tara bala table; health watch (body parts & tendencies) from the nakshatras of Lagna, Moon and the planets under pressure; **the best upcoming days to start remedies** (Guru/Ravi-Pushya, Amrit-siddhi, Sarvartha-siddhi, Ravi yoga) excluding bad taras, janma nakshatras, dagdha, ghat and Yamaghanta. | R. P. Gaur, *Nakshatra Jyotish* ch. 4, 8, 9 |

| **Life-long prediction** | Told as **your life story**: a prologue (rising sign, Moon, the lagna lord's thread, gifts and lessons, yogas and karmic knots), one chapter per mahadasha written in the past, present or future tense – what it is about, its tone, its brightest and hardest stretch, Sade Sati / Saturn and Jupiter returns and age-appropriate openings (marriage, career, children, home, studies, travel) in date order – and an epilogue; a clickable timeline of the chapters (`story.py`). Below it, the detailed analysis: overview (lagna, lagna lord, strongest/weakest planets, yogas, doshas); every mahadasha from birth to ~100 with age range, the houses and significations it activates, a rating with its reasons, the best and hardest antardasha and a table of all antardashas; milestones (Sade Sati periods, Saturn and Jupiter returns with ages); each life area's promise and timing windows. | BPHS, PVR (`predictions.py`) |
| **Year-wise prediction** | For any year: summary and rating, outlook for 8 life areas with reasons, the dasha periods in the year, Jupiter/Saturn/Rahu/Ketu transits with exact sign-change dates (from Moon and lagna, ashtakavarga bindus, aspects), Sade Sati/Dhaiya, month-by-month ratings (pratyantardasha + Sun/Mars/Venus/Mercury gochara), the Tithi Pravesha year chart and Lal Kitab annual houses; plus a clickable 12-year table. | BPHS, Phaladeepika (gochara), PVR (TP), Lal Kitab |
| **Temples & Tantra** | Temples ranked for *this* chart with the reason (doshas present, afflicted planets, running dasha lords, Sade Sati/Dhaiya, life areas needing care); a filterable directory of 24 temples/tirthas (Navagraha circuit, Mangalnath, Trimbakeshwar, Srikalahasti, Kukke, Gaya, Pehowa, Thirunallar, Shingnapur, Somnath, Baglamukhi Bankhandi …) with what is done there, when, and source links; next Ashlesha days for Ashlesha Bali; the tantra layer – Mahavidya for each planet, sadhana principles and the ten flowers of inner worship. | Web research Nov 2026 (`temples.py`); Dwivedi, *Bharatiya Tantra Shastra* ch. 8 (`tantra.py`) |

**Every report explains positions.** Each planet is described in plain words: which bhav it occupies (number, Sanskrit name and what the house covers), sign and dignity, which houses it rules for your ascendant and what that links, functional nature (yogakaraka / benefic / malefic / maraka), yuti, drishti given and received, combustion, retrogression and nakshatra (`placements.py`). The Full Kundli adds a 12-bhav table.

### Remedy systems (shown side by side)
For every planet that needs attention the app first works out the **approach**: *strengthen* a planet that is good for your ascendant but weak, or *pacify* one that rules difficult houses (and never advise its gem). Then it lists 12 systems, from free and safest to costliest (`remedies.full_set`):
Lal Kitab · beeja mantra with japa plan + Navagraha Stotra verse · stotra/path · daana (items, day, to whom) · vrata (count and method) · conduct · PVR deity · PVR arudha remedy · rudraksha · herb root (jadi) · gemstone with upratna, metal, finger and a chart-based *may suit / avoid / expert check* verdict · yantra & colours · **tantra (Mahavidya)** · **temples / tirtha**. The Issues and Nakshatra reports add the dates to begin.

- **Lal Kitab** – planet-in-house upay (verified sections), the "remedies that act within hours" table (p. 44), everyday planet help (p. 43), the 9 karmic debts with their collective family remedies (pp. 33–38), and rules (40–43 days, unbroken; Rahu ↔ Ketu; gau-grass).
- **PVR arudha remedy** (Lesson 9) – fast on the weekday of the lord of the house's arudha; worship the deity of the lord of the 2nd from that arudha.
- **PVR deity** – each planet's avatar and deity (Lesson 2 etc.).
- **Parashari** – navagraha beeja mantra with japa count, daana, weekday and practice.

### Source status
| Source | Status |
|---|---|
| PVR Narasimha Rao, *Lessons on Vedic Astrology* Vol. I | Techniques implemented (vargas, karakas, arudhas, argala, AL attitude, Tithi Pravesha, life-area method, arudha remedy) |
| Lal Kitab (Arun Sanhita) | Varshphal table (120 years, validated), 9 rin with family remedies, quick-acting upay, upay rules and the titles of all 108 placements done. Per-house upay written up and verified: Sun 2, Sun 7. **Every one of the 108 placements links to its exact book pages**, generated locally by `tools/extract_book_pages.py`, so the original text is always one click away. Add more paraphrased upay in `lalkitab/data/upay.yaml`. |
| Bhrigu Samhita (Hindi, 638 pp.) | Indexed: 1,059 of 1,296 lagna × planet × house readings split automatically from OCR (`vedic_engine/bhrigu_index.json`, `bhrigu.py`); the rest link to the planet's 4-page block. *Bhrigu Samhita* report + `/report/bhrigu`. Part 3 (planetary conjunctions, printed pp. 592–630) is mapped for the next phase. |

| R. P. Gaur, *Nakshatra Jyotish* (Manoj Pocket Books) | OCR'd (scan, 227 pp.). Implemented: gand-mool/gandanta/abhukta mool and their shanti timing (pp. 83–85), Vishkanya (p. 82) and Jwalamukhi (p. 178), tara bala, muhurta yogas and kuyogas for starting remedies (pp. 173–179), body parts & health tendencies for all 27 nakshatras (ch. 9). Note: the book's example on p. 179 prints Purva Bhadrapada where the 16th nakshatra is Uttara Bhadrapada; the app uses the correct count. Occupations per nakshatra (ch. 9) and KP sub-lords (ch. 7) are next. |
| Dr. S. K. Dwivedi 'Anand', *Bharatiya Tantra Shastra – Siddhanta aur Sadhana* (Chowkhamba, 814 pp.) | OCR'd. A philosophical (Trika/Shakta) work with no planet remedies and no abhichara. Used for the principles of sadhana (pp. 365–391), inner puja and the ten flowers (Tara Rahasya, p. 391), and the ten Mahavidyas (p. 388). The planet→Mahavidya pairing is labelled as tradition, not the book. Tantric beeja mantras are deliberately not given (guru diksha), and shatkarma aimed at others is excluded. |
| Temple directory | 24 entries researched Nov 2026 with source links per entry. Timings/fees change – the app tells users to confirm before travelling. |

All texts are our own paraphrases with page references, kept as `draft` until a Jyotishi reviews them. The books are copyrighted, so the app should not reproduce them verbatim.

## Languages (English / हिन्दी)

The web app has an **English | हिन्दी** switch in the header, and the choice is remembered. Everything is translated: the interface, all Jyotish terms (grahas, rashis, nakshatras, tithis, yogas, karanas, vara, kootas, yonis, ganas, nadis, dignities, Sade Sati phases), the chart drawings (सू चं मं बु गु शु श रा के), dates, and every interpretation text.

- Translations live in `vedic_engine/i18n/<lang>.yaml`, with sections `ui`, `terms`, `abbr` and `rules`. The API keeps canonical English data. The UI loads `GET /i18n/{lang}`, and `/interpret` takes `"lang": "hi"`.
- **To add a language** (e.g. Punjabi): copy `hi.yaml` to `pa.yaml`, translate it, and add `"pa"` to `LANGS` in `i18n/__init__.py` and to the `lang` values in `api.py`. `tests/test_i18n.py` fails if any UI key, term or rule is missing a translation.

## Rules engine (interpretations)

Interpretations are **data, not code**. They live in `vedic_engine/rules/data/*.yaml`, so a Jyotishi can add or correct rules without a developer.

```yaml
- id: gajakesari
  name: Gajakesari Yoga
  category: yoga              # yoga | dosha | placement
  nature: benefic             # benefic | challenging | mixed | neutral
  when: {planet_in_house: {planet: Jupiter, houses: [1, 4, 7, 10], from: Moon}}
  text: Jupiter is in an angle from the Moon. ...
  source: Phaladeepika – Yogas; BPHS – Lunar Yogas
  status: draft               # only "reviewed" rules ship when include_draft=false
  remedy_tags: [jupiter, moon]  # read by the future remedies module
```

**Condition building blocks.** Combine them with `all: [...]`, `any: [...]` and `not: {...}`.

| Primitive | Meaning | Example |
|---|---|---|
| `planet_in_house` | planet(s) in houses, counted from `Lagna` / `Moon` / any planet; `count: all` requires every listed planet | `{planet: [Mercury, Jupiter, Venus], houses: [6,7,8], from: Moon, count: all}` |
| `dignity` | planet's dignity is one of the listed values | `{planet: Mars, is: [own, exalted]}` |
| `conjunct` | all listed planets in the same sign | `{planets: [Sun, Mercury]}` |
| `lord_in_house` | lord of house N sits in the listed houses | `{lord_of: 6, houses: [6, 8, 12]}` |
| `lords_associated` | a lord of group `a` and a lord of group `b` are joined by conjunction, exchange or mutual aspect | `{a: [4,7,10], b: [1,5,9]}` |
| `owns_both` | one planet rules a house in `a` and one in `b` | `{a: [4,7,10], b: [5,9]}` |
| `empty_houses` / `occupied_houses` | house occupancy, with an `ignore` list | `{houses: [2,12], from: Moon, ignore: [Sun, Rahu, Ketu]}` |
| `exchange`, `neecha_bhanga`, `hemmed_by_nodes`, `vargottama` | the named classical tests | `{}` |
| `flag` | a dosha flag computed by the engine | `{name: manglik}` |
| `lagna_sign` | the ascendant is in the listed signs (0 = Aries) | `{in: [1, 6]}` |

Planet lists accept the shortcuts `benefics`, `malefics`, `seven` and `all`. Aspects follow Parashari graha drishti: 7th for every planet; Mars also 4th and 8th; Jupiter 5th and 9th; Saturn 3rd and 10th; Rahu and Ketu 5th and 9th.

**Starter rule set** (37 rules, all `draft`): the Pancha Mahapurusha yogas, the lunar yogas (Gajakesari, Sunapha, Anapha, Durudhura, Kemadruma with cancellation, Adhi, Chandra-Mangala), Budhaditya, Amala, Yogakaraka, Raja and Dhana yogas, the Viparita Raja yogas (Harsha, Sarala, Vimala), Parivartana, Neecha Bhanga, Vargottama, Manglik and Kaal Sarp dosha texts, and the ascendant lord in each of the 12 houses.

**Workflow:** the Jyotishi reviews each rule's condition and wording, adds the exact chapter and verse for the chosen translation, and sets `status: reviewed`. Production calls `/interpret` with `include_draft: false`.

**Remedies hook:** `/interpret` returns a combined `remedy_tags` list (for example `["kaal_sarp", "moon", "rahu"]`). The remedies module will map those tags to vetted remedy records.

## Known limitations (deliberate, to be reviewed with a Jyotishi)

- **Dosha cancellations** (Manglik parihara, Kaal Sarp exceptions, Nadi/Bhakoot exceptions) are not applied. They belong in the rules engine.
- **Vashya and Yoni** matching scores use simplified tables (marked `simplified: true` in the output). Replace them with the full matrices.
- **Rahu/Ketu dignity** returns `n/a`, because schools differ. Make it configurable.
- **Houses** are whole-sign only. Bhava chalit, Placidus and KP cusps are for later.
- Ephemeris files in `ephe/` cover 1800–2399 CE. Outside that range the library falls back to its lower-precision built-in model.

## Licensing (important)

`pysweph` (Swiss Ephemeris) is **AGPL-3.0** unless you buy the **Swiss Ephemeris Professional License** from Astrodienst. Under AGPL, a hosted closed-source app must publish its source code. Before launch, either buy the license or swap `ephemeris.py` for an MIT-licensed backend. All astronomy goes through that one file, and the parity tests will confirm any swap.
