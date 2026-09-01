# Auditoría heurística — Nielsen (10 principios)

**Proyecto:** Drilling Telemetry Engine · ADI TP3  
**Objeto:** wireframes v1 evaluados → **correcciones aplicadas en v2**  
**Pantallas:** [Dashboard gemelo digital](wireframes/dashboard-gemelo-digital.md), [Alerta + Advisor](wireframes/alerta-stick-slip-advisor.md)

Metodología: recorrido cognitivo con Personas A (Martín) y B (Claudia); escala de severidad **Alta / Media / Baja**.

---

## Resumen por heurística

| # | Heurística Nielsen | Dashboard | Alerta+Advisor | Notas |
|---|-------------------|-----------|----------------|-------|
| 1 | Visibilidad del estado del sistema | Media | Alta | WS badge existe; faltaba timestamp último frame (v2) |
| 2 | Coincidencia sistema ↔ mundo real | Media | Alta | Presets técnicos → etiquetas humanas (v2) |
| 3 | Control y libertad del usuario | Media | Media | Stop demo añadido como acción primaria en alerta |
| 4 | Consistencia y estándares | Alta | Alta | Unidades en nombres de campo alineadas a SPEC |
| 5 | Prevención de errores | Baja | Media | Disclaimer “demo” en Simulation Control (v2) |
| 6 | Reconocimiento vs recuerdo | Baja | Baja | SSI sin umbral visible; SOP solo en feed (v2 corrige) |
| 7 | Flexibilidad y eficiencia | Alta | Media | Layout denso OK para ingeniero; supervisor necesita banner |
| 8 | Diseño estético y minimalista | Alta | Media | Panel Advisor compite con 3D en alerta (v2 prioriza Advisor) |
| 9 | Ayuda a reconocer, diagnosticar y recuperar errores | Media | Baja | Errores WS/sim sin guía (v2 mensajes explícitos) |
| 10 | Ayuda y documentación | Baja | Baja | Empty state Advisor genérico (v2 texto contextual) |

---

## Problemas identificados y correcciones aplicadas (≥ 3)

### H-01 — SSI crítico comunicado solo por color (Heurística 6 + accesibilidad)

| | |
|---|---|
| **Pantalla** | Dashboard + Alerta |
| **Problema v1** | Zonas verde/ámbar/rojo del gauge sin texto de régimen para usuarios con daltonismo o bajo brillo en rig. |
| **Severidad** | Alta |
| **Corrección v2** | Badge textual `NORMAL` / `WARNING` / `CRITICAL` junto al título del gauge (ya en código `SsiGauge`); wireframe alerta añade banner `STICK-SLIP CRITICAL` con umbral explícito `SSI > 1.0`. |
| **Criterio SPEC** | RF-UI-ACC-01 contraste + texto; RF-09 Gherkin alerta textual |

### H-02 — Presets de simulación incomprensibles para supervisor (Heurística 2)

| | |
|---|---|
| **Pantalla** | Dashboard |
| **Problema v1** | Botones `severe_stick_slip`, `transient_choke` — léxico de desarrollador, no de toolpusher. |
| **Severidad** | Alta |
| **Corrección v2** | Wireframe muestra etiquetas **Normal · Stick-slip · Choke** manteniendo valor interno `ScenarioName`; tooltip/aria con nombre técnico para ingeniero. Journey 2 Claudia elige “Stick-slip” sin traducir snake_case. |
| **Criterio SPEC** | RF-UI-02 Gherkin preset legible |

### H-03 — Advisor vacío tras alerta sin explicación (Heurística 9 + 10)

| | |
|---|---|
| **Pantalla** | Dashboard / Alerta |
| **Problema v1** | Texto “No recommendations yet.” no indica trigger (`SSI > 1.0`) ni estado de carga del LLM. |
| **Severidad** | Media |
| **Corrección v2** | Empty state propuesto: “Sin SOP aún. Las recomendaciones aparecen cuando SSI supera 1.0.” + estado `Generando SOP…` durante debounce; wireframe alerta coloca Advisor **arriba** del canvas en critical. |
| **Criterio SPEC** | RF-07 Gherkin Advisor visible tras critical |

### H-04 — Desconexión WebSocket invisible en el flujo crítico (Heurística 1)

| | |
|---|---|
| **Pantalla** | Dashboard |
| **Problema v1** | Badge de conexión en header lejano al canvas; último frame congelado parece “pozo quieto”. |
| **Severidad** | Media |
| **Corrección v2** | `ConnectionBadge` incluye timestamp último frame + estado `reconnecting`; wireframe v2 lo muestra en header con hora. Abandono Journey 1 mitigado. |
| **Criterio SPEC** | RF-08 Gherkin desconexión |

### H-05 — Canvas 3D sin alternativa para teclado (Heurística 7 + accesibilidad)

| | |
|---|---|
| **Pantalla** | Dashboard |
| **Problema v1** | Foco WebGL sin skip link; métricas SSI/RPM no alcanzables si usuario no usa mouse. |
| **Severidad** | Media |
| **Corrección v2** | Wireframe anota “Tab: foco panel métricas”; SPEC RF-UI-ACC-02 orden de tabulación banner → gauges → controles → Advisor. |
| **Criterio SPEC** | RF-UI-ACC-02 |

---

## Hallazgos menores (sin cambio de wireframe en Sprint 1)

- Rotación libre del modelo 3D no esencial para MVP; deferido (NG-03).
- Sonido de alarma en rig no implementado — podría violar heurística 1 en producción; fuera alcance académico.

---

## Trazabilidad

| Documento | Relación |
|-----------|----------|
| [`SPEC.md` §1.2.1](../../SPEC.md) | Criterios Gherkin + accesibilidad |
| [`ADR-004-stack-ui.md`](../adr/ADR-004-stack-ui.md) | Stack UI |
| [`usuarios.md`](usuarios.md) | Personas y journeys |
