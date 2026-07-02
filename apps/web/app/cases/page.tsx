"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Case } from "@/lib/api";
import { severityBadgeClass } from "@/lib/risk";
import { useLang } from "@/lib/i18n";

export default function CasesPage() {
  const { t } = useLang();
  const [cases, setCases] = useState<Case[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listCases()
      .then(setCases)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between">
        <h1 className="text-2xl font-bold">{t("caseHistory")}</h1>
        <Link href="/analyze" className="btn-primary text-sm">
          + New analysis
        </Link>
      </header>

      {error && (
        <div className="card border-alert-600/50 p-5 text-sm text-ink-300">
          Could not load cases: {error}. Is the API running?
        </div>
      )}

      {!cases && !error && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-20" />
          ))}
        </div>
      )}

      {cases && cases.length === 0 && (
        <div className="card grid place-items-center p-14 text-center">
          <p className="text-ink-300">No cases yet.</p>
          <p className="mt-1 text-sm text-ink-500">
            Run the seed script or start a new analysis to see cases here.
          </p>
        </div>
      )}

      <div className="space-y-2.5">
        {cases?.map((c) => (
          <Link
            key={c.id}
            href={`/cases/${c.id}`}
            className="card flex flex-wrap items-center gap-3 p-4 transition-colors hover:border-accent-400/60"
          >
            <div
              className="grid h-12 w-12 shrink-0 place-items-center rounded-lg text-sm font-black tabular-nums"
              style={{
                background:
                  c.final_risk_score >= 75
                    ? "rgba(224,45,60,.12)"
                    : c.final_risk_score >= 50
                      ? "rgba(249,115,22,.12)"
                      : c.final_risk_score >= 25
                        ? "rgba(245,158,11,.12)"
                        : "rgba(34,197,94,.12)",
              }}
            >
              {Math.round(c.final_risk_score)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate font-semibold">{c.title}</div>
              <div className="mt-0.5 flex flex-wrap gap-2 text-[11px] text-ink-500">
                <span>{c.case_number}</span>
                <span>· {c.source_type}</span>
                <span>· {c.language === "hi" ? "हिंदी" : "English"}</span>
                {c.city && <span>· {c.city}</span>}
                <span>· {new Date(c.created_at).toLocaleString()}</span>
              </div>
            </div>
            <span className={`rounded-full border px-2.5 py-1 text-[11px] font-bold ${severityBadgeClass(c.severity)}`}>
              {c.severity}
            </span>
            <span
              className={`rounded-full border px-2.5 py-1 text-[11px] ${
                c.status === "reviewed"
                  ? "border-safe-500/40 text-safe-500"
                  : "border-navy-600 text-ink-500"
              }`}
            >
              {c.status}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
