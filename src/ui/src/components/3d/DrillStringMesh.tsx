"use client";

import { Instance, Instances } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef, useState } from "react";
import type { Group, MeshStandardMaterial } from "three";
import type { MutableRefObject } from "react";

import type { TelemetryFrame } from "@/types/telemetry";

export interface DrillStringMeshProps {
  frameRef: MutableRefObject<TelemetryFrame | null>;
  segmentLength?: number;
  radius?: number;
}

/**
 * Ganancia puramente visual — NO es física, solo hace perceptible la
 * microdeformación torsional real (orden de mrad) al renderizar.
 */
export const VISUAL_TORSION_GAIN = 18;

const PLACEHOLDER_COUNT = 6;
const METALNESS = 0.75;
const GROOVE_COUNT = 6;
const STABILIZER_FINS = 3;
const PDC_CUTTERS = 8;

/** Idle spin (rad/s) when no telemetry frame is available. */
const IDLE_OMEGA_TOP = 0.6;
/** Each deeper node spins slower than the one above (visual torsion lag). */
const IDLE_DECAY = 0.75;
/** Soft sync of integrated angle toward UKF theta every ~2 s of wall time. */
const THETA_SYNC_INTERVAL_S = 2;
const THETA_SYNC_BLEND = 0.15;

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

function TopDriveSection({
  materialRef,
}: {
  materialRef: (m: MeshStandardMaterial | null) => void;
}) {
  return (
    <group>
      <mesh castShadow receiveShadow position={[0, 0.12, 0]}>
        <cylinderGeometry args={[0.22, 0.2, 0.28, 28]} />
        <meshStandardMaterial
          ref={materialRef}
          color="#2b2f36"
          metalness={METALNESS}
          roughness={0.3}
        />
      </mesh>
      <mesh castShadow position={[0, 0.32, 0]}>
        <boxGeometry args={[0.28, 0.1, 0.18]} />
        <meshStandardMaterial
          color="#1f2329"
          metalness={METALNESS}
          roughness={0.35}
        />
      </mesh>
      <mesh castShadow position={[0, -0.08, 0]}>
        <cylinderGeometry args={[0.08, 0.08, 0.16, 16]} />
        <meshStandardMaterial
          color="#3a3f48"
          metalness={METALNESS}
          roughness={0.28}
        />
      </mesh>
    </group>
  );
}

function DrillpipeSection({
  segmentLength,
  radius,
  materialRef,
  grooveMaterialRef,
}: {
  segmentLength: number;
  radius: number;
  materialRef: (m: MeshStandardMaterial | null) => void;
  grooveMaterialRef: (m: MeshStandardMaterial | null) => void;
}) {
  const jointR = radius * 1.35;
  const jointH = segmentLength * 0.12;
  const pipeH = segmentLength * 0.72;
  const groovePositions = useMemo(() => {
    const items: {
      position: [number, number, number];
      rotation: [number, number, number];
    }[] = [];
    for (let g = 0; g < GROOVE_COUNT; g += 1) {
      const angle = (g / GROOVE_COUNT) * Math.PI * 2;
      items.push({
        position: [
          Math.cos(angle) * (radius + 0.008),
          0,
          Math.sin(angle) * (radius + 0.008),
        ],
        rotation: [0, -angle, 0],
      });
    }
    return items;
  }, [radius]);

  return (
    <group>
      <mesh castShadow receiveShadow position={[0, pipeH * 0.5 + jointH * 0.4, 0]}>
        <cylinderGeometry args={[jointR, jointR, jointH, 20]} />
        <meshStandardMaterial
          color="#4a5568"
          metalness={METALNESS}
          roughness={0.32}
        />
      </mesh>
      <mesh castShadow receiveShadow>
        <cylinderGeometry args={[radius, radius, pipeH, 24]} />
        <meshStandardMaterial
          ref={materialRef}
          color="#3b82f6"
          metalness={METALNESS}
          roughness={0.3}
        />
      </mesh>
      <mesh
        castShadow
        receiveShadow
        position={[0, -pipeH * 0.5 - jointH * 0.4, 0]}
      >
        <cylinderGeometry args={[jointR, jointR, jointH, 20]} />
        <meshStandardMaterial
          color="#4a5568"
          metalness={METALNESS}
          roughness={0.32}
        />
      </mesh>
      <Instances limit={GROOVE_COUNT}>
        <boxGeometry args={[0.012, pipeH * 0.9, 0.006]} />
        <meshStandardMaterial
          ref={grooveMaterialRef}
          color="#1e3a5f"
          metalness={0.6}
          roughness={0.4}
        />
        {groovePositions.map((g, i) => (
          <Instance
            key={`groove-${i}`}
            position={g.position}
            rotation={g.rotation}
          />
        ))}
      </Instances>
    </group>
  );
}

function BhaBitSection({
  segmentLength,
  materialRef,
}: {
  segmentLength: number;
  materialRef: (m: MeshStandardMaterial | null) => void;
}) {
  const collarR = 0.18;
  const collarH = segmentLength * 0.55;
  const finPositions = useMemo(() => {
    const items: {
      position: [number, number, number];
      rotation: [number, number, number];
    }[] = [];
    for (let f = 0; f < STABILIZER_FINS; f += 1) {
      const baseAngle = (f / STABILIZER_FINS) * Math.PI * 2;
      for (let step = 0; step < 3; step += 1) {
        const y = -step * 0.08;
        const angle = baseAngle + step * 0.35;
        items.push({
          position: [
            Math.cos(angle) * (collarR + 0.04),
            y + 0.05,
            Math.sin(angle) * (collarR + 0.04),
          ],
          rotation: [0, -angle, 0.15],
        });
      }
    }
    return items;
  }, [collarR]);

  const cutterPositions = useMemo(() => {
    const items: {
      position: [number, number, number];
      rotation: [number, number, number];
    }[] = [];
    for (let c = 0; c < PDC_CUTTERS; c += 1) {
      const angle = (c / PDC_CUTTERS) * Math.PI * 2;
      const r = 0.09;
      items.push({
        position: [
          Math.cos(angle) * r,
          -collarH * 0.55 - 0.12,
          Math.sin(angle) * r,
        ],
        rotation: [0.6, -angle, 0],
      });
    }
    return items;
  }, [collarH]);

  return (
    <group>
      <mesh castShadow receiveShadow position={[0, 0.05, 0]}>
        <cylinderGeometry args={[collarR, collarR * 0.95, collarH, 28]} />
        <meshStandardMaterial
          ref={materialRef}
          color="#3d4450"
          metalness={METALNESS}
          roughness={0.28}
        />
      </mesh>
      <Instances limit={STABILIZER_FINS * 3}>
        <boxGeometry args={[0.05, 0.1, 0.02]} />
        <meshStandardMaterial
          color="#5a6270"
          metalness={METALNESS}
          roughness={0.25}
        />
        {finPositions.map((fin, i) => (
          <Instance
            key={`fin-${i}`}
            position={fin.position}
            rotation={fin.rotation}
          />
        ))}
      </Instances>
      <mesh
        castShadow
        position={[0, -collarH * 0.55 - 0.05, 0]}
        rotation={[Math.PI, 0, 0]}
      >
        <coneGeometry args={[0.14, 0.18, 20]} />
        <meshStandardMaterial
          color="#4b4f57"
          metalness={METALNESS}
          roughness={0.2}
        />
      </mesh>
      <Instances limit={PDC_CUTTERS}>
        <cylinderGeometry args={[0.025, 0.025, 0.02, 10]} />
        <meshStandardMaterial
          color="#6b7280"
          metalness={0.85}
          roughness={0.18}
        />
        {cutterPositions.map((c, i) => (
          <Instance
            key={`cutter-${i}`}
            position={c.position}
            rotation={c.rotation}
          />
        ))}
      </Instances>
    </group>
  );
}

/**
 * Ensamblaje industrial: Top Drive → Drillpipe/Tool Joints → BHA/PDC.
 * Integra ω·Δt para rotación continua; lee `frameRef` en `useFrame` (A-007).
 */
export function DrillStringMesh({
  frameRef,
  segmentLength = 0.55,
  radius = 0.12,
}: DrillStringMeshProps) {
  const groupRef = useRef<Group>(null);
  const materialRefs = useRef<(MeshStandardMaterial | null)[]>([]);
  const grooveMaterialRefs = useRef<(MeshStandardMaterial | null)[]>([]);
  const lastCountRef = useRef(PLACEHOLDER_COUNT);
  const angleAccum = useRef<number[]>([]);
  const syncElapsed = useRef(0);
  const [nodeCount, setNodeCount] = useState(PLACEHOLDER_COUNT);

  useFrame((state, delta) => {
    const frame = frameRef.current;
    const group = groupRef.current;
    if (!group) return;

    const children = group.children;
    const childCount = children.length;
    if (childCount === 0) return;

    // Ensure accumulators match current child count.
    while (angleAccum.current.length < childCount) {
      angleAccum.current.push(0);
    }
    if (angleAccum.current.length > childCount) {
      angleAccum.current.length = childCount;
    }

    const dt = Math.min(delta, 0.05); // clamp to avoid jumps after tab focus
    const t = state.clock.elapsedTime;

    if (frame) {
      const deformation = frame.torsional_deformation_rad;
      const theta = frame.ukf_state.theta_rad;
      const omega = frame.ukf_state.omega_rad_s;
      const n =
        deformation.length > 0
          ? deformation.length
          : theta.length > 0
            ? theta.length
            : 0;
      if (n === 0) return;

      // Remount geometry only when node count changes (rare).
      if (n !== lastCountRef.current) {
        lastCountRef.current = n;
        setNodeCount(n);
        return;
      }

      syncElapsed.current += dt;
      const doSync = syncElapsed.current >= THETA_SYNC_INTERVAL_S;
      if (doSync) syncElapsed.current = 0;

      const maxAbs = Math.max(1e-3, ...deformation.map((v) => Math.abs(v)));
      const alert = frame.alert_level;
      const lastIdx = childCount - 1;

      for (let i = 0; i < childCount; i += 1) {
        const child = children[i];
        if (!child) continue;

        const tau = deformation[i] ?? 0;
        const w = omega[i] ?? 0;
        angleAccum.current[i] =
          (angleAccum.current[i] ?? 0) + w * dt;

        if (doSync && theta.length > i) {
          const target = theta[i] ?? 0;
          // Soft-align integrated angle toward UKF theta (shortest angular path).
          const current = angleAccum.current[i] ?? 0;
          const err = Math.atan2(
            Math.sin(target - current),
            Math.cos(target - current),
          );
          angleAccum.current[i] = current + err * THETA_SYNC_BLEND;
        }

        let stickOsc = 0;
        if (alert === "critical" && i === lastIdx) {
          // Stick-slip: bit lags then releases relative to string.
          stickOsc =
            Math.sin(t * 6) *
            VISUAL_TORSION_GAIN *
            Math.abs(tau) *
            0.4;
        }

        child.rotation.y =
          (angleAccum.current[i] ?? 0) + tau * VISUAL_TORSION_GAIN + stickOsc;

        // Base X position is 0; apply lateral vibration for warning/critical on BHA.
        if (i === lastIdx) {
          if (alert === "warning") {
            child.position.x = Math.sin(t * 4) * 0.015;
            child.scale.y = 1;
          } else if (alert === "critical") {
            child.position.x = Math.sin(t * 8) * 0.025;
            child.scale.y = 1 + Math.sin(t * 10) * 0.02;
          } else {
            child.position.x = 0;
            child.scale.y = 1;
          }
        }

        const mat = materialRefs.current[i];
        if (mat) {
          mat.color.set(deformationColor(Math.abs(tau), maxAbs));
        }
        const grooveMat = grooveMaterialRefs.current[i];
        if (grooveMat) {
          grooveMat.color.set(deformationColor(Math.abs(tau), maxAbs));
        }
      }
      return;
    }

    // No telemetry: idle spin with depth decay (visual demo without backend).
    for (let i = 0; i < childCount; i += 1) {
      const child = children[i];
      if (!child) continue;
      const idleOmega = IDLE_OMEGA_TOP * Math.pow(IDLE_DECAY, i);
      angleAccum.current[i] = (angleAccum.current[i] ?? 0) + idleOmega * dt;
      child.rotation.y = angleAccum.current[i] ?? 0;
      child.position.x = 0;
      child.scale.y = 1;
    }
  });

  const count = Math.max(nodeCount, PLACEHOLDER_COUNT);

  return (
    <group ref={groupRef} position={[0, 1.2, 0]}>
      {Array.from({ length: count }, (_, i) => {
        const y = -i * segmentLength;
        const isTop = i === 0;
        const isBit = i === count - 1;

        return (
          <group key={`node-${count}-${i}`} position={[0, y, 0]}>
            {isTop ? (
              <TopDriveSection
                materialRef={(m) => {
                  materialRefs.current[i] = m;
                }}
              />
            ) : isBit ? (
              <BhaBitSection
                segmentLength={segmentLength}
                materialRef={(m) => {
                  materialRefs.current[i] = m;
                }}
              />
            ) : (
              <DrillpipeSection
                segmentLength={segmentLength}
                radius={radius}
                materialRef={(m) => {
                  materialRefs.current[i] = m;
                }}
                grooveMaterialRef={(m) => {
                  grooveMaterialRefs.current[i] = m;
                }}
              />
            )}
          </group>
        );
      })}
    </group>
  );
}
