"use client";

import { RecommendationCard } from "@/components/advisor/RecommendationCard";
import type { AdvisorRecommendationRecord } from "@/types/advisor";

export interface AdvisorFeedProps {
  recommendations: AdvisorRecommendationRecord[];
}

export function AdvisorFeed({ recommendations }: AdvisorFeedProps) {
  return (
    <aside
      className="flex h-full min-h-[240px] flex-col rounded-xl border border-slate-700/80 bg-slate-900/80"
      data-testid="advisor-feed"
    >
      <header className="border-b border-slate-700/80 px-4 py-3">
        <h2 className="text-sm font-semibold tracking-wide text-slate-200">
          LLM Advisor Feed
        </h2>
        <p className="text-xs text-slate-500">
          SOP mitigations on SSI &gt; 1.0 events
        </p>
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        {recommendations.length === 0 ? (
          <p className="text-sm text-slate-500">No recommendations yet.</p>
        ) : (
          recommendations.map((record, index) => (
            <RecommendationCard
              key={`${record.triggered_at}-${index}`}
              record={record}
            />
          ))
        )}
      </div>
    </aside>
  );
}
