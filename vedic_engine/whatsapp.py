"""Daily WhatsApp horoscope formatter, outbound sender, and 7:00 AM scheduler.

Supports four outbound transports using standard HTTP calls (httpx):
  * callmebot – CallMeBot personal WhatsApp gateway (phone + apikey)
  * twilio    – Twilio Programmable Messaging WhatsApp API
  * meta      – Meta WhatsApp Cloud API (Graph API)
  * webhook   – Any custom HTTP webhook receiving JSON {to, text, channel}

Config and subscription state are saved locally in data/whatsapp.json (or
JYOTISH_WA_CONFIG if set). The scheduler checks every 30s and fires once per
day when local time in the subscription's timezone reaches the configured HH:MM
(default 07:00, within a 15-minute window so enabling mid-day waits until the
next morning unless "Send Now" is clicked).
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import tempfile
import threading
import time as _time
from datetime import date, datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx

from . import daily as _daily, doshas, i18n, store
from .chart import build_chart
from .dasha import vimshottari
from .ephemeris import Settings


def _default_config_path() -> pathlib.Path:
    if os.environ.get("JYOTISH_WA_CONFIG"):
        return pathlib.Path(os.environ["JYOTISH_WA_CONFIG"])
    if os.environ.get("VERCEL"):
        return pathlib.Path(tempfile.gettempdir()) / "jyotish" / "whatsapp.json"
    return pathlib.Path(__file__).resolve().parent.parent / "data" / "whatsapp.json"


CONFIG = _default_config_path()
_LOCK = threading.Lock()
_STOP = threading.Event()
_THREAD: threading.Thread | None = None

PROVIDERS = ("callmebot", "twilio", "meta", "webhook")
SECRET_FIELDS = ("api_key", "auth_token", "access_token")


def _default_state() -> dict:
    return {
        "provider": "callmebot",
        "provider_config": {},
        "subscription": {
            "enabled": False,
            "phone": "",
            "kind": "rashi",       # "rashi" | "kundli"
            "sign": "Aries",
            "kundli_id": "",
            "time": "07:00",
            "tz": "Asia/Kolkata",
            "lat": 28.6139,
            "lon": 77.2090,
            "lang": "en",
            "last_sent_date": "",
            "last_sent_at": "",
            "last_status": "",
            "last_error": "",
        },
    }


def _load() -> dict:
    with _LOCK:
        st = _default_state()
        if CONFIG.exists():
            try:
                raw = json.loads(CONFIG.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    st["provider"] = raw.get("provider") or st["provider"]
                    st["provider_config"] = dict(raw.get("provider_config") or {})
                    if isinstance(raw.get("subscription"), dict):
                        st["subscription"].update(raw["subscription"])
            except Exception:  # noqa: BLE001
                pass
        return st


def _save(st: dict) -> None:
    with _LOCK:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")


def clean_phone(phone: str) -> str:
    """Keep leading + and digits only (e.g. '+91 98765-43210' -> '+919876543210')."""
    p = phone.strip()
    digits = re.sub(r"\D", "", p)
    if not digits:
        return ""
    return f"+{digits}" if p.startswith("+") else digits


def _parse_hhmm(hhmm: str) -> tuple[int, int]:
    m = re.match(r"^(\d{1,2}):(\d{2})$", (hhmm or "07:00").strip())
    if not m:
        return 7, 0
    return min(23, max(0, int(m.group(1)))), min(59, max(0, int(m.group(2))))


def next_run_iso(sub: dict, now_utc: datetime | None = None) -> str | None:
    if not sub.get("enabled"):
        return None
    tz_name = sub.get("tz") or "Asia/Kolkata"
    now_local = (now_utc or datetime.now(ZoneInfo("UTC"))).astimezone(ZoneInfo(tz_name))
    hh, mm = _parse_hhmm(sub.get("time", "07:00"))
    target = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    today_s = now_local.date().isoformat()
    if sub.get("last_sent_date") == today_s or now_local > target + timedelta(minutes=15):
        target += timedelta(days=1)
    return target.isoformat(timespec="minutes")


def _mask(cfg: dict) -> dict:
    out = {}
    for k, v in cfg.items():
        if k in SECRET_FIELDS and isinstance(v, str) and v:
            out[k] = ""
            out[f"{k}_set"] = True
            out[f"{k}_hint"] = f"…{v[-4:]}" if len(v) >= 4 else "••••"
        else:
            out[k] = v
    return out


def status(now_utc: datetime | None = None) -> dict:
    st = _load()
    sub = dict(st["subscription"])
    sub["next_run"] = next_run_iso(sub, now_utc)
    return {
        "provider": st["provider"],
        "provider_config": _mask(st["provider_config"]),
        "subscription": sub,
    }


def configure(payload: dict) -> dict:
    st = _load()
    if payload.get("provider") in PROVIDERS:
        st["provider"] = payload["provider"]
    if isinstance(payload.get("provider_config"), dict):
        merged = dict(st["provider_config"])
        for k, v in payload["provider_config"].items():
            # Preserve existing secret if UI sends blank string while *_set is used
            if k in SECRET_FIELDS and v == "":
                continue
            merged[k] = v
        st["provider_config"] = merged
    sub = st["subscription"]
    for k in ("enabled", "kind", "sign", "kundli_id", "time", "tz", "lat", "lon", "lang"):
        if k in payload and payload[k] is not None:
            sub[k] = payload[k]
    if "phone" in payload and payload["phone"] is not None:
        sub["phone"] = clean_phone(str(payload["phone"]))
    if sub.get("enabled") and not sub.get("phone"):
        raise ValueError("phone number is required to enable daily WhatsApp delivery")
    _save(st)
    return status()


def format_message(sub: dict, day: date | None = None) -> dict:
    """Build the daily horoscope text + wa.me link for a subscription."""
    tz_name = sub.get("tz") or "Asia/Kolkata"
    lang = sub.get("lang") or "en"
    hi = lang == "hi"
    T = lambda x: i18n.term(lang, x)  # noqa: E731
    d = day or datetime.now(ZoneInfo(tz_name)).date()
    lat = float(sub.get("lat") if sub.get("lat") is not None else 28.6139)
    lon = float(sub.get("lon") if sub.get("lon") is not None else 77.2090)

    if sub.get("kind") == "kundli" and sub.get("kundli_id"):
        k = store.get(sub["kundli_id"])
        if not k:
            raise ValueError(f"kundli '{sub['kundli_id']}' not found")
        s_cfg = k.get("settings") or {}
        s = Settings(ayanamsa=s_cfg.get("ayanamsa", "lahiri"), node=s_cfg.get("node", "mean"),
                     year_days=float(s_cfg.get("year_days", 365.25)))
        birth = datetime.fromisoformat(k["datetime_local"]).replace(tzinfo=None)
        c = build_chart(birth, k["tz"], k["lat"], k["lon"], s)
        d3 = vimshottari(birth, k["tz"], s, levels=3, at=datetime(d.year, d.month, d.day, 12))
        moon_sign = c["planets"]["Moon"]["sign_index"] - 1
        ss = lambda at: doshas.sade_sati_status(moon_sign, at, k["tz"], s)  # noqa: E731
        r = _daily.for_chart(c, d3, birth, k["tz"], k["lat"], k["lon"], s, d, lang, ss_status=ss)
        p = r["panchang"]
        cb = r["chandrabala"]
        tip = r["daily_tip"]
        areas_txt = "\n".join(f"• {a['title']}: *{a['rating_label']}*" for a in r["areas"][:5])
        lines = [
            f"🕉️ *{'दैनिक कुंडली राशिफल' if hi else 'Daily Kundli Horoscope'} — {k['name']}*",
            f"📅 {r['date']} · {T(p['vara'])} · {T(p['tithi']['paksha'])} {T(p['tithi']['name'])} · {T(p['nakshatra']['name'])}",
            f"✨ *{'आज का दिन' if hi else 'Overall'}:* {r['rating_label']}",
            "",
            r["summary"],
            "",
            f"🌙 *{'चंद्रबल' if hi else 'Chandrabala'}:* {T(cb['moon_sign'])} ({cb['house_from_moon']}) — {cb['label']}",
            f"⏳ *{'राहु काल' if hi else 'Rahu Kaal'}:* {p['rahu_kaal']['start'][11:16]}–{p['rahu_kaal']['end'][11:16]}",
            "",
            f"*{'मुख्य क्षेत्र' if hi else 'Life areas'}:*",
            areas_txt,
            "",
            f"🎨 *{'शुभ रंग' if hi else 'Colour'}:* {tip['colour']}",
            f"🙏 *{'सुझाव' if hi else 'Tip'}:* {tip['practice']}",
            f"📿 *{'मंत्र' if hi else 'Mantra'}:* {tip['mantra']}",
        ]
    else:
        r = _daily.by_signs(d, tz_name, lat, lon, Settings(), lang)
        sign_name = sub.get("sign") or "Aries"
        entry = next((x for x in r["signs"] if x["sign"].lower() == sign_name.lower()), r["signs"][0])
        p = r["panchang"]
        areas_txt = "\n".join(f"• {a['title']}: *{a['rating_label']}*" for a in entry["areas"])
        lines = [
            f"🕉️ *{T(entry['sign'])} — {'दैनिक राशिफल' if hi else 'Daily Horoscope'}*",
            f"📅 {r['date']} · {T(p['vara'])} · {T(p['tithi']['paksha'])} {T(p['tithi']['name'])} · {T(p['nakshatra']['name'])}",
            f"✨ *{'मूल्यांकन' if hi else 'Rating'}:* {entry['rating_label']} ({'राशि से चंद्र' if hi else 'Moon'} +{entry['moon_house']})",
            "",
            entry["overview"],
            "",
            f"*{'क्षेत्रवार फल' if hi else 'Areas today'}:*",
            areas_txt,
            "",
            f"🎨 *{'शुभ रंग' if hi else 'Lucky colour'}:* {entry['colour']} | 🔢 *{'अंक' if hi else 'Numbers'}:* {', '.join(map(str, entry['lucky_numbers']))}",
            f"⏳ *{'राहु काल' if hi else 'Rahu Kaal'}:* {p['rahu_kaal']['start'][11:16]}–{p['rahu_kaal']['end'][11:16]}",
            f"🙏 *{'उपाय/सुझाव' if hi else 'Tip'}:* {entry['tip']}",
            f"📿 *{'मंत्र' if hi else 'Mantra'}:* {entry['mantra']}",
        ]

    text = "\n".join(lines)
    digits = re.sub(r"\D", "", sub.get("phone") or "")
    wa_me = f"https://wa.me/{digits}?text={quote(text)}" if digits else f"https://wa.me/?text={quote(text)}"
    return {"date": d.isoformat(), "text": text, "wa_me_url": wa_me}


def send_via_provider(provider: str, cfg: dict, phone: str, text: str) -> dict:
    """Send `text` to `phone` via the configured provider. Raises RuntimeError on missing config or HTTP failure."""
    to = clean_phone(phone)
    if not to:
        raise RuntimeError("Recipient WhatsApp phone number is required.")

    if provider == "callmebot":
        api_key = (cfg.get("api_key") or "").strip()
        if not api_key:
            raise RuntimeError("CallMeBot API key is not set.")
        r = httpx.get(
            "https://api.callmebot.com/whatsapp.php",
            params={"phone": to.lstrip("+"), "text": text, "apikey": api_key},
            timeout=20.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"CallMeBot HTTP {r.status_code}: {r.text[:200]}")
        return {"ok": True, "provider": provider, "detail": r.text.strip()[:200]}

    if provider == "twilio":
        sid = (cfg.get("account_sid") or "").strip()
        token = (cfg.get("auth_token") or "").strip()
        from_num = (cfg.get("from_number") or "whatsapp:+14155238886").strip()
        if not sid or not token:
            raise RuntimeError("Twilio Account SID and Auth Token are required.")
        to_wa = to if to.startswith("whatsapp:") else f"whatsapp:{to if to.startswith('+') else '+' + to}"
        from_wa = from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}"
        r = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            auth=(sid, token),
            data={"From": from_wa, "To": to_wa, "Body": text},
            timeout=20.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Twilio HTTP {r.status_code}: {r.text[:200]}")
        return {"ok": True, "provider": provider, "sid": r.json().get("sid")}

    if provider == "meta":
        phone_id = (cfg.get("phone_number_id") or "").strip()
        token = (cfg.get("access_token") or "").strip()
        if not phone_id or not token:
            raise RuntimeError("Meta Phone Number ID and Access Token are required.")
        r = httpx.post(
            f"https://graph.facebook.com/v21.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "messaging_product": "whatsapp",
                "to": to.lstrip("+"),
                "type": "text",
                "text": {"preview_url": False, "body": text},
            },
            timeout=20.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Meta Graph API HTTP {r.status_code}: {r.text[:200]}")
        return {"ok": True, "provider": provider, "response": r.json()}

    if provider == "webhook":
        url = (cfg.get("webhook_url") or "").strip()
        if not url:
            raise RuntimeError("Webhook URL is required.")
        r = httpx.post(url, json={"to": to, "text": text, "channel": "whatsapp"}, timeout=20.0)
        if r.status_code >= 400:
            raise RuntimeError(f"Webhook HTTP {r.status_code}: {r.text[:200]}")
        return {"ok": True, "provider": provider, "status_code": r.status_code}

    raise RuntimeError(f"Unsupported WhatsApp provider '{provider}'.")


def send_now(override: dict | None = None, day: date | None = None) -> dict:
    """Format and send today's horoscope immediately; record outcome on the stored subscription."""
    if override:
        configure(override)
    st = _load()
    sub = st["subscription"]
    msg = format_message(sub, day=day)
    tz_name = sub.get("tz") or "Asia/Kolkata"
    now_local = datetime.now(ZoneInfo(tz_name))
    try:
        res = send_via_provider(st["provider"], st["provider_config"], sub.get("phone", ""), msg["text"])
        sub["last_sent_date"] = msg["date"]
        sub["last_sent_at"] = now_local.isoformat(timespec="seconds")
        sub["last_status"] = "sent"
        sub["last_error"] = ""
        _save(st)
        return {"sent": True, "result": res, **msg, "status": status()}
    except Exception as exc:  # noqa: BLE001
        sub["last_status"] = "error"
        sub["last_error"] = str(exc)
        _save(st)
        return {"sent": False, "error": str(exc), **msg, "status": status()}


def run_pending(now_utc: datetime | None = None) -> bool:
    """Check if the enabled subscription is due in the 15-minute window at its scheduled HH:MM."""
    st = _load()
    sub = st["subscription"]
    if not sub.get("enabled"):
        return False
    tz_name = sub.get("tz") or "Asia/Kolkata"
    now_local = (now_utc or datetime.now(ZoneInfo("UTC"))).astimezone(ZoneInfo(tz_name))
    hh, mm = _parse_hhmm(sub.get("time", "07:00"))
    target = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    today_s = now_local.date().isoformat()
    if sub.get("last_sent_date") == today_s:
        return False
    if not (target <= now_local <= target + timedelta(minutes=15)):
        return False
    send_now(day=now_local.date())
    return True


def _loop() -> None:
    while not _STOP.wait(30.0):
        try:
            run_pending()
        except Exception:  # noqa: BLE001
            pass


def start_scheduler() -> None:
    global _THREAD
    if os.environ.get("VERCEL"):
        return
    if _THREAD and _THREAD.is_alive():
        return
    _STOP.clear()
    _THREAD = threading.Thread(target=_loop, name="whatsapp-daily-scheduler", daemon=True)
    _THREAD.start()


def stop_scheduler() -> None:
    _STOP.set()
