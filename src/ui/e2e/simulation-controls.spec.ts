import { expect, test } from "@playwright/test";

import {
  installMocks,
  makeStatus,
} from "./_helpers/mockApi";

test.describe("Simulation controls", () => {
  test("Start sets running=true via mocked REST", async ({ page }) => {
    await installMocks(page, {
      initialStatus: makeStatus({ running: false, sim_time_s: 1.5 }),
    });
    await page.goto("/");

    const controls = page.getByTestId("simulation-controls");
    await controls.getByRole("button", { name: "Start" }).click();

    await expect(controls).toContainText(/running=true/, { timeout: 10_000 });
  });

  test("Stop sets running=false via mocked REST", async ({ page }) => {
    await installMocks(page, {
      initialStatus: makeStatus({ running: true, sim_time_s: 12.0 }),
    });
    await page.goto("/");

    const controls = page.getByTestId("simulation-controls");
    // Refresh status first is not automatic; Start then Stop exercises both.
    await controls.getByRole("button", { name: "Start" }).click();
    await expect(controls).toContainText(/running=true/, { timeout: 10_000 });

    await controls.getByRole("button", { name: "Stop" }).click();
    await expect(controls).toContainText(/running=false/, { timeout: 10_000 });
  });

  test("preset buttons POST correct ScenarioName", async ({ page }) => {
    const mocks = await installMocks(page);
    await page.goto("/");

    const controls = page.getByTestId("simulation-controls");
    await controls.getByRole("button", { name: "severe_stick_slip" }).click();

    await expect
      .poll(() => mocks.getLastPresetBody())
      .toEqual({ preset: "severe_stick_slip" });

    await controls.getByRole("button", { name: "transient_choke" }).click();
    await expect
      .poll(() => mocks.getLastPresetBody())
      .toEqual({ preset: "transient_choke" });

    await controls.getByRole("button", { name: "normal" }).click();
    await expect
      .poll(() => mocks.getLastPresetBody())
      .toEqual({ preset: "normal" });
  });

  test("Start API 500 shows sim-error", async ({ page }) => {
    await installMocks(page, { failStart: true });
    await page.goto("/");

    const controls = page.getByTestId("simulation-controls");
    await controls.getByRole("button", { name: "Start" }).click();

    await expect(page.getByTestId("sim-error")).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByTestId("sim-error")).toContainText(/HTTP 500/);
  });
});
