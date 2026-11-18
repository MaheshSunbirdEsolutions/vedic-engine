"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// Shared report pieces: a planet's placement in plain words, the full multi-system remedy set,
// and the bhav (house) table. Used by every report so positions are always explained.
import { createContext, useContext, type ReactNode } from "react";
import { useI18n } from "@/lib/i18n";

export const ExpandCtx = createContext(false);

const strengthChip = (s: string) => (s === "strong" ? "good" : s === "weak" ? "bad" : "gray");
const ordEn = (n: number) => (n === 1 ? "1st" : n === 2 ? "2nd" : n === 3 ? "3rd" : `${n}th`);

/** "Saturn · 2nd house (Dhana bhav) · Virgo" + strength + the paragraph. */
export function PlacementCard({ pl, compact = false }: { pl: any; compact?: boolean }) {
  const { t, T, lang } = useI18n();
  const houseLabel = lang === "hi" ? `${pl.house}वाँ भाव (${pl.bhav})` : `${ordEn(pl.house)} house (${pl.bhav})`;
  return (
    <div className={`finding ${pl.strength === "weak" ? "challenging" : pl.strength === "strong" ? "benefic" : "mixed"}`}>
      <h4>
        {T(pl.planet)} · {houseLabel} · {T(pl.sign)} {pl.degree}
        {" "}<span className={`chip ${strengthChip(pl.strength)}`}>{t("strength_" + pl.strength)}</span>
        {pl.retrograde && <span className="chip gray">{T("retrograde") !== "retrograde" ? T("retrograde") : "R"}</span>}
        {pl.combust && <span className="chip bad">{lang === "hi" ? "अस्त" : "combust"}</span>}
      </h4>
      {!compact && pl.owns?.length > 0 && (
        <div className="note" style={{ marginBottom: 4 }}>
          {lang === "hi" ? "स्वामी: " : "Rules: "}
          {pl.owns_meaning.map((o: any) => <span key={o.house} className="chip gray">{lang === "hi" ? `भाव ${o.house}` : `H${o.house}`} – {o.meaning.split(",").slice(0, 2).join(",")}</span>)}
        </div>)}
      <p style={{ fontSize: 14 }}>{pl.text}</p>
    </div>);
}

/** All remedy systems for one planet, with the strengthen / pacify approach on top. */
export function RemedySet({ fs, title }: { fs: any; title?: ReactNode }) {
  const { t, lang } = useI18n();
  return (
    <div style={{ marginTop: 8 }}>
      {title}
      <p style={{ margin: "6px 0" }}>
        <span className={`chip ${fs.approach === "strengthen" ? "good" : "mixed"}`}>{t("approach_" + fs.approach)}</span>{" "}
        {fs.approach_text}
      </p>
      <div className="rem">
        {fs.systems.map((s: any) => (
          <div key={s.id} className="box" style={s.tone === "bad" ? { borderColor: "var(--bad)" } : s.tone === "good" ? { borderColor: "var(--good)" } : undefined}>
            <h5>{t("sys_" + s.id)}{s.id === "gem" && fs.gem_verdict && (
              <span className={`chip ${s.tone || "gray"}`} style={{ marginLeft: 6 }}>{GEM_LABEL[fs.gem_verdict]?.[lang === "hi" ? 1 : 0]}</span>)}</h5>
            {s.items.length ? <ul>{s.items.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul> : null}
            {s.note && <div className="note">{s.note}</div>}
            <div className="note" style={{ marginTop: 4 }}>{s.source}</div>
          </div>))}
      </div>
      <p className="note">{t("rem_order_note")}</p>
    </div>);
}

const GEM_LABEL: Record<string, [string, string]> = {
  suitable: ["may suit", "उपयुक्त"], avoid: ["avoid", "न पहनें"], caution: ["expert check first", "पहले जाँच"] };

/** Collapsible block that follows the report's Expand-all toggle. */
export function Fold({ summary, children, open }: { summary: ReactNode; children: ReactNode; open?: boolean }) {
  const all = useContext(ExpandCtx);
  return (
    <details open={open || all} key={String(open || all)}>
      <summary style={{ fontWeight: 600, color: "var(--accent)" }}>{summary}</summary>
      {children}
    </details>);
}

export function BhavTable({ rows }: { rows: any[] }) {
  const { t, T } = useI18n();
  return (
    <div style={{ overflow: "auto" }}><table><tbody>
      <tr><th>#</th><th>{t("bhav")}</th><th>{t("meaning")}</th><th>{t("sign")}</th><th>{t("lord_in")}</th><th>{t("occupants")}</th></tr>
      {rows.map((r) => (
        <tr key={r.house}><td><b>{r.house}</b></td><td>{r.name}</td><td className="note">{r.meaning}</td><td>{T(r.sign)}</td>
          <td>{T(r.lord)} → {r.lord_in}</td><td>{r.occupants.map(T).join(", ") || "—"}</td></tr>))}
    </tbody></table></div>);
}

/** Remedy plan: one section per afflicted planet – why, where it sits, every remedy. */
export function RemedyPlan({ plan }: { plan: any[] }) {
  const { t, T } = useI18n();
  if (!plan?.length) return null;
  return (<>
    <h2>{t("remedy_plan")}</h2>
    {plan.map((fs) => (
      <div key={fs.planet} className="issue">
        <div className="head"><h3 style={{ margin: 0 }}>{T(fs.planet)}</h3>
          <span className={`chip ${fs.severity >= 3 ? "bad" : "mixed"}`}>{t("severity")} {fs.severity}</span></div>
        <p><b>{t("why_afflicted")}:</b> {fs.reasons.join("; ")}</p>
        <PlacementCard pl={fs.placement} />
        <Fold summary={`${t("all_remedies")} ${T(fs.planet)}`} open><RemedySet fs={fs} /></Fold>
      </div>))}
  </>);
}

/** Upcoming auspicious days (Guru/Ravi-Pushya, Amrit/Sarvartha-siddhi, Ravi yoga) to begin remedies. */
export function RemedyDays({ days, note }: { days: any[]; note?: string }) {
  const { t, T, fmtD } = useI18n();
  if (!days?.length) return null;
  return (<>
    <h2>{t("remedy_days")}</h2>
    {note && <p className="note">{note}</p>}
    <div style={{ overflow: "auto" }}><table><tbody>
      <tr><th>{t("date")}</th><th>{t("weekday")}</th><th>{t("nakshatra")}</th><th>{t("yogas")}</th><th>{t("tara")}</th><th>{t("for_planet")}</th></tr>
      {days.map((d) => (
        <tr key={d.date} className={d.for_planets?.length ? "cur" : ""}>
          <td><b>{fmtD(d.date)}</b></td><td>{d.weekday}</td>
          <td>{T(d.nakshatra)} <span className="note">({T(d.tithi)})</span></td>
          <td>{d.yogas.map((y: string) => <span key={y} className="chip good">{y}</span>)}</td>
          <td>{d.tara}</td><td>{d.for_planets?.map(T).join(", ") || "—"}</td>
        </tr>))}
    </tbody></table></div>
    <p className="note">R. P. Gaur, Nakshatra Jyotish – ch. 8 (muhurta), pp. 173–179</p>
  </>);
}

export function NakDoshas({ list, showEmpty = false }: { list: any[]; showEmpty?: boolean }) {
  const { t } = useI18n();
  if (!list?.length) return showEmpty ? <><h3>{t("nak_doshas")}</h3><p className="note">{t("no_nak_doshas")}</p></> : null;
  return (<>
    <h3>{t("nak_doshas")}</h3>
    {list.map((x, i) => (
      <div key={i} className={`finding ${x.severity >= 2 ? "challenging" : "mixed"}`}>
        <h4>{x.text} <span className={`chip ${x.severity >= 3 ? "bad" : "mixed"}`}>{t("severity")} {x.severity}</span></h4>
        <b>{t("remedies")}:</b><ul>{x.remedies.map((r: string, k: number) => <li key={k}>{r}</li>)}</ul>
        <div className="src">{x.source}</div>
      </div>))}
  </>);
}

export function HealthWatch({ rows }: { rows: any[] }) {
  const { t, T } = useI18n();
  if (!rows?.length) return null;
  return (<>
    <h3>{t("health_watch")}</h3>
    <div style={{ overflow: "auto" }}><table><tbody>
      <tr><th>{t("point")}</th><th>{t("nakshatra")}</th><th>{t("body_parts")}</th><th>{t("watch_for")}</th></tr>
      {rows.map((r, i) => <tr key={i}><td><b>{T(r.point)}</b></td><td>{T(r.nakshatra)}</td><td>{r.parts}</td><td className="note">{r.watch}</td></tr>)}
    </tbody></table></div>
    <p className="note">{t("health_disclaimer")} · {rows[0].source}</p>
  </>);
}
