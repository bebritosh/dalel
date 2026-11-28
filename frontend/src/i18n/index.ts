import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { ru } from "./ru";
import { en } from "./en";
import { kk } from "./kk";

export type Lang = "ru" | "en" | "kk";
const DICTS: Record<Lang, Record<string, string>> = { ru, en, kk };
const STORAGE_KEY = "dalel:lang";

function readLang(): Lang {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v === "ru" || v === "en" || v === "kk") return v;
  } catch {
    /* ignore */
  }
  return "en"; // EN by default for the pitch; RU/KK are one click away
}

interface I18n {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readLang);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* ignore */
    }
    document.documentElement.lang = l;
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      // Fall back to EN for any key missing in the active language (KK is a
      // draft and may be incomplete), and only then show the key itself.
      let s = DICTS[lang][key] ?? DICTS.en[key] ?? key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          s = s.replace(`{${k}}`, String(v));
        }
      }
      return s;
    },
    [lang],
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return createElement(I18nContext.Provider, { value }, children);
}

export function useI18n(): I18n {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
