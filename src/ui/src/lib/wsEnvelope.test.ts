import { describe, expect, it } from "vitest";

import { isWsEnvelope, parseWsMessage } from "@/lib/wsEnvelope";

const validFrame = {
  type: "telemetry_frame",
  data: {
    timestamp: "2026-08-25T12:00:00Z",
    frame_id: 1,
    ukf_state: {
      theta_rad: [0, 0.1],
      omega_rad_s: [12, 10],
      rpm_bit_est: 95,
      torque_bit_est_knm: 3.1,
    },
    torsional_deformation_rad: [0, 0.1],
    ssi: 0.4,
    alert_level: "normal",
  },
};

describe("wsEnvelope", () => {
  it("accepts a valid telemetry envelope", () => {
    expect(isWsEnvelope(validFrame)).toBe(true);
  });

  it("rejects invalid payloads", () => {
    expect(isWsEnvelope({ type: "telemetry_frame", data: {} })).toBe(false);
    expect(isWsEnvelope(null)).toBe(false);
    expect(parseWsMessage("{")).toBeNull();
  });

  it("accepts advisor recommendation envelopes", () => {
    const env = {
      type: "advisor_recommendation",
      data: {
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
          physical_root_cause: "friction",
          immediate_actions: ["reduce WOB"],
          target_wob_kn: 60,
          target_rpm: 130,
          rationale: "SOP",
        },
      },
    };
    expect(isWsEnvelope(env)).toBe(true);
  });
});
