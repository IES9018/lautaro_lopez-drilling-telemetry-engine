import { describe, expect, it } from "vitest";

import { en, es, type Dictionary } from "@/lib/i18n/dictionaries";

function collectKeys(obj: unknown, prefix = ""): string[] {
  if (obj === null || typeof obj !== "object") {
    return [prefix];
  }
  return Object.entries(obj as Record<string, unknown>).flatMap(([key, value]) =>
    collectKeys(value, prefix ? `${prefix}.${key}` : key),
  );
}

describe("dictionaries", () => {
  it("en and es expose identical key trees", () => {
    const enKeys = collectKeys(en).sort();
    const esKeys = collectKeys(es).sort();
    expect(esKeys).toEqual(enKeys);
  });

  it("en SSI regimes match legacy uppercase labels", () => {
    expect(en.ssiRegimes).toEqual({
      normal: "NORMAL",
      warning: "WARNING",
      critical: "CRITICAL",
    });
  });

  it("typed Dictionary values are non-empty strings", () => {
    const assertLeaves = (node: Dictionary | Dictionary[keyof Dictionary]) => {
      if (typeof node === "string") {
        expect(node.length).toBeGreaterThan(0);
        return;
      }
      for (const value of Object.values(node)) {
        assertLeaves(value as Dictionary[keyof Dictionary]);
      }
    };
    assertLeaves(en);
    assertLeaves(es);
  });
});
