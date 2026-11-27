"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api, birthOf, nowIn, type Kundli as K } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Kundli, NorthChart, SIGNS, useLabels } from "./Charts";
import { isCurrent } from "./Tabs";
import { BhavTable, ExpandCtx, Fold, HealthWatch, NakDoshas, PlacementCard, RemedyDays, RemedyPlan, RemedySet } from "./Explain";
import { DailyView } from "./DailyReport";

const REPORTS = [
  { key: "simple", ep: "simple", label: "rep_simple" },
  { key: "daily", ep: "daily", label: "rep_daily" },
  { key: "lifepred", ep: "lifelong", label: "rep_life_pred" }, { key: "yearpred", ep: "yearly", label: "rep_year_pred" },
  { key: "issues", ep: "issues", label: "rep_issues" }, { key: "wrong", ep: "full", label: "rep_wrong" },
  { key: "full", ep: "full", label: "rep_full" }, { key: "life", ep: "life-areas", label: "rep_life" },
  { key: "varsh", ep: "varshphal", label: "rep_varsh" }, { key: "lk", ep: "lal-kitab", label: "rep_lk" },
  { key: "nak", ep: "nakshatra", label: "rep_nakshatra" }, { key: "tirtha", ep: "tirtha", label: "rep_tirtha" }, { key: "bhrigu", ep: "bhrigu", label: "rep_bhrigu" },
];
const pad3 = (n: number) => String(n).padStart(3, "0");

export default function Reports({ kundli, chart }: { kundli: K; chart: any }) {
  const { t, lang } = useI18n();
  const [rep, setRep] = useState("simple");
  const [year, setYear] = useState(new Date().getFullYear());
  const [day, setDay] = useState(() => nowIn(kundli.tz).slice(0, 10));
  const [data, setData] = useState<Record<string, any>>({});
  const [err, setErr] = useState("");
  const [books, setBooks] = useState({ lalkitab: 0, bhrigu: 0 });
  const [expand, setExpand] = useState(false);
  const cur = REPORTS.find((r) => r.key === rep)!;
  const key = `${cur.ep}|${lang}|${rep === "daily" ? day : year}`;

  useEffect(() => { api("/books/status").then(setBooks).catch(() => {}); }, []);
  useEffect(() => {
    if (data[key]) return;
    setErr("");
    api(`/report/${cur.ep}`, { ...birthOf(kundli), lang, year, day, at: nowIn(kundli.tz) })
      .then((d) => setData((x) => ({ ...x, [key]: d }))).catch((e) => setErr(e.message));
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const d = data[key];
  return (
    <div>
      <div className="subtabs noprint">
        {REPORTS.map((r) => <button key={r.key} className={rep === r.key ? "on" : ""} onClick={() => setRep(r.key)}>{t(r.label)}</button>)}
      </div>
      <div className="noprint btnrow" style={{ marginBottom: 10, alignItems: "end" }}>
        {rep === "daily"
          ? <div style={{ maxWidth: 180 }}><label>{t("date")}</label><input type="date" value={day} onChange={(e) => setDay(e.target.value)} /></div>
          : <div style={{ maxWidth: 140 }}><label>{t("year")}</label><input type="number" value={year} onChange={(e) => setYear(+e.target.value)} /></div>}
        <button className="ghost" onClick={() => setExpand((x) => !x)}>{expand ? t("collapse_all") : t("expand_all")}</button>
        <button className="ghost" onClick={() => { setExpand(true); setTimeout(() => window.print(), 300); }}>{t("print")}</button>
      </div>
      {err && <p className="err" style={{ display: "block" }}>{err}</p>}
      {!d && !err && <div className="empty">{t("loading")}</div>}
      {d && (
        <ExpandCtx.Provider value={expand}>
        <div className="rep">
          <HeaderBlock title={t(cur.label) + (rep === "varsh" ? ` ${d.year}` : "")} kundli={kundli} chart={chart} />
          {rep === "simple" && <Simple r={d} />}
          {rep === "daily" && <DailyView r={d} onSelectDay={setDay} />}
          {rep === "issues" && <Issues r={d} books={books} />}
          {rep === "wrong" && <Wrong r={d} />}
          {rep === "full" && <Full r={d} />}
          {rep === "life" && <Life r={d} />}
          {rep === "varsh" && <Varsh r={d} books={books} />}
          {rep === "lk" && <LK r={d} books={books} />}
          {rep === "nak" && <Nak r={d} />}
          {rep === "tirtha" && <Tirtha r={d} />}
          {rep === "lifepred" && <LifePred r={d} />}
          {rep === "yearpred" && <YearPred r={d} setYear={setYear} />}
          {rep === "bhrigu" && <Bhrigu r={d} books={books} />}
        </div>
        </ExpandCtx.Provider>)}
    </div>
  );
}

function HeaderBlock({ title, kundli, chart }: { title: string; kundli: K; chart: any }) {
  const { t, T } = useI18n();
  return (<><h2>{title}</h2>
    <p className="note">{kundli.name} · {kundli.datetime_local.replace("T", " ")} · {kundli.place} · {t("lagna")}: {T(chart.lagna.sign)} · {t("moon_sign")}: {T(chart.planets.Moon.sign)} · {t("nakshatra")}: {T(chart.planets.Moon.nakshatra.name)}</p></>);
}

function PageLinks({ kind, pages, books, offset = 0 }: { kind: "lalkitab" | "bhrigu"; pages: number[]; books: any; offset?: number }) {
  const { t } = useI18n();
  if (!books[kind]) return <span className="note">{t("books_missing")}</span>;
  return <>{pages.map((p) => (
    <a key={p} href={`/books/${kind}/p${pad3(p)}.jpg`} target="_blank" rel="noopener noreferrer" className="chip gray" style={{ textDecoration: "none" }}>
      {t("view_page")} {kind === "lalkitab" ? (p <= 142 ? p - 20 : p - 22) : p + offset}</a>))}</>;
}

const sevClass = (n: number) => (n >= 3 ? "bad" : n === 2 ? "mixed" : "gray");

function AfflList({ list }: { list: any[] }) {
  const { t } = useI18n();
  const area = (a: string) => (t("area_" + a) !== "area_" + a ? t("area_" + a) : a.replace(/_/g, " "));
  if (!list.length) return <p className="note">{t("no_afflictions")}</p>;
  return <>{["dosha", "yuti", "position"].map((cat) => {
    const xs = list.filter((a) => a.category === cat);
    if (!xs.length) return null;
    return (<div key={cat}><h3>{t("cat_" + cat)} ({xs.length})</h3>
      {xs.map((a, i) => (
        <div key={i} className={`finding ${a.severity >= 3 ? "challenging" : a.severity === 2 ? "mixed" : ""}`}>
          <h4>{a.text} <span className={`chip ${sevClass(a.severity)}`}>{t("severity")} {a.severity}</span></h4>
          <div className="src">{t("house")}: {a.houses.join(", ")} · {t("affects")}: {a.areas.map(area).join(", ")}</div>
        </div>))}</div>);
  })}</>;
}

function RinBlock({ rin, rules }: { rin: any[]; rules?: any[] }) {
  const { t, T } = useI18n();
  return (<>
    <h2>{t("rin")}</h2>
    {rin.length ? rin.map((x, i) => (
      <div key={i} className="finding challenging"><h4>{x.name}</h4>
        <p><b>{t("rin_trigger")}:</b> {x.trigger.map(T).join(", ")} → {t("house")} {x.houses.join("/")}</p>
        <p><b>{t("rin_sign")}:</b> {x.sign}</p><p><b>{t("family_upay")}:</b> {x.upay}</p><div className="src">{x.source}</div></div>))
      : <p className="note">{t("no_rin")}</p>}
    {rules?.length ? <><h3>{t("upay_rules")}</h3><ul>{rules.map((r, i) => <li key={i}>{r.text} <span className="note">({r.source})</span></li>)}</ul></> : null}
  </>);
}

function Issues({ r }: { r: any; books: any }) {
  const { t, T, fmtD, lang } = useI18n();
  const tp = r.tithi_pravesha, ss = r.sade_sati;
  return (<>
    <div className="summary">
      <div className="stat"><span>{t("as_of")}</span><b>{fmtD(r.as_of)}</b></div>
      <div className="stat"><span>{t("running_now")}</span><b>{r.dasha_now.map(T).join(" / ")}</b></div>
      <div className="stat"><span>{t("age_running")}</span><b>{r.age_running}</b></div>
      {tp && <div className="stat"><span>{t("tp")}</span><b>{fmtD(tp.moment)} → {fmtD(tp.valid_until)}</b><span>{t("vara_lord")}: {T(tp.vara_lord)} · {t("hora_lord")}: {T(tp.hora_lord)}</span></div>}
      <div className="stat"><span>{t("tab_sade")}</span><b>{ss.sade_sati ? T(ss.phase) : ss.dhaiya ? T(ss.dhaiya) : t("no")}</b></div>
    </div>
    {r.issues.map((i: any) => (
      <div key={i.rank} className="issue">
        <div className="head"><div className="rank">{i.rank}</div><h3 style={{ margin: 0 }}>{i.area_name}</h3>
          <span className={`chip ${i.priority === "high" ? "bad" : i.priority === "medium" ? "mixed" : "gray"}`}>{t(i.priority)}</span>
          <span className="note">{t("key_planet")}: <b>{T(i.key_planet)}</b> · {lang === "hi" ? "अंक" : "score"} {i.score}</span></div>
        <div className="bar" style={{ margin: "8px 0" }}><i style={{ width: `${Math.min(100, i.score * 7)}%` }} /></div>
        {i.house_info && <p className="note">{t("this_house")} <b>{i.house_info.house} – {i.house_info.name}</b>: {i.house_info.meaning}</p>}
        <b>{t("why")}:</b><ul>{i.evidence.map((e: any, k: number) => <li key={k}>{e.text} <span className="note">({e.source})</span></li>)}</ul>
        <b>{t("key_planet")}:</b><PlacementCard pl={i.remedies.full.placement} />
        {i.other_planets?.length > 0 && <Fold summary={t("also_involved")}>{i.other_planets.map((pl: any) => <PlacementCard key={pl.planet} pl={pl} compact />)}</Fold>}
        <Fold summary={`${t("remedies")} – ${T(i.key_planet)}`} open={i.rank <= 2}><RemedySet fs={i.remedies.full} /></Fold>
      </div>))}
    <RemedyDays days={r.remedy_days} note={r.remedy_days_note} />
    {r.nakshatra_doshas?.length > 0 && <NakDoshas list={r.nakshatra_doshas} />}
    <HealthWatch rows={r.health_watch} />
    <RinBlock rin={r.rin} rules={r.upay_rules} />
    <h2>{t("natal_afflictions")}</h2><AfflList list={r.natal_afflictions} />
    <p className="note">{r.disclaimer}</p>
  </>);
}

function Wrong({ r }: { r: any }) {
  const { t } = useI18n();
  const bad = r.interpretation.filter((f: any) => f.nature === "challenging" || f.category === "dosha");
  return (<><AfflList list={r.afflictions} />
    <NakDoshas list={r.nakshatra_doshas || []} />
    <RemedyPlan plan={r.remedy_plan} />
    {bad.length > 0 && <><h2>{t("cat_dosha")} / {t("cat_yoga")}</h2>
      {bad.map((f: any) => <div key={f.id} className="finding challenging"><h4>{f.name}</h4><p>{f.text}</p><div className="src">{t("source")}: {f.source}</div></div>)}</>}</>);
}

function Full({ r }: { r: any }) {
  const { t, T, lang, fmtD } = useI18n();
  const labels = useLabels();
  const c = r.chart, j = r.jaimini, av = r.ashtakavarga;
  const vargas = Object.keys(c.vargas);
  const vmap = (D: string) => Object.fromEntries(Object.entries<any>(c.vargas[D].planets).map(([p, s]) => [p, SIGNS.indexOf(s)]));
  const d1 = Object.fromEntries(Object.entries<any>(c.planets).map(([p, v]) => [p, v.sign_index - 1]));
  const short = (s: string) => (lang === "en" ? s.slice(0, 3) : T(s));
  return (<>
    <div className="mini">
      {["D1", "D9", "D10", "D2", "D4", "D7", "D12", "D24", "D60"].map((D) => (
        <div key={D} className="chartbox"><div className="cap">{D}</div>
          <NorthChart lagna={D === "D1" ? c.lagna.sign_index - 1 : SIGNS.indexOf(c.vargas[D].lagna)} bySign={labels(D === "D1" ? d1 : vmap(D))} /></div>))}
    </div>
    <h3>{t("positions")}</h3>
    <div style={{ overflow: "auto" }}><table><tbody>
      <tr><th>{t("graha")}</th><th>{t("sign")}</th><th>{t("degree")}</th><th>{t("nakshatra")}</th><th>{t("house")}</th><th>{t("dignity")}</th></tr>
      {Object.entries<any>(c.planets).map(([p, v]) => <tr key={p}><td><b>{T(p)}</b></td><td>{T(v.sign)}</td><td>{v.degree_in_sign}</td><td>{T(v.nakshatra.name)} ({v.nakshatra.pada})</td><td>{v.house}</td><td>{v.dignity === "n/a" ? "—" : T(v.dignity)}</td></tr>)}
    </tbody></table></div>
    <h3>{t("bhav_table")}</h3><BhavTable rows={r.bhavas} />
    <h3>{t("planets_explained")}</h3>
    {r.placements.map((pl: any) => <PlacementCard key={pl.planet} pl={pl} />)}
    <h3>{t("vargas_all")}</h3>
    <div style={{ overflow: "auto" }}><table><tbody>
      <tr><th>{t("graha")}</th>{vargas.map((D) => <th key={D}>{D}</th>)}</tr>
      <tr><td><b>{T("Lagna")}</b></td>{vargas.map((D) => <td key={D}>{short(c.vargas[D].lagna)}</td>)}</tr>
      {Object.keys(c.planets).map((p) => <tr key={p}><td><b>{T(p)}</b></td>{vargas.map((D) => <td key={D}>{short(c.vargas[D].planets[p])}</td>)}</tr>)}
    </tbody></table></div>
    <div className="grid2">
      <div><h3>{t("karakas")}</h3><table><tbody>{Object.entries<any>(j.karakas).map(([k, v]) => <tr key={k}><td><b>{k}</b></td><td>{T(v.planet)}</td><td className="note">{v.meaning}</td></tr>)}</tbody></table></div>
      <div><h3>{t("arudhas")}</h3><table><tbody>{Object.entries<any>(j.arudhas).map(([k, v]) => <tr key={k}><td><b>{k}</b></td><td>{T(v)}</td><td>{t("house")} {j.arudha_houses[k]}</td></tr>)}</tbody></table></div>
    </div>
    <h3>{t("sav")}</h3>
    <div style={{ overflow: "auto" }}><table><tbody>
      <tr>{av.signs.map((s: string) => <th key={s}>{short(s)}</th>)}<th>Σ</th></tr>
      <tr>{av.sav.map((x: number, i: number) => <td key={i} style={x >= 30 ? { color: "var(--good)", fontWeight: 700 } : x < 25 ? { color: "var(--bad)", fontWeight: 700 } : {}}>{x}</td>)}<td><b>{av.sav.reduce((a: number, b: number) => a + b, 0)}</b></td></tr>
    </tbody></table></div>
    <h3>{t("dasha_ad")}</h3>
    <table><tbody>
      <tr><th>{t("mahadasha")}</th><th>{t("start")}</th><th>{t("end")}</th><th>AD</th></tr>
      {r.dasha.mahadashas.map((md: any) => <tr key={md.start} className={isCurrent(md) ? "cur" : ""}><td><b>{T(md.lord)}</b></td><td>{fmtD(md.start)}</td><td>{fmtD(md.end)}</td>
        <td className="note">{md.sub.map((a: any) => `${T(a.lord)} ${a.start.slice(0, 7)}`).join(" · ")}</td></tr>)}
    </tbody></table>
    <h2>{t("tab_interp")}</h2>
    {r.interpretation.map((f: any) => <div key={f.id} className={`finding ${f.nature}`}><h4>{f.name}</h4><p>{f.text}</p><div className="src">{t("source")}: {f.source}</div></div>)}
    <h2>{t("natal_afflictions")}</h2><AfflList list={r.afflictions} />
    <RemedyPlan plan={r.remedy_plan} />
  </>);
}

function Life({ r }: { r: any }) {
  const { t, T } = useI18n();
  return (<>
    {r.areas.map((a: any) => (
      <div key={a.area} className="issue">
        <div className="head"><h3 style={{ margin: 0 }}>{a.title}</h3>
          <span className={`chip ${a.verdict_key === "strong" ? "good" : a.verdict_key === "moderate" ? "mixed" : "bad"}`}>{a.verdict}</span>
          <span className="note">{t("house")} {a.house} ({T(a.sign)}, {T(a.lord)}) · {a.varga} · {T(a.karaka)}{a.chara_karaka ? ` · ${T(a.chara_karaka)}` : ""}</span></div>
        {a.house_info && <p className="note">{t("this_house")} <b>{a.house_info.name}</b>: {a.house_info.meaning}</p>}
        <ul>{a.points.map((p: any, i: number) => <li key={i}>{p.text}</li>)}</ul>
        {a.lord_placement && <><b>{t("house_lord_sits")}:</b><PlacementCard pl={a.lord_placement} compact /></>}
        {a.occupants?.length > 0 && <Fold summary={`${t("planets_in_house")} (${a.occupants.length})`}>{a.occupants.map((pl: any) => <PlacementCard key={pl.planet} pl={pl} compact />)}</Fold>}
        {a.periods.length > 0 && <><b>{t("periods")}:</b> <span className="note">{a.periods.map((w: any) => `${T(w.md)}–${T(w.ad)} (${w.start.slice(0, 7)} → ${w.end.slice(0, 7)})`).join(" · ")}</span></>}
        {a.remedy && <Fold summary={`${t("remedies")} – ${T(a.lord)}`}><RemedySet fs={a.remedy} /></Fold>}
      </div>))}
    <p className="note">{r.areas[0]?.source}</p>
  </>);
}

function LkRows({ list, annual, books }: { list: any[]; annual: boolean; books: any }) {
  const { t, T } = useI18n();
  return <>{list.map((e: any) => {
    const x = annual ? e.annual : e;
    return (
      <div key={e.planet} className="finding">
        <h4>{T(e.planet)} – {t("house")} {x.house}{x.house_info ? ` (${x.house_info.name})` : ""} <span className="note">“{x.title_hi}”</span> {x.pakka_ghar && <span className="chip good">{t("pakka")}</span>}</h4>
        {x.house_info && <p className="note">{t("meaning")}: {x.house_info.meaning}</p>}
        {x.theme && <p>{x.theme}</p>}
        {x.upay.length ? <><b>{t("lk_upay")}:</b><ul>{x.upay.map((u: string, i: number) => <li key={i}>{u}</li>)}</ul></> : <p className="note">{t("upay_pending")}</p>}
        <div className="src">Lal Kitab (Arun Sanhita), p. {x.book_page} · {t("read_in_book")}: <PageLinks kind="lalkitab" pages={x.pdf_pages || []} books={books} /></div>
        {e.vedic && <Fold summary={t("vedic_view")}><PlacementCard pl={e.vedic} /></Fold>}
        {e.other_remedies && <Fold summary={t("other_remedies")}><RemedySet fs={e.other_remedies} /></Fold>}
      </div>);
  })}</>;
}

function lkHouses(houses: Record<string, number>) {
  const by: Record<number, string[]> = {};
  for (let i = 0; i < 12; i++) by[i] = [];
  return { by, houses };
}

function LkChart({ houses }: { houses: Record<string, number> }) {
  const { abbr } = useI18n();
  const { by } = lkHouses(houses);
  for (const [p, h] of Object.entries(houses)) by[h - 1].push(abbr(p));
  return <NorthChart lagna={0} bySign={by} />;
}

function Varsh({ r, books }: { r: any; books: any }) {
  const { t, T } = useI18n();
  const labels = useLabels();
  const tp = r.tithi_pravesha, tc = tp.chart;
  const d1 = Object.fromEntries(Object.entries<any>(tc.planets).map(([p, v]) => [p, v.sign_index - 1]));
  return (<>
    <h3>{t("tp")}</h3>
    <div className="summary">
      <div className="stat"><span>{t("start")}</span><b>{tp.moment.replace("T", " ")}</b></div>
      <div className="stat"><span>{t("valid_until")}</span><b>{tp.valid_until.replace("T", " ")}</b></div>
      <div className="stat"><span>{t("vara_lord")}</span><b>{T(tp.vara_lord)}</b></div>
      <div className="stat"><span>{t("hora_lord")}</span><b>{T(tp.hora_lord)}</b></div>
      <div className="stat"><span>{t("lagna")}</span><b>{T(tc.lagna.sign)}</b></div>
    </div>
    <div className="mini">
      <div className="chartbox"><div className="cap">{t("tp")}</div><Kundli style="north" lagna={tc.lagna.sign_index - 1} bySign={labels(d1)} /></div>
      <div className="chartbox"><div className="cap">{t("lk_annual")} ({t("year")} {r.age})</div><LkChart houses={r.lal_kitab.varshphal.annual_houses} /></div>
    </div>
    <table><tbody><tr><th>{t("graha")}</th><th>{t("house")} (TP)</th><th>{t("bhav")}</th><th>{t("sign")}</th><th>{t("dignity")}</th><th>{t("meaning")}</th></tr>
      {Object.entries<any>(tc.planets).map(([p, v]) => <tr key={p}><td><b>{T(p)}</b></td><td>{v.house}</td><td>{r.bhav_names?.[v.house]?.name}</td><td>{T(v.sign)}</td>
        <td>{v.dignity === "n/a" ? "—" : T(v.dignity)}</td><td className="note">{r.bhav_names?.[v.house]?.meaning}</td></tr>)}</tbody></table>
    {tp.placements && <Fold summary={t("planets_explained")}>{tp.placements.map((pl: any) => <PlacementCard key={pl.planet} pl={pl} compact />)}</Fold>}
    <h3>{t("lk_annual")}</h3><LkRows list={r.lal_kitab.planets} annual books={books} />
  </>);
}

function LK({ r, books }: { r: any; books: any }) {
  const { t, T } = useI18n();
  return (<>
    <p className="note">{t("lk_note")}</p>
    <div className="mini">
      <div className="chartbox"><div className="cap">{t("lk_chart")}</div><LkChart houses={r.varshphal.natal_houses} /></div>
      <div className="chartbox"><div className="cap">{t("lk_annual")} ({t("age_running")} {r.age})</div><LkChart houses={r.varshphal.annual_houses} /></div>
    </div>
    <p><b>{t("empty_houses")}:</b> {r.empty_houses.join(", ")}</p>
    <LkRows list={r.planets} annual={false} books={books} />
    <h3>{t("lk_quick")}</h3>
    <ul>{r.quick.filter(Boolean).map((q: any) => <li key={q.planet}><b>{T(q.planet)}:</b> {q.text}</li>)}</ul>
    <p className="note">{r.quick.find(Boolean)?.source}</p>
    <RinBlock rin={r.rin} rules={r.rules} />
  </>);
}

function Nak({ r }: { r: any }) {
  const { t, T } = useI18n();
  return (<>
    <div className="summary">
      <div className="stat"><span>{t("janma_nak")}</span><b>{T(r.janma_nakshatra)} ({r.pada})</b><span>{T(r.lord)}</span></div>
      <div className="stat"><span>{t("anujanma")}</span><b>{T(r.anujanma)}</b></div>
      <div className="stat"><span>{t("trijanma")}</span><b>{T(r.trijanma)}</b></div>
      <div className="stat"><span>{t("ghat_nak")}</span><b>{T(r.ghat_nakshatra)}</b></div>
    </div>
    <NakDoshas list={r.birth_doshas} showEmpty />
    {r.planets_considered?.length > 0 && <p className="note">{t("considered")}: {r.planets_considered.map(T).join(", ")}</p>}
    <RemedyDays days={r.remedy_days} note={r.remedy_days_note} />
    <h3>{t("taras")}</h3>
    <table><tbody>
      <tr><th>#</th><th>{t("tara")}</th><th></th><th>{t("nakshatra")}</th></tr>
      {r.taras.map((x: any, i: number) => <tr key={i}><td>{i + 1}</td><td><b>{x.tara}</b> <span className="note">{x.meaning}</span></td>
        <td>{x.good === true ? <span className="chip good">{t("good")}</span> : x.good === false ? <span className="chip bad">{t("avoid")}</span> : <span className="chip gray">—</span>}</td>
        <td>{x.nakshatras.map(T).join(", ")}</td></tr>)}
    </tbody></table>
    <HealthWatch rows={r.health} />
    {r.placements?.length > 0 && <Fold summary={t("planets_explained")}>{r.placements.map((pl: any) => <PlacementCard key={pl.planet} pl={pl} />)}</Fold>}
    <p className="note">{r.source}</p>
  </>);
}

const DOSHA_KEYS = ["manglik", "kaal_sarp", "pitra", "sade_sati", "guru_chandal", "surya_grahan", "chandra_grahan", "shrapit", "vish", "angarak"];

function TempleCard({ x }: { x: any }) {
  const { t, T } = useI18n();
  return (
    <div className="finding">
      <h4>{x.name} <span className="note">· {x.place}, {x.state}</span></h4>
      <div>{x.planets.map((p: string) => <span key={p} className="chip gray">{T(p)}</span>)}{x.doshas.slice(0, 4).map((d: string) => <span key={d} className="chip mixed">{d.replace(/_/g, " ")}</span>)}</div>
      <p>{x.what}</p>
      <p className="note"><b>{t("when_to_go")}:</b> {x.when} · <b>{t("deity_label")}:</b> {x.deity}</p>
      {x.reasons?.length > 0 && <p><b>{t("why_here")}:</b> {x.reasons.join("; ")}</p>}
      <div className="src">{t("sources")}: {x.sources.map((u: string, i: number) => <a key={i} href={u} target="_blank" rel="noopener noreferrer" style={{ marginRight: 8 }}>{new URL(u).hostname.replace("www.", "")}</a>)}</div>
    </div>);
}

function Tirtha({ r }: { r: any }) {
  const { t, T, fmtD } = useI18n();
  const [fp, setFp] = useState(""); const [fd, setFd] = useState("");
  const list = r.directory.filter((x: any) => (!fp || x.planets.includes(fp)) && (!fd || x.doshas.includes(fd)));
  const tn = r.tantra;
  return (<>
    <p className="note">{r.note}</p>
    <h2>{t("temples_for_you")}</h2>
    {r.planets_considered?.length > 0 && <p className="note">{t("considered")}: {r.planets_considered.map(T).join(", ")}</p>}
    {r.suggested.map((x: any) => <TempleCard key={x.id} x={x} />)}
    {r.next_ashlesha?.length > 0 && <p><b>{t("next_ashlesha")}:</b> {r.next_ashlesha.map((a: any) => fmtD(a.date) + (a.from !== "sunrise" ? ` (${t("from_time")} ${a.from.slice(11, 16)})` : "")).join(" · ")}</p>}

    <h2>{t("tantra_layer")}</h2>
    <p className="note">{t("tantra_mapping_note")}</p>
    <h3>{t("for_you")}</h3>
    <div className="rem">{tn.for_you.map((m: any) => (
      <div key={m.planet} className="box"><h5>{T(m.planet)} → {m.mahavidya}</h5><ul>{m.items.map((i: string, k: number) => <li key={k}>{i}</li>)}</ul></div>))}</div>
    <h3>{t("tantra_principles")}</h3>
    <ol>{tn.principles.map((p: any, i: number) => <li key={i} style={{ marginBottom: 6 }}>{p.text} <span className="note">({t("book_page")} {p.page})</span></li>)}</ol>
    <p className="note">{tn.book}</p>
    <h3>{t("ten_flowers")}</h3>
    <p lang="sa" style={{ fontSize: 15 }}>{tn.ten_flowers.verse}</p>
    <p>{tn.ten_flowers.flowers.map((f: any) => <span key={f.key} className="chip good">{f.name}</span>)}</p>
    <p className="note">{tn.ten_flowers.source}</p>
    <Fold summary={t("mahavidya_table")}>
      <table><tbody><tr><th>{t("planet")}</th><th>{t("mahavidya")}</th><th>{t("meaning")}</th><th>{t("open_practice")}</th><th>{t("inner_flowers")}</th></tr>
        {tn.mahavidyas.map((m: any) => <tr key={m.planet}><td><b>{T(m.planet)}</b></td><td>{m.mahavidya}</td><td className="note">{m.essence}</td><td>{m.practice} <span className="note">({m.days})</span></td><td>{m.inner_flowers.join(", ")}</td></tr>)}
      </tbody></table>
    </Fold>
    <p className="note">{tn.excluded_note}</p>

    <h2>{t("temple_directory")}</h2>
    <div className="btnrow noprint" style={{ marginBottom: 10 }}>
      <div style={{ maxWidth: 200 }}><label>{t("planet")}</label><select value={fp} onChange={(e) => setFp(e.target.value)}>
        <option value="">{t("all")}</option>{["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"].map((p) => <option key={p} value={p}>{T(p)}</option>)}</select></div>
      <div style={{ maxWidth: 220 }}><label>{t("dosha")}</label><select value={fd} onChange={(e) => setFd(e.target.value)}>
        <option value="">{t("all")}</option>{DOSHA_KEYS.map((d) => <option key={d} value={d}>{d.replace(/_/g, " ")}</option>)}</select></div>
    </div>
    {list.map((x: any) => <TempleCard key={x.id} x={x} />)}
  </>);
}

const rateChip = (k: string) => (k === "excellent" || k === "good" ? "good" : k === "mixed" ? "mixed" : "bad");
const rateCls = (k: string) => (k === "excellent" || k === "good" ? "benefic" : k === "mixed" ? "mixed" : "challenging");

function Simple({ r }: { r: any }) {
  const { t } = useI18n();
  return (<div className="simple">
    {r.rating_label && <p><span className={`chip ${r.rating === "excellent" || r.rating === "good" ? "good" : r.rating === "mixed" ? "mixed" : "bad"}`}>{t("simple_now")}: {r.rating_label}</span></p>}
    {r.sections.map((s: any) => (
      <section key={s.id} className={`simple-sec ${s.id}`}>
        <h3>{s.title}</h3>
        {s.id !== "remedies" && (s.paras || []).map((p: string, i: number) => <p key={i}>{p}</p>)}
        {s.months && <div className="simple-months">{s.months.map((m: any) => <span key={m.label} className={`chip ${m.rating === "excellent" || m.rating === "good" ? "good" : m.rating === "mixed" ? "mixed" : "bad"}`}>{m.label}: {m.rating_label}</span>)}</div>}
        {s.items && <ul>{s.items.map((x: any, i: number) => <li key={i} className={x.priority}>{x.text}</li>)}</ul>}
        {s.plans && <>{(s.paras || []).map((p: string, i: number) => <p key={i} className="note">{p}</p>)}
          {s.plans.map((pl: any) => (
            <div key={pl.planet} className={`finding ${rateCls("mixed")}`}>
              <h4>{pl.planet} · {pl.day}</h4><p>{pl.why}</p>
              <ol>{pl.steps.map((st: string, i: number) => <li key={i}>{st}</li>)}</ol>
            </div>))}</>}
      </section>))}
    <p className="note" style={{ marginTop: 18 }}>{r.closing}</p>
  </div>);
}

function LifePred({ r }: { r: any }) {
  const { t, T, fmtD } = useI18n();
  const o = r.overview;
  const st = r.story;
  return (<>
    {st && <div className="story">
      <h2>{t("life_story")}</h2>
      <div className="timeline noprint">
        {st.chapters.map((c: any) => (
          <a key={c.n} href={`#ch${c.n}`} className={`seg ${rateChip(c.rating)} ${c.status === "present" ? "now" : ""}`}
             style={{ flex: Math.max(1, c.age_to - c.age_from) }} title={`${c.title} (${c.age_from}–${c.age_to})`}>
            <span>{T(c.lord)}</span><small>{Math.round(c.age_from)}</small></a>))}
      </div>
      <div className="prologue">{st.prologue.map((p: string, i: number) => <p key={i}>{p}</p>)}</div>
      {st.chapters.map((c: any) => (
        <section key={c.n} id={`ch${c.n}`} className={`chapter ${c.status}`}>
          <div className="chead">
            <span className="cnum">{t("chapter")} {c.n}</span>
            <h3>{c.title}</h3>
            <span className="note">{c.start.slice(0, 4)}–{c.end.slice(0, 4)} · {t("age")} {Math.round(c.age_from)}–{Math.round(c.age_to)}</span>
            <span className={`chip ${rateChip(c.rating)}`}>{c.rating_label}</span>
            {c.status === "present" && <span className="chip">{t("current_period")}</span>}
          </div>
          {c.paragraphs.map((p: string, i: number) => <p key={i} className={i === 0 ? "lead" : ""}>{p}</p>)}
        </section>))}
      <div className="epilogue">{st.epilogue.map((p: string, i: number) => <p key={i}>{p}</p>)}</div>
    </div>}
    <Fold summary={t("detailed_analysis")}>
    <h2>{t("overview")}</h2>
    <p>{o.text}</p>
    <div className="summary">
      <div className="stat"><span>{t("strongest")}</span><b>{o.strongest.map(T).join(", ")}</b></div>
      <div className="stat"><span>{t("weakest")}</span><b>{o.weakest.map(T).join(", ")}</b></div>
    </div>
    {o.yogas.length > 0 && <p><b>{t("yogas_present")}:</b> {o.yogas.map((y: string) => <span key={y} className="chip good">{y}</span>)}</p>}
    {o.doshas.length > 0 && <p><b>{t("cat_dosha")} / {t("natal_afflictions")}:</b> {o.doshas.map((a: any, i: number) => <span key={i} className="chip bad">{a.text}</span>)}</p>}

    <h2>{t("dasha_journey")}</h2>
    {r.journey.map((m: any) => (
      <div key={m.lord + m.start} className={`issue`} style={m.current ? { borderColor: "var(--accent)", borderWidth: 2 } : undefined}>
        <div className="head">
          <h3 style={{ margin: 0 }}>{T(m.lord)} {t("mahadasha")}</h3>
          <span className={`chip ${rateChip(m.rating)}`}>{m.rating_label}</span>
          {m.current && <span className="chip">{t("current_period")}</span>}
          <span className="note">{fmtD(m.start)} → {fmtD(m.end)} · {t("age")} {m.age_from}–{m.age_to}</span>
        </div>
        <p>{m.text}</p>
        <p className="note">{m.reasons.join(" · ")}</p>
        {m.best_ad && <p className="note"><b>{t("best_period")}:</b> {T(m.best_ad.lord)} ({m.best_ad.start.slice(0, 7)} → {m.best_ad.end.slice(0, 7)}) · <b>{t("hardest_period")}:</b> {T(m.hardest_ad.lord)} ({m.hardest_ad.start.slice(0, 7)} → {m.hardest_ad.end.slice(0, 7)})</p>}
        <Fold summary={`${t("antardashas")} (${m.antardashas.length})`} open={m.current}>
          <table><tbody>
            <tr><th>AD</th><th>{t("start")}</th><th>{t("end")}</th><th>{t("age")}</th><th>{t("rating")}</th><th>{t("meaning")}</th></tr>
            {m.antardashas.map((a: any) => (
              <tr key={a.start} className={isCurrent({ start: a.start, end: a.end }) ? "cur" : ""}>
                <td><b>{T(a.lord)}</b></td><td>{a.start}</td><td>{a.end}</td><td>{a.age_from}</td>
                <td><span className={`chip ${rateChip(a.rating)}`}>{a.rating_label}</span></td><td className="note">{a.themes.join("; ")}</td></tr>))}
          </tbody></table>
        </Fold>
      </div>))}

    <h2>{t("milestones")}</h2>
    <table><tbody>
      <tr><th>{t("age")}</th><th>{t("start")}</th><th>{t("end")}</th><th></th></tr>
      {r.milestones.map((m: any, i: number) => <tr key={i}><td><b>{m.age}</b></td><td>{m.start}</td><td>{m.end || "—"}</td><td>{m.text}</td></tr>)}
    </tbody></table>

    <h2>{t("life_areas_summary")}</h2>
    {r.life_areas.map((a: any) => (
      <div key={a.area} className={`finding ${a.verdict_key === "strong" ? "benefic" : a.verdict_key === "moderate" ? "mixed" : "challenging"}`}>
        <h4>{a.title} <span className={`chip ${a.verdict_key === "strong" ? "good" : a.verdict_key === "moderate" ? "mixed" : "bad"}`}>{a.verdict}</span></h4>
        <ul>{a.points.map((p: string, i: number) => <li key={i}>{p}</li>)}</ul>
        {a.periods.length > 0 && <p className="note"><b>{t("windows")}:</b> {a.periods.map((w: any) => `${T(w.md)}–${T(w.ad)} (${w.start.slice(0, 7)} → ${w.end.slice(0, 7)})`).join(" · ")}</p>}
      </div>))}
    </Fold>
    <p className="note"><b>{t("method")}:</b> {r.method}</p>
    <p className="note">{r.disclaimer} {t("remedy_hint")}</p>
  </>);
}

function YearPred({ r, setYear }: { r: any; setYear: (y: number) => void }) {
  const { t, T, fmtD } = useI18n();
  const tp = r.tithi_pravesha;
  return (<>
    <h2>{r.year} <span className={`chip ${rateChip(r.rating)}`}>{r.rating_label}</span></h2>
    <p style={{ fontSize: 15 }}>{r.summary}</p>

    <h3>{t("area_outlook")}</h3>
    <div className="rem">{r.areas.map((a: any) => (
      <div key={a.area} className="box" style={{ borderLeft: `4px solid var(--${rateChip(a.rating) === "good" ? "good" : rateChip(a.rating) === "mixed" ? "mixed" : "bad"})` }}>
        <h5>{a.title} <span className={`chip ${rateChip(a.rating)}`}>{a.rating_label}</span></h5>
        <ul>{a.reasons.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
      </div>))}</div>

    <h3>{t("dasha_periods_year")}</h3>
    {r.periods.map((p: any) => (
      <div key={p.start} className={`finding ${rateCls(p.rating)}`}>
        <h4>{T(p.md)} / {T(p.ad)} <span className="note">{fmtD(p.start)} → {fmtD(p.end)}</span> <span className={`chip ${rateChip(p.rating)}`}>{p.rating_label}</span></h4>
        <p>{p.themes.join("; ")}</p><div className="src">{p.reasons.join(" · ")}</div>
      </div>))}

    <h3>{t("transits_year")}</h3>
    <table><tbody>
      <tr><th>{t("graha")}</th><th>{t("sign")}</th><th>{t("start")}</th><th>{t("end")}</th><th></th></tr>
      {r.transits.map((x: any, i: number) => <tr key={i}><td><b>{T(x.planet)}</b></td><td>{T(x.sign)}</td><td>{x.from}</td><td>{x.to}</td>
        <td><span className={`chip ${x.good ? "good" : "bad"}`}>{x.house_from_moon}</span> <span className="note">{x.text}</span></td></tr>)}
    </tbody></table>
    {(r.sade_sati?.sade_sati || r.sade_sati?.dhaiya) && <p><b>{t("tab_sade")}:</b> {r.sade_sati.sade_sati ? T(r.sade_sati.phase) : T(r.sade_sati.dhaiya)}</p>}

    <h3>{t("month_by_month")}</h3>
    <div className="mini" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(130px,1fr))" }}>
      {r.months.map((m: any) => <div key={m.month} className="stat"><span>{m.month}</span><b><span className={`chip ${rateChip(m.rating)}`}>{m.rating_label}</span></b><span>{m.notes.join(" · ")}</span></div>)}
    </div>

    {tp && <><h3>{t("tp_year")}</h3>
      <p>{fmtD(tp.moment)} → {fmtD(tp.valid_until)} · {t("lagna")}: {T(tp.lagna)} · {t("vara_lord")}: {T(tp.vara_lord)} ({T(tp.vara_nature)}) · {t("hora_lord")}: {T(tp.hora_lord)} ({T(tp.hora_nature)})</p></>}
    {r.lal_kitab && <p className="note"><b>{t("lk_year")} ({t("year")} {r.lal_kitab.age}):</b> {Object.entries<any>(r.lal_kitab.houses).map(([p, h]) => `${T(p)} ${h}`).join(" · ")}</p>}

    <h3>{t("years_ahead")}</h3>
    <table><tbody>
      <tr><th>{t("year")}</th><th>{t("age")}</th><th>{t("rating")}</th><th>{t("mahadasha")}</th><th>{t("jupiter_sign")}</th><th>{t("saturn_sign")}</th><th>{t("tab_sade")}</th></tr>
      {r.years.map((y: any) => (
        <tr key={y.year} className={y.year === r.year ? "cur" : ""} style={{ cursor: "pointer" }} onClick={() => setYear(y.year)}>
          <td><b>{y.year}</b></td><td>{y.age}</td><td><span className={`chip ${rateChip(y.rating)}`}>{y.rating_label}</span></td>
          <td>{y.dasha}</td><td>{T(y.jupiter)}</td><td>{T(y.saturn)}</td><td>{y.sade_sati ? "✓" : y.dhaiya ? T(y.dhaiya) : "—"}</td></tr>))}
    </tbody></table>
    <p className="note">{t("remedy_hint")}</p>
  </>);
}

function Bhrigu({ r, books }: { r: any; books: any }) {
  const { t, T } = useI18n();
  return (<>
    <p className="note">{t("ocr_note")}</p>
    <h3>{t("bhrigu_lagna")}: {T(r.lagna)}</h3>
    {r.readings.map((x: any) => (
      <div key={x.planet} className="finding">
        <h4>{T(x.planet)} – {t("house")} {x.house} <span className="note">(p. {x.printed_page})</span></h4>
        {x.found ? <><p lang="hi">{x.text_hi}</p><div className="src"><PageLinks kind="bhrigu" pages={[x.pdf_page]} books={books} offset={8} /></div></>
          : <><p className="note">{t("not_split")}</p><div className="src"><PageLinks kind="bhrigu" pages={x.block_pdf_pages} books={books} offset={8} /></div></>}
      </div>))}
    <p className="note">{r.source}</p>
  </>);
}
