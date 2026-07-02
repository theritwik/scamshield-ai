"use client";
/** Demo-only investigator login. Clearly labelled: not production authentication. */
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useToast } from "@/components/Toast";
import { api } from "@/lib/api";

export default function InvestigatorLogin() {
  const router = useRouter();
  const { push } = useToast();
  const [token, setToken] = useState("demo-investigator");
  const [busy, setBusy] = useState(false);

  return (
    <div className="mx-auto max-w-md space-y-5 pt-10">
      <div className="card p-6">
        <h1 className="text-xl font-bold">Command Centre access</h1>
        <p className="mt-2 text-sm text-ink-300">
          Role-gated dashboard for banks and law-enforcement teams. This prototype uses a{" "}
          <span className="font-semibold text-warn-500">static demo token</span> instead of real
          authentication — intentionally, and documented as such.
        </p>
        <form
          className="mt-4 space-y-3"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            localStorage.setItem("ssa_investigator_token", token);
            try {
              await api.dashboardSummary();
              push("Investigator session started (demo)", "success");
              router.push("/investigator/dashboard");
            } catch {
              localStorage.removeItem("ssa_investigator_token");
              push("Invalid token. The demo token is: demo-investigator", "error");
              setBusy(false);
            }
          }}
        >
          <div>
            <label className="label" htmlFor="token">Demo token</label>
            <input
              id="token"
              className="input font-mono"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          </div>
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? "Verifying…" : "Enter Command Centre"}
          </button>
        </form>
      </div>
      <p className="text-center text-xs text-ink-500">
        Investigator access reveals seeded synthetic identifiers only. All complaint data is
        fictional.
      </p>
    </div>
  );
}
