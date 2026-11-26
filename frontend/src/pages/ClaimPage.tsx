import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError, GuardError } from "../api";
import type { CaseDetail, Claim, Fact, OcrLine } from "../api/types";
import { useI18n } from "../i18n";
import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { ErrorBox } from "../components/ErrorBox";
import { ClaimText, type ClaimToken } from "../components/ClaimText";
import { ClaimSummary } from "../components/ClaimSummary";
import { ReceiptViewer } from "../components/ReceiptViewer";
import { DeleteCaseButton } from "../components/DeleteCaseButton";
import { getToken } from "../util/session";
import { fmtAmount, fmtDate } from "../util/format";
import { saveBlob } from "../util/download";

function buildTokens(data: CaseDetail): ClaimToken[] {
  const tokens: ClaimToken[] = [];
  const grounded = (f: Fact) =>
    f.confirmed_by_user &&
    f.line_ids.length > 0 &&
    f.document_id === data.receipt_document_id;

  for (const f of data.facts) {
    if (!grounded(f)) continue;
    if (f.field === "total_amount") {
      tokens.push({ match: fmtAmount(f.value), lineIds: f.line_ids });
    } else if (f.field === "purchase_date") {
      tokens.push({ match: fmtDate(f.value), lineIds: f.line_ids });
    } else if (f.field.startsWith("item_") && !f.field.endsWith("_price")) {
      tokens.push({ match: f.value, lineIds: f.line_ids });
    }
  }
  return tokens;
}

function Timer({ deadline }: { deadline: string | null }) {
  const { t } = useI18n();
  // 10 calendar days: para. 2 of art. 42-4 of the consumer protection law
  // (rules/legal_refs.json, seller_response_term).
  const note = (
    <span className="font-medium">{t("claim.timerBefore")}</span>
  );
  if (!deadline) {
    return (
      <div className="rounded-card border border-border bg-surface px-4 py-3 text-sm">
        <span className="font-medium text-muted">{t("claim.notSent")}.</span>{" "}
        {note}
        <span className="ml-2 text-muted">{t("claim.timerIdle")}</span>
      </div>
    );
  }
  // Whole calendar days from today to the deadline date, so the count matches
  // the stated 10-day period (date-only diff, no partial-day rounding up).
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const end = new Date(`${deadline}T00:00:00`).getTime();
  const days = Math.max(0, Math.round((end - today.getTime()) / 86400000));
  return (
    <div className="rounded-card border border-accent/30 bg-accent/5 px-4 py-3 text-sm">
      <span className="font-medium text-accent">{t("claim.sent")}.</span> {note}
      <div className="tabular mt-1">
        {t("claim.deadlineDate", { date: fmtDate(deadline), n: days })}
      </div>
    </div>
  );
}

export function ClaimPage() {
  const { t } = useI18n();
  const { id } = useParams();
  const caseId = Number(id);
  const token = getToken(caseId);

  const [data, setData] = useState<CaseDetail | null>(null);
  const [claim, setClaim] = useState<Claim | null>(null);
  const [lines, setLines] = useState<OcrLine[]>([]);
  const [imageUrl, setImageUrl] = useState<string>("");
  const [selected, setSelected] = useState<number[]>([]);
  const [activeMatch, setActiveMatch] = useState<string | null>(null);
  const [deadline, setDeadline] = useState<string | null>(null);
  const [violations, setViolations] = useState<GuardError["violations"] | null>(null);
  const [needConfirm, setNeedConfirm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportNote, setExportNote] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    setViolations(null);
    setNeedConfirm(false);
    try {
      const c = await api.getCase(caseId, token);
      setData(c);
      setDeadline(c.response_deadline);
      if (c.receipt_document_id) {
        const [ls, url] = await Promise.all([
          api.getReceiptLines(caseId, token, c.receipt_document_id),
          api.getReceiptImageUrl(caseId, token, c.receipt_document_id),
        ]);
        setLines(ls);
        setImageUrl(url);
      }
      try {
        setClaim(await api.createClaim(caseId, token));
      } catch (e) {
        if (e instanceof GuardError) setViolations(e.violations);
        else if (e instanceof ApiError && e.status === 409) setNeedConfirm(true);
        else throw e;
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("common.error"));
    } finally {
      setLoading(false);
    }
  }, [caseId, token, t]);

  useEffect(() => {
    load();
  }, [load]);

  async function download(format: "docx" | "pdf") {
    if (!token) return;
    setExportNote(null);
    try {
      const blob = await api.exportClaim(caseId, token, format);
      saveBlob(blob, `pretenziya_case_${caseId}.${format}`);
    } catch (e) {
      // 422 (guard), 503 (no LibreOffice) etc.: show the server's message.
      setExportNote(e instanceof ApiError ? e.message : t("common.error"));
    }
  }

  async function markSent() {
    if (!token) return;
    const res = await api.markSent(caseId, token);
    setDeadline(res.response_deadline);
  }

  function onSelect(tk: ClaimToken) {
    setSelected(tk.lineIds);
    setActiveMatch(tk.match);
  }

  if (!token) {
    return (
      <AppShell>
        <EmptyState
          title={t("common.noToken")}
          action={<Link to="/"><Button>{t("common.createNew")}</Button></Link>}
        />
      </AppShell>
    );
  }

  if (loading) {
    return (
      <AppShell>
        <div className="h-64 animate-pulse rounded-card bg-border" aria-busy="true" />
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <ErrorBox message={error} onRetry={load} />
      </AppShell>
    );
  }

  if (needConfirm) {
    return (
      <AppShell>
        <EmptyState
          title={t("claim.emptyNeedConfirm")}
          action={
            <Link to={`/case/${caseId}/review`}>
              <Button>{t("claim.backToFields")}</Button>
            </Link>
          }
        />
      </AppShell>
    );
  }

  const tokens = data ? buildTokens(data) : [];

  return (
    <AppShell>
      <h1 className="text-[28px] font-bold leading-9">{t("claim.title")}</h1>
      <div className="mt-4"><Timer deadline={deadline} /></div>

      {!violations && claim && data && <ClaimSummary data={data} />}

      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[3fr_2fr]">
        {/* Left: claim text — bounded with its own scroll on desktop so the
            long legal section doesn't stretch the whole page. */}
        <section className="rounded-card border border-border bg-surface p-5 lg:max-h-[75vh] lg:overflow-y-auto">
          {violations ? (
            <div>
              <h2 className="text-lg font-semibold text-danger">{t("claim.blocked")}</h2>
              <p className="mt-2 text-sm text-text">{t("claim.blockedHint")}</p>
              <ul className="mt-2 space-y-1">
                {violations.map((v, i) => (
                  <li key={i} className="text-sm">
                    <span className="tabular font-medium text-danger">{v.value}</span>
                    <span className="text-muted"> — {v.hint}</span>
                  </li>
                ))}
              </ul>
              <Link to={`/case/${caseId}/review`} className="mt-4 inline-block">
                <Button variant="secondary">{t("claim.backToFields")}</Button>
              </Link>
            </div>
          ) : claim ? (
            <ClaimText
              text={claim.text}
              tokens={tokens}
              activeMatch={activeMatch}
              onSelect={onSelect}
            />
          ) : null}
        </section>

        {/* Right: receipt */}
        <section>
          {imageUrl ? (
            <ReceiptViewer
              imageUrl={imageUrl}
              lines={lines}
              selectedLineIds={selected}
            />
          ) : (
            <EmptyState title={t("receipt.hint")} />
          )}
        </section>
      </div>

      {!violations && claim && (
        <div className="mt-6">
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => download("docx")}>{t("claim.download")}</Button>
            <Button variant="secondary" onClick={() => download("pdf")}>
              {t("claim.downloadPdf")}
            </Button>
            <Button variant="secondary" onClick={markSent}>
              {t("claim.markSent")}
            </Button>
          </div>
          {exportNote && (
            <p className="mt-3 text-sm text-muted" role="status">
              {exportNote}
            </p>
          )}
          <p className="mt-4 text-sm text-muted">{t("claim.deliveryHint")}</p>
          <p className="mt-1 text-xs text-muted">{t("claim.legalNote")}</p>
        </div>
      )}
      <div className="mt-6">
        <DeleteCaseButton caseId={caseId} />
      </div>
    </AppShell>
  );
}
