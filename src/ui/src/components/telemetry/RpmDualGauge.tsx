"use client";

import { cn } from "@/lib/cn";

export interface RpmDualGaugeProps {
  surfaceRpm: number;
  bitRpm: number;
  maxRpm?: number;
}

function Bar({
  label,
  value,
  maxRpm,
  accent,
}: {
  label: string;
  value: number;
  maxRpm: number;
  accent: string;
}) {
  const pct = Math.max(0, Math.min(100, (value / maxRpm) * 100));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-400">
        <span>{label}</span>
        <span className="font-mono text-slate-200">{value.toFixed(1)} rpm</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-800">
        <div
          className={cn("h-full rounded-full transition-[width] duration-150", accent)}
          style={{ width: `${pct}%` }}
          data-testid={`rpm-bar-${label}`}
        />
      </div>
    </div>
  );
}

export function RpmDualGauge({
  surfaceRpm,
  bitRpm,
  maxRpm = 220,
}: RpmDualGaugeProps) {
  return (
    <div
      className="rounded-xl border border-slate-700/80 bg-slate-900/80 p-4"
      data-testid="rpm-dual-gauge"
    >
      <h3 className="mb-3 text-sm font-semibold tracking-wide text-slate-200">
        RPM Surface vs Bit
      </h3>
      <div className="space-y-3">
        <Bar
          label="Surface (est.)"
          value={surfaceRpm}
          maxRpm={maxRpm}
          accent="bg-sky-500"
        />
        <Bar
          label="Bit (est.)"
          value={bitRpm}
          maxRpm={maxRpm}
          accent="bg-violet-500"
        />
      </div>
    </div>
  );
}
