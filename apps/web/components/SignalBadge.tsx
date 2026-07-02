"use client";
import type { DetectedSignal } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const kindStyle: Record<string, string> = {
  signal: "border-warn-500/40 bg-warn-500/10 text-warn-500",
  sequence_bonus: "border-accent-400/40 bg-accent-400/10 text-accent-400",
  entity_reputation: "border-alert-600/40 bg-alert-600/10 text-alert-600",
};

export function SignalBadge({ signal }: { signal: DetectedSignal }) {
  const { lang } = useLang();
  return (
    <span
      title={lang === "hi" ? signal.explanation_hi : signal.explanation}
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
        kindStyle[signal.kind] ?? kindStyle.signal
      }`}
    >
      {signal.kind === "sequence_bonus" && <span aria-hidden>⛓</span>}
      {signal.kind === "entity_reputation" && <span aria-hidden>⚑</span>}
      {lang === "hi" ? signal.label_hi : signal.label}
      <span className="opacity-70">+{Math.round(signal.weight)}</span>
    </span>
  );
}

export function MessageBubble({
  speaker,
  text,
  signals,
  delta,
  cumulative,
}: {
  speaker: string;
  text: string;
  signals: DetectedSignal[];
  delta: number;
  cumulative: number;
}) {
  const { t, lang } = useLang();
  const isCaller = speaker === "caller";
  const hasSignals = signals.some((s) => s.kind === "signal");
  return (
    <div className={`flex ${isCaller ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[85%] rounded-xl border p-3 ${
          isCaller
            ? hasSignals
              ? "border-alert-600/50 bg-alert-600/5"
              : "border-navy-700 bg-navy-850"
            : "border-navy-600 bg-navy-800"
        }`}
      >
        <div className="mb-1 flex items-center justify-between gap-4 text-[11px] text-ink-500">
          <span className="font-semibold uppercase tracking-wide">
            {isCaller ? t("caller") : t("victim")}
          </span>
          {delta > 0 && (
            <span className="font-bold text-alert-600">
              +{delta.toFixed(0)} → {cumulative.toFixed(0)}%
            </span>
          )}
        </div>
        <p className="text-sm leading-relaxed">{text}</p>
        {signals.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {signals.map((s, i) => (
              <SignalBadge key={`${s.signal_id}-${i}`} signal={s} />
            ))}
          </div>
        )}
        {hasSignals && (
          <details className="mt-2 text-xs text-ink-300">
            <summary className="cursor-pointer text-ink-500 hover:text-ink-300">
              {t("whyFlagged")}
            </summary>
            <ul className="mt-1 list-disc space-y-1 pl-4">
              {signals.map((s, i) => (
                <li key={i}>{lang === "hi" ? s.explanation_hi : s.explanation}</li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
