"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { api, type Place } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PlaceSearch from "@/components/PlaceSearch";

export default function Panchang() {
  const { t, T, fmtD } = useI18n();
  const [day, setDay] = useState(new Date().toISOString().slice(0, 10));
  const [place, setPlace] = useState<Place | null>(null);
  const [p, setP] = useState<any>(null);
  const [err, setErr] = useState("");
  const show = async () => {
    if (!place) return setErr(t("choose_place"));
    setErr("");
    try { setP(await api("/panchang", { day, tz: place.tz, lat: place.lat, lon: place.lon })); } catch (e: any) { setErr(e.message); }
  };
  const tm = (s: string) => s.slice(11, 16) + (p && s.slice(0, 10) !== p.date ? ` (${fmtD(s)})` : "");
  return (
    <div className="page"><section className="card">
      <h2>{t("tab_panchang")}</h2>
      <div className="row" style={{ maxWidth: 640 }}>
        <div><label>{t("date")}</label><input type="date" value={day} onChange={(e) => setDay(e.target.value)} /></div>
        <div><label>{t("place")}</label><PlaceSearch value={place} onSelect={setPlace} placeholder={t("city_ph")} /></div>
      </div>
      <button className="btn" style={{ marginTop: 12 }} onClick={show}>{t("show_panchang")}</button>
      {err && <p className="err" style={{ display: "block" }}>{err}</p>}
      {p && <div style={{ marginTop: 18 }}>
        <div className="summary">
          <div className="stat"><span>{t("sunrise")}</span><b>{tm(p.sunrise)}</b></div>
          <div className="stat"><span>{t("sunset")}</span><b>{tm(p.sunset)}</b></div>
          <div className="stat"><span>{t("vara")}</span><b>{T(p.vara)}</b></div>
          <div className="stat"><span>{t("rahu_kaal")}</span><b>{tm(p.rahu_kaal.start)}–{tm(p.rahu_kaal.end)}</b></div>
        </div>
        <table><tbody>
          <tr><th>{t("limb")}</th><th>{t("at_sunrise")}</th><th>{t("ends")}</th></tr>
          <tr><td>{t("tithi")}</td><td><b>{T(p.tithi.paksha)} {T(p.tithi.name)}</b> ({p.tithi.number})</td><td>{tm(p.tithi.ends)}</td></tr>
          <tr><td>{t("nakshatra")}</td><td><b>{T(p.nakshatra.name)}</b></td><td>{tm(p.nakshatra.ends)}</td></tr>
          <tr><td>{t("yoga")}</td><td><b>{T(p.yoga.name)}</b></td><td>{tm(p.yoga.ends)}</td></tr>
          <tr><td>{t("karana")}</td><td><b>{T(p.karana.name)}</b></td><td>{tm(p.karana.ends)}</td></tr>
        </tbody></table>
        <p className="note">{t("panchang_note")} {p.tz}.</p>
      </div>}
    </section></div>
  );
}
