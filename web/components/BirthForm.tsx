"use client";
import { useState } from "react";
import type { Kundli, Place } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PlaceSearch from "./PlaceSearch";

export default function BirthForm({ initial, onSubmit, submitLabel, onCancel, compact }: {
  initial?: Partial<Kundli>; onSubmit: (k: Kundli) => void; submitLabel?: string; onCancel?: () => void; compact?: boolean;
}) {
  const { t } = useI18n();
  const [name, setName] = useState(initial?.name || "");
  const [gender, setGender] = useState(initial?.gender || "");
  const [dob, setDob] = useState(initial?.datetime_local?.slice(0, 10) || "");
  const [tob, setTob] = useState(initial?.datetime_local?.slice(11, 19) || "");
  const [place, setPlace] = useState<Place | null>(initial?.tz ? { name: initial.place || "", country: "", lat: initial.lat!, lon: initial.lon!, tz: initial.tz } : null);
  const [lat, setLat] = useState(initial?.lat?.toString() || "");
  const [lon, setLon] = useState(initial?.lon?.toString() || "");
  const [tz, setTz] = useState(initial?.tz || "");
  const [ay, setAy] = useState(initial?.settings?.ayanamsa || "lahiri");
  const [node, setNode] = useState(initial?.settings?.node || "mean");
  const [notes, setNotes] = useState(initial?.notes || "");
  const [tags, setTags] = useState(initial?.tags || "");
  const [err, setErr] = useState("");

  const choose = (p: Place) => { setPlace(p); setLat(String(p.lat)); setLon(String(p.lon)); setTz(p.tz); };
  const submit = () => {
    if (!dob || !tob) return setErr(t("err_dt"));
    const la = parseFloat(lat), lo = parseFloat(lon);
    if (isNaN(la) || isNaN(lo) || !tz) return setErr(t("err_place"));
    setErr("");
    onSubmit({
      ...(initial?.id ? { id: initial.id } : {}),
      name: name.trim() || `${dob} ${tob.slice(0, 5)}`, gender, place: place?.name || initial?.place || "",
      datetime_local: `${dob}T${tob.length === 5 ? tob + ":00" : tob}`, tz: tz.trim(), lat: la, lon: lo,
      settings: { ayanamsa: ay, node }, notes, tags,
    });
  };

  return (
    <div>
      <div className={compact ? "row" : ""}>
        <div><label>{t("name")}</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder={t("name_ph")} /></div>
        <div><label>{t("gender")}</label>
          <select value={gender} onChange={(e) => setGender(e.target.value)}>
            <option value="">—</option><option value="male">{t("male")}</option><option value="female">{t("female")}</option><option value="other">{t("other")}</option>
          </select></div>
      </div>
      <div className="row">
        <div><label>{t("dob")}</label><input type="date" value={dob} onChange={(e) => setDob(e.target.value)} /></div>
        <div><label>{t("tob")}</label><input type="time" step={1} value={tob} onChange={(e) => setTob(e.target.value)} /></div>
      </div>
      <label>{t("pob")}</label>
      <PlaceSearch value={place} onSelect={choose} />
      <details>
        <summary>{t("advanced")}</summary>
        <div className="row3">
          <div><label>{t("latitude")}</label><input type="number" step="0.0001" value={lat} onChange={(e) => setLat(e.target.value)} /></div>
          <div><label>{t("longitude")}</label><input type="number" step="0.0001" value={lon} onChange={(e) => setLon(e.target.value)} /></div>
          <div><label>{t("timezone")}</label><input value={tz} onChange={(e) => setTz(e.target.value)} placeholder="Asia/Kolkata" /></div>
        </div>
        <div className="row">
          <div><label>{t("ayanamsa")}</label>
            <select value={ay} onChange={(e) => setAy(e.target.value)}>
              <option value="lahiri">Lahiri</option><option value="raman">Raman</option>
              <option value="krishnamurti">Krishnamurti (KP)</option><option value="true_chitra">True Chitra</option>
            </select></div>
          <div><label>{t("node")}</label>
            <select value={node} onChange={(e) => setNode(e.target.value)}>
              <option value="mean">{t("mean_node")}</option><option value="true">{t("true_node")}</option>
            </select></div>
        </div>
        <label>{t("tags")}</label><input value={tags} onChange={(e) => setTags(e.target.value)} />
        <label>{t("notes")}</label><textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
      </details>
      <div className="btnrow" style={{ marginTop: 14 }}>
        <button className="btn" onClick={submit}>{submitLabel || t("generate")}</button>
        {onCancel && <button className="btn light" onClick={onCancel}>{t("cancel")}</button>}
      </div>
      {err && <div className="err" style={{ display: "block" }}>{err}</div>}
    </div>
  );
}
