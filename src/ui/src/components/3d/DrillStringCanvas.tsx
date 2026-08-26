"use client";

import { Canvas } from "@react-three/fiber";
import { OrbitControls, Grid } from "@react-three/drei";
import type { MutableRefObject } from "react";

import { DrillStringMesh } from "@/components/3d/DrillStringMesh";
import { SceneLights } from "@/components/3d/SceneLights";
import type { TelemetryFrame } from "@/types/telemetry";

export interface DrillStringCanvasProps {
  frameRef: MutableRefObject<TelemetryFrame | null>;
}

export function DrillStringCanvas({ frameRef }: DrillStringCanvasProps) {
  return (
    <div className="h-full min-h-[320px] w-full overflow-hidden rounded-xl border border-slate-700/80 bg-slate-950">
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [3.2, 2.4, 4.2], fov: 42, near: 0.1, far: 100 }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={["#0b1220"]} />
        <SceneLights />
        <DrillStringMesh frameRef={frameRef} />
        <Grid
          position={[0, -2.2, 0]}
          args={[12, 12]}
          cellSize={0.5}
          cellThickness={0.6}
          cellColor="#1e293b"
          sectionSize={2}
          sectionThickness={1.1}
          sectionColor="#334155"
          fadeDistance={18}
          infiniteGrid
        />
        <OrbitControls
          makeDefault
          enableDamping
          dampingFactor={0.08}
          minDistance={2}
          maxDistance={14}
          target={[0, -0.4, 0]}
        />
      </Canvas>
    </div>
  );
}
