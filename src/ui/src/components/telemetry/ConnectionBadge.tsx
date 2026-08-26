"use client";

import { cn } from "@/lib/cn";
import type { ConnectionStatus } from "@/hooks/useTelemetryStream";

const LABELS: Record<ConnectionStatus, string> = {
  connecting: "Connecting",
  open: "Live",
  closed: "Disconnected",
  error: "Error",
};

export function ConnectionBadge({ status }: { status: ConnectionStatus }) {
  return (
    <span
      data-testid="connection-badge"
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide",
        status === "open" && "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
        status === "connecting" && "border-sky-500/40 bg-sky-500/10 text-sky-300",
        status === "closed" && "border-slate-500/40 bg-slate-500/10 text-slate-300",
        status === "error" && "border-red-500/40 bg-red-500/10 text-red-300",
      )}
    >
      <span
        className={cn(
          "h-2 w-2 rounded-full",
          status === "open" && "bg-emerald-400",
          status === "connecting" && "animate-pulse bg-sky-400",
          status === "closed" && "bg-slate-400",
          status === "error" && "bg-red-400",
        )}
      />
      {LABELS[status]}
    </span>
  );
}
