"use client";
/** Live call simulation — the primary demo. Messages are analysed one by one
 *  and the risk score climbs as the coercion sequence unfolds. */
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api, type Assessment, type Case, type Message } from "@/lib/api";
import { AssessmentPanel } from "@/components/AssessmentPanel";
import { MessageBubble } from "@/components/SignalBadge";
import { RiskGauge } from "@/components/RiskGauge";
import { RiskTimelineChart } from "@/components/RiskTimelineChart";
import { SafetyOverlay } from "@/components/SafetyOverlay";
import { useToast } from "@/components/Toast";
import { useLang } from "@/lib/i18n";

const DEMO_SCRIPT_EN: { speaker: string; text: string }[] = [
  { speaker: "caller", text: "Hello, I am calling from TRAI. Your Aadhaar has been linked to an illegal parcel intercepted by Customs." },
  { speaker: "victim", text: "What parcel? I never sent anything." },
  { speaker: "caller", text: "This is serious. I am transferring your call to a CBI officer." },
  { speaker: "caller", text: "This is Inspector Rathi, CBI Mumbai. A case of money laundering has been registered against you." },
  { speaker: "caller", text: "This is a confidential matter. Do not tell your family about this investigation." },
  { speaker: "caller", text: "Go to a separate room. Do not disconnect this video call. You are under digital arrest." },
  { speaker: "victim", text: "Please, I have done nothing wrong." },
  { speaker: "caller", text: "If you want to avoid arrest tonight, act immediately." },
  { speaker: "caller", text: "Transfer ₹50,000 to the safe RBI verification account rbi.verify@ybl right now. The money will be returned after verification." },
];

const DEMO_SCRIPT_HI: { speaker: string; text: string }[] = [
  { speaker: "caller", text: "मैं दिल्ली पुलिस साइबर सेल से इंस्पेक्टर बोल रहा हूं। आपके आधार से एक अवैध पार्सल जुड़ा है।" },
  { speaker: "victim", text: "मुझे कुछ नहीं पता, कोई गलती हुई है।" },
  { speaker: "caller", text: "आपके खिलाफ मनी लॉन्ड्रिंग का केस दर्ज है। गिरफ्तारी का वारंट जारी हो चुका है।" },
  { speaker: "caller", text: "यह गुप्त जांच है। परिवार में किसी को मत बताना। अलग कमरे में जाइए।" },
  { speaker: "caller", text: "वीडियो कॉल मत काटिए। आप डिजिटल अरेस्ट में हैं।" },
  { speaker: "caller", text: "बचना है तो तुरंत 2 लाख रुपये cbi.clearance@ptyes पर ट्रांसफर करें।" },
];

export default function SimulatePage() {
  const { lang, t } = useLang();
  const { push } = useToast();
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [input, setInput] = useState("");
  const [speaker, setSpeaker] = useState("caller");
  const [busy, setBusy] = useState(false);
  const [scriptIdx, setScriptIdx] = useState(0);
  const [safetyShown, setSafetyShown] = useState(false);
  const [showSafety, setShowSafety] = useState(false);
  const [apiDown, setApiDown] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const script = lang === "hi" ? DEMO_SCRIPT_HI : DEMO_SCRIPT_EN;

  useEffect(() => {
    api.health().catch(() => setApiDown(true));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function ensureCase(): Promise<Case> {
    if (caseData) return caseData;
    const c = await api.createCase({
      title: lang === "hi" ? "लाइव कॉल सिमुलेशन" : "Live call simulation",
      language: lang,
      source_type: "call",
      consent_given: true,
    });
    setCaseData(c);
    return c;
  }

  async function send(sp: string, text: string) {
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      const c = await ensureCase();
      const res = await api.addMessage(c.id, { speaker: sp, text: text.trim(), language: lang });
      setMessages((m) => [...m, res.message]);
      setAssessment(res.assessment);
      if (res.assessment.score >= 75 && !safetyShown) {
        setSafetyShown(true);
        setShowSafety(true);
      }
    } catch (e) {
      push(e instanceof Error ? e.message : "Message failed", "error");
    } finally {
      setBusy(false);
    }
  }

  async function playNext() {
    if (scriptIdx >= script.length) return;
    const line = script[scriptIdx];
    setScriptIdx((i) => i + 1);
    await send(line.speaker, line.text);
  }

  function reset() {
    setCaseData(null);
    setMessages([]);
    setAssessment(null);
    setScriptIdx(0);
    setSafetyShown(false);
    setShowSafety(false);
  }

  if (apiDown) {
    return (
      <div className="card mx-auto max-w-lg p-8 text-center">
        <h1 className="text-xl font-bold text-alert-600">API unavailable</h1>
        <p className="mt-2 text-sm text-ink-300">
          The ScamShield API is not reachable. Start it with{" "}
          <code className="rounded bg-navy-800 px-1.5 py-0.5 text-xs">make api</code> (or{" "}
          <code className="rounded bg-navy-800 px-1.5 py-0.5 text-xs">docker compose up</code>) and reload.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {showSafety && (
        <SafetyOverlay caseId={caseData?.id} onDismiss={() => setShowSafety(false)} />
      )}

      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{t("liveSimulation")}</h1>
          <p className="mt-1 max-w-2xl text-sm text-ink-300">
            Simulates real-time call analysis with a typed transcript (prototype — no live call
            interception). Play the scripted digital-arrest demo or type your own lines and watch
            the coercion sequence drive the risk score.
          </p>
        </div>
        <div className="flex gap-2">
          {caseData && (
            <Link className="btn-secondary text-sm" href={`/cases/${caseData.id}`}>
              Full report view
            </Link>
          )}
          <button className="btn-secondary text-sm" onClick={reset}>
            Reset demo
          </button>
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <section className="card flex min-h-[420px] flex-col p-4">
          <div className="flex-1 space-y-3 overflow-y-auto pr-1" style={{ maxHeight: 460 }}>
            {messages.length === 0 && (
              <div className="grid h-full place-items-center py-16 text-center text-sm text-ink-500">
                <div>
                  <p className="mb-3">No messages yet.</p>
                  <button className="btn-danger" onClick={playNext} disabled={busy}>
                    ▶ Play scripted scam call
                  </button>
                </div>
              </div>
            )}
            {messages.map((m) => (
              <MessageBubble
                key={m.id}
                speaker={m.speaker}
                text={m.text}
                signals={m.detected_signals}
                delta={m.risk_delta}
                cumulative={m.cumulative_risk}
              />
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="mt-3 border-t border-navy-800 pt-3">
            <div className="flex flex-wrap gap-2">
              <button
                className="btn-danger flex-1 text-sm"
                onClick={playNext}
                disabled={busy || scriptIdx >= script.length}
              >
                {scriptIdx >= script.length
                  ? "Script finished"
                  : `▶ Next scripted line (${scriptIdx + 1}/${script.length})`}
              </button>
              <select
                className="input w-28 text-sm"
                value={speaker}
                onChange={(e) => setSpeaker(e.target.value)}
                aria-label="Speaker"
              >
                <option value="caller">{t("caller")}</option>
                <option value="victim">{t("victim")}</option>
              </select>
            </div>
            <form
              className="mt-2 flex gap-2"
              onSubmit={async (e) => {
                e.preventDefault();
                const v = input;
                setInput("");
                await send(speaker, v);
              }}
            >
              <input
                className="input flex-1"
                placeholder={lang === "hi" ? "अपना संदेश लिखें…" : "Type a message to analyse…"}
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <button className="btn-primary" disabled={busy || !input.trim()}>
                {busy ? "…" : t("send")}
              </button>
            </form>
          </div>
        </section>

        <aside className="space-y-4">
          <div className="card flex flex-col items-center p-5">
            <div className="label self-start">{t("riskScore")}</div>
            <RiskGauge score={assessment?.score ?? 0} />
            {assessment && (
              <p className="mt-2 text-center text-xs text-ink-500">
                {t("confidence")}: {(assessment.confidence * 100).toFixed(0)}% ·{" "}
                {assessment.processing_ms?.toFixed(0)} ms
              </p>
            )}
          </div>
          {messages.length > 0 && (
            <div className="card p-4">
              <div className="label">{t("riskTimeline")}</div>
              <RiskTimelineChart points={messages} />
            </div>
          )}
        </aside>
      </div>

      {assessment && messages.length > 0 && <AssessmentPanel assessment={assessment} />}
    </div>
  );
}
