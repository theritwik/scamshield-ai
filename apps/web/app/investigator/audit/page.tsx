"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type AuditEvent } from "@/lib/api";

export default function GlobalAuditPage() {
  const router = useRouter();
  const [events, setEvents] = useState<AuditEvent[] | null>(null);

  useEffect(() => {
    api
      .allAudit()
      .then(setEvents)
      .catch(() => router.push("/investigator"));
  }, [router]);

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Audit trail</h1>
        <p className="mt-1 text-sm text-ink-500">
          Append-only event log across all cases — no deletion path exists in the prototype.
        </p>
      </header>
      {!events ? (
        <div className="skeleton h-96" />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-700 text-left text-[11px] uppercase tracking-wider text-ink-500">
                <th className="px-4 py-3">Timestamp (UTC)</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Case</th>
                <th className="px-4 py-3">Metadata</th>
              </tr>
            </thead>
            <tbody>
              {events.map((a) => (
                <tr key={a.event_id} className="border-b border-navy-800/60 align-top">
                  <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-ink-300">
                    {new Date(a.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">{a.actor}</td>
                  <td className="px-4 py-2">{a.action.replace(/_/g, " ")}</td>
                  <td className="px-4 py-2 font-mono text-xs text-ink-500">
                    {a.case_id ? a.case_id.slice(0, 8) : "—"}
                  </td>
                  <td className="max-w-64 truncate px-4 py-2 font-mono text-[11px] text-ink-500">
                    {JSON.stringify(a.meta)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
