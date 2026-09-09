"use client";

import { Play, Square } from "lucide-react";

import { cn } from "@/lib/cn";
import { useTranslation } from "@/lib/i18n/useTranslation";
import type { SimulationControlState } from "@/hooks/useSimulationControl";
import type { ScenarioName } from "@/types/telemetry";

const PRESETS: ScenarioName[] = [
  "normal",
  "severe_stick_slip",
  "transient_choke",
];

export interface SimulationControlsProps {
  control: SimulationControlState;
}

export function SimulationControls({ control }: SimulationControlsProps) {
  const { dictionary } = useTranslation();
  const { status, busy, error, start, stop, setPreset } = control;
  const sc = dictionary.simulationControls;

  return (
    <div
      className="rounded-xl border border-slate-700/80 bg-slate-900/80 p-4"
      data-testid="simulation-controls"
    >
      <h3 className="mb-3 text-sm font-semibold tracking-wide text-slate-200">
        {sc.title}
      </h3>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => void start()}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white",
            "hover:bg-emerald-500 disabled:opacity-50",
          )}
        >
          <Play className="h-4 w-4" />
          {sc.start}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => void stop()}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-lg bg-slate-700 px-3 py-2 text-sm font-medium text-white",
            "hover:bg-slate-600 disabled:opacity-50",
          )}
        >
          <Square className="h-4 w-4" />
          {sc.stop}
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset}
            type="button"
            disabled={busy}
            onClick={() => void setPreset(preset)}
            className={cn(
              "rounded-lg border px-2.5 py-1.5 text-xs font-medium",
              status?.preset === preset
                ? "border-sky-400 bg-sky-500/20 text-sky-200"
                : "border-slate-600 text-slate-300 hover:border-slate-400",
              "disabled:opacity-50",
            )}
          >
            {preset}
          </button>
        ))}
      </div>
      {status ? (
        <p className="mt-3 font-mono text-xs text-slate-400">
          {sc.running}={String(status.running)} · {sc.simTime}=
          {status.sim_time_s.toFixed(2)}s · {sc.mwdDrops}={status.mwd_drops}
        </p>
      ) : null}
      {error ? (
        <p className="mt-2 text-xs text-red-400" data-testid="sim-error">
          {error}
        </p>
      ) : null}
    </div>
  );
}
