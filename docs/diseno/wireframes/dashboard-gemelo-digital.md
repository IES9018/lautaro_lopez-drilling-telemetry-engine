# Wireframe — Dashboard Gemelo Digital (monitoreo continuo)

**Pantalla crítica #1** · Journey 1 (Persona A)  
**Fidelidad:** baja (ASCII + anotaciones)  
**Implementación de referencia:** `src/ui/src/components/layout/DashboardShell.tsx`

---

## Objetivo

Permitir monitoreo soft real-time de la sarta en 3D con SSI y RPM dual (superficie vs broca UKF) mientras el WebSocket entrega `broadcast.state.v1` a ~60 FPS.

---

## Entrada principal

- URL: `/` (Next.js App Router)
- Conexión automática a `ws://<api>/ws/telemetry` al montar `useTelemetryStream`
- Sin login en MVP académico (NG-08)

---

## Wireframe (v2 — post auditoría heurística)

```text
+--------------------------------------------------------------------------------+
|  Drillstring Digital Twin          [Connection: ● CONNECTED  last: 12:04:01]   |
|  Torsional deformation · SSI · LLM Advisor                                     |
+--------------------------------------------------------------------------------+
|                                    |  +---------------- SSI Gauge ----------+ |
|                                    |  | SSI Gauge          [ CRITICAL ]      | |
|   [ 3D Drillstring Canvas ]        |  |    (semicircle green|amber|red)      | |
|   - nodos con torsión coloreada    |  |         needle                       | |
|   - leyenda: θ nodal (rad)         |  |           1.24                       | |
|   - Tab: foco panel métricas       |  |  Umbral crítico: SSI > 1.0           | |
|   - aria-label descriptivo         |  +--------------------------------------+ |
|                                    |  +---------------- RPM Dual -------------+ |
|                                    |  | Surface RPM    |    Bit RPM (UKF)    | |
|                                    |  |    120         |        45           | |
|                                    |  +--------------------------------------+ |
|                                    |  +------------ Simulation Control ------+ |
|                                    |  | [Start] [Stop]                       | |
|                                    |  | Presets: Normal | Stick-slip | Choke | |
|                                    |  | running=true · t=42.50s              | |
|                                    |  +--------------------------------------+ |
+--------------------------------------------------------------------------------+
|  LLM Advisor Feed — SOP mitigations on SSI > 1.0                                |
|  +----------------------------------------------------------------------------+|
|  | (vacío o lista RecommendationCard)                                         ||
|  +----------------------------------------------------------------------------+|
+--------------------------------------------------------------------------------+
```

---

## Error probable y prevención

| Error | Causa | Prevención en diseño |
|-------|-------|---------------------|
| Usuario interpreta broca detenida cuando solo hay lag MWD | Retardo acústico 15–45 s no visible | Mostrar `last frame timestamp` en `ConnectionBadge`; RPM UKF etiquetado “Bit (UKF est.)” |
| Cree que la UI calcula SSI | Recalculo client-side | Texto fijo: “SSI desde motor físico”; `alert_level` solo del broadcast |
| Abandona tras pantalla negra 3D | SSR/WebGL fail | Placeholder “Loading 3D twin…” + skip link a panel métricas (teclado) |
| No distingue warning vs critical | Solo color | Badge textual `NORMAL` / `WARNING` / `CRITICAL` + valor numérico |

---

## Contratos UI ↔ backend

| Elemento | Campo / evento |
|----------|----------------|
| SSI gauge | `ssi`, `alert_level` |
| RPM dual | `ukf_state.omega_rad_s[0]`, `ukf_state.rpm_bit_est` |
| Canvas 3D | `torsional_deformation_rad[]`, `ukf_state.theta_rad[]` |
| Conexión | estado hook + `timestamp` último frame |
