"use client";

export function SceneLights() {
  return (
    <>
      <ambientLight intensity={0.35} />
      <directionalLight
        position={[4, 8, 3]}
        intensity={1.15}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <directionalLight position={[-3, 2, -4]} intensity={0.35} color="#94a3b8" />
    </>
  );
}
