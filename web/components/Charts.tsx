"use client";
// North and South Indian kundli drawings (SVG). `bySign[signIndex]` = labels to place in that sign.
import { useI18n } from "@/lib/i18n";

export const SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];

export function useLabels() {
  const { abbr, lang } = useI18n();
  return (planetSigns: Record<string, number>, retro?: Record<string, boolean>) => {
    const by: Record<number, string[]> = {};
    for (let i = 0; i < 12; i++) by[i] = [];
    for (const [p, s] of Object.entries(planetSigns)) by[s].push(abbr(p) + (retro?.[p] ? (lang === "en" ? "ᴿ" : "(व)") : ""));
    return by;
  };
}

const H: number[][][] = [
  [[200, 0], [300, 100], [200, 200], [100, 100], [200, 95]], [[0, 0], [200, 0], [100, 100], [100, 38]],
  [[0, 0], [100, 100], [0, 200], [36, 104]], [[0, 200], [100, 100], [200, 200], [100, 300], [100, 195]],
  [[0, 200], [100, 300], [0, 400], [36, 302]], [[0, 400], [100, 300], [200, 400], [100, 365]],
  [[200, 400], [100, 300], [200, 200], [300, 300], [200, 300]], [[200, 400], [300, 300], [400, 400], [300, 365]],
  [[400, 400], [300, 300], [400, 200], [364, 302]], [[400, 200], [300, 300], [200, 200], [300, 100], [300, 195]],
  [[400, 200], [300, 100], [400, 0], [364, 104]], [[400, 0], [300, 100], [200, 0], [300, 38]],
];
const N = [[200, 180], [100, 82], [82, 104], [180, 200], [82, 300], [100, 322], [200, 224], [300, 322], [318, 300], [220, 200], [318, 104], [300, 82]];

export function NorthChart({ lagna, bySign }: { lagna: number; bySign: Record<number, string[]> }) {
  const { t } = useI18n();
  return (
    <svg className="kundli" viewBox="-2 -2 404 404">
      <rect x={0} y={0} width={400} height={400} fill="#fffdf9" stroke="#c9b9a6" strokeWidth={2} />
      <path d="M0 0L400 400M400 0L0 400M200 0L400 200L200 400L0 200Z" fill="none" stroke="#c9b9a6" strokeWidth={1.5} />
      {H.map((h, i) => {
        const sign = (lagna + i) % 12, a = h[h.length - 1], labels = bySign[sign] || [];
        const cols = labels.length > 3 ? 2 : 1;
        return (
          <g key={i}>
            <text x={N[i][0]} y={N[i][1]} fontSize={11} fill="#b39a82" textAnchor="middle">{sign + 1}</text>
            {i === 0 && <text x={200} y={62} fontSize={11} fill="#c2571a" textAnchor="middle" fontWeight={700}>{t("asc")}</text>}
            {labels.map((x, k) => {
              const col = k % cols, rw = Math.floor(k / cols);
              const px = a[0] + (cols === 2 ? (col ? 18 : -18) : 0), py = a[1] + rw * 15 - (Math.ceil(labels.length / cols) - 1) * 7.5;
              return <text key={k} x={px} y={py} fontSize={13} fontWeight={600} fill="#2b2420" textAnchor="middle" dominantBaseline="middle">{x}</text>;
            })}
          </g>
        );
      })}
    </svg>
  );
}

const POS: Record<number, [number, number]> = { 11: [0, 0], 0: [1, 0], 1: [2, 0], 2: [3, 0], 3: [3, 1], 4: [3, 2], 5: [3, 3], 6: [2, 3], 7: [1, 3], 8: [0, 3], 9: [0, 2], 10: [0, 1] };

export function SouthChart({ lagna, bySign }: { lagna: number; bySign: Record<number, string[]> }) {
  const { t, T, lang } = useI18n();
  return (
    <svg className="kundli" viewBox="-2 -2 404 404">
      <rect x={0} y={0} width={400} height={400} fill="#fffdf9" stroke="#c9b9a6" strokeWidth={2} />
      {Object.entries(POS).map(([sg, [c, r]]) => {
        const s = +sg, x = c * 100, y = r * 100, labels = bySign[s] || [];
        return (
          <g key={s}>
            <rect x={x} y={y} width={100} height={100} fill={s === lagna ? "#fbeadf" : "none"} stroke="#c9b9a6" />
            <text x={x + 6} y={y + 14} fontSize={10.5} fill="#b39a82">{lang === "en" ? SIGNS[s].slice(0, 3) : T(SIGNS[s])}</text>
            {s === lagna && <text x={x + 94} y={y + 14} fontSize={10.5} fill="#c2571a" textAnchor="end" fontWeight={700}>{t("asc")}</text>}
            {labels.map((p, k) => <text key={k} x={x + 50 + (k % 2 ? 22 : -22) * (labels.length > 1 ? 1 : 0)} y={y + 40 + Math.floor(k / 2) * 17} fontSize={13} fontWeight={600} textAnchor="middle">{p}</text>)}
          </g>
        );
      })}
      <text x={200} y={196} fontSize={14} textAnchor="middle" fill="#7a6f66">{t("rashi")}</text>
    </svg>
  );
}

export function Kundli({ style, lagna, bySign }: { style: "north" | "south"; lagna: number; bySign: Record<number, string[]> }) {
  return style === "north" ? <NorthChart lagna={lagna} bySign={bySign} /> : <SouthChart lagna={lagna} bySign={bySign} />;
}
