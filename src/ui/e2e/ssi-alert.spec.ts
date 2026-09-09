import { expect, test } from "@playwright/test";

import {
  installMocks,
  makeCriticalFrame,
  makeTelemetryFrame,
  telemetryEnvelope,
} from "./_helpers/mockApi";

test.describe("SSI alert states", () => {
  test("CRITICAL frame shows textual CRITICAL badge (not color-only)", async ({
    page,
  }) => {
    await installMocks(page, {
      initialFrames: [telemetryEnvelope(makeCriticalFrame())],
    });
    await page.goto("/");

    await expect(page.getByTestId("ssi-zone")).toHaveText("CRITICAL", {
      timeout: 15_000,
    });
    await expect(page.getByTestId("ssi-gauge")).toContainText("1.50");
  });

  test("pushing CRITICAL after NORMAL updates the zone", async ({ page }) => {
    const mocks = await installMocks(page, {
      initialFrames: [telemetryEnvelope(makeTelemetryFrame())],
    });
    await page.goto("/");

    await expect(page.getByTestId("ssi-zone")).toHaveText("NORMAL", {
      timeout: 15_000,
    });

    await mocks.pushTelemetry(
      telemetryEnvelope(makeCriticalFrame({ frame_id: 99 })),
    );

    await expect(page.getByTestId("ssi-zone")).toHaveText("CRITICAL", {
      timeout: 15_000,
    });
  });

  test("WARNING frame shows WARNING badge", async ({ page }) => {
    await installMocks(page, {
      initialFrames: [
        telemetryEnvelope(
          makeTelemetryFrame({ ssi: 0.75, alert_level: "warning" }),
        ),
      ],
    });
    await page.goto("/");

    await expect(page.getByTestId("ssi-zone")).toHaveText("WARNING", {
      timeout: 15_000,
    });
  });
});
