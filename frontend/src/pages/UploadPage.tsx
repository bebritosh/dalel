import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";
import type { DocumentKind } from "../api/types";
import { useI18n } from "../i18n";
import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { ErrorBox } from "../components/ErrorBox";
import { setToken } from "../util/session";

const MAX_BYTES = 15 * 1024 * 1024;
const KINDS: DocumentKind[] = ["receipt", "chat", "photo", "warranty"];

interface Picked {
  file: File;
  kind: DocumentKind;
  error?: string;
}

const CONSENT_KEY = "dalel:consent";

function readConsent(): boolean {
  try {
    return localStorage.getItem(CONSENT_KEY) === "1";
  } catch {
    return false;
  }
}

// The first image is assumed to be the receipt; further images are defect photos.
function guessKind(file: File, haveReceipt: boolean): DocumentKind {
  if (file.type.startsWith("image/")) return haveReceipt ? "photo" : "receipt";
  if (file.name.endsWith(".txt") || file.name.endsWith(".json")) return "chat";
  return "receipt";
}

export function UploadPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<Picked[]>([]);
  const [dragging, setDragging] = useState(false);
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [consent, setConsent] = useState(readConsent);

  function toggleConsent(v: boolean) {
    setConsent(v);
    try {
      localStorage.setItem(CONSENT_KEY, v ? "1" : "0");
    } catch {
      /* ignore */
    }
  }

  function addFiles(list: FileList | null) {
    if (!list) return;
    setFiles((prev) => {
      let haveReceipt = prev.some((p) => p.kind === "receipt");
      const picked: Picked[] = Array.from(list).map((file) => {
        const kind = guessKind(file, haveReceipt);
        if (kind === "receipt") haveReceipt = true;
        return {
          file,
          kind,
          error: file.size > MAX_BYTES ? t("err.tooLarge") : undefined,
        };
      });
      return [...prev, ...picked];
    });
  }

  function setKind(i: number, kind: DocumentKind) {
    setFiles((prev) => prev.map((p, j) => (j === i ? { ...p, kind } : p)));
  }

  function remove(i: number) {
    setFiles((prev) => prev.filter((_, j) => j !== i));
  }

  const hasReceipt = files.some((f) => f.kind === "receipt" && !f.error);
  const anyError = files.some((f) => f.error);

  function mapError(e: unknown): string {
    if (e instanceof ApiError) {
      if (e.status === 413) return t("err.tooLarge");
      if (e.status === 415) return t("err.wrongType");
      if (e.status === 409) return t("err.duplicate");
      return e.message;
    }
    return t("common.error");
  }

  async function analyze() {
    setError(null);
    try {
      setStep(t("upload.step.create"));
      const created = await api.createCase();
      setToken(created.id, created.access_token);

      setStep(t("upload.step.upload"));
      for (const p of files) {
        if (p.error) continue;
        await api.uploadDocument(created.id, created.access_token, p.file, p.kind);
      }

      setStep(t("upload.step.extract"));
      await api.extract(created.id, created.access_token);

      navigate(`/case/${created.id}/review`);
    } catch (e) {
      setError(mapError(e));
      setStep(null);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl">
        <h1 className="text-[28px] font-bold leading-9">{t("upload.title")}</h1>
        <p className="mt-2 text-muted">{t("upload.subtitle")}</p>

        <div
          className="mt-4 rounded-card border border-border bg-surface p-4 text-sm"
          data-testid="consent"
        >
          <p className="text-muted">{t("consent.text")}</p>
          <label className="mt-3 flex items-start gap-2 font-medium">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => toggleConsent(e.target.checked)}
              className="mt-1"
            />
            <span>{t("consent.check")}</span>
          </label>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            addFiles(e.dataTransfer.files);
          }}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
          }}
          className={`mt-6 cursor-pointer rounded-card border-2 border-dashed p-8 text-center transition-colors ${
            dragging ? "border-accent bg-accent/5" : "border-border bg-surface"
          }`}
        >
          <p className="font-medium">{t("upload.drop")}</p>
          <p className="mt-1 text-sm text-muted">{t("upload.accepted")}</p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.pdf,.txt,.json"
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
        </div>

        <div className="mt-6">
          {files.length === 0 ? (
            <p className="text-sm text-muted">{t("upload.empty")}</p>
          ) : (
            <ul className="space-y-2">
              {files.map((p, i) => (
                <li
                  key={i}
                  className="flex flex-wrap items-center gap-3 rounded-card border border-border bg-surface p-3"
                >
                  <span className="flex-1 truncate text-sm">{p.file.name}</span>
                  <select
                    value={p.kind}
                    onChange={(e) => setKind(i, e.target.value as DocumentKind)}
                    aria-label={`${t("upload.kindLabel")} ${p.file.name}`}
                    className="rounded-md border border-border px-2 py-1 text-sm"
                  >
                    {KINDS.map((k) => (
                      <option key={k} value={k}>
                        {t(`kind.${k}`)}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => remove(i)}
                    className="text-sm text-danger hover:underline"
                  >
                    {t("upload.remove")}
                  </button>
                  {p.error && (
                    <p className="w-full text-sm text-danger">{p.error}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        {error && (
          <div className="mt-4">
            <ErrorBox message={error} onRetry={analyze} />
          </div>
        )}

        <div className="mt-6">
          <Button
            onClick={analyze}
            disabled={!hasReceipt || anyError || !!step || !consent}
          >
            {step ?? t("upload.analyze")}
          </Button>
          {!hasReceipt && (
            <p className="mt-2 text-sm text-muted">{t("upload.needReceipt")}</p>
          )}
          {!files.some((f) => f.kind === "photo") && (
            <p className="mt-2 text-sm text-muted">{t("upload.photoHint")}</p>
          )}
        </div>
      </div>
    </AppShell>
  );
}
