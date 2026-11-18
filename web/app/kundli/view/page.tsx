"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { kundliFromQuery } from "@/lib/api";
import KundliView from "@/components/KundliView";

function View() {
  const k = kundliFromQuery(new URLSearchParams(useSearchParams().toString()));
  if (!k) return <div className="page"><p className="err" style={{ display: "block" }}>Missing birth details.</p></div>;
  return <KundliView key={JSON.stringify(k)} initial={k} />;
}

export default function Page() {
  return <Suspense><View /></Suspense>;
}
