"use client";
import { useLang } from "@/lib/i18n";

export default function SafetyPage() {
  const { t, lang } = useLang();
  const steps = [
    t("doNotSendMoney"),
    t("doNotShareOtp"),
    t("endTheCall"),
    t("contactTrusted"),
    t("contactBank"),
    t("preserveEvidence"),
    t("reportIncident"),
  ];
  return (
    <div className="mx-auto max-w-lg space-y-5">
      <div className="pulse-alert rounded-2xl border-2 border-alert-600 bg-navy-900 p-6 text-center">
        <div className="mx-auto mb-4 grid h-20 w-20 place-items-center rounded-full bg-alert-600 text-4xl font-black text-white">
          !
        </div>
        <h1 className="text-4xl font-black text-alert-600">
          {lang === "hi" ? "रुकिए" : "STOP"}
        </h1>
        <p className="mt-3 text-base font-semibold leading-relaxed">{t("stopWarning")}</p>
      </div>

      <ol className="space-y-2">
        {steps.map((s, i) => (
          <li key={s} className="card flex items-center gap-3 p-4 text-sm font-medium">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-navy-800 font-bold text-accent-400">
              {i + 1}
            </span>
            {s}
          </li>
        ))}
      </ol>

      <div className="card space-y-2 p-4 text-sm">
        <div className="label">{lang === "hi" ? "आधिकारिक हेल्पलाइन" : "Official helplines"}</div>
        <p>
          🇮🇳 {lang === "hi" ? "राष्ट्रीय साइबर अपराध हेल्पलाइन" : "National cybercrime helpline"}:{" "}
          <span className="font-bold text-white">1930</span>
        </p>
        <p>
          🌐 {lang === "hi" ? "ऑनलाइन रिपोर्ट" : "Report online"}:{" "}
          <span className="font-bold text-white">cybercrime.gov.in</span>
        </p>
      </div>

      <p className="text-center text-xs leading-relaxed text-ink-500">{t("disclaimer")}</p>
    </div>
  );
}
