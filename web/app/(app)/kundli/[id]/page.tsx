"use client";
import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ApiError, api, type Kundli } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import KundliView from "@/components/KundliView";

export default function SavedKundli({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t } = useI18n();
  const { isLoaded, isSignedIn, userId } = useAuth();
  const router = useRouter();
  const [k, setK] = useState<Kundli | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      router.replace(`/sign-in?redirect_url=${encodeURIComponent(`/kundli/${id}`)}`);
      return;
    }
    setErr("");
    api<Kundli>(`/kundlis/${id}`)
      .then(setK)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) {
          router.replace(`/sign-in?redirect_url=${encodeURIComponent(`/kundli/${id}`)}`);
        } else {
          setErr(t("not_found"));
        }
      });
  }, [id, isLoaded, isSignedIn, userId, router, t]);

  if (!isLoaded || !isSignedIn) return <div className="page"><div className="empty">{t("loading")}</div></div>;
  if (err) return <div className="page"><p className="err" style={{ display: "block" }}>{err}</p></div>;
  if (!k) return <div className="page"><div className="empty">{t("loading")}</div></div>;
  return <KundliView key={k.id} initial={k} />;
}
