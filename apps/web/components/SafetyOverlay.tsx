"use client";
import Link from "next/link";
import { useLang } from "@/lib/i18n";
import { useToast } from "@/components/Toast";
import { api } from "@/lib/api";
import { useState } from "react";

export function SafetyOverlay({
  caseId,
  onDismiss,
}: {
  caseId?: string;
  onDismiss: () => void;
}) {
  const { t } = useLang();
  const { push } = useToast();
  const [alerting, setAlerting] = useState(false);

  const actions = [
    t("doNotSendMoney"),
    t("doNotShareOtp"),
    t("endTheCall"),
    t("contactTrusted"),
    t("contactBank"),
    t("preserveEvidence"),
    t("reportIncident"),
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-navy-950/95 p-4 backdrop-blur-sm">
      <div className="mx-auto mt-6 max-w-lg">
        <div className="pulse-alert rounded-2xl border-2 border-alert-600 bg-navy-900 p-6 text-center">
          <div className="mx-auto mb-4 grid h-16 w-16 place-items-center rounded-full bg-alert-600 text-3xl font-black text-white">
            !
          </div>
          <h2 className="text-3xl font-black tracking-tight text-alert-600">STOP</h2>
          <p className="mt-3 text-base font-semibold leading-relaxed">{t("stopWarning")}</p>

          <ul className="mt-5 space-y-2 text-left">
            {actions.map((a) => (
              <li
                key={a}
                className="flex items-start gap-2 rounded-lg bg-navy-850 px-3 py-2.5 text-sm font-medium"
              >
                <span className="mt-0.5 text-alert-600">■</span> {a}
              </li>
            ))}
          </ul>

          <div className="mt-5 grid gap-2 sm:grid-cols-2">
            <button
              className="btn-danger w-full"
              disabled={alerting || !caseId}
              onClick={async () => {
                if (!caseId) return;
                setAlerting(true);
                try {
                  const res = await api.simulateAlert(caseId);
                  push(res.message, "success");
                } catch (e) {
                  push(e instanceof Error ? e.message : "Alert failed", "error");
                } finally {
                  setAlerting(false);
                }
              }}
            >
              {alerting ? "…" : "Simulate alerts (demo)"}
            </button>
            {caseId ? (
              <Link href={`/cases/${caseId}`} className="btn-secondary w-full">
                {t("generateReport")}
              </Link>
            ) : (
              <Link href="/safety" className="btn-secondary w-full">
                {t("safetyMode")}
              </Link>
            )}
          </div>

          <button onClick={onDismiss} className="mt-4 text-sm text-ink-500 underline hover:text-ink-300">
            Continue reviewing the conversation
          </button>
          <p className="mt-4 text-[11px] leading-snug text-ink-500">{t("disclaimer")}</p>
        </div>
      </div>
    </div>
  );
}
