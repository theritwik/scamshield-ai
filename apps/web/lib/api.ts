/** Typed client for the ScamShield AI FastAPI backend. */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface DetectedSignal {
  signal_id: string;
  stage: string;
  label: string;
  label_hi: string;
  weight: number;
  excerpt: string;
  explanation: string;
  explanation_hi: string;
  kind: "signal" | "sequence_bonus" | "entity_reputation";
}

export interface Message {
  id: string;
  seq: number;
  speaker: string;
  text: string;
  timestamp?: string;
  detected_signals: DetectedSignal[];
  risk_delta: number;
  cumulative_risk: number;
}

export interface StageDetected {
  stage: string;
  label: string;
  label_hi: string;
  order: number;
}

export interface Assessment {
  score: number;
  severity: "Low" | "Medium" | "High" | "Critical";
  confidence: number;
  category: string;
  category_label?: string;
  category_label_hi?: string;
  stages_detected: StageDetected[];
  top_reasons: {
    label: string;
    label_hi: string;
    weight: number;
    kind: string;
    excerpt: string;
    explanation: string;
    explanation_hi: string;
  }[];
  recommended_actions: string[];
  missing_evidence: string[];
  false_positive_caution: string;
  engine_version?: string;
  processing_ms?: number;
  timestamp?: string;
}

export interface Case {
  id: string;
  case_number: string;
  title: string;
  language: string;
  status: string;
  source_type: string;
  consent_given: boolean;
  final_risk_score: number;
  severity: string;
  confidence: number;
  suspected_category: string;
  payment_prevented: boolean;
  city: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
  entities?: EntityOut[];
}

export interface EntityOut {
  id: string;
  entity_type: string;
  masked: string;
  source: string;
  previously_reported: boolean;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  risk: number;
  degree: number;
  centrality: number;
  component: number;
  meta: Record<string, unknown>;
}

export interface GraphPayload {
  nodes: GraphNode[];
  edges: { source: string; target: string; relation: string }[];
  components: number;
  suspected_mules: {
    id: string;
    label: string;
    type: string;
    complaints: number;
    risk: number;
  }[];
  insights: string[];
  disclaimer: string;
}

export interface DashboardSummary {
  total_complaints: number;
  critical_cases: number;
  high_cases: number;
  open_cases: number;
  reviewed_cases: number;
  hindi_cases: number;
  english_cases: number;
  payments_prevented: number;
  repeated_phones: { masked: string; cases: number }[];
  repeated_upi_ids: { masked: string; cases: number }[];
  avg_detection_message: number | null;
  detected_before_payment_pct: number | null;
}

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor: string;
  action: string;
  case_id: string;
  meta: Record<string, unknown>;
  previous_value?: string;
  new_value?: string;
}

export function investigatorToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("ssa_investigator_token") ?? "";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string>),
  };
  if (!(init?.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const token = investigatorToken();
  if (token) headers["X-Investigator-Token"] = token;

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  createCase: (payload: {
    title: string;
    language: string;
    source_type: string;
    consent_given: boolean;
    city?: string;
  }) => request<Case>("/api/cases", { method: "POST", body: JSON.stringify(payload) }),

  listCases: () => request<Case[]>("/api/cases"),
  getCase: (id: string) => request<Case>(`/api/cases/${id}`),

  addMessage: (caseId: string, payload: { speaker: string; text: string; language?: string }) =>
    request<{ message: Message; assessment: Assessment }>(
      `/api/cases/${caseId}/messages`,
      { method: "POST", body: JSON.stringify(payload) },
    ),

  addMessagesBulk: (caseId: string, messages: { speaker: string; text: string }[]) =>
    request<{ added: number; assessment: Assessment }>(
      `/api/cases/${caseId}/messages/bulk`,
      { method: "POST", body: JSON.stringify({ messages }) },
    ),

  analyse: (caseId: string) =>
    request<Assessment>(`/api/cases/${caseId}/analyse`, { method: "POST" }),

  assessment: (caseId: string) => request<Assessment>(`/api/cases/${caseId}/assessment`),

  riskTimeline: (caseId: string) =>
    request<{ final_score: number; severity: string; points: Message[] }>(
      `/api/cases/${caseId}/risk-timeline`,
    ),

  entities: (caseId: string) => request<EntityOut[]>(`/api/cases/${caseId}/entities`),

  addEntity: (caseId: string, payload: { entity_type: string; value: string }) =>
    request<{
      entities: { entity_type: string; masked: string; previously_reported: boolean }[];
      assessment: Assessment | null;
    }>(`/api/cases/${caseId}/entities`, { method: "POST", body: JSON.stringify(payload) }),

  uploadEvidence: (caseId: string, kind: string, file: File) => {
    const form = new FormData();
    form.append("kind", kind);
    form.append("file", file);
    return request<{
      evidence_id: string;
      sha256: string;
      provider: string;
      simulated: boolean;
      extraction: Record<string, unknown>;
      entities_found: number;
      assessment: Assessment | null;
    }>(`/api/cases/${caseId}/evidence`, { method: "POST", body: form });
  },

  generateReport: (caseId: string) =>
    request<{ report_id: string; sha256: string; download: string }>(
      `/api/cases/${caseId}/generate-report`,
      { method: "POST" },
    ),

  caseGraph: (caseId: string) => request<GraphPayload>(`/api/cases/${caseId}/graph`),
  networkGraph: () => request<GraphPayload>("/api/graph/network"),

  dashboardSummary: () => request<DashboardSummary>("/api/dashboard/summary"),
  emergingPatterns: () =>
    request<{
      top_signals: { stage: string; label: string; count: number }[];
      categories: { category: string; count: number }[];
    }>("/api/dashboard/emerging-patterns"),
  hotspots: () =>
    request<{ synthetic: boolean; cities: { city: string; cases: number; avg_risk: number }[] }>(
      "/api/dashboard/hotspots",
    ),
  watchlist: () =>
    request<{ entity_type: string; masked: string; cases: number; watch: boolean }[]>(
      "/api/dashboard/watchlist",
    ),

  review: (caseId: string, payload: { decision: string; notes: string }) =>
    request<{ status: string }>(`/api/cases/${caseId}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  caseAudit: (caseId: string) => request<AuditEvent[]>(`/api/audit/${caseId}`),
  allAudit: () => request<AuditEvent[]>("/api/audit"),

  simulateAlert: (caseId: string) =>
    request<{ simulated: boolean; message: string }>(
      `/api/cases/${caseId}/simulate-alert`,
      { method: "POST" },
    ),
};
