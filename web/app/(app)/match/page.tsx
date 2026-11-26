"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { ApiError, api, birthOf, type Kundli } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import BirthForm from "@/components/BirthForm";

function Person({ title, saved, value, onChange }: { title: string; saved: Kundli[]; value: Kundli | null; onChange: (k: Kundli | null) => void }) {
  const { t } = useI18n();
  const [manual, setManual] = useState(false);
  return (
    <div className="card">
      <h2>{title}</h2>
      <label>{t("choose_saved")}</label>
      <select value={value?.id || ""} onChange={(e) => onChange(saved.find((k) => k.id === e.target.value) || null)}>
        <option value="">—</option>
        {saved.map((k) => <option key={k.id} value={k.id}>{k.name} · {k.datetime_local.slice(0, 10)}</option>)}
      </select>
      {value && !value.id && <p className="note">{value.name} · {value.datetime_local.replace("T", " ")} · {value.place}</p>}
      <button className="ghost" onClick={() => setManual(!manual)}>{t("new_kundli")} …</button>
      {manual && <BirthForm compact submitLabel="OK" onSubmit={(k) => { onChange(k); setManual(false); }} onCancel={() => setManual(false)} />}
    </div>
  );
}

export default function Match() {
  const { t, T, lang } = useI18n();
  const { isLoaded, isSignedIn, userId } = useAuth();
  const [saved, setSaved] = useState<Kundli[]>([]);
  const [g, setG] = useState<Kundli | null>(null);
  const [b, setB] = useState<Kundli | null>(null);
  const [m, setM] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) { setSaved([]); return; }
    api<Kundli[]>("/kundlis")
      .then(setSaved)
      .catch((e) => {
        if (!(e instanceof ApiError && e.status === 401)) setErr(t("engine_down"));
      });
  }, [isLoaded, isSignedIn, userId, t]);

  const run = async () => {
    if (!g) return setErr(t("complete_groom"));
    if (!b) return setErr(t("complete_bride"));
    setErr("");
    try { setM(await api("/match", { groom: birthOf(g), bride: birthOf(b) })); } catch (e: any) { setErr(e.message); }
  };
  const ok = m && m.total >= 18;
  return (
    <div className="page"><section className="card">
      <h2>{t("tab_match")}</h2>
      {isLoaded && !isSignedIn && (
        <p className="note" style={{ marginBottom: 12 }}>
          {lang === "hi" ? "सहेजी गई कुंडलियाँ चुनने के लिए " : "To pick from your saved kundlis, "}
          <Link href="/sign-in?redirect_url=%2Fmatch">{lang === "hi" ? "साइन इन करें" : "sign in"}</Link>
          {lang === "hi" ? " (या नीचे जन्म विवरण सीधे भरें)।" : " (or enter birth details manually below)."}
        </p>
      )}
      <div className="grid2">
        <Person title={t("groom")} saved={saved} value={g} onChange={setG} />
        <Person title={t("bride")} saved={saved} value={b} onChange={setB} />
      </div>
      <button className="btn" style={{ marginTop: 12 }} onClick={run}>{t("match_btn")}</button>
      {err && <p className="err" style={{ display: "block" }}>{err}</p>}
      {m && <div style={{ marginTop: 18 }}>
        <div className="summary">
          <div className="stat"><span>{t("guna_milan")}</span><div className="big">{m.total}<span style={{ fontSize: 18, color: "var(--muted)" }}> / 36</span></div></div>
          <div className="stat"><span>{t("verdict")}</span><b><span className={`chip ${ok ? "good" : "bad"}`}>{t(ok ? "acceptable" : "below")}</span></b></div>
          <div className="stat"><span>{t("doshas")}</span><b>
            {m.doshas.nadi_dosha && <span className="chip bad">{t("nadi_dosha")}</span>}
            {m.doshas.bhakoot_dosha && <span className="chip bad">{t("bhakoot_dosha")}</span>}
            {!m.doshas.nadi_dosha && !m.doshas.bhakoot_dosha && <span className="chip good">{t("none")}</span>}</b></div>
          <div className="stat"><span>{t("manglik_gb")}</span><b>{t(m.manglik.groom ? "yes" : "no")} / {t(m.manglik.bride ? "yes" : "no")}</b></div>
        </div>
        <table><tbody>
          <tr><th>{t("koota")}</th><th>{t("groom")}</th><th>{t("bride")}</th><th>{t("score")}</th></tr>
          {Object.entries<any>(m.kootas).map(([k, v]) => <tr key={k}><td><b>{T(k) === k ? k.replace("_", " ").replace(/^./, (c: string) => c.toUpperCase()) : T(k)}</b>{v.simplified && <span className="chip gray"> {t("simplified")}</span>}</td>
            <td>{v.groom ? T(v.groom) : "—"}</td><td>{v.bride ? T(v.bride) : "—"}</td><td><b>{v.score}</b> / {v.max}</td></tr>)}
        </tbody></table>
        <p className="note">{t("match_note")}</p>
      </div>}
    </section></div>
  );
}
