import type {
  CaseCreated,
  CaseDetail,
  Claim,
  CheckResult,
  DocumentDto,
  DocumentKind,
  Fact,
  MarkSent,
  MissingItem,
  OcrLine,
  TimelineEvent,
} from "./types";

// A value of 404 we surface to the UI as "Дело не найдено".
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// Thrown when the output guard blocks claim creation/export.
export class GuardError extends Error {
  violations: { value: string; kind: string; hint: string }[];
  constructor(violations: { value: string; kind: string; hint: string }[]) {
    super("Экспорт заблокирован");
    this.violations = violations;
  }
}

export interface ApiClient {
  createCase(): Promise<CaseCreated>;
  uploadDocument(
    caseId: number,
    token: string,
    file: File,
    kind: DocumentKind,
  ): Promise<DocumentDto>;
  getCase(caseId: number, token: string): Promise<CaseDetail>;
  deleteCase(caseId: number, token: string): Promise<void>;
  extract(caseId: number, token: string): Promise<Fact[]>;
  patchFact(
    factId: number,
    token: string,
    body: { value?: string; confirmed_by_user?: boolean },
  ): Promise<Fact>;
  getTimeline(caseId: number, token: string): Promise<TimelineEvent[]>;
  getMissing(caseId: number, token: string): Promise<MissingItem[]>;
  getChecks(caseId: number, token: string): Promise<CheckResult[]>;
  createClaim(caseId: number, token: string): Promise<Claim>;
  exportClaim(caseId: number, token: string, format: "docx"): Promise<Blob>;
  markSent(caseId: number, token: string): Promise<MarkSent>;
  getReceiptLines(
    caseId: number,
    token: string,
    docId: number,
  ): Promise<OcrLine[]>;
  getReceiptImageUrl(
    caseId: number,
    token: string,
    docId: number,
  ): Promise<string>;
}
