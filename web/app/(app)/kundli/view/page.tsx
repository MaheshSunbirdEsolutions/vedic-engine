"use client";
import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { kundliFromQuery } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import KundliView from "@/components/KundliView";

function View() {
  const { t } = useI18n();
  const { isLoaded, isSignedIn } = useAuth();
  const router = useRouter();
  const q = useSearchParams().toString();
  const k = kundliFromQuery(new URLSearchParams(q));

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      const target = q ? `/kundli/view?${q}` : "/kundli/view";
      router.replace(`/sign-in?redirect_url=${encodeURIComponent(target)}`);
    }
  }, [isLoaded, isSignedIn, q, router]);

  if (!isLoaded || !isSignedIn) {
    return <div className="page"><div className="empty">{t("loading")}</div></div>;
  }
  if (!k) return <div className="page"><p className="err" style={{ display: "block" }}>Missing birth details.</p></div>;
  return <KundliView key={JSON.stringify(k)} initial={k} />;
}

export default function Page() {
  return <Suspense><View /></Suspense>;
}
