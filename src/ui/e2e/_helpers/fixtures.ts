/** Fixtures de telemetría y Advisor para E2E (alineados a broadcast.state.v1). */

import type { AdvisorRecommendationRecord } from "../../src/types/advisor";
import type { OrchestratorStatus, TelemetryFrame } from "../../src/types/telemetry";

export function makeTelemetryFrame(
  overrides: Partial<TelemetryFrame> = {},
): TelemetryFrame {
  return {
    timestamp: "2026-08-31T12:04:01.000Z",
    frame_id: 42,
    ukf_state: {
      theta_rad: [0.0, 0.1, 0.2, 0.3],
      omega_rad_s: [12.56, 10.0, 6.0, 4.7],
      rpm_bit_est: 45.0,
      torque_bit_est_knm: 8.5,
    },
    torsional_deformation_rad: [0.0, 0.1, 0.2, 0.3],
    ssi: 0.3,
    alert_level: "normal",
    ...overrides,
  };
}

export function makeCriticalFrame(
  overrides: Partial<TelemetryFrame> = {},
): TelemetryFrame {
  return makeTelemetryFrame({
    ssi: 1.5,
    alert_level: "critical",
    ukf_state: {
      theta_rad: [0.0, 0.5, 1.2, 2.0],
      omega_rad_s: [12.56, 2.0, 0.5, 0.2],
      rpm_bit_est: 5.0,
      torque_bit_est_knm: 18.0,
    },
    ...overrides,
  });
}

export function makeAdvisorRecord(
  overrides: Partial<AdvisorRecommendationRecord> = {},
): AdvisorRecommendationRecord {
  return {
    triggered_at: "2026-08-31T12:04:02.000Z",
    snapshot: {
      timestamp: "2026-08-31T12:04:02.000Z",
      surface_rpm: 120.0,
      estimated_bit_rpm: 5.0,
      wob_kn: 90.0,
      ssi: 1.5,
      regime: "critical",
      torque_contrast: 4.0,
    },
    recommendation: {
      incident_type: "stick_slip",
      severity_level: "critical",
      physical_root_cause: "Severe stick-slip detected at bit",
      immediate_actions: [
        "Reduce WOB 10–15%",
        "Vary surface RPM ±5–10%",
        "Monitor torque and SSI every 30 s",
      ],
      target_wob_kn: 75.0,
      target_rpm: 110.0,
      rationale: "Mitigate torsional oscillations before BHA damage",
    },
    ...overrides,
  };
}

export function makeStatus(
  overrides: Partial<OrchestratorStatus> = {},
): OrchestratorStatus {
  return {
    running: false,
    preset: "normal",
    sim_time_s: 0,
    mwd_drops: 0,
    ...overrides,
  };
}

export function telemetryEnvelope(frame: TelemetryFrame) {
  return { type: "telemetry_frame" as const, data: frame };
}

export function advisorEnvelope(record: AdvisorRecommendationRecord) {
  return { type: "advisor_recommendation" as const, data: record };
}
