"use client";
import { useEffect, useRef, useState } from "react";
import { api, type Place } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function PlaceSearch({ value, onSelect, placeholder }: { value?: Place | null; onSelect: (p: Place) => void; placeholder?: string }) {
  const { t } = useI18n();
  const [text, setText] = useState(value ? `${value.name}${value.country ? ", " + value.country : ""}` : "");
  const [items, setItems] = useState<Place[]>([]);
  const [idx, setIdx] = useState(-1);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { if (value) setText(`${value.name}${value.country ? ", " + value.country : ""}`); }, [value]);

  const search = (q: string) => {
    setText(q);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      const s = q.split(",")[0].trim();
      if (s.length < 2) { setItems([]); return; }
      try { setItems(await api<Place[]>(`/places?q=${encodeURIComponent(s)}`)); setIdx(-1); } catch { setItems([]); }
    }, 180);
  };
  const pick = (p: Place) => { onSelect(p); setItems([]); setText(`${p.name}, ${p.country}`); };

  return (
    <div className="place-wrap">
      <input value={text} placeholder={placeholder || t("place_ph")} autoComplete="off"
        onChange={(e) => search(e.target.value)} onBlur={() => setTimeout(() => setItems([]), 150)}
        onKeyDown={(e) => {
          if (!items.length) return;
          if (e.key === "ArrowDown") { setIdx(Math.min(idx + 1, items.length - 1)); e.preventDefault(); }
          if (e.key === "ArrowUp") { setIdx(Math.max(idx - 1, 0)); e.preventDefault(); }
          if (e.key === "Enter" && idx >= 0) { pick(items[idx]); e.preventDefault(); }
        }} />
      {items.length > 0 && (
        <div className="suggest">
          {items.map((p, i) => (
            <div key={`${p.name}-${p.lat}`} className={i === idx ? "active" : ""} onMouseDown={() => pick(p)}>
              {p.name} <small>{p.country} · {p.tz}</small>
            </div>
          ))}
        </div>
      )}
      {value && <div className="placeinfo">{(+value.lat).toFixed(4)}°, {(+value.lon).toFixed(4)}° · {value.tz}</div>}
    </div>
  );
}
