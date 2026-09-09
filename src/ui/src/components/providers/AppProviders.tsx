"use client";

import type { ReactNode } from "react";

import { LanguageProvider } from "@/lib/i18n/LanguageContext";

/** Client boundary so RootLayout can stay a Server Component. */
export function AppProviders({ children }: { children: ReactNode }) {
  return <LanguageProvider>{children}</LanguageProvider>;
}
