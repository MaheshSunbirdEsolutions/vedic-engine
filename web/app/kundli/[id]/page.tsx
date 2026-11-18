"use client";
import { use, useEffect, useState } from "react";
import { api, type Kundli } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import KundliView from "@/components/KundliView";

export default function SavedKundli({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t } = useI18n();
  const [k, setK] = useState<Kundli | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api<Kundli>(`/kundlis/${id}`).then(setK).catch(() => setErr(t("not_found"))); }, [id, t]);
  if (err) return <div className="page"><p className="err" style={{ display: "block" }}>{err}</p></div>;
  if (!k) return <div className="page"><div className="empty">{t("loading")}</div></div>;
  return <KundliView key={k.id} initial={k} />;
}
