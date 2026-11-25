import type { CaseDetail } from "../api/types";
import { useI18n } from "../i18n";

// Pick provenance from the receipt document first, then any fact/document.
export function provenanceOf(data: CaseDetail) {
  const receipt = data.documents.find((d) => d.id === data.receipt_document_id);
  const sources = [receipt, ...data.documents, ...data.facts];
  const ocr = sources.find((s) => s?.ocr_source)?.ocr_source ?? null;
  const extract = sources.find((s) => s?.extract_source)?.extract_source ?? null;
  return { ocr, extract };
}

const LIVE = "bg-accent/10 text-accent";
const NOT_LIVE = "bg-warning/10 text-warning";

// Shows how OCR and extraction were produced, so nothing is passed off as real.
// Renders nothing when the backend sends no provenance fields.
export function ProvenanceBadge({ data }: { data: CaseDetail }) {
  const { t } = useI18n();
  const { ocr, extract } = provenanceOf(data);
  if (!ocr && !extract) return null;

  const chip = (key: string, label: string, live: boolean) => (
    <span
      key={key}
      className={`rounded-full px-3 py-1 text-xs font-medium ${live ? LIVE : NOT_LIVE}`}
    >
      {label}
    </span>
  );

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="provenance">
      {ocr && chip("ocr", t(`prov.ocr.${ocr}`), ocr !== "fixture")}
      {extract && chip("ext", t(`prov.extract.${extract}`), extract !== "fixture" && extract !== "rules")}
      {extract === "openai" && (
        <span className="text-xs text-muted">{t("prov.openaiNote")}</span>
      )}
    </div>
  );
}
