import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px 16px",
      gap: 18,
    }}>
      <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "inherit" }}>
        <span style={{
          width: 38, height: 38, borderRadius: "50%", background: "var(--accent)", color: "#fff",
          display: "grid", placeItems: "center", fontSize: 20,
        }}>ॐ</span>
        <span style={{ fontSize: 22, fontWeight: 700 }}>Jyotish Lab</span>
      </Link>
      {children}
    </div>
  );
}
