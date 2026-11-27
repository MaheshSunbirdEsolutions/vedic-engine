"use client";
import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton, useAuth } from "@clerk/nextjs";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function Header() {
  const { t, lang, setLang } = useI18n();
  const { isLoaded, isSignedIn, userId } = useAuth();
  const path = usePathname();
  const nav = [
    { href: "/", key: "nav_home", on: path === "/" || path.startsWith("/kundli") },
    { href: "/horoscope", key: "nav_horoscope", on: path.startsWith("/horoscope") },
    { href: "/panchang", key: "nav_panchang", on: path.startsWith("/panchang") },
    { href: "/match", key: "nav_match", on: path.startsWith("/match") },
  ];

  // Ensure the signed-in user's profile row exists in Supabase on first visit.
  useEffect(() => {
    if (isLoaded && isSignedIn && userId) {
      api("/me").catch(() => {});
    }
  }, [isLoaded, isSignedIn, userId]);

  return (
    <header>
      <div className="om">ॐ</div>
      <div><h1>Jyotish Lab</h1><div className="sub">{t("app_sub")}</div></div>
      <nav className="nav">
        {nav.map((n) => <Link key={n.href} href={n.href} className={n.on ? "on" : ""}>{t(n.key)}</Link>)}
      </nav>
      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
        <div className="lang" style={{ marginLeft: 0 }}>
          <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>English</button>
          <button className={lang === "hi" ? "on" : ""} onClick={() => setLang("hi")}>हिन्दी</button>
        </div>
        {isLoaded && !isSignedIn && (
          <Link href="/sign-in" className="btn light" style={{ padding: "6px 12px" }}>
            {lang === "hi" ? "साइन इन" : "Sign in"}
          </Link>
        )}
        {isLoaded && isSignedIn && <UserButton />}
      </div>
    </header>
  );
}
