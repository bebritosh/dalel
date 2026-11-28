import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";
import type { CaseDetail, CheckResult, MissingItem, TimelineEvent } from "../api/types";
import { useI18n } from "../i18n";
import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { ErrorBox } from "../components/ErrorBox";
import { FieldRow } from "../components/FieldRow";
import { Timeline } from "../components/Timeline";
import { DeleteCaseButton } from "../components/DeleteCaseButton";
import { ProvenanceBadge } from "../components/ProvenanceBadge";
import { MissingList } from "../components/MissingList";
import { getToken, setToken } from "../util/session";

const REQUIRED = ["seller_name", "purchase_date", "total_amount"];

function fieldOrder(field: string): number {
  const map: Record<string, number> = {
    seller_name: 0,
    purchase_date: 1,
    total_amount: 2,
    currency: 3,
  };
  if (field in map) return map[field];
  if (field.startsWith("item_") && field.endsWith("_price")) return 5;
  if (field.startsWith("item_")) return 4;
  return 9;
}

export function ReviewPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { id } = useParams();
  const caseId = Number(id);
  const [params] = useSearchParams();

  const queryToken = params.get("token");
  if (queryToken) setToken(caseId, queryToken);
  const token = getToken(caseId);

  const [data, setData] = useState<CaseDetail | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [missing, setMissing] = useState<MissingItem[]>([]);
  const [checks, setChecks] = useState<CheckResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [c, tl, ms, ch] = await Promise.all([
        api.getCase(caseId, token),
        api.getTimeline(caseId, token),
        api.getMissing(caseId, token),
        api.getChecks(caseId, token),
      ]);
      setData(c);
      setEvents(tl);
      setMissing(ms);
      setChecks(ch);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("common.error"));
    } finally {
      setLoading(false);
    }
  }, [caseId, token, t]);

  useEffect(() => {
    load();
  }, [load]);

  const onPatch = useCallback(
    async (factId: number, body: { value?: string; confirmed_by_user?: boolean }) => {
      if (!token) return;
      const updated = await api.patchFact(factId, token, body);
      setData((prev) =>
        prev
          ? { ...prev, facts: prev.facts.map((f) => (f.id === factId ? updated : f)) }
          : prev,
      );
      // Grounding/confirmation can change checks.
      setChecks(await api.getChecks(caseId, token));
    },
    [token, caseId],
  );

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
        <div className="space-y-3" aria-busy="true">
          <div className="h-6 w-1/3 animate-pulse rounded bg-border" />
          <div className="h-24 animate-pulse rounded-card bg-border" />
          <div className="h-24 animate-pulse rounded-card bg-border" />
        </div>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <ErrorBox message={error ?? t("common.error")} onRetry={load} />
      </AppShell>
    );
  }

  const facts = [...data.facts].sort(
    (a, b) => fieldOrder(a.field) - fieldOrder(b.field) || a.field.localeCompare(b.field),
  );
  const generalChecks = checks.filter((c) => c.fact_ids.length === 0);
  const remaining = REQUIRED.filter(
    (f) => !data.facts.find((x) => x.field === f && x.confirmed_by_user),
  ).length;

  return (
    <AppShell>
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: fields */}
        <section>
          <h2 className="text-xl font-semibold">{t("review.fieldsTitle")}</h2>
          <ProvenanceBadge data={data} />
          {generalChecks.map((c) => (
            <p key={c.code + c.message} className="mt-2 text-sm text-danger">
              {c.message} <span className="text-muted">({c.code})</span>
            </p>
          ))}
          <ul className="mt-3 rounded-card border border-border bg-surface px-4">
            {facts.map((f) => (
              <FieldRow
                key={f.id}
                fact={f}
                checks={checks.filter((c) => c.fact_ids.includes(f.id))}
                onPatch={onPatch}
              />
            ))}
          </ul>

          <div className="mt-6">
            <Button
              disabled={remaining > 0}
              onClick={() => navigate(`/case/${caseId}/claim`)}
            >
              {t("review.toClaim")}
            </Button>
            {remaining > 0 && (
              <p className="mt-2 text-sm text-muted">
                {t("review.remaining", { n: remaining })}
              </p>
            )}
          </div>
          <div className="mt-6">
            <DeleteCaseButton caseId={caseId} />
          </div>
        </section>

        {/* Right: timeline + missing */}
        <section className="space-y-8">
          <div>
            <h2 className="text-xl font-semibold">{t("review.timelineTitle")}</h2>
            <div className="mt-3">
              {events.length ? (
                <Timeline events={events} />
              ) : (
                <EmptyState title={t("review.emptyTimeline")} />
              )}
            </div>
          </div>
          <div>
            <h2 className="text-xl font-semibold">{t("review.missingTitle")}</h2>
            <div className="mt-3">
              <MissingList items={missing} />
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
