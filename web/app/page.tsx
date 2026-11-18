"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, kundliToQuery, type Kundli } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import BirthForm from "@/components/BirthForm";

export default function Home() {
  const { t, fmtD } = useI18n();
  const router = useRouter();
  const [list, setList] = useState<Kundli[]>([]);
  const [q, setQ] = useState("");
  const [down, setDown] = useState(false);
  const [msg, setMsg] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = (query = q) => api<Kundli[]>(`/kundlis?q=${encodeURIComponent(query)}`).then((x) => { setList(x); setDown(false); }).catch(() => setDown(true));
  useEffect(() => { load(""); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const h = setTimeout(() => load(q), 200); return () => clearTimeout(h); }, [q]); // eslint-disable-line react-hooks/exhaustive-deps

  const exportAll = async () => {
    const data = await api("/kundlis/export");
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = `kundlis-${new Date().toISOString().slice(0, 10)}.json`; a.click();
    URL.revokeObjectURL(url);
  };
  const importFile = async (f: File) => {
    try { const r = await api<{ imported: number }>("/kundlis/import", JSON.parse(await f.text())); setMsg(`${t("imported")}: ${r.imported}`); load(); }
    catch (e) { setMsg(String(e)); }
  };
  const del = async (id: string) => { if (confirm(t("confirm_delete"))) { await api(`/kundlis/${id}`, undefined, "DELETE"); load(); } };

  return (
    <main>
      <aside>
        <div className="card">
          <h2>{t("new_kundli")}</h2>
          <BirthForm onSubmit={(k) => router.push(`/kundli/view?${kundliToQuery(k)}`)} />
        </div>
      </aside>
      <section className="card">
        <div className="kheader">
          <h2>{t("saved_kundlis")}</h2><span className="note">{list.length} {t("count")}</span>
          <div className="btnrow" style={{ marginLeft: "auto" }}>
            <button className="btn light" onClick={exportAll}>{t("export")}</button>
            <button className="btn light" onClick={() => fileRef.current?.click()}>{t("import")}</button>
            <input ref={fileRef} type="file" accept="application/json" hidden onChange={(e) => e.target.files?.[0] && importFile(e.target.files[0])} />
          </div>
        </div>
        {down && <p className="err" style={{ display: "block" }}>{t("engine_down")}</p>}
        {msg && <p className="note">{msg}</p>}
        <input placeholder={t("search")} value={q} onChange={(e) => setQ(e.target.value)} style={{ marginBottom: 12 }} />
        {!list.length && !down && <div className="empty">{t("no_saved")}</div>}
        <div className="klist">
          {list.map((k) => (
            <div key={k.id} className="kitem">
              <div className="om" style={{ width: 30, height: 30, fontSize: 14 }}>{(k.name || "?").slice(0, 1)}</div>
              <div className="who">
                <b>{k.name}</b>
                <span>{k.datetime_local.replace("T", " ")} · {k.place || k.tz}{k.tags ? ` · ${k.tags}` : ""} · {t("updated")} {k.updated_at ? fmtD(k.updated_at) : ""}</span>
              </div>
              <Link className="btn" href={`/kundli/${k.id}`}>{t("open")}</Link>
              <button className="btn danger" onClick={() => del(k.id!)}>{t("delete")}</button>
            </div>))}
        </div>
      </section>
    </main>
  );
}
