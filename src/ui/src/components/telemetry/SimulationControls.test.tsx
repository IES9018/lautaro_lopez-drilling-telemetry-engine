import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SimulationControls } from "@/components/telemetry/SimulationControls";
import type { SimulationControlState } from "@/hooks/useSimulationControl";

function mockControl(
  overrides: Partial<SimulationControlState> = {},
): SimulationControlState {
  return {
    status: {
      running: false,
      preset: "normal",
      sim_time_s: 0,
      mwd_drops: 0,
    },
    busy: false,
    error: null,
    start: vi.fn(async () => undefined),
    stop: vi.fn(async () => undefined),
    setPreset: vi.fn(async () => undefined),
    refresh: vi.fn(async () => undefined),
    ...overrides,
  };
}

describe("SimulationControls", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("invokes start and stop handlers", async () => {
    const control = mockControl();
    render(<SimulationControls control={control} />);
    fireEvent.click(screen.getByRole("button", { name: /start/i }));
    fireEvent.click(screen.getByRole("button", { name: /stop/i }));
    await waitFor(() => {
      expect(control.start).toHaveBeenCalled();
      expect(control.stop).toHaveBeenCalled();
    });
  });

  it("invokes setPreset for severe_stick_slip", async () => {
    const control = mockControl();
    render(<SimulationControls control={control} />);
    fireEvent.click(screen.getByRole("button", { name: "severe_stick_slip" }));
    await waitFor(() => {
      expect(control.setPreset).toHaveBeenCalledWith("severe_stick_slip");
    });
  });
});
