"use client";
/** Bank & law-enforcement command centre. */
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type Case, type DashboardSummary } from "@/lib/api";
import { severityBadgeClass } from "@/lib/risk";
import { useToast } from "@/components/Toast";

function StatCard({ label, value, tone }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className="card p-4">
      <div className="text-2xl font-black tabular-nums" style={{ color: tone }}>
        {value}
      </div>
      <div className="mt-1 text-[11px] font-medium uppercase tracking-wider text-ink-500">{label}</div>
    </div>
  );
}

export default function InvestigatorDashboard() {
  const router = useRouter();
  const { push } = useToast();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [cases, setCases] = useState<Case[]>([]);
  const [patterns, setPatterns] = useState<{ stage: string; label: string; count: number }[]>([]);
  const [watchlist, setWatchlist] = useState<
    { entity_type: string; masked: string; cases: number; watch: boolean }[]
  >([]);
  const [statusFilter, setStatusFilter] = useState("all");

  const load = useCallback(async () => {
    try {
      const [s, c, p, w] = await Promise.all([
        api.dashboardSummary(),
        api.listCases(),
        api.emergingPatterns(),
        api.watchlist(),
      ]);
      setSummary(s);
      setCases(c);
      setPatterns(p.top_signals.slice(0, 8));
      setWatchlist(w);
    } catch {
      router.push("/investigator");
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  if (!summary) {
    return (
      <div className="grid gap-3 sm:grid-cols-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="skeleton h-24" />
        ))}
      </div>
    );
  }

  const filtered = cases.filter((c) =>
    statusFilter === "all"
      ? true
      : statusFilter === "critical"
        ? c.severity === "Critical"
        : c.status === statusFilter,
  );

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Command Centre</h1>
          <p className="mt-1 text-sm text-ink-500">
            Synthetic complaint data · human review required · entities are suspected, not guilty
          </p>
        </div>
        <nav className="flex gap-2 text-sm">
          <Link className="btn-secondary" href="/investigator/graph">Fraud network</Link>
          <Link className="btn-secondary" href="/investigator/map">Hotspots</Link>
          <Link className="btn-secondary" href="/investigator/audit">Audit</Link>
        </nav>
      </header>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <StatCard label="Total complaints" value={summary.total_complaints} />
        <StatCard label="Critical cases" value={summary.critical_cases} tone="#e02d3c" />
        <StatCard label="High cases" value={summary.high_cases} tone="#f97316" />
        <StatCard label="Payment interruptions" value={summary.payments_prevented} tone="#22c55e" />
        <StatCard label="Open / reviewed" value={`${summary.open_cases} / ${summary.reviewed_cases}`} />
        <StatCard
          label="Avg detection message"
          value={summary.avg_detection_message ?? "—"}
        />
        <StatCard
          label="Detected before payment"
          value={summary.detected_before_payment_pct !== null ? `${summary.detected_before_payment_pct}%` : "—"}
          tone="#22c55e"
        />
        <StatCard label="Hindi / English" value={`${summary.hindi_cases} / ${summary.english_cases}`} />
        <StatCard label="Repeated phones" value={summary.repeated_phones.length} tone="#f59e0b" />
        <StatCard label="Repeated UPI IDs" value={summary.repeated_upi_ids.length} tone="#f59e0b" />
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="card p-4">
          <div className="label">Emerging script signals</div>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={patterns} layout="vertical" margin={{ left: 10, right: 12 }}>
                <CartesianGrid stroke="#1c3059" strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" stroke="#7e90b8" fontSize={11} allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="label"
                  width={210}
                  stroke="#7e90b8"
                  fontSize={10}
                  tickFormatter={(v: string) => (v.length > 34 ? v.slice(0, 33) + "…" : v)}
                />
                <Tooltip
                  contentStyle={{ background: "#0e1b36", border: "1px solid #1c3059", borderRadius: 8, fontSize: 12 }}
                  cursor={{ fill: "rgba(79,142,247,0.06)" }}
                />
                <Bar dataKey="count" fill="#4f8ef7" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="card p-4">
          <div className="label">Entity watchlist (revealed synthetic data)</div>
          <div className="max-h-64 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wider text-ink-500">
                  <th className="py-2">Type</th>
                  <th className="py-2">Identifier</th>
                  <th className="py-2">Cases</th>
                  <th className="py-2">Watch</th>
                </tr>
              </thead>
              <tbody>
                {watchlist.map((w, i) => (
                  <tr key={i} className="border-t border-navy-800/60">
                    <td className="py-2 capitalize text-ink-300">{w.entity_type.replace("_", " ")}</td>
                    <td className="py-2 font-mono text-[12px]">{w.masked}</td>
                    <td className="py-2 tabular-nums">{w.cases}</td>
                    <td className="py-2">
                      {w.watch && (
                        <span className="rounded bg-alert-600/15 px-2 py-0.5 text-[11px] font-bold text-alert-600">
                          WATCH
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="card">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-navy-800 p-4">
          <div className="label mb-0">Case queue</div>
          <select
            className="input max-w-40 text-sm"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter cases"
          >
            <option value="all">All cases</option>
            <option value="critical">Critical only</option>
            <option value="open">Open</option>
            <option value="reviewed">Reviewed</option>
          </select>
        </div>
        <div className="max-h-[430px] overflow-y-auto">
          {filtered.map((c) => (
            <div key={c.id} className="flex flex-wrap items-center gap-3 border-b border-navy-800/60 px-4 py-3">
              <span className={`w-16 rounded-full border px-2 py-0.5 text-center text-[11px] font-bold ${severityBadgeClass(c.severity)}`}>
                {Math.round(c.final_risk_score)}
              </span>
              <Link href={`/cases/${c.id}`} className="min-w-0 flex-1 truncate text-sm font-medium hover:text-accent-400">
                {c.title}
              </Link>
              <span className="text-[11px] text-ink-500">{c.city || "—"}</span>
              <span className="text-[11px] text-ink-500">{c.language === "hi" ? "HI" : "EN"}</span>
              <span className={`text-[11px] ${c.status === "reviewed" ? "text-safe-500" : "text-ink-500"}`}>
                {c.status}
              </span>
              {c.status !== "reviewed" && (
                <div className="flex gap-1">
                  <button
                    className="rounded border border-alert-600/40 px-2 py-1 text-[11px] font-semibold text-alert-600 hover:bg-alert-600/10"
                    onClick={async () => {
                      await api.review(c.id, { decision: "confirmed_scam", notes: "Confirmed from command centre" });
                      push(`${c.case_number} marked confirmed scam`, "success");
                      load();
                    }}
                  >
                    Confirm scam
                  </button>
                  <button
                    className="rounded border border-safe-500/40 px-2 py-1 text-[11px] font-semibold text-safe-500 hover:bg-safe-500/10"
                    onClick={async () => {
                      await api.review(c.id, { decision: "not_scam", notes: "Cleared from command centre" });
                      push(`${c.case_number} marked not scam`, "success");
                      load();
                    }}
                  >
                    Not scam
                  </button>
                </div>
              )}
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="p-8 text-center text-sm text-ink-500">No cases match this filter.</div>
          )}
        </div>
      </section>
    </div>
  );
}
