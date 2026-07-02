"use client";
/** New analysis: paste text, upload evidence, or check an identifier. */
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import { useToast } from "@/components/Toast";

export default function AnalyzePage() {
  const router = useRouter();
  const { lang, t } = useLang();
  const { push } = useToast();

  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("call");
  const [text, setText] = useState("");
  const [entityType, setEntityType] = useState("phone");
  const [entityValue, setEntityValue] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileKind, setFileKind] = useState("screenshot");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function run() {
    if (!consent) {
      push("Please confirm consent before analysing.", "error");
      return;
    }
    if (!text.trim() && !file && !entityValue.trim()) {
      push("Add a conversation, a file or an identifier to analyse.", "error");
      return;
    }
    setBusy(true);
    try {
      const c = await api.createCase({
        title: title.trim() || "Citizen analysis",
        language: lang,
        source_type: sourceType,
        consent_given: true,
      });
      if (text.trim()) {
        const lines = text
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
          .map((l) => {
            const m = l.match(/^(caller|victim|scammer|me|user)\s*[:\-]\s*(.+)$/i);
            if (m) {
              const sp = ["victim", "me", "user"].includes(m[1].toLowerCase())
                ? "victim"
                : "caller";
              return { speaker: sp, text: m[2] };
            }
            return { speaker: "caller", text: l };
          });
        await api.addMessagesBulk(c.id, lines);
      }
      if (entityValue.trim()) {
        await api.addEntity(c.id, { entity_type: entityType, value: entityValue.trim() });
      }
      if (file) {
        await api.uploadEvidence(c.id, fileKind, file);
      }
      if (text.trim() || file) {
        router.push(`/cases/${c.id}`);
      } else {
        router.push(`/cases/${c.id}`);
      }
    } catch (e) {
      push(e instanceof Error ? e.message : "Analysis failed", "error");
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold">{t("startAnalysis")}</h1>
        <p className="mt-1 text-sm text-ink-300">
          Paste a suspicious conversation, upload evidence, or check a phone / UPI / account
          identifier. Everything is analysed by the explainable coercion engine.
        </p>
      </header>

      <div className="card space-y-4 p-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="title">Case title (optional)</label>
            <input
              id="title"
              className="input"
              placeholder="e.g. Suspicious CBI call"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
            />
          </div>
          <div>
            <label className="label" htmlFor="source">Source</label>
            <select id="source" className="input" value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
              <option value="call">Phone / video call</option>
              <option value="sms">SMS</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="email">Email</option>
              <option value="text">Other text</option>
            </select>
          </div>
        </div>

        <div>
          <label className="label" htmlFor="convo">Suspicious conversation</label>
          <textarea
            id="convo"
            className="input min-h-40 font-mono text-[13px]"
            placeholder={
              "One message per line. Optional speaker prefix:\ncaller: Your Aadhaar is linked to an illegal parcel...\nvictim: What parcel?\ncaller: Do not tell your family..."
            }
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="efile">Upload evidence (optional)</label>
            <select className="input mb-2" value={fileKind} onChange={(e) => setFileKind(e.target.value)} aria-label="Evidence kind">
              <option value="screenshot">Screenshot (OCR)</option>
              <option value="qr">QR code image</option>
              <option value="audio">Audio recording</option>
              <option value="transcript">Transcript file (.txt)</option>
            </select>
            <input
              id="efile"
              type="file"
              accept=".png,.jpg,.jpeg,.mp3,.wav,.txt"
              className="input"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <p className="mt-1 text-[11px] text-ink-500">
              PNG/JPG, MP3/WAV or TXT, max 8 MB. Files are hashed (SHA-256) and never altered.
            </p>
          </div>
          <div>
            <label className="label" htmlFor="entity">Check an identifier (optional)</label>
            <select className="input mb-2" value={entityType} onChange={(e) => setEntityType(e.target.value)} aria-label="Identifier type">
              <option value="phone">Phone number</option>
              <option value="upi_id">UPI ID</option>
              <option value="bank_account">Bank account</option>
              <option value="url">URL</option>
            </select>
            <input
              id="entity"
              className="input"
              placeholder="e.g. rbi.verify@ybl"
              value={entityValue}
              onChange={(e) => setEntityValue(e.target.value)}
            />
            <p className="mt-1 text-[11px] text-ink-500">
              Checked against the synthetic reported-entity registry.
            </p>
          </div>
        </div>

        <label className="flex items-start gap-2 text-sm text-ink-300">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-1 accent-[#2f6fe4]"
          />
          I consent to this content being analysed to assess fraud risk. I understand this is a
          prototype using decision-support analysis, that sensitive identifiers are masked, and
          that no real alerts are sent.
        </label>

        <button className="btn-primary w-full py-3 text-base" onClick={run} disabled={busy}>
          {busy ? t("analyzing") : "Analyse for fraud risk"}
        </button>
      </div>

      <p className="text-center text-xs text-ink-500">
        Prefer a live message-by-message demo? Try the{" "}
        <a href="/simulate" className="text-accent-400 underline">
          live call simulation
        </a>
        .
      </p>
    </div>
  );
}
