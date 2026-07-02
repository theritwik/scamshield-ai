"use client";
/** Minimal English/Hindi dictionary + context. User-facing strings only. */
import { createContext, useContext, useEffect, useState } from "react";

export type Lang = "en" | "hi";

const dict = {
  tagline: {
    en: "Detect coercion. Interrupt fraud. Protect before payment.",
    hi: "दबाव पहचानें। धोखाधड़ी रोकें। भुगतान से पहले सुरक्षा।",
  },
  startAnalysis: { en: "Start a fraud-risk analysis", hi: "धोखाधड़ी जोखिम विश्लेषण शुरू करें" },
  liveSimulation: { en: "Live call simulation", hi: "लाइव कॉल सिमुलेशन" },
  caseHistory: { en: "Case history", hi: "केस इतिहास" },
  safetyMode: { en: "Safety Mode", hi: "सुरक्षा मोड" },
  riskScore: { en: "Risk score", hi: "जोखिम स्कोर" },
  severity: { en: "Severity", hi: "गंभीरता" },
  confidence: { en: "Confidence", hi: "विश्वसनीयता" },
  low: { en: "Low", hi: "कम" },
  medium: { en: "Medium", hi: "मध्यम" },
  high: { en: "High", hi: "उच्च" },
  critical: { en: "Critical", hi: "गंभीर" },
  stopWarning: {
    en: "STOP. This is highly likely to be a digital-arrest scam. Government agencies do not demand money or conduct arrests through video calls.",
    hi: "रुकिए। यह डिजिटल अरेस्ट धोखाधड़ी होने की बहुत अधिक संभावना है। कोई भी सरकारी एजेंसी वीडियो कॉल पर गिरफ्तारी या पैसे ट्रांसफर करने की मांग नहीं करती।",
  },
  doNotSendMoney: { en: "Do NOT send money", hi: "पैसे न भेजें" },
  doNotShareOtp: {
    en: "Do NOT share OTP, PIN, CVV, passwords or screen access",
    hi: "OTP, PIN, CVV, पासवर्ड या स्क्रीन एक्सेस साझा न करें",
  },
  endTheCall: { en: "End the call now", hi: "कॉल तुरंत समाप्त करें" },
  contactTrusted: { en: "Call a trusted person", hi: "किसी विश्वसनीय व्यक्ति को कॉल करें" },
  contactBank: {
    en: "Contact your bank on its official number",
    hi: "बैंक के आधिकारिक नंबर पर संपर्क करें",
  },
  preserveEvidence: {
    en: "Preserve screenshots and recordings",
    hi: "स्क्रीनशॉट और रिकॉर्डिंग सुरक्षित रखें",
  },
  reportIncident: {
    en: "Report at cybercrime.gov.in or call 1930",
    hi: "cybercrime.gov.in पर रिपोर्ट करें या 1930 पर कॉल करें",
  },
  generateReport: { en: "Generate evidence report", hi: "साक्ष्य रिपोर्ट बनाएं" },
  detectedStages: { en: "Detected coercion stages", hi: "पहचाने गए दबाव चरण" },
  riskTimeline: { en: "Progressive risk timeline", hi: "प्रगतिशील जोखिम समयरेखा" },
  suspiciousStatements: { en: "Suspicious statements", hi: "संदिग्ध कथन" },
  recommendedActions: { en: "Safety recommendations", hi: "सुरक्षा सिफारिशें" },
  disclaimer: {
    en: "ScamShield AI provides decision support, not legal confirmation. Assessments require human review.",
    hi: "ScamShield AI निर्णय सहायता देता है, कानूनी पुष्टि नहीं। आकलन के लिए मानवीय समीक्षा आवश्यक है।",
  },
  whyFlagged: { en: "Why was this flagged?", hi: "इसे क्यों चिह्नित किया गया?" },
  caller: { en: "Caller", hi: "कॉलर" },
  victim: { en: "You", hi: "आप" },
  send: { en: "Send", hi: "भेजें" },
  analyzing: { en: "Analysing…", hi: "विश्लेषण हो रहा है…" },
} as const;

export type DictKey = keyof typeof dict;

const LangContext = createContext<{
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (k: DictKey) => string;
}>({ lang: "en", setLang: () => {}, t: (k) => dict[k].en });

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  useEffect(() => {
    const saved = localStorage.getItem("ssa_lang");
    if (saved === "hi" || saved === "en") setLangState(saved);
  }, []);
  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem("ssa_lang", l);
  };
  const t = (k: DictKey) => dict[k][lang];
  return (
    <LangContext.Provider value={{ lang, setLang, t }}>{children}</LangContext.Provider>
  );
}

export const useLang = () => useContext(LangContext);
