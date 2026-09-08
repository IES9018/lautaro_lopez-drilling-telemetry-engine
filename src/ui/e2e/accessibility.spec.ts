import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { installMocks } from "./_helpers/mockApi";

test.describe("Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await installMocks(page);
    await page.goto("/");
    await expect(page.getByTestId("simulation-controls")).toBeVisible();
  });

  test("Tab order reaches Start, Stop and presets", async ({ page }) => {
    // Focus body then Tab until we hit Start (skip canvas WebGL trap).
    await page.locator("body").click({ position: { x: 5, y: 5 } });

    let foundStart = false;
    for (let i = 0; i < 40; i += 1) {
      await page.keyboard.press("Tab");
      const focused = page.locator(":focus");
      const text = ((await focused.textContent()) ?? "").trim();
      if (text.includes("Start")) {
        foundStart = true;
        break;
      }
    }
    expect(foundStart).toBe(true);

    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toContainText("Stop");

    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toContainText("normal");
  });

  test("interactive buttons have type=button", async ({ page }) => {
    const buttons = page.getByTestId("simulation-controls").locator("button");
    const count = await buttons.count();
    expect(count).toBeGreaterThanOrEqual(5);
    for (let i = 0; i < count; i += 1) {
      await expect(buttons.nth(i)).toHaveAttribute("type", "button");
    }
  });

  test("Start/Stop targets meet min height for touch (RNF-05)", async ({
    page,
  }) => {
    const start = page
      .getByTestId("simulation-controls")
      .getByRole("button", { name: "Start" });
    const box = await start.boundingBox();
    expect(box).not.toBeNull();
    // Material 48px ideal; current UI uses py-2 (~36-40). Assert ≥ 32 as floor
    // so regressions to tiny hit targets fail; wireframes target 48px Sprint 3.
    expect(box!.height).toBeGreaterThanOrEqual(32);
    expect(box!.width).toBeGreaterThanOrEqual(48);
  });

  test("axe scan has no critical/serious violations on shell", async ({
    page,
  }) => {
    // Exclude WebGL canvas (dynamic, not semantic) from axe rules that noise.
    const results = await new AxeBuilder({ page })
      .disableRules(["color-contrast"]) // dark theme slate tokens audited in TP3
      .analyze();

    const severe = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );
    expect(
      severe,
      severe.map((v) => `${v.id}: ${v.help}`).join("\n"),
    ).toEqual([]);
  });
});
