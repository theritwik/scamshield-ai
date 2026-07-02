"use client";
/** Analysis result page: timeline, transcript, entities, report, audit. */
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  API_URL,
  type Assessment,
  type AuditEvent,
  type Case,
  type EntityOut,
  type GraphPayload,
} from "@/lib/api";
import { AssessmentPanel } from "@/components/AssessmentPanel";
import { FraudGraph } from "@/components/FraudGraph";
import { MessageBubble } from "@/components/SignalBadge";
import { RiskTimelineChart } from "@/components/RiskTimelineChart";
import { useToast } from "@/components/Toast";
import { useLang } from "@/lib/i18n";
import { severityBadgeClass } from "@/lib/risk";

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useLang();
  const { push } = useToast();
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [entities, setEntities] = useState<EntityOut[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [graph, setGraph] = useState<GraphPayload | null>(null);
  const [tab, setTab] = useState<"timeline" | "entities" | "graph" | "audit">("timeline");
  const [error, setError] = useState("");
  const [generating, setGenerating] = useState(false);
  const msgRefs = useRef<Record<number, HTMLDivElement | null>>({});

  const load = useCallback(async () => {
    try {
      const c = await api.getCase(id);
      setCaseData(c);
      setEntities(await api.entities(id));
      setAudit(await api.caseAudit(id));
      try {
        setAssessment(await api.assessment(id));
      } catch {
        setAssessment(null);
      }
      try {
        setGraph(await api.caseGraph(id));
      } catch {
        setGraph(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load case");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) {
    return <div className="card border-alert-600/50 p-6 text-sm">Error: {error}</div>;
  }
  if (!caseData) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-10 w-2/3" />
        <div className="skeleton h-48" />
        <div className="skeleton h-64" />
      </div>
    );
  }

  const messages = caseData.messages ?? [];

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-bold sm:text-2xl">{caseData.title}</h1>
            <span className={`rounded-full border px-2.5 py-1 text-[11px] font-bold ${severityBadgeClass(caseData.severity)}`}>
              {caseData.severity}
            </span>
          </div>
          <p className="mt-1 text-xs text-ink-500">
            {caseData.case_number} · {caseData.source_type} ·{" "}
            {caseData.language === "hi" ? "हिंदी" : "English"} · created{" "}
            {new Date(caseData.created_at).toLocaleString()} · status {caseData.status}
            {caseData.payment_prevented && (
              <span className="ml-2 rounded bg-safe-500/10 px-1.5 py-0.5 text-safe-500">
                payment interruption triggered
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className="btn-primary text-sm"
            disabled={generating || messages.length === 0}
            onClick={async () => {
              setGenerating(true);
              try {
                const r = await api.generateReport(id);
                push(`Report generated (SHA-256 ${r.sha256.slice(0, 12)}…)`, "success");
                window.open(`${API_URL}${r.download}`, "_blank");
                setAudit(await api.caseAudit(id));
              } catch (e) {
                push(e instanceof Error ? e.message : "Report failed", "error");
              } finally {
                setGenerating(false);
              }
            }}
          >
            {generating ? "Generating…" : `⬇ ${t("generateReport")}`}
          </button>
          <Link href="/safety" className="btn-danger text-sm">
            {t("safetyMode")}
          </Link>
        </div>
      </header>

      {assessment ? (
        <AssessmentPanel assessment={assessment} />
      ) : (
        <div className="card p-6 text-sm text-ink-300">
          No analysis yet — add messages to this case from the Analyze page.
        </div>
      )}

      <nav className="flex gap-1 overflow-x-auto border-b border-navy-800 text-sm">
        {(
          [
            ["timeline", t("riskTimeline")],
            ["entities", "Entities"],
            ["graph", "Fraud graph"],
            ["audit", "Audit trail"],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`whitespace-nowrap rounded-t-lg px-4 py-2 font-medium ${
              tab === k ? "bg-navy-800 text-white" : "text-ink-500 hover:text-ink-300"
            }`}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === "timeline" && (
        <div className="space-y-4">
          {messages.length > 0 && (
            <div className="card p-4">
              <div className="label">
                {t("riskTimeline")} — click a point to jump to the message
              </div>
              <RiskTimelineChart
                points={messages}
                onSelect={(seq) =>
                  msgRefs.current[seq]?.scrollIntoView({ behavior: "smooth", block: "center" })
                }
              />
            </div>
          )}
          <div className="space-y-3">
            {messages.map((m) => (
              <div
                key={m.id}
                ref={(el) => {
                  msgRefs.current[m.seq] = el;
                }}
              >
                <MessageBubble
                  speaker={m.speaker}
                  text={m.text}
                  signals={m.detected_signals}
                  delta={m.risk_delta}
                  cumulative={m.cumulative_risk}
                />
              </div>
            ))}
            {messages.length === 0 && (
              <div className="card p-8 text-center text-sm text-ink-500">
                No conversation recorded for this case.
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "entities" && (
        <div className="card overflow-x-auto">
          {entities.length === 0 ? (
            <div className="p-8 text-center text-sm text-ink-500">No entities extracted.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-navy-700 text-left text-[11px] uppercase tracking-wider text-ink-500">
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Masked value</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Previously reported</th>
                </tr>
              </thead>
              <tbody>
                {entities.map((e) => (
                  <tr key={e.id} className="border-b border-navy-800/60">
                    <td className="px-4 py-2.5 capitalize">{e.entity_type.replace("_", " ")}</td>
                    <td className="px-4 py-2.5 font-mono text-[13px]">{e.masked}</td>
                    <td className="px-4 py-2.5 text-ink-500">{e.source}</td>
                    <td className="px-4 py-2.5">
                      {e.previously_reported ? (
                        <span className="rounded bg-alert-600/15 px-2 py-0.5 text-xs font-bold text-alert-600">
                          YES — in registry
                        </span>
                      ) : (
                        <span className="text-ink-500">no</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="px-4 py-3 text-[11px] text-ink-500">
            Sensitive identifiers are masked. Investigators with the demo token can reveal
            synthetic values in the Command Centre.
          </p>
        </div>
      )}

      {tab === "graph" &&
        (graph ? (
          <FraudGraph data={graph} height={420} />
        ) : (
          <div className="card p-8 text-center text-sm text-ink-500">No graph data.</div>
        ))}

      {tab === "audit" && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-700 text-left text-[11px] uppercase tracking-wider text-ink-500">
                <th className="px-4 py-3">Timestamp (UTC)</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Change</th>
              </tr>
            </thead>
            <tbody>
              {audit.map((a) => (
                <tr key={a.event_id} className="border-b border-navy-800/60">
                  <td className="whitespace-nowrap px-4 py-2.5 font-mono text-xs text-ink-300">
                    {new Date(a.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5">{a.actor}</td>
                  <td className="px-4 py-2.5">{a.action.replace(/_/g, " ")}</td>
                  <td className="px-4 py-2.5 text-xs text-ink-500">
                    {a.previous_value && a.new_value
                      ? `${a.previous_value} → ${a.new_value}`
                      : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="px-4 py-3 text-[11px] text-ink-500">
            Append-only audit log — the prototype exposes no deletion path for audit records.
          </p>
        </div>
      )}
    </div>
  );
}
