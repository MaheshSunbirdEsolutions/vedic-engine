"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useI18n } from "@/lib/i18n";
import type { Kundli } from "@/lib/api";
import { Fold } from "./Explain";
import EmailShareButton from "./EmailShareButton";

const rateChip = (k: string) => (k === "excellent" || k === "good" ? "good" : k === "mixed" ? "mixed" : "bad");
const rateCls = (k: string) => (k === "excellent" || k === "good" ? "benefic" : k === "mixed" ? "mixed" : "challenging");

export function DailyView({
  r,
  kundli,
  chart,
  userEmail,
  lockToUserEmail = false,
  showAllDetails = false,
  onSelectDay,
}: {
  r: any;
  kundli?: Kundli;
  chart?: any;
  userEmail?: string;
  lockToUserEmail?: boolean;
  showAllDetails?: boolean;
  onSelectDay?: (day: string) => void;
}) {
  const { t, T, fmtD } = useI18n();
  const p = r.panchang;
  const cb = r.chandrabala;
  const tb = r.tarabala;
  const tip = r.daily_tip;
  const natal = r.natal || (chart ? {
    lagna: chart.lagna?.sign,
    lagna_sanskrit: chart.lagna?.sign_sanskrit,
    moon_sign: chart.planets?.Moon?.sign,
    moon_rashi_sanskrit: chart.planets?.Moon?.sign_sanskrit,
    nakshatra: chart.planets?.Moon?.nakshatra?.name,
    pada: chart.planets?.Moon?.nakshatra?.pada,
  } : null);
  const dr = r.dasha_reading;
  const dp = r.dasha_period;
  const ss = r.sade_sati;
  const tm = (s?: string) => (s ? s.slice(11, 16) : "");
  const rashiLabel = natal?.moon_sign
    ? `${T(natal.moon_sign)}${natal.moon_rashi_sanskrit && T(natal.moon_sign) !== natal.moon_rashi_sanskrit ? ` (${natal.moon_rashi_sanskrit})` : ""}`
    : "";
  const lagnaLabel = natal?.lagna
    ? `${T(natal.lagna)}${natal.lagna_sanskrit && T(natal.lagna) !== natal.lagna_sanskrit ? ` (${natal.lagna_sanskrit})` : ""}`
    : "";

  return (
    <>
      <h2>
        {kundli?.name ? `${kundli.name} · ` : ""}
        {rashiLabel ? `${t("janma_rashi")}: ${rashiLabel} · ` : ""}
        {fmtD(r.date)}{" "}
        <span className={`chip ${rateChip(r.rating)}`}>{r.rating_label}</span>
        <span className="note" style={{ marginLeft: 8 }}>{t("score")}: {r.score}</span>
      </h2>
      {kundli && (
        <EmailShareButton
          kind="kundli"
          kundli={kundli}
          userEmail={userEmail}
          lockToUserEmail={lockToUserEmail}
          tz={kundli.tz}
          lat={kundli.lat}
          lon={kundli.lon}
          day={r.date}
        />
      )}

      {natal && (
        <div className="summary" style={{ marginTop: 6 }}>
          {kundli?.name && (
            <div className="stat">
              <span>{t("name")}</span>
              <b>{kundli.name}</b>
              <span>{kundli.place || kundli.tz}</span>
            </div>
          )}
          <div className="stat" style={{ borderColor: "var(--accent)", borderWidth: 2 }}>
            <span>{t("janma_rashi")}</span>
            <b>{rashiLabel}</b>
            <span>{natal.moon_lord ? `${t("rashi_lord")}: ${T(natal.moon_lord)}` : ""}</span>
          </div>
          <div className="stat">
            <span>{t("lagna")}</span>
            <b>{lagnaLabel}</b>
            {natal.ghat_nakshatra && <span>{t("ghat_nak")}: {T(natal.ghat_nakshatra)}</span>}
          </div>
          {natal.nakshatra && (
            <div className="stat">
              <span>{t("janma_nak")}</span>
              <b>{T(natal.nakshatra)} ({t("pada")} {natal.pada})</b>
            </div>
          )}
        </div>
      )}

      <p style={{ fontSize: 15 }}>{r.summary}</p>

      <div className="summary">
        <div className="stat">
          <span>{t("vara")} / {t("tithi")}</span>
          <b>{T(p.vara)}</b>
          <span>{T(p.tithi.paksha)} {T(p.tithi.name)} ({t("ends")} {tm(p.tithi.ends)})</span>
        </div>
        <div className="stat">
          <span>{t("nakshatra")} / {t("yoga")}</span>
          <b>{T(p.nakshatra.name)}</b>
          <span>{T(p.yoga.name)} · {T(p.karana.name)}</span>
        </div>
        <div className="stat">
          <span>{t("chandrabala")}</span>
          <b>{T(cb.moon_sign)} ({cb.house_from_moon})</b>
          <span>
            <span className={`chip ${cb.chandrashtama ? "bad" : cb.favourable ? "good" : "mixed"}`}>{cb.label}</span>
            {" "}{t("bindus")}: {cb.bindus}/8 (SAV {cb.sav})
          </span>
        </div>
        {tb && (
          <div className="stat">
            <span>{t("tarabala")}</span>
            <b>{tb.name} (#{tb.index})</b>
            <span className={tb.good === false ? "err" : "note"} style={tb.good === false ? { display: "inline", padding: "1px 6px" } : undefined}>
              {tb.meaning}
            </span>
          </div>
        )}
        {r.dasha_now?.length > 0 && (
          <div className="stat">
            <span>{t("running_now")}</span>
            <b>{r.dasha_now.map(T).join(" / ")}</b>
            {dr && <span>{dr.rating_label}{dp ? ` (${fmtD(dp.start)} → ${fmtD(dp.end)})` : ""}</span>}
          </div>
        )}
        <div className="stat">
          <span>{t("rahu_kaal")} / {t("abhijit_muhurta")}</span>
          <b>{tm(p.rahu_kaal.start)}–{tm(p.rahu_kaal.end)}</b>
          <span>
            {p.abhijit ? `${t("abhijit_muhurta")}: ${tm(p.abhijit.start)}–${tm(p.abhijit.end)}` : `${t("sunrise")} ${tm(p.sunrise)}`}
          </span>
        </div>
      </div>

      {(r.yogas?.length > 0 || r.cautions?.length > 0 || ss?.sade_sati || ss?.dhaiya) && (
        <p>
          {r.yogas?.map((y: string) => <span key={y} className="chip good">{y}</span>)}
          {r.cautions?.map((c: string) => <span key={c} className="chip bad">{c}</span>)}
          {ss?.sade_sati && <span className="chip mixed">{t("sade_sati_status")}: {T(ss.phase)}</span>}
          {!ss?.sade_sati && ss?.dhaiya && <span className="chip mixed">{t("sade_sati_status")}: {T(ss.dhaiya)}</span>}
        </p>
      )}

      {dr && (
        <div className={`finding ${rateCls(dr.rating)}`} style={{ marginTop: 10 }}>
          <h4>
            {t("dasha_backdrop")}: {r.dasha_now.map(T).join(" / ")}{" "}
            <span className={`chip ${rateChip(dr.rating)}`}>{dr.rating_label}</span>
          </h4>
          {dr.themes?.length > 0 && <p><b>{t("dasha_themes")}:</b> {dr.themes.join(" · ")}</p>}
          {dr.karaka && <p><b>{t("karaka_focus")}:</b> {dr.karaka}</p>}
          {dr.reasons?.length > 0 && <p className="note">{dr.reasons.join(" · ")}</p>}
        </div>
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
          <p>
            <b>{t("lucky_colour")}:</b> {tip.colour}
            {tip.lucky_numbers?.length > 0 && <> · <b>{t("lucky_numbers")}:</b> {tip.lucky_numbers.join(", ")}</>}
            {tip.deity && <> · <b>{t("deity_worship")}:</b> {tip.deity}</>}
          </p>
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
            {a.text && <p style={{ margin: "4px 0 6px" }}>{a.text}</p>}
            <ul>{a.reasons.map((x: string, i: number) => <li key={i} className="note">{x}</li>)}</ul>
          </div>
        ))}
      </div>

      {r.health_watch?.length > 0 && (
        <div className="finding" style={{ marginTop: 12 }}>
          <h4>{t("health_watch")}</h4>
          <ul>
            {r.health_watch.map((hw: any) => (
              <li key={hw.kind}>
                <b>{hw.kind === "birth" ? t("birth_nak_watch") : t("today_nak_watch")} ({T(hw.nakshatra)}):</b>{" "}
                {hw.parts} <span className="note">({hw.watch})</span>
              </li>
            ))}
          </ul>
          <p className="note" style={{ marginBottom: 0 }}>{t("health_disclaimer")}</p>
        </div>
      )}

      {r.week?.length > 0 && (
        <>
          <h3>{t("next_7_days")}</h3>
          <div className="mini" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(145px,1fr))" }}>
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
                <span>{T(w.moon_sign)} (+{w.house_from_moon})</span>
                <span className="note">{T(w.nakshatra)} · {w.tara}{w.chandrashtama ? " · ⚠ 8th" : ""}</span>
              </div>
            ))}
          </div>
        </>
      )}

      <Fold summary={t("transits_today")} open={showAllDetails}>
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
