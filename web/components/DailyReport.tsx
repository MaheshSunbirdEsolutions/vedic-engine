"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useI18n } from "@/lib/i18n";
import type { Kundli } from "@/lib/api";
import { Fold } from "./Explain";
import EmailShareButton from "./EmailShareButton";

const rateChip = (k: string) => (k === "excellent" || k === "good" ? "good" : k === "mixed" ? "mixed" : "bad");
const rateCls = (k: string) => (k === "excellent" || k === "good" ? "benefic" : k === "mixed" ? "mixed" : "challenging");

export function DailyView({ r, kundli, onSelectDay }: { r: any; kundli?: Kundli; onSelectDay?: (day: string) => void }) {
  const { t, T, fmtD } = useI18n();
  const p = r.panchang;
  const cb = r.chandrabala;
  const tb = r.tarabala;
  const tip = r.daily_tip;
  const tm = (s?: string) => (s ? s.slice(11, 16) : "");

  return (
    <>
      <h2>
        {fmtD(r.date)}{" "}
        <span className={`chip ${rateChip(r.rating)}`}>{r.rating_label}</span>
      </h2>
      {kundli && (
        <EmailShareButton
          kind="kundli"
          kundli={kundli}
          tz={kundli.tz}
          lat={kundli.lat}
          lon={kundli.lon}
          day={r.date}
        />
      )}
      <p style={{ fontSize: 15 }}>{r.summary}</p>

      <div className="summary">
        <div className="stat">
          <span>{t("vara")} / {t("tithi")}</span>
          <b>{T(p.vara)}</b>
          <span>{T(p.tithi.paksha)} {T(p.tithi.name)}</span>
        </div>
        <div className="stat">
          <span>{t("nakshatra")}</span>
          <b>{T(p.nakshatra.name)}</b>
          <span>{t("ends")} {tm(p.nakshatra.ends)}</span>
        </div>
        <div className="stat">
          <span>{t("chandrabala")}</span>
          <b>{T(cb.moon_sign)} ({cb.house_from_moon})</b>
          <span>
            <span className={`chip ${cb.chandrashtama ? "bad" : cb.favourable ? "good" : "mixed"}`}>{cb.label}</span>
            {" "}{t("bindus")}: {cb.bindus}
          </span>
        </div>
        {tb && (
          <div className="stat">
            <span>{t("tarabala")}</span>
            <b>{tb.name}</b>
            <span className={tb.good === false ? "err" : "note"} style={tb.good === false ? { display: "inline", padding: "1px 6px" } : undefined}>
              {tb.meaning}
            </span>
          </div>
        )}
        {r.dasha_now?.length > 0 && (
          <div className="stat">
            <span>{t("running_now")}</span>
            <b>{r.dasha_now.map(T).join(" / ")}</b>
            {r.dasha_reading && <span>{r.dasha_reading.rating_label}</span>}
          </div>
        )}
        <div className="stat">
          <span>{t("rahu_kaal")}</span>
          <b>{tm(p.rahu_kaal.start)}–{tm(p.rahu_kaal.end)}</b>
          <span>{t("sunrise")} {tm(p.sunrise)}</span>
        </div>
      </div>

      {(r.yogas?.length > 0 || r.cautions?.length > 0) && (
        <p>
          {r.yogas?.map((y: string) => <span key={y} className="chip good">{y}</span>)}
          {r.cautions?.map((c: string) => <span key={c} className="chip bad">{c}</span>)}
        </p>
      )}

      <div className="grid2" style={{ marginTop: 12 }}>
        <div className="finding benefic">
          <h4>{t("daily_favour")}</h4>
          <ul>{r.guidance.favour.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
        </div>
        <div className="finding challenging">
          <h4>{t("daily_avoid")}</h4>
          <ul>{r.guidance.avoid.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
        </div>
      </div>

      {tip && (
        <div className="finding mixed">
          <h4>{t("daily_tip")} · {T(tip.planet)}</h4>
          <p><b>{t("lucky_colour")}:</b> {tip.colour}</p>
          <p>{tip.practice}</p>
          <p className="note"><b>{t("sys_mantra")}:</b> {tip.mantra} · <b>{t("daana")}:</b> {tip.daana}</p>
        </div>
      )}

      <h3>{t("area_outlook")}</h3>
      <div className="rem">
        {r.areas.map((a: any) => (
          <div
            key={a.area}
            className="box"
            style={{ borderLeft: `4px solid var(--${rateChip(a.rating) === "good" ? "good" : rateChip(a.rating) === "mixed" ? "mixed" : "bad"})` }}
          >
            <h5>{a.title} <span className={`chip ${rateChip(a.rating)}`}>{a.rating_label}</span></h5>
            <ul>{a.reasons.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
          </div>
        ))}
      </div>

      {r.week?.length > 0 && (
        <>
          <h3>{t("next_7_days")}</h3>
          <div className="mini" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(135px,1fr))" }}>
            {r.week.map((w: any) => (
              <div
                key={w.date}
                className={`stat ${w.date === r.date ? "cur" : ""}`}
                style={{
                  cursor: onSelectDay ? "pointer" : undefined,
                  borderColor: w.date === r.date ? "var(--accent)" : undefined,
                  borderWidth: w.date === r.date ? 2 : undefined,
                }}
                onClick={() => onSelectDay?.(w.date)}
              >
                <span>{fmtD(w.date)} · {w.weekday}</span>
                <b><span className={`chip ${rateChip(w.rating)}`}>{w.rating_label}</span></b>
                <span>{T(w.nakshatra)}</span>
                <span className="note">{w.tara}{w.chandrashtama ? " · ⚠ 8th" : ""}</span>
              </div>
            ))}
          </div>
        </>
      )}

      <Fold summary={t("transits_today")}>
        <div style={{ overflow: "auto" }}>
          <table>
            <tbody>
              <tr>
                <th>{t("graha")}</th>
                <th>{t("sign")}</th>
                <th>{t("nakshatra")}</th>
                <th>{t("house")}</th>
                <th>{t("bindus")}</th>
                <th></th>
              </tr>
              {r.transits.map((x: any) => (
                <tr key={x.planet} className={rateCls(x.good ? "good" : "mixed")}>
                  <td><b>{T(x.planet)}</b></td>
                  <td>{T(x.sign)}</td>
                  <td>{T(x.nakshatra)}</td>
                  <td>
                    <span className={`chip ${x.good ? "good" : "gray"}`}>{x.house_from_moon}</span>
                    <span className="note">/{x.house_from_lagna}</span>
                  </td>
                  <td>{x.bindus ?? "—"}</td>
                  <td className="note">{x.text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Fold>

      <p className="note" style={{ marginTop: 14 }}><b>{t("method")}:</b> {r.method}</p>
      <p className="note">{r.disclaimer}</p>
    </>
  );
}
