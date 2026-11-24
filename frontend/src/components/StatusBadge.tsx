import { useI18n } from "../i18n";

export function StatusBadge({ confirmed }: { confirmed: boolean }) {
  const { t } = useI18n();
  const cls = confirmed
    ? "bg-success/10 text-success"
    : "bg-warning/10 text-warning";
  const dot = confirmed ? "bg-success" : "bg-warning";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-medium ${cls}`}
    >
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
      {confirmed ? t("status.confirmed") : t("status.review")}
    </span>
  );
}
