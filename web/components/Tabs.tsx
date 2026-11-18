"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { useI18n } from "@/lib/i18n";
import { Kundli, SIGNS, useLabels } from "./Charts";

const DIG: Record<string, string> = { exalted: "good", own: "good", moolatrikona: "good", debilitated: "bad", enemy: "bad" };
const NAT: Record<string, string> = { benefic: "good", challenging: "bad", mixed: "mixed" };
export const isCurrent = (p: { start: string; end: string }) => { const n = new Date(); return new Date(p.start) <= n && n < new Date(p.end); };

export function ChartTab({ c }: { c: any }) {
  const { t, T, lang } = useI18n();
  const labels = useLabels();
  const [style, setStyle] = useState<"north" | "south">("north");
  const retro = Object.fromEntries(Object.entries<any>(c.planets).map(([p, v]) => [p, v.retrograde && !["Rahu", "Ketu"].includes(p)]));
  const d1 = Object.fromEntries(Object.entries<any>(c.planets).map(([p, v]) => [p, v.sign_index - 1]));
  const d9 = Object.fromEntries(Object.entries<any>(c.vargas.D9.planets).map(([p, s]) => [p, SIGNS.indexOf(s as string)]));
  const m = c.planets.Moon, ds = c.doshas;
  return (
    <div>
      <div className="summary">
        <div className="stat"><span>{t("lagna")}</span><b>{T(c.lagna.sign)} {c.lagna.degree_in_sign}</b></div>
        <div className="stat"><span>{t("moon_sign")}</span><b>{T(m.sign)}</b></div>
        <div className="stat"><span>{t("nakshatra")}</span><b>{T(m.nakshatra.name)} · {t("pada")} {m.nakshatra.pada}</b></div>
        <div className="stat"><span>{t("ayanamsa")} ({c.ayanamsa.name})</span><b>{c.ayanamsa.dms}</b></div>
        <div className="stat"><span>{t("doshas")}</span><b>
          {ds.manglik.present && <span className="chip bad">{t("manglik")}</span>}
          {ds.kaal_sarp.present && <span className="chip bad">{t("kaal_sarp")}</span>}
          {!ds.manglik.present && !ds.kaal_sarp.present && <span className="chip good">{t("none")}</span>}</b></div>
      </div>
      <div style={{ marginBottom: 8 }}><span className="note">{t("chart_style")}</span>
        <button className="ghost" onClick={() => setStyle("north")}>{style === "north" ? <b>{t("north")}</b> : t("north")}</button>
        <button className="ghost" onClick={() => setStyle("south")}>{style === "south" ? <b>{t("south")}</b> : t("south")}</button></div>
      <div className="charts">
        <div className="chartbox"><div className="cap">{t("d1")}</div><Kundli style={style} lagna={c.lagna.sign_index - 1} bySign={labels(d1, retro)} /></div>
        <div className="chartbox"><div className="cap">{t("d9")}</div><Kundli style={style} lagna={SIGNS.indexOf(c.vargas.D9.lagna)} bySign={labels(d9)} /></div>
      </div>
      <h3>{t("positions")}</h3>
      <div style={{ overflow: "auto" }}><table><tbody>
        <tr><th>{t("graha")}</th><th>{t("sign")}</th><th>{t("degree")}</th><th>{t("nakshatra")}</th><th>{t("nak_lord")}</th><th>{t("house")}</th><th>{t("dignity")}</th><th>D9</th><th>D10</th></tr>
        <tr><td><b>{T("Lagna")}</b></td><td>{T(c.lagna.sign)}</td><td>{c.lagna.degree_in_sign}</td><td>{T(c.lagna.nakshatra.name)} ({c.lagna.nakshatra.pada})</td><td>{T(c.lagna.nakshatra.lord)}</td><td>1</td><td /><td>{T(c.lagna.vargas.D9)}</td><td>{T(c.lagna.vargas.D10)}</td></tr>
        {Object.entries<any>(c.planets).map(([p, v]) => (
          <tr key={p}><td><b>{T(p)}</b>{retro[p] && <span className="chip gray"> {lang === "en" ? "R" : "वक्री"}</span>}</td><td>{T(v.sign)}</td><td>{v.degree_in_sign}</td>
            <td>{T(v.nakshatra.name)} ({v.nakshatra.pada})</td><td>{T(v.nakshatra.lord)}</td><td>{v.house}</td>
            <td>{v.dignity === "n/a" ? "—" : <span className={`chip ${DIG[v.dignity] || "gray"}`}>{T(v.dignity)}</span>}</td>
            <td>{T(v.vargas.D9)}</td><td>{T(v.vargas.D10)}</td></tr>))}
      </tbody></table></div>
      <h3>{t("houses_title")}</h3>
      <div style={{ overflow: "auto" }}><table><tbody>
        <tr><th>{t("house")}</th><th>{t("sign")}</th><th>{t("lord")}</th><th>{t("occupants")}</th></tr>
        {c.houses.map((h: any) => <tr key={h.house}><td>{h.house}</td><td>{T(h.sign)}</td><td>{T(h.lord)}</td><td>{h.planets.map(T).join(", ") || "—"}</td></tr>)}
      </tbody></table></div>
    </div>
  );
}

export function DashaTab({ d }: { d: any }) {
  const { t, T, fmtD } = useI18n();
  const [openMd, setOpenMd] = useState<Record<number, boolean>>(() => Object.fromEntries(d.mahadashas.map((m: any, i: number) => [i, isCurrent(m)])));
  const [openAd, setOpenAd] = useState<Record<string, boolean>>(() => {
    const o: Record<string, boolean> = {};
    d.mahadashas.forEach((m: any, i: number) => m.sub.forEach((a: any, j: number) => { if (isCurrent(a)) o[`${i}-${j}`] = true; }));
    return o;
  });
  return (
    <div>
      <div className="summary">
        <div className="stat"><span>{t("birth_dasha")}</span><b>{T(d.birth_dasha.lord)} · {d.birth_dasha.balance_years.toFixed(2)} {t("yrs_left")}</b></div>
        <div className="stat"><span>{t("running_now")}</span><b>{d.current.map(T).join(" / ") || "—"}</b></div>
      </div>
      <p className="note">{t("dasha_hint")}</p>
      <table><tbody>
        <tr><th>{t("period")}</th><th>{t("start")}</th><th>{t("end")}</th></tr>
        {d.mahadashas.map((md: any, i: number) => [
          <tr key={`m${i}`} className={`dasha-row ${isCurrent(md) ? "cur" : ""}`} onClick={() => setOpenMd({ ...openMd, [i]: !openMd[i] })}>
            <td><b>{T(md.lord)}</b> {t("mahadasha")}</td><td>{fmtD(md.start)}</td><td>{fmtD(md.end)}</td></tr>,
          ...(openMd[i] ? md.sub.flatMap((ad: any, j: number) => [
            <tr key={`a${i}-${j}`} className={`dasha-row lvl2 ${isCurrent(ad) ? "cur" : ""}`} onClick={() => setOpenAd({ ...openAd, [`${i}-${j}`]: !openAd[`${i}-${j}`] })}>
              <td>{T(md.lord)} – {T(ad.lord)}</td><td>{fmtD(ad.start)}</td><td>{fmtD(ad.end)}</td></tr>,
            ...(openAd[`${i}-${j}`] ? (ad.sub || []).map((pd: any, k: number) => (
              <tr key={`p${i}-${j}-${k}`} className={`lvl3 ${isCurrent(pd) ? "cur" : ""}`}><td>{T(ad.lord)} – {T(pd.lord)}</td><td>{fmtD(pd.start)}</td><td>{fmtD(pd.end)}</td></tr>)) : []),
          ]) : []),
        ])}
      </tbody></table>
    </div>
  );
}

export function InterpTab({ r }: { r: any }) {
  const { t, T } = useI18n();
  return (
    <div>
      <p className="note" dangerouslySetInnerHTML={{ __html: t("interp_note") }} />
      {["yoga", "dosha", "placement"].map((cat) => {
        const fs = r.findings.filter((f: any) => f.category === cat);
        return (
          <div key={cat}>
            <h3>{t("cat_" + cat)} ({fs.length})</h3>
            {!fs.length && <p className="note">{t("none_found")}</p>}
            {fs.map((f: any) => (
              <div key={f.id} className={`finding ${f.nature}`}>
                <h4>{f.name} <span className={`chip ${NAT[f.nature] || "gray"}`}>{t(f.nature)}</span>{f.status === "draft" && <span className="chip gray">{t("draft")}</span>}</h4>
                <p>{f.text}</p>
                <div className="src">{t("source")}: {f.source}{f.planets.length > 0 && ` · ${t("planets")}: ${f.planets.map(T).join(", ")}`}</div>
              </div>))}
          </div>);
      })}
    </div>
  );
}

export function SadeTab({ s }: { s: any }) {
  const { t, T, fmtD } = useI18n();
  const n = s.now;
  const cur = (p: any) => new Date(p.start) <= new Date() && (!p.end || new Date() < new Date(p.end));
  return (
    <div>
      <div className="summary">
        <div className="stat"><span>{t("natal_moon")}</span><b>{T(s.moon_sign)}</b></div>
        <div className="stat"><span>{t("saturn_today")}</span><b>{T(n.saturn_sign)}</b></div>
        <div className="stat"><span>{t("sade_now")}</span><b>{n.sade_sati ? <span className="chip bad">{t("yes")} · {T(n.phase)}</span> : <span className="chip good">{t("no")}</span>}</b></div>
        <div className="stat"><span>{t("dhaiya")}</span><b>{n.dhaiya ? <span className="chip mixed">{T(n.dhaiya)}</span> : "—"}</b></div>
      </div>
      <h3>{t("lifetime_sade")}</h3>
      <table><tbody>
        <tr><th>{t("from")}</th><th>{t("to")}</th><th>{t("phases")}</th></tr>
        {s.periods.map((p: any, i: number) => (
          <tr key={i} className={cur(p) ? "cur" : ""}><td>{fmtD(p.start)}</td><td>{p.end ? fmtD(p.end) : "—"}</td>
            <td>{p.phases.map((ph: any, k: number) => <span key={k} className="chip gray">{T(ph.sign)}: {T(ph.phase)} · {fmtD(ph.from)}</span>)}</td></tr>))}
      </tbody></table>
      <p className="note">{t("sade_note")}</p>
    </div>
  );
}
