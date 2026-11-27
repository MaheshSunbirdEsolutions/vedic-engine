"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth, useUser } from "@clerk/nextjs";
import { api, birthOf, nowIn, type Kundli } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import BirthForm from "@/components/BirthForm";
import { DailyView } from "@/components/DailyReport";

export default function HoroscopePage() {
  const { t, T, lang } = useI18n();
  const { isLoaded, isSignedIn, userId } = useAuth();
  const { user } = useUser();
  const [day, setDay] = useState(() => new Date().toISOString().slice(0, 10));
  const [saved, setSaved] = useState<Kundli[]>([]);
  const [kundlisLoaded, setKundlisLoaded] = useState(false);
  const [kid, setKid] = useState("");
  const [fallbackKundli, setFallbackKundli] = useState<Kundli | null>(null);
  const [personal, setPersonal] = useState<any>(null);
  const [chart, setChart] = useState<any>(null);
  const [profileEmail, setProfileEmail] = useState("");
  const [adding, setAdding] = useState(false);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const lbl = (k: string, en: string, hi: string) => {
    const v = t(k);
    return v === k ? (lang === "hi" ? hi : en) : v;
  };

  const userEmail =
    user?.primaryEmailAddress?.emailAddress ||
    user?.emailAddresses?.[0]?.emailAddress ||
    profileEmail;

  const rememberKid = (id: string) => {
    setKid(id);
    try {
      if (userId && id) localStorage.setItem(`jyotish_horoscope_kid:${userId}`, id);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn || !userId) {
      setSaved([]);
      setKid("");
      setFallbackKundli(null);
      setPersonal(null);
      setChart(null);
      setProfileEmail("");
      setKundlisLoaded(false);
      return;
    }

    let cancelled = false;
    setKundlisLoaded(false);
    setErr("");

    api<{ email?: string }>("/me")
      .then((p) => { if (!cancelled && p?.email) setProfileEmail(p.email); })
      .catch(() => {});

    api<Kundli[]>("/kundlis")
      .then(async (xs) => {
        if (cancelled) return;
        if (xs.length > 0) {
          setSaved(xs);
          setFallbackKundli(null);
          let preferred = "";
          try { preferred = localStorage.getItem(`jyotish_horoscope_kid:${userId}`) || ""; } catch { /* ignore */ }
          const pick = xs.find((x) => x.id === preferred) || xs[0];
          rememberKid(pick.id || "");
          return;
        }
        let cached: Kundli | null = null;
        try {
          const raw = localStorage.getItem(`jyotish_last_kundli:${userId}`);
          if (raw) cached = JSON.parse(raw);
        } catch { /* ignore */ }

        if (cached && cached.datetime_local && cached.tz) {
          try {
            const created = await api<Kundli>("/kundlis", cached);
            if (cancelled) return;
            setSaved([created]);
            setFallbackKundli(null);
            rememberKid(created.id || "");
          } catch {
            if (!cancelled) setFallbackKundli(cached);
          }
        } else {
          setSaved([]);
        }
      })
      .catch((e) => { if (!cancelled) setErr(e.message); })
      .finally(() => { if (!cancelled) setKundlisLoaded(true); });

    return () => { cancelled = true; };
  }, [isLoaded, isSignedIn, userId]); // eslint-disable-line react-hooks/exhaustive-deps

  const activeKundli = saved.find((x) => x.id === kid) || fallbackKundli;

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !activeKundli) return;
    let cancelled = false;
    setLoading(true);
    setErr("");
    setPersonal(null);
    setChart(null);
    Promise.all([
      api("/report/daily", { ...birthOf(activeKundli), lang, day, at: nowIn(activeKundli.tz) }),
      api("/chart", birthOf(activeKundli)).catch(() => null),
    ])
      .then(([rep, ch]) => {
        if (cancelled) return;
        setPersonal(rep);
        if (ch) setChart(ch);
      })
      .catch((e) => { if (!cancelled) setErr(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [isLoaded, isSignedIn, activeKundli, day, lang]);

  const saveNewKundli = async (k: Kundli) => {
    setErr("");
    try {
      const created = await api<Kundli>("/kundlis", k);
      setSaved((prev) => [created, ...prev]);
      setFallbackKundli(null);
      rememberKid(created.id || "");
      try {
        if (userId) localStorage.setItem(`jyotish_last_kundli:${userId}`, JSON.stringify(created));
      } catch { /* ignore */ }
      setAdding(false);
    } catch (e: any) {
      setErr(e.message);
    }
  };

  const natal = personal?.natal || (chart ? {
    lagna: chart.lagna?.sign,
    lagna_sanskrit: chart.lagna?.sign_sanskrit,
    moon_sign: chart.planets?.Moon?.sign,
    moon_rashi_sanskrit: chart.planets?.Moon?.sign_sanskrit,
    nakshatra: chart.planets?.Moon?.nakshatra?.name,
    pada: chart.planets?.Moon?.nakshatra?.pada,
  } : null);

  const rashiTop = natal?.moon_sign
    ? `${T(natal.moon_sign)}${natal.moon_rashi_sanskrit && T(natal.moon_sign) !== natal.moon_rashi_sanskrit ? ` (${natal.moon_rashi_sanskrit})` : ""}`
    : "";
  const lagnaTop = natal?.lagna
    ? `${T(natal.lagna)}${natal.lagna_sanskrit && T(natal.lagna) !== natal.lagna_sanskrit ? ` (${natal.lagna_sanskrit})` : ""}`
    : "";
  const sunTop = chart?.planets?.Sun?.sign
    ? `${T(chart.planets.Sun.sign)}${chart.planets.Sun.sign_sanskrit && T(chart.planets.Sun.sign) !== chart.planets.Sun.sign_sanskrit ? ` (${chart.planets.Sun.sign_sanskrit})` : ""}`
    : "";

  return (
    <div className="page">
      <section className="card">
        <div className="kheader" style={{ marginBottom: 10 }}>
          <h2 style={{ margin: 0 }}>{t("daily_title")}</h2>
          {activeKundli?.name && <span className="chip gray">{activeKundli.name}</span>}
          {rashiTop && (
            <span className="chip" style={{ fontSize: 13.5, padding: "4px 12px" }}>
              {lbl("janma_rashi", "Janma Rashi (Moon)", "जन्म राशि (चंद्र)")}: {rashiTop}
            </span>
          )}
          {lagnaTop && (
            <span className="chip gray">
              {t("lagna")}: {lagnaTop}
            </span>
          )}
          {sunTop && (
            <span className="chip gray">
              {T("Sun")}: {sunTop}
            </span>
          )}
          {isLoaded && isSignedIn && userEmail && (
            <span className="chip gray" style={{ marginLeft: "auto" }}>
              {lbl("signed_in_as", "Signed in as", "साइन इन:")} {user?.fullName ? `${user.fullName} · ` : ""}{userEmail}
            </span>
          )}
        </div>

        {!isLoaded && <div className="empty">{t("loading")}</div>}

        {isLoaded && !isSignedIn && (
          <div className="empty">
            <p style={{ marginBottom: 12 }}>
              {lbl("sign_in_horoscope", "Sign in to view your personal daily horoscope with full details and send it to your email.", "अपना विस्तृत व्यक्तिगत दैनिक राशिफल देखने और अपने ईमेल पर भेजने के लिए साइन इन करें।")}
            </p>
            <Link href="/sign-in" className="btn">{lang === "hi" ? "साइन इन करें" : "Sign in"}</Link>
          </div>
        )}

        {isLoaded && isSignedIn && !kundlisLoaded && <div className="empty">{t("loading")}</div>}

        {isLoaded && isSignedIn && kundlisLoaded && (
          <>
            {activeKundli && (
              <div className="row" style={{ maxWidth: 780, marginBottom: 14, alignItems: "end" }}>
                <div>
                  <label>{t("date")}</label>
                  <input type="date" value={day} onChange={(e) => setDay(e.target.value)} />
                </div>
                <div>
                  <label>{t("choose_saved")}</label>
                  <div className="btnrow" style={{ alignItems: "center" }}>
                    {saved.length > 0 ? (
                      <select value={kid} onChange={(e) => rememberKid(e.target.value)} style={{ flex: 1 }}>
                        {saved.map((k) => (
                          <option key={k.id} value={k.id}>{k.name} · {k.datetime_local.slice(0, 10)}</option>
                        ))}
                      </select>
                    ) : (
                      <span className="chip gray">{activeKundli.name} · {activeKundli.datetime_local.slice(0, 10)}</span>
                    )}
                    {kid && <Link className="btn light" href={`/kundli/${kid}`}>{t("open_kundli_full")}</Link>}
                    <button type="button" className="ghost" onClick={() => setAdding((x) => !x)}>
                      {adding ? t("cancel") : `+ ${lbl("add_kundli", "Add new birth chart", "नई कुंडली जोड़ें")}`}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {(adding || !activeKundli) && (
              <div className="card" style={{ marginBottom: 16 }}>
                <h3 style={{ marginTop: 0 }}>
                  {!activeKundli
                    ? lbl("need_kundli_horoscope", "Save your birth details once to see your personal daily horoscope.", "अपना व्यक्तिगत दैनिक राशिफल देखने के लिए एक बार अपना जन्म विवरण सहेजें।")
                    : lbl("add_kundli", "Add new birth chart", "नई कुंडली जोड़ें")}
                </h3>
                <BirthForm
                  compact
                  submitLabel={lbl("create_my_kundli", "Save my birth details", "मेरा जन्म विवरण सहेजें")}
                  onSubmit={saveNewKundli}
                  onCancel={activeKundli ? () => setAdding(false) : undefined}
                />
              </div>
            )}

            {err && <p className="err" style={{ display: "block" }}>{err}</p>}
            {loading && <div className="empty">{t("loading")}</div>}

            {!loading && personal && activeKundli && (
              <div className="rep">
                <DailyView
                  r={personal}
                  kundli={activeKundli}
                  chart={chart}
                  userEmail={userEmail}
                  lockToUserEmail
                  showAllDetails
                  onSelectDay={setDay}
                />
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
