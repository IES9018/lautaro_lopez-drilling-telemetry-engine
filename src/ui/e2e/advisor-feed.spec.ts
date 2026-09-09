import { expect, test } from "@playwright/test";

import {
  advisorEnvelope,
  installMocks,
  makeAdvisorRecord,
} from "./_helpers/mockApi";

test.describe("Advisor feed", () => {
  test("shows empty state when no recommendations", async ({ page }) => {
    await installMocks(page);
    await page.goto("/");

    const feed = page.getByTestId("advisor-feed");
    await expect(feed).toBeVisible();
    await expect(feed).toContainText("No recommendations yet.");
  });

  test("renders SOP card when advisor_recommendation arrives on WS", async ({
    page,
  }) => {
    await installMocks(page, { emitAdvisorOnOpen: true });
    await page.goto("/");

    const card = page.getByTestId("recommendation-card");
    await expect(card).toBeVisible({ timeout: 15_000 });
    await expect(card).toContainText("stick_slip");
    await expect(card).toContainText("Reduce WOB 10–15%");
    await expect(card).toContainText("critical");
  });

  test("pushAdvisor appends a new card", async ({ page }) => {
    const mocks = await installMocks(page);
    await page.goto("/");

    await expect(page.getByTestId("advisor-feed")).toContainText(
      "No recommendations yet.",
    );

    await mocks.pushAdvisor(
      advisorEnvelope(
        makeAdvisorRecord({
          triggered_at: "2026-08-31T12:05:00.000Z",
          recommendation: {
            incident_type: "over_torque",
            severity_level: "warning",
            physical_root_cause: "Torque contrast elevated",
            immediate_actions: ["Reduce WOB gently"],
            target_wob_kn: 70,
            target_rpm: 100,
            rationale: "Prevent over-torque",
          },
        }),
      ),
    );

    await expect(page.getByTestId("recommendation-card")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("recommendation-card")).toContainText(
      "over_torque",
    );
  });
});
