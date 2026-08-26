import type { AdvisorRecommendationRecord } from "@/types/advisor";
import type { AlertLevel, TelemetryFrame, UkfState } from "@/types/telemetry";

export type WsEnvelope =
  | { type: "telemetry_frame"; data: TelemetryFrame }
  | { type: "advisor_recommendation"; data: AdvisorRecommendationRecord };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNumberArray(value: unknown): value is number[] {
  return Array.isArray(value) && value.every((v) => typeof v === "number");
}

function isAlertLevel(value: unknown): value is AlertLevel {
  return value === "normal" || value === "warning" || value === "critical";
}

function isUkfState(value: unknown): value is UkfState {
  if (!isRecord(value)) return false;
  return (
    isNumberArray(value.theta_rad) &&
    isNumberArray(value.omega_rad_s) &&
    typeof value.rpm_bit_est === "number" &&
    typeof value.torque_bit_est_knm === "number"
  );
}

function isTelemetryFrame(value: unknown): value is TelemetryFrame {
  if (!isRecord(value)) return false;
  return (
    typeof value.timestamp === "string" &&
    typeof value.frame_id === "number" &&
    isUkfState(value.ukf_state) &&
    isNumberArray(value.torsional_deformation_rad) &&
    typeof value.ssi === "number" &&
    isAlertLevel(value.alert_level)
  );
}

function isAdvisorRecord(value: unknown): value is AdvisorRecommendationRecord {
  if (!isRecord(value)) return false;
  if (typeof value.triggered_at !== "string") return false;
  if (!isRecord(value.recommendation)) return false;
  const rec = value.recommendation;
  return (
    typeof rec.incident_type === "string" &&
    typeof rec.severity_level === "string" &&
    typeof rec.physical_root_cause === "string" &&
    Array.isArray(rec.immediate_actions) &&
    typeof rec.target_wob_kn === "number" &&
    typeof rec.target_rpm === "number" &&
    typeof rec.rationale === "string"
  );
}

export function isWsEnvelope(value: unknown): value is WsEnvelope {
  if (!isRecord(value)) return false;
  if (value.type === "telemetry_frame") {
    return isTelemetryFrame(value.data);
  }
  if (value.type === "advisor_recommendation") {
    return isAdvisorRecord(value.data);
  }
  return false;
}

export function parseWsMessage(raw: string): WsEnvelope | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    return isWsEnvelope(parsed) ? parsed : null;
  } catch {
    return null;
  }
}
