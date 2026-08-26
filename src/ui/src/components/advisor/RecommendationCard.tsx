"use client";

import { cn } from "@/lib/cn";
import type { AdvisorRecommendationRecord } from "@/types/advisor";

export function RecommendationCard({
  record,
}: {
  record: AdvisorRecommendationRecord;
}) {
  const { recommendation: rec } = record;
  return (
    <article
      className="rounded-lg border border-slate-700/70 bg-slate-950/60 p-3"
      data-testid="recommendation-card"
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "rounded px-2 py-0.5 text-[10px] font-bold uppercase",
            rec.severity_level === "critical"
              ? "bg-red-500/20 text-red-300"
              : "bg-amber-500/20 text-amber-300",
          )}
        >
          {rec.severity_level}
        </span>
        <span className="text-xs font-medium text-slate-300">
          {rec.incident_type}
        </span>
      </div>
      <p className="text-sm text-slate-200">{rec.physical_root_cause}</p>
      <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-400">
        {rec.immediate_actions.map((action) => (
          <li key={action}>{action}</li>
        ))}
      </ul>
      <p className="mt-2 font-mono text-[11px] text-slate-500">
        target WOB {rec.target_wob_kn.toFixed(1)} kN · RPM {rec.target_rpm.toFixed(1)}
      </p>
      <p className="mt-1 text-[11px] italic text-slate-500">{rec.rationale}</p>
    </article>
  );
}
