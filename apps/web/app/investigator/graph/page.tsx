"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type GraphPayload } from "@/lib/api";
import { FraudGraph } from "@/components/FraudGraph";

export default function InvestigatorGraphPage() {
  const router = useRouter();
  const [graph, setGraph] = useState<GraphPayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .networkGraph()
      .then(setGraph)
      .catch((e) => {
        if (String(e.message).includes("token")) router.push("/investigator");
        else setError(e.message);
      });
  }, [router]);

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Fraud network</h1>
        <p className="mt-1 text-sm text-ink-500">
          Complaints linked through shared phones, UPI IDs, accounts, URLs and scripts.
          {graph && (
            <>
              {" "}
              {graph.nodes.length} nodes · {graph.edges.length} edges · {graph.components}{" "}
              connected component{graph.components === 1 ? "" : "s"}
            </>
          )}
        </p>
      </header>

      {error && <div className="card border-alert-600/50 p-5 text-sm">{error}</div>}
      {!graph && !error && <div className="skeleton h-[480px]" />}
      {graph && <FraudGraph data={graph} />}

      {graph && graph.suspected_mules.length > 0 && (
        <section className="card p-4">
          <div className="label">Suspected mule endpoints (ranked)</div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-ink-500">
                <th className="py-2">Rank</th>
                <th className="py-2">Type</th>
                <th className="py-2">Identifier</th>
                <th className="py-2">Complaints</th>
                <th className="py-2">Max linked risk</th>
              </tr>
            </thead>
            <tbody>
              {graph.suspected_mules.map((m, i) => (
                <tr key={m.id} className="border-t border-navy-800/60">
                  <td className="py-2 font-bold tabular-nums">#{i + 1}</td>
                  <td className="py-2 capitalize">{m.type.replace("_", " ")}</td>
                  <td className="py-2 font-mono text-[12px]">{m.label}</td>
                  <td className="py-2 tabular-nums">{m.complaints}</td>
                  <td className="py-2 tabular-nums text-alert-600">{Math.round(m.risk)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-[11px] text-ink-500">
            “Suspected” and “reported” only — requires human verification before any action.
          </p>
        </section>
      )}
    </div>
  );
}
