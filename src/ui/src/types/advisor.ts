import type { AlertLevel } from "@/types/telemetry";

export type IncidentType =
  | "stick_slip"
  | "over_torque"
  | "transient_choke"
  | "unknown";

export type SeverityLevel = "warning" | "critical";

export interface AdvisorRecommendation {
  incident_type: IncidentType;
  severity_level: SeverityLevel;
  physical_root_cause: string;
  immediate_actions: string[];
  target_wob_kn: number;
  target_rpm: number;
  rationale: string;
}

export interface AdvisorIncidentSnapshot {
  timestamp: string;
  surface_rpm: number;
  estimated_bit_rpm: number;
  wob_kn: number;
  ssi: number;
  regime: AlertLevel;
  torque_contrast: number;
}

export interface AdvisorRecommendationRecord {
  recommendation: AdvisorRecommendation;
  triggered_at: string;
  snapshot: AdvisorIncidentSnapshot;
}
