import type { MissingItem } from "../api/types";
import { useI18n } from "../i18n";

// "What to attach" checklist on the claim screen. State (done/missing) comes
// from the /missing endpoint (rules M1-M5); labels are localized here. It is a
// reminder only — it never blocks export, and the app sends nothing itself.
const ORDER = ["M1", "M2", "M3", "M4", "M5"] as const;

export function AttachChecklist({ items }: { items: MissingItem[] }) {
  const { t } = useI18n();
  const byRule = new Map(items.map((m) => [m.rule_id, m]));
  const rows = ORDER.filter((id) => byRule.has(id));
  if (rows.length === 0) return null;

  return (
    <section className="mt-6 rounded-card border border-border bg-surface p-5">
      <h2 className="text-base font-semibold text-text">{t("claim.attachTitle")}</h2>
      <p className="mt-1 text-sm text-muted">{t("claim.attachHint")}</p>
      <ul className="mt-3 space-y-2">
        {rows.map((id) => {
          const done = byRule.get(id)!.resolved;
          return (
            <li key={id} className="flex items-start gap-2.5 text-sm">
              {done ? (
                <svg
                  className="mt-0.5 h-4 w-4 flex-none text-success"
                  viewBox="0 0 16 16" fill="none" aria-hidden="true"
                >
                  <circle cx="8" cy="8" r="8" fill="currentColor" opacity="0.15" />
                  <path d="M4.5 8.3l2 2 4-4.3" stroke="currentColor" strokeWidth="1.6"
                    strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              ) : (
                <span
                  className="mt-0.5 h-4 w-4 flex-none rounded-full border border-muted"
                  aria-hidden="true"
                />
              )}
              <span className={done ? "text-muted" : "text-text"}>
                {t(`attach.${id}`)}
                {!done && <span className="text-muted"> — {t("attach.todo")}</span>}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
