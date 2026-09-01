# Wireframe móvil — Dashboard Gemelo Digital (&lt; 400 px)

**Pantalla crítica #1** · ADI TP5 · Journey 1  
**Desktop de referencia:** [`dashboard-gemelo-digital.md`](dashboard-gemelo-digital.md)

---

## Comparación desktop vs móvil

| Aspecto | Desktop (≥ 1024 px) | Móvil (&lt; 400 px) | Por qué cambió |
|---------|---------------------|---------------------|----------------|
| Layout | Grid 7+5 cols: 3D izquierda, métricas derecha | **Columna única** apilada | Una mano; evitar scroll horizontal |
| Orden visual | 3D dominante | **SSI → RPM → Controles → 3D** | Métricas críticas antes que WebGL pesado (LCP RNF-01) |
| Canvas 3D | ~70% ancho, min 320 px alto | **100% ancho, 200 px alto** fijo | Legible sin robar espacio a gauges |
| Advisor feed | Footer ancho completo abajo | **Colapsable** bajo gauges o tab “SOP” | Priorizar SSI en viewport inicial |
| Targets táctiles | Botones ~40 px histórico | **min 48×48 px** Start/Stop/presets | RNF-05 · Material / web.dev |
| Connection badge | Header derecha | **Sticky top** full width | Siempre visible al hacer scroll |
| Tipografía SSI | `text-2xl` | **`text-3xl`** valor numérico | Legibilidad en cabina con reflejos |

---

## Desktop (recordatorio — v2)

```text
+------------------------------------------+--------+
|  Title                    [CONNECTED]    | gauges |
|  [ 3D Canvas grande      ]               | SSI    |
|                                          | RPM    |
|                                          | Sim    |
+------------------------------------------+--------+
|  Advisor Feed (ancho completo)           |
+------------------------------------------+
```

---

## Móvil (&lt; 400 px) — wireframe v3

```text
+----------------------------------+
| ● CONNECTED · last 12:04:01      |  <- sticky
| Drillstring Digital Twin         |
+----------------------------------+
| SSI Gauge    [ CRITICAL ]        |
|     (needle)      1.24           |
| Umbral crítico SSI > 1.0         |
+----------------------------------+
| Surface RPM  |  Bit RPM (UKF)    |
|    120       |       45          |
+----------------------------------+
| [  Start 48px ] [ Stop 48px ]    |
| [Normal][Stick-slip][Choke]     |  <- chips 48px touch
| running · t=42.5s                |
+----------------------------------+
| [ 3D twin — 200px height ]      |
| (lazy load · pinch optional)    |
+----------------------------------+
| v Advisor / SOP (scroll)         |
| RecommendationCard…            |
+----------------------------------+
```

---

## Contenido recortado / diferido

| Elemento desktop | Móvil |
|------------------|-------|
| Subtítulo largo bajo H1 | Una línea: “SSI · Advisor” |
| Leyenda θ nodal en 3D | `aria-label` + tooltip on tap |
| Advisor siempre expandido | Scroll bajo métricas; crítico sube en pantalla alerta |

---

## RNF trazables

| RNF | Cómo valida este wireframe |
|-----|---------------------------|
| RNF-01 | SSI gauge antes del chunk 3D = candidato LCP |
| RNF-02 | Botones 48 px = INP en Start/Stop |
| RNF-05 | Targets ≥ 48 px explícitos |

---

*Wireframe móvil TP5 · Dashboard*
