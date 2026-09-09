"use client";

import { cn } from "@/lib/cn";
import { useTranslation } from "@/lib/i18n/useTranslation";
import type { Language } from "@/lib/i18n/dictionaries";

const OPTIONS: Language[] = ["en", "es"];

export function LanguageSwitcher() {
  const { locale, setLocale } = useTranslation();

  return (
    <div
      className="inline-flex items-center gap-1 rounded-lg border border-slate-700/80 bg-slate-900/80 p-0.5"
      data-testid="language-switcher"
      role="group"
      aria-label="Language"
    >
      {OPTIONS.map((lang) => (
        <button
          key={lang}
          type="button"
          data-testid={`lang-${lang}`}
          onClick={() => setLocale(lang)}
          aria-pressed={locale === lang}
          className={cn(
            "rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wide transition-colors",
            locale === lang
              ? "bg-slate-700 text-slate-100"
              : "text-slate-400 hover:bg-slate-800 hover:text-slate-200",
          )}
        >
          {lang}
        </button>
      ))}
    </div>
  );
}
