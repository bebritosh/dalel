import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useI18n, type Lang } from "../i18n";

function LangSwitch() {
  const { lang, setLang, t } = useI18n();
  const opt = (l: Lang, label: string) => (
    <button
      type="button"
      onClick={() => setLang(l)}
      aria-pressed={lang === l}
      className={`px-2 py-1 text-sm font-medium rounded-md ${
        lang === l ? "bg-accent text-white" : "text-muted hover:text-text"
      }`}
    >
      {label}
    </button>
  );
  return (
    <div className="flex items-center gap-1" role="group" aria-label="Language">
      {opt("ru", t("langRu"))}
      {opt("en", t("langEn"))}
      {opt("kk", t("langKk"))}
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  return (
    <div className="min-h-full">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-[1120px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
          <Link
            to="/"
            className="order-1 text-lg font-bold tracking-tight text-text"
          >
            {t("appName")}
          </Link>
          <span className="order-3 basis-full rounded-full bg-bg px-3 py-1 text-xs font-medium text-muted sm:order-2 sm:basis-auto">
            {t("disclaimer")}
          </span>
          <div className="order-2 ml-auto sm:order-3">
            <LangSwitch />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[1120px] px-4 py-6">{children}</main>
    </div>
  );
}
