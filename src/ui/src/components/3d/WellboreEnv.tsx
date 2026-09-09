"use client";

import { BackSide } from "three";

export interface WellboreEnvProps {
  /** Number of drillstring nodes (drives wellbore height). */
  nodeCount?: number;
  segmentLength?: number;
  /** Inner radius of the open-hole / casing wall. */
  radius?: number;
}

/**
 * Semi-transparent open-hole / casing cylinder surrounding the drillstring.
 */
export function WellboreEnv({
  nodeCount = 6,
  segmentLength = 0.55,
  radius = 0.55,
}: WellboreEnvProps) {
  const height = (nodeCount + 1.5) * segmentLength;
  // Align with DrillStringMesh group origin at y=1.2, extending downward.
  const centerY = 1.2 - ((nodeCount - 1) * segmentLength) / 2;

  return (
    <mesh position={[0, centerY, 0]}>
      <cylinderGeometry args={[radius, radius, height, 48, 1, true]} />
      <meshStandardMaterial
        color="#1e3a5f"
        transparent
        opacity={0.15}
        side={BackSide}
        metalness={0.1}
        roughness={0.85}
        depthWrite={false}
      />
    </mesh>
  );
}
