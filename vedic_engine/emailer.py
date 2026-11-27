"""Share daily horoscope via SMTP email (plain text + styled HTML).

SMTP configuration is read strictly from environment variables (loaded from root `.env`):
  SMTP_HOST, SMTP_PORT, SMTP_SECURITY (starttls | ssl | none),
  SMTP_USER, SMTP_PASSWORD, SMTP_FROM
"""
from __future__ import annotations

import html
import os
import pathlib
import re
import smtplib
import ssl
from datetime import date, datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from . import daily as _daily, doshas, i18n, store
from .chart import build_chart
from .dasha import vimshottari
from .ephemeris import Settings

_ROOT_ENV = pathlib.Path(__file__).resolve().parent.parent / ".env"
if load_dotenv and _ROOT_ENV.exists():
    load_dotenv(_ROOT_ENV, override=False)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def env_config() -> dict:
    if load_dotenv and _ROOT_ENV.exists():
        load_dotenv(_ROOT_ENV, override=False)
    host = os.environ.get("SMTP_HOST", "").strip()
    port_raw = os.environ.get("SMTP_PORT", "").strip()
    sec = os.environ.get("SMTP_SECURITY", "").strip().lower()
    if not sec:
        if os.environ.get("SMTP_USE_SSL", "").strip().lower() in ("1", "true", "yes"):
            sec = "ssl"
        elif os.environ.get("SMTP_STARTTLS", "").strip().lower() in ("0", "false", "no"):
            sec = "none"
        else:
            sec = "ssl" if port_raw == "465" else "starttls"
    if sec not in ("starttls", "ssl", "none"):
        sec = "starttls"
    username = os.environ.get("SMTP_USER", "").strip()
    from_email = os.environ.get("SMTP_FROM", "").strip() or username
    return {
        "host": host,
        "port": int(port_raw) if port_raw.isdigit() else (465 if sec == "ssl" else 587),
        "security": sec,
        "username": username,
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "from_email": from_email,
    }


def status() -> dict:
    cfg = env_config()
    return {
        "configured": bool(cfg["host"] and cfg["from_email"]),
        "host": cfg["host"],
        "port": cfg["port"],
        "security": cfg["security"],
        "from_email": cfg["from_email"],
    }


def _parse_recipients(raw: str) -> list[str]:
    addrs = [a.strip() for a in re.split(r"[,;]+", raw or "") if a.strip()]
    if not addrs:
        raise ValueError("Recipient email address is required.")
    for a in addrs:
        if not _EMAIL_RE.match(a):
            raise ValueError(f"Invalid email address: {a}")
    return addrs


def _build_rashi_email(req: dict, d: date, lang: str) -> dict:
    hi = lang == "hi"
    T = lambda x: i18n.term(lang, x)  # noqa: E731
    tz = req.get("tz") or "Asia/Kolkata"
    lat = float(req.get("lat") if req.get("lat") is not None else 28.6139)
    lon = float(req.get("lon") if req.get("lon") is not None else 77.2090)
    r = _daily.by_signs(d, tz, lat, lon, Settings(), lang)
    sign_name = req.get("sign") or "Aries"
    entry = next((x for x in r["signs"] if x["sign"].lower() == sign_name.lower()), r["signs"][0])
    p = r["panchang"]

    title = f"{T(entry['sign'])} — {'दैनिक राशिफल' if hi else 'Daily Horoscope'}"
    subject = f"{title} ({r['date']})"
    panchang_line = f"{T(p['vara'])} · {T(p['tithi']['paksha'])} {T(p['tithi']['name'])} · {T(p['nakshatra']['name'])}"
    rahu_line = f"{p['rahu_kaal']['start'][11:16]}–{p['rahu_kaal']['end'][11:16]}"

    lines = [
        title,
        f"{r['date']} · {panchang_line}",
        f"{'मूल्यांकन' if hi else 'Rating'}: {entry['rating_label']} ({'राशि से चंद्र' if hi else 'Moon'} +{entry['moon_house']})",
        "",
        entry["overview"],
        "",
        f"{'क्षेत्रवार फल' if hi else 'Area Outlook'}:",
        *[f"- {a['title']} ({a['rating_label']}): {a['text']}" for a in entry["areas"]],
        "",
        f"{'अनुकूल' if hi else 'Supportive today'}:",
        *[f"- {x}" for x in entry["guidance"]["favour"]],
        f"{'सावधानी' if hi else 'Be mindful of'}:",
        *[f"- {x}" for x in entry["guidance"]["avoid"]],
        "",
        f"{'शुभ रंग' if hi else 'Lucky colour'}: {entry['colour']} | {'शुभ अंक' if hi else 'Numbers'}: {', '.join(map(str, entry['lucky_numbers']))}",
        f"{'राहु काल' if hi else 'Rahu Kaal'}: {rahu_line}",
        f"{'उपाय / सुझाव' if hi else 'Daily tip'}: {entry['tip']}",
        f"{'मंत्र' if hi else 'Mantra'}: {entry['mantra']}",
    ]

    area_rows = "".join(
        f"<tr><td style='padding:6px 8px;border-bottom:1px solid #eee'><b>{html.escape(a['title'])}</b></td>"
        f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>{html.escape(a['rating_label'])}</td>"
        f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>{html.escape(a['text'])}</td></tr>"
        for a in entry["areas"]
    )
    html_body = f"""<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:0 auto;background:#faf7f2;padding:18px;color:#2b2420">
  <div style="background:#fff;border:1px solid #e8e0d6;border-radius:12px;padding:18px">
    <h2 style="margin:0 0 6px;color:#c2571a">{html.escape(title)}</h2>
    <p style="margin:0 0 12px;color:#7a6f66;font-size:13px">{html.escape(r['date'])} · {html.escape(panchang_line)} · Rahu Kaal {html.escape(rahu_line)}</p>
    <p style="margin:0 0 10px"><b>{'मूल्यांकन' if hi else 'Rating'}:</b> {html.escape(entry['rating_label'])} ({'चंद्र' if hi else 'Moon'} +{entry['moon_house']})</p>
    <p style="line-height:1.5">{html.escape(entry['overview'])}</p>
    <h3 style="margin:16px 0 8px;font-size:15px">{'क्षेत्रवार फल' if hi else 'Area Outlook'}</h3>
    <table style="width:100%;border-collapse:collapse;font-size:13.5px">{area_rows}</table>
    <p style="margin:14px 0 6px"><b>{'शुभ रंग' if hi else 'Lucky colour'}:</b> {html.escape(entry['colour'])} · <b>{'शुभ अंक' if hi else 'Lucky numbers'}:</b> {', '.join(map(str, entry['lucky_numbers']))}</p>
    <p style="margin:6px 0"><b>{'उपाय / सुझाव' if hi else 'Daily tip'}:</b> {html.escape(entry['tip'])}</p>
    <p style="margin:6px 0;color:#7a6f66;font-size:13px"><b>{'मंत्र' if hi else 'Mantra'}:</b> {html.escape(entry['mantra'])}</p>
    <p style="margin:14px 0 0;color:#7a6f66;font-size:12px">{html.escape(r['disclaimer'])}</p>
  </div>
</div>"""
    return {"subject": subject, "text": "\n".join(lines), "html": html_body, "date": r["date"]}


def _build_kundli_email(req: dict, d: date, lang: str, user_id: str = "local", token: str | None = None) -> dict:
    hi = lang == "hi"
    T = lambda x: i18n.term(lang, x)  # noqa: E731
    k: dict | None = None
    if req.get("datetime_local") and req.get("tz") and req.get("lat") is not None and req.get("lon") is not None:
        k = req
    elif req.get("kundli_id"):
        k = store.get(req["kundli_id"], user_id=user_id, token=token)
    if not k:
        raise ValueError("Kundli birth details or valid kundli_id are required.")

    s_cfg = k.get("settings") or {}
    s = Settings(ayanamsa=s_cfg.get("ayanamsa", "lahiri"), node=s_cfg.get("node", "mean"),
                 year_days=float(s_cfg.get("year_days", 365.25)))
    birth = datetime.fromisoformat(str(k["datetime_local"]).replace("Z", "")).replace(tzinfo=None)
    tz = k["tz"]
    lat = float(k["lat"])
    lon = float(k["lon"])
    c = build_chart(birth, tz, lat, lon, s)
    d3 = vimshottari(birth, tz, s, levels=3, at=datetime(d.year, d.month, d.day, 12))
    moon_sign = c["planets"]["Moon"]["sign_index"] - 1
    ss = lambda at: doshas.sade_sati_status(moon_sign, at, tz, s)  # noqa: E731
    r = _daily.for_chart(c, d3, birth, tz, lat, lon, s, d, lang, ss_status=ss)

    p = r["panchang"]
    cb = r["chandrabala"]
    tip = r["daily_tip"]
    name = (k.get("name") or "").strip()
    base_title = "दैनिक कुंडली राशिफल" if hi else "Daily Kundli Horoscope"
    title = f"{base_title} — {name}" if name else base_title
    subject = f"{title} ({r['date']})"
    panchang_line = f"{T(p['vara'])} · {T(p['tithi']['paksha'])} {T(p['tithi']['name'])} · {T(p['nakshatra']['name'])}"
    rahu_line = f"{p['rahu_kaal']['start'][11:16]}–{p['rahu_kaal']['end'][11:16]}"

    lines = [
        title,
        f"{r['date']} · {panchang_line}",
        f"{'मूल्यांकन' if hi else 'Overall'}: {r['rating_label']}",
        f"{'चंद्रबल' if hi else 'Chandrabala'}: {T(cb['moon_sign'])} ({cb['house_from_moon']}) — {cb['label']} ({cb['bindus']} bindus)",
        "",
        r["summary"],
        "",
        f"{'क्षेत्रवार फल' if hi else 'Area Outlook'}:",
        *[f"- {a['title']} ({a['rating_label']}): {'; '.join(a['reasons'])}" for a in r["areas"]],
        "",
        f"{'अनुकूल' if hi else 'Supportive today'}:",
        *[f"- {x}" for x in r["guidance"]["favour"]],
        f"{'सावधानी' if hi else 'Be mindful of'}:",
        *[f"- {x}" for x in r["guidance"]["avoid"]],
        "",
        f"{'राहु काल' if hi else 'Rahu Kaal'}: {rahu_line}",
        f"{'शुभ रंग' if hi else 'Colour'}: {tip['colour']}",
        f"{'सुझाव' if hi else 'Tip'}: {tip['practice']}",
        f"{'मंत्र' if hi else 'Mantra'}: {tip['mantra']}",
    ]

    area_rows = "".join(
        f"<tr><td style='padding:6px 8px;border-bottom:1px solid #eee'><b>{html.escape(a['title'])}</b></td>"
        f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>{html.escape(a['rating_label'])}</td>"
        f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>{html.escape('; '.join(a['reasons']))}</td></tr>"
        for a in r["areas"]
    )
    html_body = f"""<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:0 auto;background:#faf7f2;padding:18px;color:#2b2420">
  <div style="background:#fff;border:1px solid #e8e0d6;border-radius:12px;padding:18px">
    <h2 style="margin:0 0 6px;color:#c2571a">{html.escape(title)}</h2>
    <p style="margin:0 0 12px;color:#7a6f66;font-size:13px">{html.escape(r['date'])} · {html.escape(panchang_line)} · Rahu Kaal {html.escape(rahu_line)}</p>
    <p style="margin:0 0 10px"><b>{'मूल्यांकन' if hi else 'Overall'}:</b> {html.escape(r['rating_label'])} · <b>{'चंद्रबल' if hi else 'Chandrabala'}:</b> {html.escape(T(cb['moon_sign']))} ({cb['house_from_moon']}) — {html.escape(cb['label'])}</p>
    <p style="line-height:1.5">{html.escape(r['summary'])}</p>
    <h3 style="margin:16px 0 8px;font-size:15px">{'क्षेत्रवार फल' if hi else 'Area Outlook'}</h3>
    <table style="width:100%;border-collapse:collapse;font-size:13.5px">{area_rows}</table>
    <p style="margin:14px 0 6px"><b>{'शुभ रंग' if hi else 'Colour'}:</b> {html.escape(tip['colour'])}</p>
    <p style="margin:6px 0"><b>{'सुझाव' if hi else 'Tip'}:</b> {html.escape(tip['practice'])}</p>
    <p style="margin:6px 0;color:#7a6f66;font-size:13px"><b>{'मंत्र' if hi else 'Mantra'}:</b> {html.escape(tip['mantra'])}</p>
    <p style="margin:14px 0 0;color:#7a6f66;font-size:12px">{html.escape(r['disclaimer'])}</p>
  </div>
</div>"""
    return {"subject": subject, "text": "\n".join(lines), "html": html_body, "date": r["date"]}


def format_horoscope_email(req: dict, user_id: str = "local", token: str | None = None) -> dict:
    tz = req.get("tz") or "Asia/Kolkata"
    lang = req.get("lang") or "en"
    raw_day = req.get("day")
    if isinstance(raw_day, date):
        d = raw_day
    elif isinstance(raw_day, str) and raw_day.strip():
        d = date.fromisoformat(raw_day.strip()[:10])
    else:
        d = datetime.now(ZoneInfo(tz)).date()
    if req.get("kind") == "kundli":
        return _build_kundli_email(req, d, lang, user_id=user_id, token=token)
    return _build_rashi_email(req, d, lang)


def send_smtp(to_emails: list[str], subject: str, text_body: str, html_body: str, cfg: dict) -> None:
    host = cfg["host"]
    port = cfg["port"]
    sec = cfg["security"]
    username = cfg["username"]
    password = cfg["password"]
    from_email = cfg["from_email"]

    if not host or not from_email:
        raise ValueError("SMTP is not configured in .env (set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM).")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    ctx = ssl.create_default_context()
    if sec == "ssl":
        with smtplib.SMTP_SSL(host, port, timeout=20, context=ctx) as server:
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            if sec == "starttls":
                server.starttls(context=ctx)
                server.ehlo()
            if username and password:
                server.login(username, password)
            server.send_message(msg)


def share_horoscope(req: dict, user_id: str = "local", token: str | None = None) -> dict:
    recipients = _parse_recipients(req.get("to_email", ""))
    formatted = format_horoscope_email(req, user_id=user_id, token=token)
    cfg = env_config()
    send_smtp(recipients, formatted["subject"], formatted["text"], formatted["html"], cfg)
    return {
        "sent": True,
        "to": recipients,
        "subject": formatted["subject"],
        "date": formatted["date"],
        "status": status(),
    }
