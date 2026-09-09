"use client";

import { cn } from "@/lib/cn";
import { useTranslation } from "@/lib/i18n/useTranslation";
import type { ConnectionStatus } from "@/hooks/useTelemetryStream";

export function ConnectionBadge({ status }: { status: ConnectionStatus }) {
  const { dictionary } = useTranslation();
  const labels: Record<ConnectionStatus, string> = {
    connecting: dictionary.metrics.status.connecting,
    open: dictionary.metrics.status.live,
    closed: dictionary.metrics.status.disconnected,
    error: dictionary.metrics.status.error,
  };

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
      {labels[status]}
    </span>
  );
}
