// Thin client for the Python Vedic Engine, reached through the Next.js /engine proxy.
/* eslint-disable @typescript-eslint/no-explicit-any */
export type Settings = { ayanamsa: string; node: string };
export type Birth = { datetime_local: string; tz: string; lat: number; lon: number; settings?: Settings };
export type Kundli = Birth & {
  id?: string; name: string; gender?: string; place?: string; notes?: string; tags?: string;
  created_at?: string; updated_at?: string;
};
export type Place = { name: string; country: string; lat: number; lon: number; tz: string; population?: number };

export async function api<T = any>(path: string, body?: unknown, method?: string): Promise<T> {
  const r = await fetch(`/engine${path}`, {
    method: method || (body !== undefined ? "POST" : "GET"),
    headers: body !== undefined ? { "content-type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!r.ok) {
    let msg = await r.text();
    try { msg = JSON.stringify(JSON.parse(msg).detail); } catch { /* keep text */ }
    throw new Error(`${path}: ${r.status} ${msg}`);
  }
  return r.json();
}

export const birthOf = (k: Kundli): Birth => ({
  datetime_local: k.datetime_local, tz: k.tz, lat: k.lat, lon: k.lon,
  settings: k.settings || { ayanamsa: "lahiri", node: "mean" },
});

/** Current local time in a time zone, as "YYYY-MM-DDTHH:MM:SS". */
export const nowIn = (tz: string) => new Date().toLocaleString("sv-SE", { timeZone: tz }).replace(" ", "T");

export const kundliToQuery = (k: Kundli) =>
  new URLSearchParams({
    name: k.name || "", dt: k.datetime_local, tz: k.tz, lat: String(k.lat), lon: String(k.lon), place: k.place || "",
    ay: k.settings?.ayanamsa || "lahiri", node: k.settings?.node || "mean", gender: k.gender || "",
  }).toString();

export const kundliFromQuery = (q: URLSearchParams): Kundli | null => {
  const dt = q.get("dt"), tz = q.get("tz"), lat = q.get("lat"), lon = q.get("lon");
  if (!dt || !tz || !lat || !lon) return null;
  return {
    name: q.get("name") || "", datetime_local: dt, tz, lat: +lat, lon: +lon, place: q.get("place") || "",
    gender: q.get("gender") || "", settings: { ayanamsa: q.get("ay") || "lahiri", node: q.get("node") || "mean" },
  };
};
