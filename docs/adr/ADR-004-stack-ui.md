# ADR-004 — Stack de interfaz (gemelo digital)

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-08-31 |
| **Sprint / TP** | ADI TP3 · PP3 Sprint 1 |
| **Proyecto** | `lautaro_lopez-drilling-telemetry-engine` |
| **Decisores** | lautaro_lopez (alumno) · contraste contra [`SPEC.md`](../../SPEC.md) |
| **Dominios impactados** | `src/ui/` |
| **Relacionado** | [ADR-001](ADR-001-stack-tecnologico.md) · [`docs/diseno/`](../diseno/) |

---

## Contexto del problema técnico

El gemelo digital debe:

1. Consumir **WebSocket** ~60 FPS con frames `broadcast.state.v1` (SSI, UKF, deformación nodal).
2. Renderizar **deformación torsional 3D** de la sarta (RF-09) sin bloquear el hilo principal.
3. Mostrar gauges SSI/RPM y feed del **LLM Advisor** (RF-07) en layout responsive para sala de control.
4. Cumplir **TypeScript strict**, tests de componentes y criterios de accesibilidad del SPEC v3 (teclado + contraste AA en pantallas críticas).
5. Mantener separación de dominio: UI no recalcula SSI ni `alert_level` (regla de contrato).

ADR-001 fijó “Next.js + Three.js” a nivel macro; este ADR detalla la **pila UI concreta** y alternativas descartadas para TP3.

---

## Decisión tomada

Adoptar el stack en `src/ui/`:

| Capa | Tecnología | Rol |
|------|------------|-----|
| Framework | **Next.js 15** (App Router) | Routing, SSR shell, `dynamic()` para WebGL |
| UI library | **React 19** | Componentes gauges, Advisor, layout |
| 3D | **Three.js** + **@react-three/fiber (R3F)** + **@react-three/drei** | Canvas drillstring, helpers 3D |
| Estilos | **Tailwind CSS 4** + `clsx` / `tailwind-merge` | Layout grid, tokens slate/emerald/amber/red |
| Iconos | **lucide-react** | Start/Stop, estados |
| Tipado | **TypeScript 5.8 strict** | Tipos `AlertLevel`, DTOs WS |
| Tests UI | **Vitest** + **Testing Library** | Componentes críticos (`SsiGauge`, etc.) |
| Transporte | Cliente WS nativo (`useTelemetryStream`) | Envelope `telemetry_frame` + `advisor_recommendation` |

**Principios no negociables**

- `alert_level` y `ssi` se **muestran** del broadcast; no se derivan en cliente.
- WebGL solo en cliente (`ssr: false` en `DrillStringCanvas`).
- Controles de simulación vía REST (`useSimulationControl`) — no mezclar con paso RK4.

---

## Alternativas descartadas

### Alternativa A — Vue 3 + Nuxt + TresJS

| Criterio | Evaluación |
|----------|------------|
| Ecosistema 3D | TresJS maduro pero menor adopción en equipo académico |
| Alineación ADR-001 | ADR-001 ya citó Next/React |
| Tipado | TS strict viable; cambio de stack sin beneficio físico |
| **Veredicto** | **Descartada** — costo de migración sin ganancia RF |

### Alternativa B — SvelteKit + Threlte

| Criterio | Evaluación |
|----------|------------|
| Performance | Excelente; bundle pequeño |
| Contratos / tests | Menos ejemplos institucionales; curva para PP3 |
| R3F / drei | Ecosistema React más amplio para drillstring procedural |
| **Veredicto** | **Descartada** — riesgo tiempo Sprint 1 |

### Alternativa C — React + Vite (SPA) sin Next.js

| Criterio | Evaluación |
|----------|------------|
| Simplicidad | Menos capas para SPA única |
| SSR / routing | No necesario para MVP; pero Next ya integrado en repo |
| Despliegue | Similar con `output: standalone` en Next |
| **Veredicto** | **Descartada** — código existente en Next; reescritura innecesaria |

### Alternativa D — Unity WebGL / Babylon.js standalone

| Criterio | Evaluación |
|----------|------------|
| Fidelidad 3D | Alta para juegos |
| Integración React | Peor que R3F; build pesado |
| Mantenimiento | Segundo runtime (C# / WASM) fuera de monolito TS |
| **Veredicto** | **Descartada** — NG-03 scaffolding, no motor 3D AAA |

### Alternativa E — Dashboard 2D solo (sin Three.js)

| Criterio | Evaluación |
|----------|------------|
| Alcance | Incumple RF-09 y propuesta PP3 gemelo digital |
| Stick-slip | Deformación torsional nodal no comunicada |
| **Veredicto** | **Descartada** — viola RF-09 |

---

## Consecuencias

### Positivas

- Un solo idioma en frontend (TS) coherente con contratos JSON.
- R3F permite animar `torsional_deformation_rad[]` por nodo con reconciliación React.
- Next `dynamic` evita fallos SSR WebGL.
- Vitest + RTL alineados a RF-11 en dominio UI.

### Negativas / deuda

- Bundle Three.js grande; mitigado con lazy load del canvas.
- Accesibilidad 3D limitada — métricas 2D y Advisor deben ser navegables por teclado (SPEC RF-UI-ACC).
- Pulido visual producción (NG-03) diferido; wireframes TP3 son baja fidelidad.

---

## Trazabilidad HCI

| Artefacto | Ubicación |
|-----------|-----------|
| Personas + journeys | [`docs/diseno/usuarios.md`](../diseno/usuarios.md) |
| Wireframes | [`docs/diseno/wireframes/`](../diseno/wireframes/) |
| Auditoría Nielsen | [`docs/diseno/auditoria-heuristica.md`](../diseno/auditoria-heuristica.md) |
| Criterios Gherkin UI | [`SPEC.md`](../../SPEC.md) §1.2.1 |

---

*ADR-004 — Aceptado · ADI TP3*
