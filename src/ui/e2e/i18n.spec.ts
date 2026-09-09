import { expect, test } from "@playwright/test";

import { installMocks } from "./_helpers/mockApi";

test.describe("i18n language switcher", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.removeItem("dte-locale");
    });
    await installMocks(page);
    await page.goto("/");
  });

  test("defaults to English title", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Drillstring Digital Twin" }),
    ).toBeVisible();
    await expect(page.getByTestId("language-switcher")).toBeVisible();
  });

  test("switching to ES updates the header title", async ({ page }) => {
    await page.getByTestId("lang-es").click();
    await expect(
      page.getByRole("heading", { name: "Gemelo Digital de Sarta" }),
    ).toBeVisible();
    await expect(
      page.getByTestId("simulation-controls").getByRole("button", {
        name: "Iniciar",
      }),
    ).toBeVisible();
  });
});
