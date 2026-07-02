"use client";
import Link from "next/link";
import { useLang } from "@/lib/i18n";

const stages = [
  "Authority impersonation",
  "Fake accusation",
  "Isolation",
  "Secrecy",
  "Digital-arrest threat",
  "'Safe account' payment",
];

export default function Landing() {
  const { t } = useLang();
  return (
    <div className="space-y-14">
      <section className="mx-auto max-w-3xl pt-10 text-center">
        <div className="mx-auto mb-4 inline-flex items-center gap-2 rounded-full border border-navy-600 px-3 py-1 text-xs text-ink-300">
          <span className="h-2 w-2 animate-pulse rounded-full bg-safe-500" />
          Hackathon prototype · Synthetic data · Simulated integrations
        </div>
        <h1 className="text-4xl font-black leading-tight tracking-tight sm:text-5xl">
          ScamShield <span className="text-accent-400">AI</span>
        </h1>
        <p className="mt-3 text-lg font-semibold text-ink-100">{t("tagline")}</p>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-ink-300">
          Digital-arrest scammers impersonate the CBI, police, customs and banks — and trap
          victims through fear, isolation and continuous video calls. Most tools scan keywords.
          ScamShield AI detects the <span className="font-semibold text-white">evolving sequence of
          psychological coercion</span> across the whole conversation, and interrupts the fraud
          before money moves.
        </p>
        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <Link href="/simulate" className="btn-danger px-6 py-3 text-base">
            ▶ {t("liveSimulation")}
          </Link>
          <Link href="/analyze" className="btn-primary px-6 py-3 text-base">
            {t("startAnalysis")}
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {[
          {
            title: "Psychological captivity detection",
            body: "A sequence-aware engine scores 13 coercion stages — impersonation → accusation → isolation → secrecy → threat → payment — with sequence bonuses, not just keywords.",
          },
          {
            title: "Explainable, auditable evidence",
            body: "Every point of risk traces to a named rule. One click produces a timestamped PDF report with SHA-256 hashes, masked entities and the full audit trail.",
          },
          {
            title: "Fraud-network intelligence",
            body: "Phones, UPI IDs and mule accounts are linked across complaints into a fraud graph, surfacing rings and repeated payment endpoints for investigators.",
          },
        ].map((f) => (
          <div key={f.title} className="card p-5">
            <h3 className="font-bold">{f.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-300">{f.body}</p>
          </div>
        ))}
      </section>

      <section className="card p-6">
        <div className="label">How the risk climbs during a real digital-arrest script</div>
        <div className="mt-4 grid gap-2 sm:grid-cols-6">
          {stages.map((s, i) => {
            const pct = [24, 43, 63, 78, 89, 98][i];
            const color = pct >= 75 ? "#e02d3c" : pct >= 50 ? "#f97316" : "#f59e0b";
            return (
              <div key={s} className="rounded-lg border border-navy-700 p-3 text-center">
                <div className="text-xl font-black tabular-nums" style={{ color }}>
                  {pct}%
                </div>
                <div className="mt-1 text-[11px] leading-tight text-ink-300">{s}</div>
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-[11px] text-ink-500">
          Illustrative sequence — in the product the score emerges live from the detected signals,
          never from hardcoded values. Try it in the live simulation.
        </p>
      </section>
    </div>
  );
}
