import type { CaseDetail } from "../api/types";
import { useI18n } from "../i18n";
import { fmtAmount, fmtDate } from "../util/format";
import { StatusBadge } from "./StatusBadge";
import { ProvenanceBadge } from "./ProvenanceBadge";

function value(data: CaseDetail, field: string): string {
  return data.facts.find((f) => f.field === field)?.value ?? "";
}

// A compact header card for the claim screen: the claim amount is highlighted,
// seller and purchase date are shown, the confirmed status is explicit, and the
// backing documents are listed as source chips. All values come from confirmed
// facts — the claim text, numbers, dates and token ids are untouched.
export function ClaimSummary({ data }: { data: CaseDetail }) {
  const { t } = useI18n();
  const total = value(data, "total_amount");
  const currency = value(data, "currency");
  const seller = value(data, "seller_name");
  const purchaseDate = value(data, "purchase_date");

  return (
    <section className="mt-6 rounded-card border border-border bg-surface p-5">
      <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
        <div>
          <div className="text-sm text-muted">{t("claim.amountLabel")}</div>
          <div className="mt-1.5 inline-flex items-baseline gap-2 rounded-lg bg-highlight px-3 py-1.5 ring-1 ring-highlight-border">
            <span className="tabular text-2xl font-bold leading-none text-text">
              {total ? fmtAmount(total) : "—"}
            </span>
            {currency && (
              <span className="text-sm font-medium text-text/70">{currency}</span>
            )}
          </div>
        </div>

        <dl className="grid grid-cols-1 gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted">{t("field.seller_name")}</dt>
            <dd className="mt-0.5 font-medium text-text">{seller || "—"}</dd>
          </div>
          <div>
            <dt className="text-muted">{t("field.purchase_date")}</dt>
            <dd className="tabular mt-0.5 font-medium text-text">
              {purchaseDate ? fmtDate(purchaseDate) : "—"}
            </dd>
          </div>
        </dl>

        <StatusBadge confirmed />
      </div>

      <div className="mt-4 border-t border-border pt-4">
        <div className="text-xs font-medium uppercase tracking-wide text-muted">
          {t("claim.sources")}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {data.documents.map((doc) => (
            <span
              key={doc.id}
              className="rounded-full border border-border bg-bg px-3 py-1 text-xs font-medium text-text"
            >
              {t(`kind.${doc.kind}`)}
            </span>
          ))}
        </div>
        <ProvenanceBadge data={data} />
      </div>
    </section>
  );
}
