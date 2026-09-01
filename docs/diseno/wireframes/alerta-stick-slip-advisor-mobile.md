# Wireframe móvil — Alerta Stick-Slip + Advisor (&lt; 400 px)

**Pantalla crítica #2** · ADI TP5 · Journey 2  
**Desktop de referencia:** [`alerta-stick-slip-advisor.md`](alerta-stick-slip-advisor.md)

---

## Comparación desktop vs móvil

| Aspecto | Desktop | Móvil (&lt; 400 px) | Por qué cambió |
|---------|---------|---------------------|----------------|
| Jerarquía | Advisor panel grande + 3D lateral | **Banner alerta full-bleed primero** | Toolpusher lee en &lt; 2 s (journey Claudia) |
| Banner crítico | Una línea en header ancho | **2–3 líneas + icono ⚠ 24px** | Sin depender solo del color rojo |
| SOP lista | Card ancha | **Card full width**, numeración 1–3 | Scroll vertical natural |
| 3D | Visible junto al gauge | **Oculto por defecto** o thumbnail 120 px | SOP es prioridad; 3D no bloquea acción |
| Acción primaria | Stop en panel lateral | **FAB o botón full-width Stop 48px** bajo SOP | Una mano; INP RNF-02 |
| Connection | Header | Junto al banner (sticky stack) | Contexto de live vs stale |

---

## Desktop (recordatorio — v2)

```text
+--------------------------------------------------+
| ⚠ STICK-SLIP CRITICAL — SSI 1.24    [CONNECTED] |
| ADVISOR (panel grande)                           |
| [ 3D borde rojo ]     | SSI CRITICAL + Stop      |
+--------------------------------------------------+
```

---

## Móvil (&lt; 400 px) — wireframe v3

```text
+----------------------------------+
| ● CONNECTED                    |
+----------------------------------+
| ⚠ STICK-SLIP CRITICAL            |
| SSI 1.24 (> 1.0)                 |
| Revisar SOP abajo                |
+----------------------------------+
| LLM Advisor · 12:04:02           |
| +------------------------------+ |
| | SSI=1.24 stick-slip          | |
| | 1. Reducir WOB 10–15%        | |
| | 2. Variar RPM ±5–10%         | |
| | 3. Monitorear cada 30 s      | |
| +------------------------------+ |
+----------------------------------+
| [ STOP SIMULATION  full 48px ]   |  <- acción primaria
+----------------------------------+
| SSI 1.24 [CRITICAL] mini gauge   |
+----------------------------------+
| (3D thumbnail opcional 120px)    |
+----------------------------------+
```

---

## Targets táctiles

| Control | Tamaño mínimo | Nota |
|---------|---------------|------|
| Stop simulation | 48×48 px (full width ≥ 48 height) | `role="alert"` en banner |
| Scroll SOP | área táctil nativa | Sin links &lt; 48 px en acciones |
| Presets (si visibles) | chips 48 px altura | Secundario en alerta |

---

## Contenido recortado

| Desktop | Móvil |
|---------|-------|
| Provider / ISO8601 en card | Pie de card colapsable “Detalles” |
| 3D con borde rojo grande | Thumbnail o omitido |
| RPM dual completo | Solo SSI + badge en alerta |

---

## RNF trazables

| RNF | Validación |
|-----|------------|
| RNF-01 | Banner o SOP card = LCP en vista crítica |
| RNF-02 | Stop full-width 48 px |
| RNF-05 | Todos los controles ≥ 48 px |

---

*Wireframe móvil TP5 · Alerta Stick-Slip*
