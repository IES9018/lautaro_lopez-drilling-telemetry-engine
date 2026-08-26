import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AdvisorFeed } from "@/components/advisor/AdvisorFeed";
import type { AdvisorRecommendationRecord } from "@/types/advisor";

const sample: AdvisorRecommendationRecord = {
  triggered_at: "2026-08-25T12:00:01Z",
  snapshot: {
    timestamp: "2026-08-25T12:00:01Z",
    surface_rpm: 120,
    estimated_bit_rpm: 10,
    wob_kn: 80,
    ssi: 1.5,
    regime: "critical",
    torque_contrast: 2,
  },
  recommendation: {
    incident_type: "stick_slip",
    severity_level: "critical",
    physical_root_cause: "Static friction at bit",
    immediate_actions: ["Reduce WOB gradually", "Adjust surface RPM"],
    target_wob_kn: 68,
    target_rpm: 132,
    rationale: "Mock SOP stick_slip",
  },
};

describe("AdvisorFeed", () => {
  it("renders empty state", () => {
    render(<AdvisorFeed recommendations={[]} />);
    expect(screen.getByText(/No recommendations yet/i)).toBeInTheDocument();
  });

  it("renders SOP actions from recommendation", () => {
    render(<AdvisorFeed recommendations={[sample]} />);
    expect(screen.getByText("Static friction at bit")).toBeInTheDocument();
    expect(screen.getByText("Reduce WOB gradually")).toBeInTheDocument();
    expect(screen.getByText("Adjust surface RPM")).toBeInTheDocument();
  });
});
