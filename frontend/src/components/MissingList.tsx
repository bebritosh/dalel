import type { MissingItem } from "../api/types";
import { useI18n } from "../i18n";

export function MissingList({ items }: { items: MissingItem[] }) {
  const { t } = useI18n();
  return (
    <ul className="space-y-3">
      {items.map((m) => (
        <li
          key={m.rule_id}
          className={`rounded-card border border-border p-4 ${
            m.resolved ? "bg-bg" : "bg-surface"
          }`}
        >
          <div className="flex items-center gap-2">
            <h3
              className={`text-sm font-semibold ${
                m.resolved ? "text-muted line-through" : "text-text"
              }`}
            >
              {m.title}
            </h3>
            {m.resolved && (
              <span className="rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success">
                {t("missing.resolved")}
              </span>
            )}
          </div>
          {!m.resolved && (
            <dl className="mt-2 space-y-1 text-sm">
              <div>
                <dt className="inline font-medium text-muted">{t("missing.why")}: </dt>
                <dd className="inline text-text">{m.why}</dd>
              </div>
              <div>
                <dt className="inline font-medium text-muted">{t("missing.fix")}: </dt>
                <dd className="inline text-text">{m.fix}</dd>
              </div>
            </dl>
          )}
        </li>
      ))}
    </ul>
  );
}
