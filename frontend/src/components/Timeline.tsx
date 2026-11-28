import type { TimelineEvent } from "../api/types";
import { useI18n } from "../i18n";
import { fmtDate } from "../util/format";

// Source is inferred from the message_id shape: WhatsApp events use "line:N",
// Telegram events use the numeric message id.
function eventSource(messageId?: string | null): "whatsapp" | "telegram" | null {
  if (!messageId) return null;
  if (messageId.startsWith("line:")) return "whatsapp";
  if (/^\d+$/.test(messageId)) return "telegram";
  return null;
}

// Event descriptions are generated in Russian by the backend
// (app/services/timeline.py, app/services/chat.py): either a fixed label or
// "<label>: «<chat quote>»". Swap the known label for the localized one and
// keep the quote verbatim; anything else is shown as is.
const RU_LABELS: Record<string, string> = {
  "Покупка товара по чеку": "purchase",
  "Первое обращение к продавцу": "contact",
  "Ответ продавца": "reply",
  "Отказ продавца": "refusal",
};

function localizeDescription(text: string, t: (key: string) => string): string {
  const m = /^([^:«]+?)(: («[\s\S]*»))?$/.exec(text);
  const kind = m ? RU_LABELS[m[1]] : undefined;
  if (!m || !kind) return text;
  const label = t(`eventDesc.${kind}`);
  return m[3] ? `${label}: ${m[3]}` : label;
}

export function Timeline({ events }: { events: TimelineEvent[] }) {
  const { t } = useI18n();
  return (
    <ol className="relative ml-3 border-l border-border">
      {events.map((e) => {
        const source = eventSource(e.message_id);
        return (
          <li key={e.id} className="relative mb-6 pl-6 last:mb-0">
            <span
              className="absolute -left-[7px] top-1.5 h-3 w-3 rounded-full bg-accent"
              aria-hidden="true"
            />
            <div className="flex flex-wrap items-baseline gap-2">
              <span className="tabular text-sm font-medium text-muted">
                {fmtDate(e.date)}
              </span>
              <span className="rounded-full bg-bg px-2 py-0.5 text-xs font-medium text-text">
                {t(`event.${e.kind}`)}
              </span>
              {source && (
                <span className="rounded-full border border-border px-2 py-0.5 text-xs font-medium text-muted">
                  {t(`source.${source}`)}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-text">{localizeDescription(e.description, t)}</p>
          </li>
        );
      })}
    </ol>
  );
}
