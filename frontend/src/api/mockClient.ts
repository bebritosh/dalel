import { ApiClient, ApiError } from "./client";
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
import {
  mockCase,
  mockChecks,
  mockClaimText,
  mockEvents,
  mockFacts,
  mockLines,
  mockMissing,
} from "../mock/data";

// In-memory mock backend. State lives for the session (reset on reload).
export class MockClient implements ApiClient {
  private facts: Fact[] = mockFacts.map((f) => ({ ...f }));
  private deadline: string | null = null;
  private hasPhoto = false;

  private delay<T>(value: T): Promise<T> {
    return new Promise((resolve) => setTimeout(() => resolve(value), 180));
  }

  async createCase(): Promise<CaseCreated> {
    return this.delay({ id: 1, access_token: "mock" });
  }

  async uploadDocument(
    _caseId: number,
    _token: string,
    file: File,
    kind: DocumentKind,
  ): Promise<DocumentDto> {
    if (kind === "photo") this.hasPhoto = true;
    return this.delay({
      id: kind === "receipt" ? 1 : 2,
      case_id: 1,
      kind,
      sha256: file.name,
      mime_type: file.type || "application/octet-stream",
      created_at: new Date().toISOString(),
    });
  }

  async getCase(): Promise<CaseDetail> {
    return this.delay({ ...mockCase, facts: this.facts, response_deadline: this.deadline });
  }

  async deleteCase(): Promise<void> {
    return this.delay(undefined);
  }

  async extract(): Promise<Fact[]> {
    return this.delay(this.facts);
  }

  async patchFact(
    factId: number,
    _token: string,
    body: { value?: string; confirmed_by_user?: boolean },
  ): Promise<Fact> {
    const f = this.facts.find((x) => x.id === factId);
    if (!f) throw new Error("not found");
    if (body.value !== undefined) f.value = body.value;
    if (body.confirmed_by_user !== undefined) {
      f.confirmed_by_user = body.confirmed_by_user;
      if (body.confirmed_by_user) f.needs_review = false;
    }
    return this.delay({ ...f });
  }

  async getTimeline(): Promise<TimelineEvent[]> {
    return this.delay(mockEvents);
  }

  async getMissing(): Promise<MissingItem[]> {
    // M3 closes once a defect photo has been uploaded (mirrors the backend rule).
    return this.delay(
      mockMissing.map((m) =>
        m.rule_id === "M3" && this.hasPhoto ? { ...m, resolved: true } : m,
      ),
    );
  }

  async getChecks(): Promise<CheckResult[]> {
    return this.delay(mockChecks);
  }

  async createClaim(): Promise<Claim> {
    return this.delay({
      id: 1,
      version: 1,
      text: mockClaimText,
      fact_ids: this.facts.filter((f) => f.confirmed_by_user).map((f) => f.id),
      created_at: new Date().toISOString(),
    });
  }

  async exportClaim(
    _caseId: number,
    _token: string,
    format: "docx" | "pdf" = "docx",
  ): Promise<Blob> {
    // Real files exported by the backend for the synthetic demo case
    // (scripts/make_mock_exports.py), so Word/PDF viewers open them as-is.
    const resp = await fetch(
      `${import.meta.env.BASE_URL}mock/pretenziya_demo.${format}`,
    ).catch(() => null);
    if (!resp || !resp.ok) {
      throw new ApiError(
        503,
        format === "pdf"
          ? "PDF недоступен в демо без бэкенда. Скачайте DOCX."
          : "Файл демо-претензии не найден в сборке.",
      );
    }
    return this.delay(await resp.blob());
  }

  async markSent(): Promise<MarkSent> {
    const d = new Date();
    d.setDate(d.getDate() + 10);
    this.deadline = d.toISOString().slice(0, 10);
    return this.delay({ id: 1, status: "claim_ready", response_deadline: this.deadline });
  }

  async getReceiptLines(): Promise<OcrLine[]> {
    return this.delay(mockLines);
  }

  async getReceiptImageUrl(): Promise<string> {
    return this.delay(`${import.meta.env.BASE_URL}mock/receipt-001.svg`);
  }
}
