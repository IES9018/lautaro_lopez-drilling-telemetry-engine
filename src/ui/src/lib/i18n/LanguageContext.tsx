"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getDictionary,
  isLanguage,
  type Dictionary,
  type Language,
} from "./dictionaries";

const STORAGE_KEY = "dte-locale";

export interface LanguageContextValue {
  locale: Language;
  setLocale: (lang: Language) => void;
  dictionary: Dictionary;
}

export const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  // Always start with "en" on first render to avoid SSR/hydration mismatch.
  const [locale, setLocaleState] = useState<Language>("en");

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored && isLanguage(stored)) {
        setLocaleState(stored);
      }
    } catch {
      // localStorage may be unavailable (private mode / SSR edge).
    }
  }, []);

  const setLocale = useCallback((lang: Language) => {
    setLocaleState(lang);
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // Ignore persistence failures.
    }
  }, []);

  const value = useMemo<LanguageContextValue>(
    () => ({
      locale,
      setLocale,
      dictionary: getDictionary(locale),
    }),
    [locale, setLocale],
  );

  return (
    <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
  );
}
