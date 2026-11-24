// Types mirror the backend responses (verified against /openapi.json).
// NOTE: ids are numbers on the backend (the written contract used string).

export type DocumentKind = "receipt" | "chat" | "photo" | "warranty";
export type CaseStatus = "draft" | "extracted" | "confirmed" | "claim_ready";
export type EventKind = "purchase" | "defect" | "contact" | "refusal" | "other";

export interface CaseCreated {
  id: number;
  access_token: string;
}

export interface DocumentDto {
  id: number;
  case_id: number;
  kind: DocumentKind;
  sha256: string;
  mime_type: string;
  created_at: string;
}

export interface Fact {
  id: number;
  field: string;
  value: string;
  confidence: number;
  document_id: number | null;
  line_ids: number[];
  grounded: boolean;
  needs_review: boolean;
  confirmed_by_user: boolean;
}

export interface CaseDetail {
  id: number;
  status: CaseStatus;
  claim_type: string;
  created_at: string;
  response_deadline: string | null;
  documents: DocumentDto[];
  facts: Fact[];
  receipt_document_id: number | null;
}

export interface TimelineEvent {
  id: number;
  date: string | null;
  kind: EventKind;
  description: string;
  document_id: number | null;
  needs_review: boolean;
}

export interface MissingItem {
  rule_id: string;
  title: string;
  why: string;
  fix: string;
  resolved: boolean;
}

export interface CheckResult {
  code: string;
  severity: "error" | "warning";
  message: string;
  fact_ids: number[];
  event_ids: number[];
}

export interface Claim {
  id: number;
  version: number;
  text: string;
  fact_ids: number[];
  created_at: string;
}

export interface OcrLine {
  id: number;
  line_no: number;
  text: string;
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  page: number;
}

export interface MarkSent {
  id: number;
  status: CaseStatus;
  response_deadline: string | null;
}

export interface GuardViolation {
  value: string;
  kind: string;
  hint: string;
}
