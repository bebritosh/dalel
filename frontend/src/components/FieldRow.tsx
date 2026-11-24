import { useState } from "react";
import type { CheckResult, Fact } from "../api/types";
import { useI18n } from "../i18n";
import { fieldLabel } from "../util/format";
import { Button } from "./Button";
import { StatusBadge } from "./StatusBadge";

interface Props {
  fact: Fact;
  checks: CheckResult[];
  onPatch: (
    factId: number,
    body: { value?: string; confirmed_by_user?: boolean },
  ) => Promise<void>;
}

export function FieldRow({ fact, checks, onPatch }: Props) {
  const { t } = useI18n();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(fact.value);
  const [busy, setBusy] = useState(false);

  const isUnreadable = fact.value === "";
  const label = fieldLabel(fact.field, t);

  async function save() {
    setBusy(true);
    try {
      await onPatch(fact.id, { value: draft });
      setEditing(false);
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    setBusy(true);
    try {
      await onPatch(fact.id, { confirmed_by_user: true });
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className="border-b border-border py-3 last:border-0">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span className="min-w-[130px] text-sm text-muted">{label}</span>

        {editing ? (
          <input
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") save();
              if (e.key === "Escape") {
                setDraft(fact.value);
                setEditing(false);
              }
            }}
            className="tabular flex-1 rounded-md border border-border px-2 py-1 text-base"
            aria-label={label}
          />
        ) : (
          <span className="tabular flex-1 text-base font-medium">
            {isUnreadable ? (
              <em className="text-warning">{t("review.unreadable")}</em>
            ) : (
              fact.value
            )}
          </span>
        )}

        <StatusBadge confirmed={fact.confirmed_by_user} />

        {editing ? (
          <div className="flex gap-2">
            <Button variant="primary" onClick={save} disabled={busy} className="px-3 py-1.5 text-sm">
              {t("review.save")}
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setDraft(fact.value);
                setEditing(false);
              }}
              className="px-3 py-1.5 text-sm"
            >
              {t("review.cancel")}
            </Button>
          </div>
        ) : (
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => setEditing(true)}
              className="px-3 py-1.5 text-sm"
            >
              {t("review.edit")}
            </Button>
            {!fact.confirmed_by_user && !isUnreadable && (
              <Button
                variant="primary"
                onClick={confirm}
                disabled={busy}
                className="px-3 py-1.5 text-sm"
              >
                {t("review.confirm")}
              </Button>
            )}
          </div>
        )}
      </div>

      {checks.map((c) => (
        <p key={c.code + c.message} className="mt-1.5 text-sm text-warning">
          {c.message} <span className="text-muted">({c.code})</span>
        </p>
      ))}
    </li>
  );
}
