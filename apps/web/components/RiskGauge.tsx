"use client";
import { severityColor, scoreToSeverity } from "@/lib/risk";
import { useLang } from "@/lib/i18n";

export function RiskGauge({ score, size = 168 }: { score: number; size?: number }) {
  const { t } = useLang();
  const severity = scoreToSeverity(score);
  const color = severityColor(severity);
  const r = size / 2 - 12;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(100, Math.max(0, score));
  const sevKey = severity.toLowerCase() as "low" | "medium" | "high" | "critical";
  return (
    <div className="relative inline-grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1c3059" strokeWidth={10} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - pct / 100)}
          style={{ transition: "stroke-dashoffset 700ms ease, stroke 400ms ease" }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-4xl font-bold tabular-nums" style={{ color }}>
          {Math.round(pct)}
          <span className="text-lg text-ink-500">%</span>
        </div>
        <div className="text-xs font-semibold uppercase tracking-widest" style={{ color }}>
          {t(sevKey)}
        </div>
      </div>
    </div>
  );
}
