"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, birthOf, nowIn, type Kundli, type Place } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PlaceSearch from "@/components/PlaceSearch";
import { DailyView } from "@/components/DailyReport";
import WhatsAppPanel from "@/components/WhatsAppPanel";

const DEFAULT_PLACE: Place = { name: "New Delhi", country: "India", lat: 28.6139, lon: 77.209, tz: "Asia/Kolkata" };
const rateChip = (k: string) => (k === "excellent" || k === "good" ? "good" : k === "mixed" ? "mixed" : "bad");
const rateCls = (k: string) => (k === "excellent" || k === "good" ? "benefic" : k === "mixed" ? "mixed" : "challenging");

function RashiDetail({ s, p, moonSign, onSelectDay, onBack }: { s: any; p: any; moonSign: string; onSelectDay: (d: string) => void; onBack: () => void }) {
  const { t, T, fmtD } = useI18n();
  return (
    <div className="rep">
      <div className="kheader" style={{ marginBottom: 10 }}>
        <h2 style={{ margin: 0 }}>{T(s.sign)}</h2>
        <span className={`chip ${rateChip(s.rating)}`}>{s.rating_label}</span>
        <span className="note">{t("lord")}: {T(s.lord)} · {t("score")}: {s.score}</span>
        {s.chandrashtama && <span className="chip bad">Chandrashtama (8th)</span>}
        {s.ghat_nakshatra && <span className="chip bad">{t("ghat_nak")}: {T(s.ghat_nakshatra_name)}</span>}
        {s.saturn_phase && <span className="chip mixed">{t("sade_dhaiya")}: {T(s.saturn_phase)}</span>}
        <button className="ghost noprint" style={{ marginLeft: "auto" }} onClick={onBack}>← {t("all_signs")}</button>
      </div>

      <p style={{ fontSize: 15 }}>{s.overview}</p>

      <div className="summary">
        <div className="stat">
          <span>{t("transit_moon")}</span>
          <b>{T(moonSign)} (+{s.moon_house})</b>
          <span>{T(p.nakshatra.name)}</span>
        </div>
        <div className="stat">
          <span>{t("lucky_colour")}</span>
          <b>{s.colour}</b>
        </div>
        <div className="stat">
          <span>{t("lucky_numbers")}</span>
          <b>{s.lucky_numbers.join(", ")}</b>
        </div>
        <div className="stat">
          <span>{t("sade_dhaiya")}</span>
          <b>{s.saturn_phase ? T(s.saturn_phase) : t("normal_saturn")}</b>
        </div>
        <div className="stat">
          <span>{t("rahu_kaal")}</span>
          <b>{p.rahu_kaal.start.slice(11, 16)}–{p.rahu_kaal.end.slice(11, 16)}</b>
          <span>{t("sunrise")} {p.sunrise.slice(11, 16)}</span>
        </div>
      </div>

      <div className="grid2" style={{ marginTop: 12 }}>
        <div className="finding benefic">
          <h4>{t("daily_favour")}</h4>
          <ul>{s.guidance.favour.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
        </div>
        <div className="finding challenging">
          <h4>{t("daily_avoid")}</h4>
          <ul>{s.guidance.avoid.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
        </div>
      </div>

      <h3>{t("area_outlook")}</h3>
      <div className="rem">
        {s.areas.map((a: any) => (
          <div
            key={a.area}
            className="box"
            style={{ borderLeft: `4px solid var(--${rateChip(a.rating) === "good" ? "good" : rateChip(a.rating) === "mixed" ? "mixed" : "bad"})` }}
          >
            <h5>{a.title} <span className={`chip ${rateChip(a.rating)}`}>{a.rating_label}</span></h5>
            <p style={{ margin: "4px 0 6px" }}>{a.text}</p>
            <ul>{a.reasons.map((x: string, i: number) => <li key={i} className="note">{x}</li>)}</ul>
          </div>
        ))}
      </div>

      <div className="finding mixed" style={{ marginTop: 14 }}>
        <h4>{t("daily_tip")} · {T(s.lord)}</h4>
        <p>{s.tip}</p>
        <p><b>{t("deity_worship")}:</b> {s.deity} · <b>{t("daana")}:</b> {s.daana}</p>
        <p className="note"><b>{t("sys_mantra")}:</b> {s.mantra}</p>
        {s.health_watch && (
          <p className="note">
            <b>{t("health_watch_today")}:</b> {s.health_watch.parts} ({s.health_watch.watch})
          </p>
        )}
      </div>

      {s.week?.length > 0 && (
        <>
          <h3>{t("next_7_days_rashi")}</h3>
          <div className="mini" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(135px,1fr))" }}>
            {s.week.map((w: any, idx: number) => (
              <div
                key={w.date}
                className={`stat ${idx === 0 ? "cur" : ""}`}
                style={{
                  cursor: "pointer",
                  borderColor: idx === 0 ? "var(--accent)" : undefined,
                  borderWidth: idx === 0 ? 2 : undefined,
                }}
                onClick={() => onSelectDay(w.date)}
              >
                <span>{fmtD(w.date)} · {w.weekday}</span>
                <b><span className={`chip ${rateChip(w.rating)}`}>{w.rating_label}</span></b>
                <span>{T(w.moon_sign)} (+{w.moon_house})</span>
                <span className="note">{T(w.nakshatra)}{w.chandrashtama ? " · ⚠ 8th" : ""}</span>
              </div>
            ))}
          </div>
        </>
      )}

      <h3>{t("transits_from_rashi")} {T(s.sign)}</h3>
      <div style={{ overflow: "auto" }}>
        <table>
          <tbody>
            <tr>
              <th>{t("graha")}</th>
              <th>{t("sign")}</th>
              <th>{t("nakshatra")}</th>
              <th>{t("house")}</th>
              <th></th>
            </tr>
            {s.transits.map((x: any) => (
              <tr key={x.planet} className={rateCls(x.good ? "good" : "mixed")}>
                <td><b>{T(x.planet)}</b></td>
                <td>{T(x.sign)}</td>
                <td>{T(x.nakshatra)}</td>
                <td><span className={`chip ${x.good ? "good" : "gray"}`}>{x.house_from_moon}</span></td>
                <td className="note">{x.text}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function HoroscopePage() {
  const { t, T, lang, fmtD } = useI18n();
  const [mode, setMode] = useState<"rashi" | "kundli">("rashi");
  const [day, setDay] = useState(() => new Date().toISOString().slice(0, 10));
  const [place, setPlace] = useState<Place | null>(DEFAULT_PLACE);
  const [rashiData, setRashiData] = useState<any>(null);
  const [selectedSign, setSelectedSign] = useState<string>("");
  const [saved, setSaved] = useState<Kundli[]>([]);
  const [kid, setKid] = useState("");
  const [personal, setPersonal] = useState<any>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api<Kundli[]>("/kundlis").then((xs) => {
      setSaved(xs);
      if (xs.length && !kid) setKid(xs[0].id || "");
    }).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (mode !== "rashi") return;
    const pl = place || DEFAULT_PLACE;
    setLoading(true);
    setErr("");
    api("/horoscope/daily", { day, tz: pl.tz, lat: pl.lat, lon: pl.lon, lang })
      .then(setRashiData)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [mode, day, place, lang]);

  useEffect(() => {
    if (mode !== "kundli" || !kid) return;
    const k = saved.find((x) => x.id === kid);
    if (!k) return;
    setLoading(true);
    setErr("");
    api("/report/daily", { ...birthOf(k), lang, day, at: nowIn(k.tz) })
      .then(setPersonal)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [mode, kid, day, lang, saved]);

  const signs = rashiData?.signs || [];
  const activeSign = selectedSign ? signs.find((s: any) => s.sign === selectedSign) : null;
  const p = rashiData?.panchang;

  return (
    <div className="page">
      <section className="card">
        <h2>{t("daily_title")}</h2>
        <p className="note">{t("daily_sub")}</p>

        <div className="subtabs">
          <button className={mode === "rashi" ? "on" : ""} onClick={() => setMode("rashi")}>{t("by_rashi")}</button>
          <button className={mode === "kundli" ? "on" : ""} onClick={() => setMode("kundli")}>{t("by_kundli")}</button>
        </div>

        <div className="row" style={{ maxWidth: 720, marginBottom: 14 }}>
          <div>
            <label>{t("date")}</label>
            <input type="date" value={day} onChange={(e) => setDay(e.target.value)} />
          </div>
          {mode === "rashi" ? (
            <div>
              <label>{t("place")}</label>
              <PlaceSearch value={place} onSelect={setPlace} placeholder={t("city_ph")} />
            </div>
          ) : (
            <div>
              <label>{t("choose_saved")}</label>
              <div className="btnrow" style={{ alignItems: "center" }}>
                <select value={kid} onChange={(e) => setKid(e.target.value)} style={{ flex: 1 }}>
                  {!saved.length && <option value="">—</option>}
                  {saved.map((k) => (
                    <option key={k.id} value={k.id}>{k.name} · {k.datetime_local.slice(0, 10)}</option>
                  ))}
                </select>
                {kid && <Link className="btn light" href={`/kundli/${kid}`}>{t("open_kundli_full")}</Link>}
              </div>
            </div>
          )}
        </div>

        {err && <p className="err" style={{ display: "block" }}>{err}</p>}
        <WhatsAppPanel
          kind={mode}
          sign={selectedSign || "Aries"}
          kundliId={kid}
          tz={(mode === "kundli" ? saved.find((x) => x.id === kid)?.tz : place?.tz) || DEFAULT_PLACE.tz}
          lat={(mode === "kundli" ? saved.find((x) => x.id === kid)?.lat : place?.lat) ?? DEFAULT_PLACE.lat}
          lon={(mode === "kundli" ? saved.find((x) => x.id === kid)?.lon : place?.lon) ?? DEFAULT_PLACE.lon}
          day={day}
        />
        {loading && <div className="empty">{t("loading")}</div>}

        {mode === "rashi" && !loading && rashiData && (
          <>
            <div className="summary">
              <div className="stat"><span>{t("date")}</span><b>{fmtD(rashiData.date)}</b><span>{T(p.vara)}</span></div>
              <div className="stat"><span>{t("transit_moon")}</span><b>{T(rashiData.moon_sign)}</b></div>
              <div className="stat"><span>{t("tithi")}</span><b>{T(p.tithi.paksha)} {T(p.tithi.name)}</b></div>
              <div className="stat"><span>{t("nakshatra")}</span><b>{T(p.nakshatra.name)}</b></div>
              <div className="stat"><span>{t("rahu_kaal")}</span><b>{p.rahu_kaal.start.slice(11, 16)}–{p.rahu_kaal.end.slice(11, 16)}</b></div>
            </div>

            {(rashiData.yogas?.length > 0 || rashiData.cautions?.length > 0) && (
              <p>
                {rashiData.yogas?.map((y: string) => <span key={y} className="chip good">{y}</span>)}
                {rashiData.cautions?.map((c: string) => <span key={c} className="chip bad">{c}</span>)}
              </p>
            )}

            <div className="subtabs" style={{ marginTop: 10 }}>
              <button className={!selectedSign ? "on" : ""} onClick={() => setSelectedSign("")}>{t("all")}</button>
              {signs.map((s: any) => (
                <button key={s.sign} className={selectedSign === s.sign ? "on" : ""} onClick={() => setSelectedSign(s.sign)}>
                  {T(s.sign)}
                </button>
              ))}
            </div>

            {activeSign ? (
              <RashiDetail s={activeSign} p={p} moonSign={rashiData.moon_sign} onSelectDay={setDay} onBack={() => setSelectedSign("")} />
            ) : (
              <div className="rem">
                {signs.map((s: any) => (
                  <div
                    key={s.sign}
                    className="box"
                    style={{
                      borderLeft: `4px solid var(--${rateChip(s.rating) === "good" ? "good" : rateChip(s.rating) === "mixed" ? "mixed" : "bad"})`,
                      cursor: "pointer",
                    }}
                    onClick={() => setSelectedSign(s.sign)}
                  >
                    <div className="kheader" style={{ marginBottom: 6 }}>
                      <h4 style={{ margin: 0 }}>{T(s.sign)}</h4>
                      <span className={`chip ${rateChip(s.rating)}`}>{s.rating_label}</span>
                      <span className="note">{t("lord")}: {T(s.lord)} · +{s.moon_house}</span>
                      {s.chandrashtama && <span className="chip bad">8th</span>}
                      {s.ghat_nakshatra && <span className="chip bad">{t("ghat_nak")}</span>}
                    </div>
                    <p style={{ margin: "6px 0" }}>{s.overview}</p>
                    <ul>{s.highlights.map((h: string, i: number) => <li key={i}>{h}</li>)}</ul>
                    <p className="note" style={{ marginTop: 6 }}>
                      <b>{t("lucky_colour")}:</b> {s.colour} · <b>{t("lucky_numbers")}:</b> {s.lucky_numbers.join(", ")}
                    </p>
                    <p style={{ marginTop: 6, marginBottom: 0 }}>
                      <span style={{ color: "var(--accent)", fontWeight: 600, fontSize: 13 }}>{t("view_details")} →</span>
                    </p>
                  </div>
                ))}
              </div>
            )}
            <p className="note" style={{ marginTop: 14 }}>{rashiData.disclaimer}</p>
          </>
        )}

        {mode === "kundli" && !saved.length && !loading && (
          <div className="empty">{t("no_saved")}</div>
        )}

        {mode === "kundli" && !loading && personal && kid && (
          <div className="rep">
            <DailyView r={personal} onSelectDay={setDay} />
          </div>
        )}
      </section>
    </div>
  );
}
