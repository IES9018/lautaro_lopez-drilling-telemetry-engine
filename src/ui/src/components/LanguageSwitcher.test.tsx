import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { cleanup, fireEvent, render, screen } from "@/test/test-utils";
import { useTranslation } from "@/lib/i18n/useTranslation";

function TitleProbe() {
  const { dictionary } = useTranslation();
  return <h1>{dictionary.header.title}</h1>;
}

describe("LanguageSwitcher", () => {
  const store = new Map<string, string>();

  beforeEach(() => {
    store.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
      clear: () => {
        store.clear();
      },
      key: (index: number) => Array.from(store.keys())[index] ?? null,
      get length() {
        return store.size;
      },
    });
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("defaults to English title", () => {
    render(
      <>
        <LanguageSwitcher />
        <TitleProbe />
      </>,
    );
    expect(screen.getByRole("heading")).toHaveTextContent(
      "Drillstring Digital Twin",
    );
  });

  it("switches to Spanish and persists locale", () => {
    render(
      <>
        <LanguageSwitcher />
        <TitleProbe />
      </>,
    );

    fireEvent.click(screen.getByTestId("lang-es"));

    expect(screen.getByRole("heading")).toHaveTextContent(
      "Gemelo Digital de Sarta",
    );
    expect(window.localStorage.getItem("dte-locale")).toBe("es");
  });

  it("switches back to English", () => {
    render(
      <>
        <LanguageSwitcher />
        <TitleProbe />
      </>,
    );

    fireEvent.click(screen.getByTestId("lang-es"));
    fireEvent.click(screen.getByTestId("lang-en"));

    expect(screen.getByRole("heading")).toHaveTextContent(
      "Drillstring Digital Twin",
    );
    expect(window.localStorage.getItem("dte-locale")).toBe("en");
  });
});
