"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api, birthOf, type Kundli } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

type Props = {
  kind: "rashi" | "kundli";
  sign?: string;
  kundli?: Kundli;
  tz: string;
  lat: number;
  lon: number;
  day: string;
};

export default function EmailShareButton({ kind, sign = "Aries", kundli, tz, lat, lon, day }: Props) {
  const { t, T, lang } = useI18n();
  const [open, setOpen] = useState(false);
  const [st, setSt] = useState<any>(null);
  const [toEmail, setToEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [preview, setPreview] = useState<{ subject: string; text: string } | null>(null);

  useEffect(() => {
    if (open && !st) {
      api("/email/status").then(setSt).catch(() => {});
    }
  }, [open, st]);

  const basePayload = () => ({
    to_email: toEmail.trim(),
    kind,
    sign,
    kundli_id: kundli?.id || "",
    name: kundli?.name || "",
    ...(kundli ? birthOf(kundli) : { tz, lat, lon }),
    lang,
    day,
  });

  const send = async () => {
    if (!toEmail.trim()) {
      setErr(t("email_need_to"));
      return;
    }
    setBusy(true); setErr(""); setMsg("");
    try {
      const r = await api("/email/horoscope", basePayload());
      setSt(r.status);
      setMsg(`✓ ${t("email_sent_ok")} ${(r.to || []).join(", ")}`);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const togglePreview = async () => {
    if (preview) { setPreview(null); return; }
    setBusy(true); setErr("");
    try {
      setPreview(await api("/email/horoscope", { ...basePayload(), preview_only: true }));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="noprint" style={{ marginTop: 8, marginBottom: 12 }}>
      <div className="btnrow" style={{ alignItems: "center" }}>
        <button type="button" className="btn light" onClick={() => setOpen((x) => !x)}>
          ✉ {t("email_share_btn")}
        </button>
        {open && st && (
          <span className={`chip ${st.configured ? "good" : "mixed"}`}>
            {st.configured ? `${t("email_smtp_ready")} (${st.host})` : t("email_smtp_missing")}
          </span>
        )}
      </div>

      {open && (
        <div className="finding mixed" style={{ marginTop: 10 }}>
          <div className="kheader" style={{ marginBottom: 6 }}>
            <h4 style={{ margin: 0 }}>{t("email_title")}</h4>
            <span className="note">
              {kind === "rashi" ? T(sign) : (kundli?.name || t("by_kundli"))} · {day}
            </span>
          </div>

          <div className="btnrow" style={{ alignItems: "end" }}>
            <div style={{ flex: 2, minWidth: 220 }}>
              <label>{t("email_to")}</label>
              <input
                type="text"
                inputMode="email"
                value={toEmail}
                placeholder={t("email_to_ph")}
                onChange={(e) => setToEmail(e.target.value)}
              />
            </div>
            <button type="button" className="btn" disabled={busy} onClick={send}>
              {busy ? t("email_sending") : t("email_send")}
            </button>
            <button type="button" className="ghost" disabled={busy} onClick={togglePreview}>
              {t("email_preview")}
            </button>
          </div>

          {st && !st.configured && (
            <p className="note" style={{ marginTop: 8, marginBottom: 0 }}>{t("email_env_hint")}</p>
          )}
          {err && <p className="err" style={{ display: "block" }}>{err}</p>}
          {msg && <p style={{ color: "var(--good)", fontWeight: 600, marginTop: 8, marginBottom: 0 }}>{msg}</p>}

          {preview && (
            <div style={{ marginTop: 10 }}>
              <div className="note" style={{ marginBottom: 4 }}><b>Subject:</b> {preview.subject}</div>
              <pre style={{ margin: 0, padding: 10, background: "#faf7f2", border: "1px solid var(--line)", borderRadius: 8, whiteSpace: "pre-wrap", fontSize: 12.5 }}>
                {preview.text}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
