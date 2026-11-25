import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useI18n } from "../i18n";
import { clearToken, getToken } from "../util/session";
import { Button } from "./Button";

// Deletes the case and its files after a confirm dialog, then returns home.
export function DeleteCaseButton({ caseId }: { caseId: number }) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function onDelete() {
    const token = getToken(caseId);
    if (!token || !window.confirm(t("delete.confirm"))) return;
    setBusy(true);
    setFailed(false);
    try {
      await api.deleteCase(caseId, token);
      clearToken(caseId);
      navigate("/");
    } catch {
      setFailed(true);
      setBusy(false);
    }
  }

  return (
    <div>
      <Button variant="secondary" onClick={onDelete} disabled={busy}>
        {t("delete.button")}
      </Button>
      {failed && <p className="mt-1 text-sm text-danger">{t("common.error")}</p>}
    </div>
  );
}
