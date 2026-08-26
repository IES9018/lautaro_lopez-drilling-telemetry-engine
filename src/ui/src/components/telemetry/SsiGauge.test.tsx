import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SsiGauge } from "@/components/telemetry/SsiGauge";

describe("SsiGauge", () => {
  it("shows CRITICAL zone for critical alert_level", () => {
    render(<SsiGauge ssi={1.4} alertLevel="critical" />);
    expect(screen.getByTestId("ssi-zone")).toHaveTextContent("CRITICAL");
    expect(screen.getByText("1.40")).toBeInTheDocument();
  });

  it("shows NORMAL zone for normal alert_level", () => {
    render(<SsiGauge ssi={0.2} alertLevel="normal" />);
    expect(screen.getByTestId("ssi-zone")).toHaveTextContent("NORMAL");
  });
});
