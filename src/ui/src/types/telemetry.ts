/** Tipos alineados a broadcast.state.v1 / envelopes del pipeline. */

export type AlertLevel = "normal" | "warning" | "critical";

export interface UkfState {
  theta_rad: number[];
  omega_rad_s: number[];
  rpm_bit_est: number;
  torque_bit_est_knm: number;
}

export interface TelemetryFrame {
  timestamp: string;
  frame_id: number;
  ukf_state: UkfState;
  torsional_deformation_rad: number[];
  ssi: number;
  alert_level: AlertLevel;
}

export type ScenarioName = "normal" | "severe_stick_slip" | "transient_choke";

export interface OrchestratorStatus {
  running: boolean;
  preset: ScenarioName;
  sim_time_s: number;
  mwd_drops: number;
}
