"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { Fragment, useEffect, useRef, useState } from "react";
import { api, birthOf, nowIn, type Kundli as K } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

type Item = { q: string; lang: string; at: string; r?: any; err?: string };

const EXAMPLES: Record<string, string[]> = {
  en: ["When will I get a promotion?", "When is a good time for marriage?", "What does Saturn in my 2nd house mean?",
       "What remedies should I do for my career?", "Do I have Kaal Sarp dosha?", "Which mahavidya should I worship for Saturn?"],
  hi: ["मेरी शादी कब होगी?", "नौकरी में तरक्की कब होगी?", "मेरे दूसरे भाव में शनि का क्या फल है?",
       "करियर के लिए क्या उपाय करूँ?", "क्या मेरी कुंडली में कालसर्प दोष है?", "शनि के लिए कौन सा मंदिर जाऊँ?"],
};

/** Tiny Markdown subset for AI answers: paragraphs, "- " bullets, **bold**, ### headings. */
function Md({ text }: { text: string }) {
  const inline = (s: string) => s.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
    p.startsWith("**") && p.endsWith("**") ? <b key={i}>{p.slice(2, -2)}</b> : <Fragment key={i}>{p}</Fragment>);
  const blocks = text.split(/\n{2,}/);
  return (<>{blocks.map((b, i) => {
    const lines = b.split("\n").filter((l) => l.trim());
    if (lines.length && lines.every((l) => /^\s*([-*]|\d+\.)\s/.test(l)))
      return <ul key={i}>{lines.map((l, j) => <li key={j}>{inline(l.replace(/^\s*([-*]|\d+\.)\s/, ""))}</li>)}</ul>;
    if (/^#{1,4}\s/.test(b)) return <h4 key={i}>{inline(b.replace(/^#{1,4}\s/, ""))}</h4>;
    return <p key={i}>{lines.map((l, j) => <Fragment key={j}>{j > 0 && <br />}{inline(l)}</Fragment>)}</p>;
  })}</>);
}

export default function Ask({ kundli }: { kundli: K }) {
  const { t, lang } = useI18n();
  const store = `ask:${kundli.id || kundli.datetime_local}`;
  const [items, setItems] = useState<Item[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [st, setSt] = useState<any>(null);
  const [useAi, setUseAi] = useState(true);
  const [key, setKey] = useState("");
  const [model, setModel] = useState("");
  const [showCfg, setShowCfg] = useState(false);
  const [imgs, setImgs] = useState<Record<string, number>>({});
  const top = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api("/books/status").then(setImgs).catch(() => {});
    api("/ask/status").then((s) => { setSt(s); setModel(s.model); }).catch(() => {});
    try { setItems(JSON.parse(localStorage.getItem(store) || "[]")); } catch { /* storage unavailable */ }
  }, [store]);
  const persist = (x: Item[]) => { setItems(x); try { localStorage.setItem(store, JSON.stringify(x.slice(0, 30))); } catch { /* ignore */ } };

  const submit = async (question: string) => {
    const qq = question.trim();
    if (qq.length < 2 || busy) return;
    setBusy(true);
    const it: Item = { q: qq, lang, at: new Date().toISOString() };
    try {
      it.r = await api("/ask", { ...birthOf(kundli), lang, at: nowIn(kundli.tz), question: qq, use_ai: useAi });
    } catch (e: any) { it.err = e.message; }
    persist([it, ...items]);
    setQ(""); setBusy(false);
    top.current?.scrollIntoView({ behavior: "smooth" });
  };
  const saveKey = async (clear = false) => {
    const s = await api("/ask/key", { api_key: clear ? "" : key, model: model || null });
    setSt(s); setKey(""); if (!clear) setShowCfg(false);
  };

  return (
    <div className="ask">
      <h2>{t("ask_title")}</h2>
      <p className="note">{t("ask_intro")}</p>
      <div className="ask-box noprint">
        <textarea rows={3} value={q} placeholder={t("ask_placeholder")} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit(q); }} />
        <div className="btnrow" style={{ alignItems: "center", marginTop: 8 }}>
          <button onClick={() => submit(q)} disabled={busy || q.trim().length < 2}>{busy ? t("ask_thinking") : t("ask_button")}</button>
          {st?.ai && <label className="ask-toggle"><input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} /> {t("ask_use_ai")}</label>}
          <span className="note" style={{ marginLeft: "auto" }}>
            {st ? (st.ai ? `${t("ask_ai_on")} (${st.model})` : t("ask_ai_off")) : ""}{" "}
            <a href="#" onClick={(e) => { e.preventDefault(); setShowCfg((x) => !x); }}>{t("ask_settings")}</a>
          </span>
        </div>
        <div className="ask-examples">
          {(EXAMPLES[lang] || EXAMPLES.en).map((x) => <button key={x} className="chip gray" onClick={() => submit(x)} disabled={busy}>{x}</button>)}
        </div>
        {showCfg && (
          <div className="card" style={{ marginTop: 10 }}>
            <p className="note">{t("ask_key_help")}</p>
            <div className="btnrow" style={{ alignItems: "end" }}>
              <div style={{ flex: 2 }}><label>{t("ask_key")}</label>
                <input type="password" value={key} placeholder={st?.key_hint || "sk-ant-…"} onChange={(e) => setKey(e.target.value)} /></div>
              <div style={{ flex: 1 }}><label>{t("ask_model")}</label><input value={model} onChange={(e) => setModel(e.target.value)} /></div>
              <button onClick={() => saveKey()} disabled={!key.trim()}>{t("ask_save_key")}</button>
              {st?.ai && <button className="ghost" onClick={() => saveKey(true)}>{t("ask_remove_key")}</button>}
            </div>
          </div>)}
      </div>

      <div ref={top} />
      {busy && <div className="empty">{t("ask_thinking")}</div>}
      {items.length === 0 && !busy && <div className="empty">{t("ask_empty")}</div>}
      {items.map((it, i) => (
        <div key={it.at + i} className="ask-item">
          <div className="ask-q">❓ {it.q} <span className="note">· {new Date(it.at).toLocaleString()}</span></div>
          {it.err && <p className="err" style={{ display: "block" }}>{it.err}</p>}
          {it.r && <Answer r={it.r} imgs={imgs} />}
        </div>))}
      {items.length > 0 && <p className="noprint"><button className="ghost" onClick={() => persist([])}>{t("ask_clear")}</button></p>}
    </div>
  );
}

function Answer({ r, imgs }: { r: any; imgs: Record<string, number> }) {
  const { t } = useI18n();
  const [more, setMore] = useState(r.mode !== "ai");
  return (
    <div className="ask-a">
      {r.mode === "ai" && <div className="ask-ai"><Md text={r.ai_text} /><div className="src">{t("ask_ai_written")} · {r.model}</div></div>}
      {r.ai_error && <p className="note">⚠ {t("ask_ai_failed")}: {r.ai_error}</p>}
      {r.mode === "ai" && <p><a href="#" onClick={(e) => { e.preventDefault(); setMore((x) => !x); }}>{more ? t("ask_hide_details") : t("ask_show_details")}</a></p>}
      {more && <>
        {r.sections.map((s: any, i: number) => (
          <div key={i} className={`finding ${s.verdict === "strong" ? "benefic" : s.verdict === "weak" ? "challenging" : s.verdict ? "mixed" : ""}`}>
            <h4>{s.title}</h4>{s.paras.map((p: string, j: number) => <p key={j}>{p}</p>)}
          </div>))}
        {r.remedies.length > 0 && <>
          <h4>{t("ask_remedies")}</h4>
          {r.remedies.map((x: any) => (
            <div key={x.planet} className="finding mixed"><h4>{x.planet}</h4><p className="note">{x.approach}</p>
              <ol>{x.steps.map((s: string, j: number) => <li key={j}>{s}</li>)}</ol></div>))}
        </>}
      </>}
      {r.refs.length > 0 && <>
        <h4>{t("ask_books")}</h4>
        <ul className="ask-refs">
          {r.refs.map((x: any, i: number) => (
            <li key={i}>
              <b>{x.title}</b>, {x.image && imgs[x.book] ? <a href={x.image} target="_blank" rel="noopener noreferrer">{x.page_label}</a> : x.page_label}
              {x.why && <> – {x.why}</>}
              {x.snippet && <div className="ask-snip">{x.snippet}</div>}
            </li>))}
        </ul>
      </>}
      <p className="note">{r.note}</p>
    </div>
  );
}
