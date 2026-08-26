"use client";

import { cn } from "@/lib/cn";
import type { AlertLevel } from "@/types/telemetry";

export interface SsiGaugeProps {
  ssi: number;
  alertLevel: AlertLevel;
}

function needleAngle(ssi: number): number {
  // Map SSI 0..2 → -90°..+90° (semicircle).
  const clamped = Math.max(0, Math.min(2, ssi));
  return -90 + (clamped / 2) * 180;
}

export function SsiGauge({ ssi, alertLevel }: SsiGaugeProps) {
  const angle = needleAngle(ssi);
  const zoneLabel =
    alertLevel === "critical"
      ? "CRITICAL"
      : alertLevel === "warning"
        ? "WARNING"
        : "NORMAL";

  return (
    <div
      className="rounded-xl border border-slate-700/80 bg-slate-900/80 p-4"
      data-testid="ssi-gauge"
    >
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold tracking-wide text-slate-200">
          SSI Gauge
        </h3>
        <span
          className={cn(
            "rounded px-2 py-0.5 text-xs font-bold uppercase",
            alertLevel === "critical" && "bg-red-500/20 text-red-300",
            alertLevel === "warning" && "bg-amber-500/20 text-amber-300",
            alertLevel === "normal" && "bg-emerald-500/20 text-emerald-300",
          )}
          data-testid="ssi-zone"
        >
          {zoneLabel}
        </span>
      </div>
      <svg viewBox="0 0 200 120" className="mx-auto h-28 w-full max-w-[220px]">
        <path
          d="M 20 100 A 80 80 0 0 1 70 28"
          fill="none"
          stroke="#34d399"
          strokeWidth="12"
        />
        <path
          d="M 70 28 A 80 80 0 0 1 130 28"
          fill="none"
          stroke="#fbbf24"
          strokeWidth="12"
        />
        <path
          d="M 130 28 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="#f87171"
          strokeWidth="12"
        />
        <g transform={`rotate(${angle} 100 100)`}>
          <line
            x1="100"
            y1="100"
            x2="100"
            y2="30"
            stroke="#e2e8f0"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </g>
        <circle cx="100" cy="100" r="6" fill="#94a3b8" />
      </svg>
      <p className="mt-1 text-center font-mono text-2xl text-slate-100">
        {ssi.toFixed(2)}
      </p>
    </div>
  );
}
