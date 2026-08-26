"use client";

import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import type { Group, MeshStandardMaterial } from "three";
import type { MutableRefObject } from "react";

import type { TelemetryFrame } from "@/types/telemetry";

export interface DrillStringMeshProps {
  frameRef: MutableRefObject<TelemetryFrame | null>;
  segmentLength?: number;
  radius?: number;
}

function deformationColor(absTau: number, maxAbs: number): string {
  const t = maxAbs > 1e-9 ? Math.min(1, absTau / maxAbs) : 0;
  if (t < 0.33) {
    const k = t / 0.33;
    return `rgb(${Math.round(40 + 40 * k)}, ${Math.round(90 + 80 * k)}, ${Math.round(200 - 40 * k)})`;
  }
  if (t < 0.66) {
    const k = (t - 0.33) / 0.33;
    return `rgb(${Math.round(80 + 140 * k)}, ${Math.round(170 - 40 * k)}, ${Math.round(160 - 100 * k)})`;
  }
  const k = (t - 0.66) / 0.34;
  return `rgb(${Math.round(220 + 35 * k)}, ${Math.round(130 - 90 * k)}, ${Math.round(60 - 40 * k)})`;
}

/**
 * Malla cilíndrica por nodos: rotación torsional + gradiente de color.
 * Lee `frameRef` en `useFrame` (sin setState) — A-007.
 */
export function DrillStringMesh({
  frameRef,
  segmentLength = 0.55,
  radius = 0.12,
}: DrillStringMeshProps) {
  const groupRef = useRef<Group>(null);
  const materialRefs = useRef<(MeshStandardMaterial | null)[]>([]);

  const placeholderCount = 6;
  const nodes = useMemo(
    () => Array.from({ length: placeholderCount }, (_, i) => i),
    [],
  );

  useFrame(() => {
    const frame = frameRef.current;
    const group = groupRef.current;
    if (!frame || !group) return;

    const deformation = frame.torsional_deformation_rad;
    const n = deformation.length > 0 ? deformation.length : frame.ukf_state.theta_rad.length;
    if (n === 0) return;

    const maxAbs = Math.max(
      1e-3,
      ...deformation.map((v) => Math.abs(v)),
    );

    // Asegura tantos hijos como nodos (recreate via React keys when length changes
    // is handled by parent keying; here we only update existing meshes).
    const children = group.children;
    for (let i = 0; i < children.length; i += 1) {
      const child = children[i];
      if (!child) continue;
      const tau = deformation[i] ?? 0;
      child.rotation.y = tau;
      const mat = materialRefs.current[i];
      if (mat) {
        mat.color.set(deformationColor(Math.abs(tau), maxAbs));
      }
    }
  });

  const count = frameRef.current?.torsional_deformation_rad.length || nodes.length;

  return (
    <group ref={groupRef} position={[0, 1.2, 0]}>
      {Array.from({ length: Math.max(count, placeholderCount) }, (_, i) => (
        <mesh
          key={`seg-${i}`}
          position={[0, -i * segmentLength, 0]}
          castShadow
          receiveShadow
        >
          <cylinderGeometry args={[radius, radius, segmentLength * 0.92, 24]} />
          <meshStandardMaterial
            ref={(m) => {
              materialRefs.current[i] = m;
            }}
            color="#3b82f6"
            metalness={0.55}
            roughness={0.35}
          />
        </mesh>
      ))}
    </group>
  );
}
