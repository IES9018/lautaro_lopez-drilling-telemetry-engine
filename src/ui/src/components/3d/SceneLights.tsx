"use client";

import { useFrame, useThree } from "@react-three/fiber";
import { useRef } from "react";
import type { PointLight } from "three";

/**
 * Point light that tracks the active camera so the drillstring stays lit
 * from the viewer's perspective regardless of OrbitControls orientation.
 */
function CameraLight() {
  const lightRef = useRef<PointLight>(null);
  const { camera } = useThree();

  useFrame(() => {
    lightRef.current?.position.copy(camera.position);
  });

  return (
    <pointLight
      ref={lightRef}
      intensity={0.65}
      distance={0}
      decay={1.2}
      color="#f8fafc"
    />
  );
}

/**
 * Omnidirectional industrial lighting:
 * Hemisphere (sky/ground) + ambient fill + camera-following key + soft top shadow caster.
 */
export function SceneLights() {
  return (
    <>
      <ambientLight intensity={0.45} />
      <hemisphereLight
        args={["#e2e8f0", "#64748b", 0.9]}
      />
      {/* Soft overhead for Grid shadows only — low intensity so it never darkens sides. */}
      <directionalLight
        position={[0, 12, 2]}
        intensity={0.3}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        color="#f1f5f9"
      />
      <CameraLight />
    </>
  );
}
