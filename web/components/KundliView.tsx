"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ApiError, api, birthOf, nowIn, type Kundli as K } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import BirthForm from "./BirthForm";
import Reports from "./Reports";
import Ask from "./Ask";
import { ChartTab, DashaTab, InterpTab, SadeTab } from "./Tabs";

const TABS = ["chart", "dasha", "interp", "sade", "reports", "ask", "raw"] as const;

export default function KundliView({ initial }: { initial: K }) {
  const { t, lang, fmtD } = useI18n();
  const { isSignedIn } = useAuth();
  const router = useRouter();
  const [k, setK] = useState<K>(initial);
  const [tab, setTab] = useState<(typeof TABS)[number]>("chart");
  const [data, setData] = useState<any>(null);
  const [interp, setInterp] = useState<any>(null);
  const [err, setErr] = useState("");
  const [editing, setEditing] = useState(false);
  const [toast, setToast] = useState("");
  const flash = (m: string) => { setToast(m); setTimeout(() => setToast(""), 2200); };
  const goSignIn = () => router.push(`/sign-in?redirect_url=${encodeURIComponent(window.location.pathname + window.location.search)}`);

  useEffect(() => {
    const b = birthOf(k);
    setData(null); setErr("");
    Promise.all([api("/chart", b), api("/dasha", { ...b, levels: 3, at: nowIn(k.tz) }), api("/sade-sati", b)])
      .then(([chart, dasha, sade]) => setData({ chart, dasha, sade })).catch((e) => setErr(e.message));
  }, [k.datetime_local, k.tz, k.lat, k.lon, k.settings?.ayanamsa, k.settings?.node]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    api("/interpret", { ...birthOf(k), lang }).then(setInterp).catch(() => {});
  }, [k.datetime_local, k.tz, k.lat, k.lon, lang]); // eslint-disable-line react-hooks/exhaustive-deps

  const save = async () => {
    if (!isSignedIn) { goSignIn(); return; }
    try {
      if (k.id) {
        const r = await api<K>(`/kundlis/${k.id}`, k, "PUT"); setK(r); flash(t("saved_ok"));
      } else {
        const r = await api<K>("/kundlis", k); setK(r); flash(t("saved_ok")); router.replace(`/kundli/${r.id}`);
      }
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 401) goSignIn();
      else setErr(e.message);
    }
  };
  const del = async () => {
    if (!isSignedIn) { goSignIn(); return; }
    if (!k.id || !confirm(t("confirm_delete"))) return;
    try {
      await api(`/kundlis/${k.id}`, undefined, "DELETE"); router.push("/");
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 401) goSignIn();
      else setErr(e.message);
    }
  };
  const applyEdit = async (nk: K) => {
    setEditing(false);
    const merged = { ...nk, id: k.id };
    if (k.id && isSignedIn) {
      try { setK(await api<K>(`/kundlis/${k.id}`, merged, "PUT")); flash(t("saved_ok")); }
      catch (e: any) { setErr(e.message); }
    } else setK(merged);
  };

  return (
    <div className="page">
      <section className="card">
        <div className="kheader noprint">
          <h2>{k.name || t("new_kundli")}</h2>
          <span className="note">{t("born")}: {k.datetime_local.replace("T", " ")} · {k.place || `${k.lat.toFixed(3)}, ${k.lon.toFixed(3)}`} · {k.tz}</span>
          {!k.id && <span className="chip mixed">{t("unsaved")}</span>}
          {k.updated_at && <span className="note">{t("updated")}: {fmtD(k.updated_at)}</span>}
          <div className="btnrow" style={{ marginLeft: "auto" }}>
            <button className="btn" onClick={save}>{k.id ? t("update") : t("save")}</button>
            <button className="btn light" onClick={() => setEditing(!editing)}>{t("edit")}</button>
            {k.id && <button className="btn danger" onClick={del}>{t("delete")}</button>}
          </div>
        </div>
        {editing && <div className="card noprint" style={{ marginBottom: 14 }}><BirthForm initial={k} compact submitLabel={t("generate")} onSubmit={applyEdit} onCancel={() => setEditing(false)} /></div>}
        {err && <p className="err" style={{ display: "block" }}>{err}</p>}
        <div className="tabs noprint">
          {TABS.map((x) => <button key={x} className={tab === x ? "on" : ""} onClick={() => setTab(x)}>{t(`tab_${x}`)}</button>)}
        </div>
        {!data && !err && <div className="empty">{t("loading")}</div>}
        {data && (<>
          {tab === "chart" && <ChartTab c={data.chart} />}
          {tab === "dasha" && <DashaTab d={data.dasha} />}
          {tab === "interp" && (interp ? <InterpTab r={interp} /> : <div className="empty">{t("loading")}</div>)}
          {tab === "sade" && <SadeTab s={data.sade} />}
          {tab === "reports" && <Reports kundli={k} chart={data.chart} />}
          {tab === "ask" && <Ask kundli={k} />}
          {tab === "raw" && <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", maxHeight: "75vh", overflow: "auto" }}>{JSON.stringify({ kundli: k, ...data, interp }, null, 2)}</pre>}
        </>)}
      </section>
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
