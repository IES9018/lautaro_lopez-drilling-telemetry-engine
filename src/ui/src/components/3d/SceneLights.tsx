"use client";

/**
 * Industrial three-point lighting for metallic PBR drillstring surfaces.
 * Key + fill + rim — keeps ambient low so metalness/roughness stay readable.
 */
export function SceneLights() {
  return (
    <>
      <ambientLight intensity={0.22} />
      {/* Key light */}
      <directionalLight
        position={[4.5, 9, 3.5]}
        intensity={1.25}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        color="#f1f5f9"
      />
      {/* Fill light */}
      <directionalLight
        position={[-4, 3, -2]}
        intensity={0.4}
        color="#94a3b8"
      />
      {/* Rim light — accent metallic edges (tool joints / PDC) */}
      <spotLight
        position={[-1.5, 5, -5]}
        intensity={0.7}
        angle={0.55}
        penumbra={0.6}
        color="#cbd5e1"
        castShadow={false}
      />
    </>
  );
}
