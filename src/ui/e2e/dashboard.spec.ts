import { expect, test } from "@playwright/test";

import { installMocks } from "./_helpers/mockApi";

test.describe("Dashboard layout", () => {
  test.beforeEach(async ({ page }) => {
    await installMocks(page);
    await page.goto("/");
  });

  test("shows title and all critical panels", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Drillstring Digital Twin" }),
    ).toBeVisible();

    await expect(page.getByTestId("connection-badge")).toBeVisible();
    await expect(page.getByTestId("ssi-gauge")).toBeVisible();
    await expect(page.getByTestId("rpm-dual-gauge")).toBeVisible();
    await expect(page.getByTestId("simulation-controls")).toBeVisible();
    await expect(page.getByTestId("advisor-feed")).toBeVisible();
  });

  test("simulation controls expose Start and Stop buttons", async ({
    page,
  }) => {
    const controls = page.getByTestId("simulation-controls");
    await expect(controls.getByRole("button", { name: "Start" })).toBeVisible();
    await expect(controls.getByRole("button", { name: "Stop" })).toBeVisible();
  });

  test("connection badge becomes Live after WS mock opens", async ({
    page,
  }) => {
    await expect(page.getByTestId("connection-badge")).toContainText(/Live/i, {
      timeout: 15_000,
    });
  });

  test("SSI gauge shows NORMAL zone for default mock frame", async ({
    page,
  }) => {
    await expect(page.getByTestId("ssi-zone")).toHaveText("NORMAL", {
      timeout: 15_000,
    });
  });
});
