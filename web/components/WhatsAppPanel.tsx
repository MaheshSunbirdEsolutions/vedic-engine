"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

type Props = {
  kind: "rashi" | "kundli";
  sign: string;
  kundliId: string;
  tz: string;
  lat: number;
  lon: number;
  day: string;
};

export default function WhatsAppPanel({ kind, sign, kundliId, tz, lat, lon, day }: Props) {
  const { t, T, lang } = useI18n();
  const [st, setSt] = useState<any>(null);
  const [phone, setPhone] = useState("");
  const [time, setTime] = useState("07:00");
  const [provider, setProvider] = useState("callmebot");
  const [cfg, setCfg] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [preview, setPreview] = useState<{ text: string; wa_me_url: string } | null>(null);

  const applyStatus = (s: any) => {
    setSt(s);
    if (s?.provider) setProvider(s.provider);
    if (s?.provider_config) {
      const next: Record<string, string> = {};
      for (const [k, v] of Object.entries<any>(s.provider_config)) {
        if (typeof v === "string") next[k] = v;
      }
      setCfg((prev) => ({ ...prev, ...next }));
    }
    if (s?.subscription?.phone) setPhone(s.subscription.phone);
    if (s?.subscription?.time) setTime(s.subscription.time);
  };

  useEffect(() => {
    api("/whatsapp/status").then(applyStatus).catch(() => {});
  }, []);

  const payload = (enabled: boolean) => ({
    enabled,
    phone,
    kind,
    sign: sign || "Aries",
    kundli_id: kundliId || "",
    time: time || "07:00",
    tz,
    lat,
    lon,
    lang,
    provider,
    provider_config: cfg,
    day,
  });

  const saveSchedule = async (enabled: boolean) => {
    if (enabled && !phone.trim()) {
      setErr(t("wa_need_phone"));
      return;
    }
    setBusy(true); setErr(""); setMsg("");
    try {
      const r = await api("/whatsapp/schedule", payload(enabled));
      applyStatus(r);
      setMsg(enabled ? `${t("wa_active")} · ${r.subscription.time} (${r.subscription.next_run || ""})` : t("wa_off"));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const sendNow = async () => {
    if (!phone.trim()) {
      setErr(t("wa_need_phone"));
      return;
    }
    setBusy(true); setErr(""); setMsg("");
    try {
      const r = await api("/whatsapp/send-now", payload(st?.subscription?.enabled ?? true));
      applyStatus(r.status);
      setPreview({ text: r.text, wa_me_url: r.wa_me_url });
      if (r.sent) setMsg(`✓ ${r.date}`);
      else setErr(r.error || "Failed to send");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const loadPreview = async (openWa = false) => {
    setBusy(true); setErr("");
    try {
      const r = await api("/whatsapp/preview", payload(false));
      setPreview(r);
      if (openWa && r.wa_me_url) window.open(r.wa_me_url, "_blank", "noopener,noreferrer");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const sub = st?.subscription;
  const pc = st?.provider_config || {};
  const enabled = Boolean(sub?.enabled);

  return (
    <div className="finding mixed" style={{ marginBottom: 16 }}>
      <div className="kheader" style={{ marginBottom: 6 }}>
        <h4 style={{ margin: 0 }}>{t("wa_title")}</h4>
        <span className={`chip ${enabled ? "good" : "gray"}`}>
          {enabled ? `${t("wa_active")} · ${sub?.time || "07:00"}` : t("wa_off")}
        </span>
        <span className="note">
          {kind === "rashi" ? T(sign || "Aries") : t("by_kundli")}
          {sub?.next_run ? ` · ${t("wa_next_run")}: ${sub.next_run.replace("T", " ")}` : ""}
          {sub?.last_sent_at ? ` · ${t("wa_last_sent")}: ${sub.last_sent_at.replace("T", " ")} (${sub.last_status})` : ""}
        </span>
      </div>
      <p className="note" style={{ marginTop: 0 }}>{t("wa_sub")}</p>

      <div className="row3">
        <div>
          <label>{t("wa_phone")}</label>
          <input value={phone} placeholder={t("wa_phone_ph")} onChange={(e) => setPhone(e.target.value)} />
        </div>
        <div>
          <label>{t("wa_time")}</label>
          <input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
        </div>
        <div>
          <label>{t("wa_provider")}</label>
          <select value={provider} onChange={(e) => setProvider(e.target.value)}>
            <option value="callmebot">CallMeBot (free key)</option>
            <option value="twilio">Twilio WhatsApp</option>
            <option value="meta">Meta WhatsApp Cloud API</option>
            <option value="webhook">Custom Webhook URL</option>
          </select>
        </div>
      </div>

      {provider === "callmebot" && (
        <div style={{ maxWidth: 360 }}>
          <label>CallMeBot API key {pc.api_key_set ? `(${pc.api_key_hint})` : ""}</label>
          <input type="password" value={cfg.api_key || ""} placeholder={pc.api_key_hint || "123456"}
            onChange={(e) => setCfg({ ...cfg, api_key: e.target.value })} />
        </div>
      )}
      {provider === "twilio" && (
        <div className="row3">
          <div>
            <label>Twilio Account SID</label>
            <input value={cfg.account_sid || ""} placeholder="AC..." onChange={(e) => setCfg({ ...cfg, account_sid: e.target.value })} />
          </div>
          <div>
            <label>Auth Token {pc.auth_token_set ? `(${pc.auth_token_hint})` : ""}</label>
            <input type="password" value={cfg.auth_token || ""} placeholder={pc.auth_token_hint || "token"}
              onChange={(e) => setCfg({ ...cfg, auth_token: e.target.value })} />
          </div>
          <div>
            <label>From WhatsApp</label>
            <input value={cfg.from_number || "whatsapp:+14155238886"} onChange={(e) => setCfg({ ...cfg, from_number: e.target.value })} />
          </div>
        </div>
      )}
      {provider === "meta" && (
        <div className="row">
          <div>
            <label>Phone Number ID</label>
            <input value={cfg.phone_number_id || ""} onChange={(e) => setCfg({ ...cfg, phone_number_id: e.target.value })} />
          </div>
          <div>
            <label>Access Token {pc.access_token_set ? `(${pc.access_token_hint})` : ""}</label>
            <input type="password" value={cfg.access_token || ""} placeholder={pc.access_token_hint || "EAAG..."}
              onChange={(e) => setCfg({ ...cfg, access_token: e.target.value })} />
          </div>
        </div>
      )}
      {provider === "webhook" && (
        <div style={{ maxWidth: 520 }}>
          <label>Webhook URL (receives POST JSON &#123;to, text&#125;)</label>
          <input value={cfg.webhook_url || ""} placeholder="http://127.0.0.1:5678/webhook/whatsapp"
            onChange={(e) => setCfg({ ...cfg, webhook_url: e.target.value })} />
        </div>
      )}

      <div className="btnrow" style={{ marginTop: 12 }}>
        <button className="btn" disabled={busy} onClick={() => saveSchedule(true)}>
          {enabled ? t("wa_save_btn") : t("wa_enable_btn")}
        </button>
        {enabled && (
          <button className="btn danger" disabled={busy} onClick={() => saveSchedule(false)}>
            {t("wa_disable_btn")}
          </button>
        )}
        <button className="btn light" disabled={busy} onClick={sendNow}>
          {t("wa_send_now")}
        </button>
        <button className="btn light" disabled={busy} onClick={() => loadPreview(true)}>
          {t("wa_open_app")}
        </button>
        <button className="ghost" disabled={busy} onClick={() => (preview ? setPreview(null) : loadPreview(false))}>
          {t("wa_preview")}
        </button>
      </div>

      {err && <p className="err" style={{ display: "block" }}>{err}</p>}
      {msg && <p style={{ color: "var(--good)", fontWeight: 600, marginTop: 8 }}>{msg}</p>}
      {sub?.last_error && !err && <p className="note" style={{ color: "var(--bad)" }}>{sub.last_error}</p>}
      <p className="note" style={{ marginTop: 8 }}>{t("wa_setup_note")}</p>

      {preview && (
        <pre style={{ marginTop: 8, padding: 10, background: "#faf7f2", border: "1px solid var(--line)", borderRadius: 8, whiteSpace: "pre-wrap", fontSize: 13 }}>
          {preview.text}
        </pre>
      )}
    </div>
  );
}
