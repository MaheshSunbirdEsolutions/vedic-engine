"use client";
// Language context: UI strings, Jyotish terms and chart abbreviations come from the engine (/i18n/{lang}).
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";

type Bundle = { ui: Record<string, string>; terms: Record<string, string>; abbr: Record<string, string> };
type Ctx = {
  lang: "en" | "hi"; setLang: (l: "en" | "hi") => void; ready: boolean;
  t: (k: string) => string; T: (v?: string | null) => string; abbr: (p: string) => string;
  locale: string; fmtD: (s: string) => string;
};
const ABBR_EN: Record<string, string> = { Sun: "Su", Moon: "Mo", Mars: "Ma", Mercury: "Me", Jupiter: "Ju", Venus: "Ve", Saturn: "Sa", Rahu: "Ra", Ketu: "Ke" };
const I18n = createContext<Ctx | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<"en" | "hi">("en");
  const [b, setB] = useState<Bundle>({ ui: {}, terms: {}, abbr: {} });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try { const s = localStorage.getItem("jyotish_lang"); if (s === "hi" || s === "en") setLangState(s); } catch { /* ignore */ }
  }, []);
  useEffect(() => {
    api<Bundle>(`/i18n/${lang}`).then((x) => { setB(x); setReady(true); document.documentElement.lang = lang; }).catch(() => setReady(true));
  }, [lang]);

  const setLang = useCallback((l: "en" | "hi") => { setLangState(l); try { localStorage.setItem("jyotish_lang", l); } catch { /* ignore */ } }, []);
  const t = useCallback((k: string) => b.ui[k] ?? k, [b]);
  const T = useCallback((v?: string | null) => (v == null ? "" : lang === "en" ? v : b.terms[v] ?? v), [b, lang]);
  const abbr = useCallback((p: string) => (lang === "en" ? ABBR_EN[p] : b.abbr[p] || ABBR_EN[p]), [b, lang]);
  const locale = lang === "hi" ? "hi-IN" : "en-GB";
  const fmtD = useCallback((s: string) => new Date(s.slice(0, 10)).toLocaleDateString(locale, { day: "2-digit", month: "short", year: "numeric" }), [locale]);

  return <I18n.Provider value={{ lang, setLang, ready, t, T, abbr, locale, fmtD }}>{children}</I18n.Provider>;
}

export function useI18n() {
  const c = useContext(I18n);
  if (!c) throw new Error("useI18n outside provider");
  return c;
}
