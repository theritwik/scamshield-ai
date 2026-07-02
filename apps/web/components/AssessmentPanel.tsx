"use client";
import type { Assessment } from "@/lib/api";
import { RiskGauge } from "@/components/RiskGauge";
import { useLang } from "@/lib/i18n";
import { fmtCategory, severityBadgeClass } from "@/lib/risk";

export function AssessmentPanel({ assessment }: { assessment: Assessment }) {
  const { t, lang } = useLang();
  const a = assessment;
  return (
    <div className="card p-5">
      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
        <RiskGauge score={a.score} />
        <div className="min-w-0 flex-1 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full border px-3 py-1 text-xs font-bold ${severityBadgeClass(a.severity)}`}>
              {a.severity.toUpperCase()}
            </span>
            <span className="rounded-full border border-navy-600 px-3 py-1 text-xs text-ink-300">
              {lang === "hi" && a.category_label_hi ? a.category_label_hi : (a.category_label ?? fmtCategory(a.category))}
            </span>
            <span className="rounded-full border border-navy-600 px-3 py-1 text-xs text-ink-300">
              {t("confidence")}: {(a.confidence * 100).toFixed(0)}%
            </span>
            {a.engine_version && (
              <span className="rounded-full border border-navy-700 px-3 py-1 text-[10px] text-ink-500">
                {a.engine_version}
              </span>
            )}
          </div>

          {a.stages_detected.length > 0 && (
            <div>
              <div className="label">{t("detectedStages")}</div>
              <ol className="flex flex-wrap items-center gap-1.5 text-xs">
                {a.stages_detected.map((s, i) => (
                  <li key={s.stage} className="flex items-center gap-1.5">
                    <span className="rounded-md border border-warn-500/40 bg-warn-500/10 px-2 py-1 font-medium text-warn-500">
                      {s.order}. {lang === "hi" ? s.label_hi : s.label}
                    </span>
                    {i < a.stages_detected.length - 1 && <span className="text-ink-500">→</span>}
                  </li>
                ))}
              </ol>
            </div>
          )}

          <div>
            <div className="label">Top evidence</div>
            <ul className="space-y-1.5 text-sm">
              {a.top_reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-0.5 shrink-0 rounded bg-navy-800 px-1.5 py-0.5 text-[10px] font-bold tabular-nums text-accent-400">
                    +{Math.round(r.weight)}
                  </span>
                  <span>
                    <span className="font-medium">{lang === "hi" ? r.label_hi : r.label}</span>
                    {r.excerpt && (
                      <span className="text-ink-500"> — “{r.excerpt}”</span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-safe-500/30 bg-safe-500/5 p-4">
          <div className="label text-safe-500">{t("recommendedActions")}</div>
          <ul className="list-disc space-y-1 pl-4 text-sm">
            {a.recommended_actions.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg border border-navy-700 p-4">
          <div className="label">Missing evidence & caution</div>
          <ul className="list-disc space-y-1 pl-4 text-sm text-ink-300">
            {a.missing_evidence.map((r) => (
              <li key={r}>{r}</li>
            ))}
            <li className="text-ink-500">{a.false_positive_caution}</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
