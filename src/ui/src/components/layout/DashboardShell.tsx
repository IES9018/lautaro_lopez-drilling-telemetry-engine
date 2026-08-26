"use client";

import dynamic from "next/dynamic";

import { AdvisorFeed } from "@/components/advisor/AdvisorFeed";
import { ConnectionBadge } from "@/components/telemetry/ConnectionBadge";
import { RpmDualGauge } from "@/components/telemetry/RpmDualGauge";
import { SimulationControls } from "@/components/telemetry/SimulationControls";
import { SsiGauge } from "@/components/telemetry/SsiGauge";
import { useSimulationControl } from "@/hooks/useSimulationControl";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { radSToRpm } from "@/lib/cn";

const DrillStringCanvas = dynamic(
  () =>
    import("@/components/3d/DrillStringCanvas").then((m) => m.DrillStringCanvas),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full min-h-[320px] items-center justify-center rounded-xl border border-slate-700/80 bg-slate-950 text-sm text-slate-500">
        Loading 3D twin…
      </div>
    ),
  },
);

export function DashboardShell() {
  const stream = useTelemetryStream();
  const control = useSimulationControl();
  const frame = stream.latestFrame;

  const omega0 = frame?.ukf_state.omega_rad_s[0] ?? 0;
  const surfaceRpm = radSToRpm(omega0);
  const bitRpm = frame?.ukf_state.rpm_bit_est ?? 0;

  return (
    <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col gap-4 p-4 md:p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-100 md:text-2xl">
            Drillstring Digital Twin
          </h1>
          <p className="text-sm text-slate-400">
            Torsional deformation · SSI · LLM Advisor (soft real-time)
          </p>
        </div>
        <ConnectionBadge status={stream.connectionStatus} />
      </header>

      <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-12">
        <section className="lg:col-span-7 xl:col-span-8">
          <DrillStringCanvas frameRef={stream.frameRef} />
        </section>

        <section className="flex flex-col gap-4 lg:col-span-5 xl:col-span-4">
          <SsiGauge
            ssi={frame?.ssi ?? 0}
            alertLevel={frame?.alert_level ?? "normal"}
          />
          <RpmDualGauge surfaceRpm={surfaceRpm} bitRpm={bitRpm} />
          <SimulationControls control={control} />
        </section>

        <section className="lg:col-span-12">
          <AdvisorFeed recommendations={stream.recommendations} />
        </section>
      </div>
    </div>
  );
}
