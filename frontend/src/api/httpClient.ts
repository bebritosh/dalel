import { ApiClient, ApiError, GuardError } from "./client";
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

const BASE = "/api";

function authHeaders(token: string): Record<string, string> {
  return { "X-Case-Token": token };
}

async function parseError(resp: Response): Promise<never> {
  if (resp.status === 404) {
    throw new ApiError(404, "Дело не найдено");
  }
  let detail: unknown = undefined;
  try {
    const body = await resp.json();
    detail = body?.detail;
    // Guard error shape: detail = { detail, violations }
    if (detail && typeof detail === "object" && "violations" in detail) {
      const d = detail as { violations: GuardError["violations"] };
      throw new GuardError(d.violations ?? []);
    }
  } catch (e) {
    if (e instanceof GuardError) throw e;
  }
  const message =
    typeof detail === "string" ? detail : `Ошибка сервера (${resp.status})`;
  throw new ApiError(resp.status, message);
}

async function json<T>(resp: Response): Promise<T> {
  if (!resp.ok) await parseError(resp);
  return (await resp.json()) as T;
}

export class HttpClient implements ApiClient {
  async createCase(): Promise<CaseCreated> {
    return json(await fetch(`${BASE}/cases`, { method: "POST" }));
  }

  async uploadDocument(
    caseId: number,
    token: string,
    file: File,
    kind: DocumentKind,
  ): Promise<DocumentDto> {
    const form = new FormData();
    form.append("kind", kind);
    form.append("file", file);
    return json(
      await fetch(`${BASE}/cases/${caseId}/documents`, {
        method: "POST",
        headers: authHeaders(token),
        body: form,
      }),
    );
  }

  async getCase(caseId: number, token: string): Promise<CaseDetail> {
    return json(
      await fetch(`${BASE}/cases/${caseId}`, { headers: authHeaders(token) }),
    );
  }

  async deleteCase(caseId: number, token: string): Promise<void> {
    const resp = await fetch(`${BASE}/cases/${caseId}`, {
      method: "DELETE",
      headers: authHeaders(token),
    });
    if (!resp.ok) await parseError(resp);
  }

  async extract(caseId: number, token: string): Promise<Fact[]> {
    return json(
      await fetch(`${BASE}/cases/${caseId}/extract`, {
        method: "POST",
        headers: authHeaders(token),
      }),
    );
  }

  async patchFact(
    factId: number,
    token: string,
    body: { value?: string; confirmed_by_user?: boolean },
  ): Promise<Fact> {
    return json(
      await fetch(`${BASE}/facts/${factId}`, {
        method: "PATCH",
        headers: { ...authHeaders(token), "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    );
  }

  async getTimeline(caseId: number, token: string): Promise<TimelineEvent[]> {
    return json(
      await fetch(`${BASE}/cases/${caseId}/timeline`, {
        headers: authHeaders(token),
      }),
    );
  }

  async getMissing(caseId: number, token: string): Promise<MissingItem[]> {
    return json(
      await fetch(`${BASE}/cases/${caseId}/missing`, {
        headers: authHeaders(token),
      }),
    );
  }

  async getChecks(caseId: number, token: string): Promise<CheckResult[]> {
    return json(
      await fetch(`${BASE}/cases/${caseId}/checks`, {
        headers: authHeaders(token),
      }),
    );
  }

  async createClaim(caseId: number, token: string): Promise<Claim> {
    return json(
      await fetch(`${BASE}/cases/${caseId}/claim`, {
        method: "POST",
        headers: authHeaders(token),
      }),
    );
  }

  async exportClaim(
    caseId: number,
    token: string,
    format: "docx",
  ): Promise<Blob> {
    const resp = await fetch(
      `${BASE}/cases/${caseId}/export?format=${format}`,
      { headers: authHeaders(token) },
    );
    if (!resp.ok) await parseError(resp);
    return await resp.blob();
  }

  async markSent(caseId: number, token: string): Promise<MarkSent> {
    return json(
      await fetch(`${BASE}/cases/${caseId}/mark-sent`, {
        method: "POST",
        headers: authHeaders(token),
      }),
    );
  }

  async getReceiptLines(
    caseId: number,
    token: string,
    docId: number,
  ): Promise<OcrLine[]> {
    return json(
      await fetch(`${BASE}/cases/${caseId}/documents/${docId}/lines`, {
        headers: authHeaders(token),
      }),
    );
  }

  async getReceiptImageUrl(
    caseId: number,
    token: string,
    docId: number,
  ): Promise<string> {
    const resp = await fetch(
      `${BASE}/cases/${caseId}/documents/${docId}/file`,
      { headers: authHeaders(token) },
    );
    if (!resp.ok) await parseError(resp);
    const blob = await resp.blob();
    return URL.createObjectURL(blob);
  }
}
