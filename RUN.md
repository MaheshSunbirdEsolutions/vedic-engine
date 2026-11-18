# How to run Jyotish Lab on your computer

## 1. One-time setup

1. **Install Node.js 20 or newer** (LTS) from https://nodejs.org. This is for the web app.
2. **Install Python 3.11 or 3.12**
   - Windows: download it from https://www.python.org/downloads/ and tick **"Add Python to PATH"** during installation.
   - Mac: `brew install python@3.12`, or use the python.org installer.
3. **Unzip** `vedic-engine.zip` anywhere, for example `C:\jyotish\vedic-engine` or `~/jyotish/vedic-engine`.

## 2. Start the app

| Windows | Mac / Linux |
|---|---|
| Double-click **`start.bat`** | Open Terminal in the folder and run `./start.sh` |

This starts two programs:
- the **Vedic Engine** (Python, http://127.0.0.1:8000), which does the calculations and stores saved kundlis in `data/kundlis.db`, and
- the **Jyotish Lab web app** (Next.js, **http://localhost:3000**), which opens in your browser.

The first start installs everything (Python libraries plus web packages and a build), which takes 3–5 minutes. Later starts take under a minute.

To stop, close both terminal windows (or press `Ctrl+C`).

**Saving and opening kundlis:** fill in *New kundli* → **Generate kundli** → **Save kundli**. Saved kundlis appear on the home page, where you can search them and **Open**, **Delete**, **Edit details**, **Export all (JSON)** for backup, or **Import JSON**. The *Matching* page can pick both people from your saved kundlis.

`start-engine.bat` / `./start-engine.sh` starts only the engine. The original single-page UI is still at http://127.0.0.1:8000.

**Manual start**, if you prefer typing the commands:

```bash
cd vedic-engine
python -m venv .venv
# Windows:  .venv\Scripts\activate        Mac/Linux:  source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn vedic_engine.api:app --port 8000
```

Then open http://127.0.0.1:8000.

## 3. (Optional) Add the book pages – Lal Kitab and Bhrigu Samhita

The reports link each placement to the exact page of the books. The page images are generated from **your own PDF copies**, once:

```bash
# with the .venv active (see above)
.venv\Scripts\python tools/extract_book_pages.py --lalkitab "C:\path\006_Arun_Sanhita_Lal_Kitab_Hare_Krishna_Trashta.pdf" --bhrigu "C:\path\bhrigu-samhita-hindi1.pdf"
```

This takes about a minute and writes about 120 MB of JPEGs to `vedic_engine/static/books/`. Restart the app afterwards. Without this step everything still works; the "book page" links just show a reminder instead.

> The books are copyrighted. Keep the page images for personal study and review, not in a public or commercial app.

## 4. Using it

1. Enter **name, date, time and place of birth**. Type the city and pick it from the list; for a village, use *Advanced* to enter latitude, longitude and time zone.
2. Click **Generate kundli**.
3. Use the tabs: **Chart · Dasha · Interpretation · Sade Sati · Panchang · Matching · Reports · Raw JSON**.
4. **Reports** → choose *Current issues & remedies*, *What's wrong*, *Full Kundli*, *Life areas*, *Varshphal* (set the **Year**), *Lal Kitab* or *Bhrigu Samhita*. Click **Print / Save as PDF** to get a PDF.
5. Switch **English | हिन्दी** in the top-right corner at any time.

## 5. Check that everything is correct (developers)

```bash
pip install pytest httpx
pytest -q          # 62 tests: astronomy, dashas, panchang, vargas, ashtakavarga, varshphal table, reports, translations
```

API documentation (every endpoint, with live "try it out" forms) is at http://127.0.0.1:8000/docs.

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `'.venv\Scripts\uvicorn' is not recognized` | An earlier install failed. Delete the `.venv` folder and run the new `start.bat`, which always checks the libraries and shows any install error. |
| `python` not found | Reinstall Python and tick "Add Python to PATH" (Windows), then reopen the terminal. |
| `Microsoft Visual C++ 14.0 or greater is required` (pyswisseph / pyyaml) | You have a newer Python (3.13–3.15). Run `py install 3.12` in Command Prompt (or install 3.12 from python.org), delete `.venv`, and run `start.bat` again. The updated `start-engine.bat` tries this automatically. |
| `No matching distribution found for pyswisseph` | You have an older copy – the app now uses `pysweph`. Use the latest zip (requirements.txt lists `pysweph`). |
| Web page says "Cannot reach the Vedic Engine" | The engine window must be running. Start `start-engine.bat`, wait for "Uvicorn running", then reload the page. |
| `node` not found | Install Node.js 20+ (LTS) from nodejs.org and reopen the terminal. |
| Port 3000 is busy | In `web/package.json` change `-p 3000` to another port (e.g. `-p 3010`) in both scripts. |
| Port 8000 is busy | Edit `start.bat`/`start.sh` and change `--port 8000` to `--port 8010`, then open http://127.0.0.1:8010. |
| City not found | Use *Advanced* → enter latitude, longitude and an IANA time zone such as `Asia/Kolkata`. |
| "Book page images are not generated yet" | Run step 3. |
