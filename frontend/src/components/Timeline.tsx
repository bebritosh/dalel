import type { TimelineEvent } from "../api/types";
import { useI18n } from "../i18n";
import { fmtDate } from "../util/format";

export function Timeline({ events }: { events: TimelineEvent[] }) {
  const { t } = useI18n();
  return (
    <ol className="relative ml-3 border-l border-border">
      {events.map((e) => (
        <li key={e.id} className="relative mb-6 pl-6 last:mb-0">
          <span
            className="absolute -left-[7px] top-1.5 h-3 w-3 rounded-full bg-accent"
            aria-hidden="true"
          />
          <div className="flex items-baseline gap-2">
            <span className="tabular text-sm font-medium text-muted">
              {fmtDate(e.date)}
            </span>
            <span className="rounded-full bg-bg px-2 py-0.5 text-xs font-medium text-text">
              {t(`event.${e.kind}`)}
            </span>
          </div>
          <p className="mt-1 text-sm text-text">{e.description}</p>
        </li>
      ))}
    </ol>
  );
}
