"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/lib/i18n";

export default function Header() {
  const { t, lang, setLang } = useI18n();
  const path = usePathname();
  const nav = [
    { href: "/", key: "nav_home", on: path === "/" || path.startsWith("/kundli") },
    { href: "/horoscope", key: "nav_horoscope", on: path.startsWith("/horoscope") },
    { href: "/panchang", key: "nav_panchang", on: path.startsWith("/panchang") },
    { href: "/match", key: "nav_match", on: path.startsWith("/match") },
  ];
  return (
    <header>
      <div className="om">ॐ</div>
      <div><h1>Jyotish Lab</h1><div className="sub">{t("app_sub")}</div></div>
      <nav className="nav">
        {nav.map((n) => <Link key={n.href} href={n.href} className={n.on ? "on" : ""}>{t(n.key)}</Link>)}
      </nav>
      <div className="lang">
        <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>English</button>
        <button className={lang === "hi" ? "on" : ""} onClick={() => setLang("hi")}>हिन्दी</button>
      </div>
    </header>
  );
}
