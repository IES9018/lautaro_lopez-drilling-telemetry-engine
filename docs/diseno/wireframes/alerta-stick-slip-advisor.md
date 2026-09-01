# Wireframe — Alerta Stick-Slip crítica + Advisor SOP

**Pantalla crítica #2** · Journey 2 (Persona B)  
**Fidelidad:** baja (ASCII) — vista de **énfasis** cuando `alert_level === critical`  
**Nota:** en implementación Sprint 1 es el mismo layout con jerarquía visual elevada (no ruta separada).

---

## Objetivo

Cuando `SSI > 1.0`, la interfaz debe hacer imposible ignorar el estado crítico y presentar la recomendación SOP del LLM Advisor en menos de dos segundos de lectura.

---

## Entrada principal

- Trigger automático: frame WS con `alert_level: critical` y `ssi > 1.0`
- Evento envelope: `advisor_recommendation` tras debounce del Advisor
- Entrada manual (demo): preset `severe_stick_slip` + Start en Simulation Control

---

## Wireframe (v2 — post auditoría heurística)

```text
+--------------------------------------------------------------------------------+
|  ⚠ STICK-SLIP CRITICAL — SSI 1.24 (> 1.0)     [Connection: ● CONNECTED]      |
|  Acción requerida: revisar SOP abajo · no ignorar solo el gauge                |
+--------------------------------------------------------------------------------+
|  +--------------------------- ADVISOR (prioridad visual) --------------------+ |
|  | LLM Advisor · CRITICAL @ 12:04:02                                        | |
|  | +------------------------------------------------------------------------+ | |
|  | | SSI=1.24 · severe stick-slip detected                                  | | |
|  | | 1. Reducir WOB 10–15%                                                  | | |
|  | | 2. Variar RPM superficie ±5–10%                                        | | |
|  | | 3. Monitorear torque y SSI cada 30 s                                   | | |
|  | | Provider: mock | triggered_at: ISO8601                                  | | |
|  | +------------------------------------------------------------------------+ | |
|  +----------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------+
|  [ 3D twin — borde rojo sutil ]     |  SSI GAUGE (enlarged focus ring)          |
|                                     |  CRITICAL badge + valor 1.24              |
|                                     |  [ Stop simulation ]  ← acción primaria   |
+--------------------------------------------------------------------------------+
```

---

## Error probable y prevención

| Error | Causa | Prevención en diseño |
|-------|-------|---------------------|
| Supervisor no ve SOP | Advisor lento o falló | Estado “Generando SOP…” + mensaje error si provider falla; mock en Sprint 1 |
| Cree que Stop arregla el pozo real | Confusión demo vs rig | Label “Simulation Control (demo)” en wireframe v2 |
| Solo miró color rojo sin leer acciones | Violación heurística reconocimiento vs recuerdo | Banner textual con umbral `SSI > 1.0` y lista numerada SOP |
| No puede operar con teclado en alerta | Foco atrapado en canvas 3D | Orden tab: banner → Advisor card → Stop → gauges (`tabindex` lógico) |

---

## Accesibilidad (pantalla crítica #2)

| Requisito | Diseño v2 |
|-----------|-----------|
| Contraste AA | Texto SOP `#e2e8f0` sobre `#0f172a` (≥ 4.5:1); badge CRITICAL texto + fondo |
| Teclado | `Stop` y presets alcanzables con Tab; Enter activa; banner con `role="alert"` |
| No solo color | Icono ⚠ + texto “STICK-SLIP CRITICAL” además de rojo |
