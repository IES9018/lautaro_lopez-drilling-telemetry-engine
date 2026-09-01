# Presupuestos de rendimiento — pantallas críticas móvil

**Proyecto:** Drilling Telemetry Engine · ADI TP5  
**Pantallas:** Dashboard gemelo digital · Alerta Stick-Slip + Advisor (TP3)  
**Breakpoint objetivo:** viewport &lt; 400 px (móvil / tablet estrecha)  
**Red de referencia:** 4G simulada (Lighthouse throttling)

Trazabilidad SPEC: **RNF-01…RNF-05** (§1.6).

---

## Tabla de presupuestos

| ID | Métrica | Presupuesto | Herramienta de verificación | Frecuencia |
|----|---------|-------------|----------------------------|------------|
| **RNF-01** | **LCP móvil** (Largest Contentful Paint) | **&lt; 2,5 s** en 4G | **Lighthouse CI** (`@lhci/cli`) — perf móvil | CI (TP6) + manual pre-release |
| **RNF-02** | **INP** (Interaction to Next Paint) | **&lt; 200 ms** | **Lighthouse CI** — categoría Performance | CI (TP6) + manual |
| **RNF-03** | **Peso JS inicial gzip** (shell sin chunk 3D) | **&lt; 200 KB** | **`source-map-explorer`** sobre `.next/static/chunks` tras `next build` | CI script (TP6) + local en PR UI |
| **RNF-04** | **Chunk 3D lazy** (`DrillStringCanvas`) | Documentado; no bloquea LCP | `source-map-explorer` chunk aislado; meta &lt; 500 KB gzip Sprint 3 | Sprint 3 auditoría |
| **RNF-05** | **Targets táctiles** controles críticos | **≥ 48 px** (Material); ≥ 44 pt Apple HIG | Inspección wireframe + RTL test `getBoundingClientRect` en CI opcional | Review diseño + test UI |

**Nota RNF-03:** el gemelo 3D se carga con `next/dynamic({ ssr: false })`. El presupuesto de 200 KB aplica al **JavaScript parseado antes del lazy load** (header, gauges, WS hook, controles). Three.js/R3F van en chunk diferido (RNF-04).

---

## Cómo medir (comandos concretos)

### RNF-01 / RNF-02 — Lighthouse CI (preparado para CI)

Config: [`lighthouserc.mobile.json`](lighthouserc.mobile.json)

```bash
# Desde raíz del repo — requiere UI en http://localhost:3000
cd src/ui && npm run build && npm run start &
npx --yes @lhci/cli autorun --config=../../docs/arquitectura/lighthouserc.mobile.json
```

Umbrales en config: `performance` ≥ 0.85; auditorías `largest-contentful-paint` y `interaction-to-next-paint` con `maxLength` acorde a presupuesto.

### RNF-03 — source-map-explorer

```bash
cd src/ui
npm run build
# Generar stats si no existen (Next 15):
# ANALYZE=true npm run build  — o inspeccionar chunks directamente:
npx --yes source-map-explorer '.next/static/chunks/*.js' --gzip \
  --exclude-source-map --only-show-errors 2>/dev/null | head -40
```

Agregación manual: sumar chunks del **initial route** `/` excluyendo chunks cuyo nombre contiene `DrillStringCanvas` o `three`.

Script de referencia (Sprint 3 / TP6):

```bash
./scripts/check-js-budget.sh
```

### RNF-05 — targets táctiles

- Wireframes móvil: botones Start/Stop y presets con min-height 48 px.
- Test manual: Chrome DevTools → device toolbar 390×844.
- Automatizable: Vitest + Testing Library en `SimulationControls` (`min-h-12` = 48px Tailwind).

---

## Presupuestos por pantalla crítica

| Pantalla | LCP elemento esperado | INP interacción crítica |
|----------|----------------------|-------------------------|
| Dashboard gemelo | Título + `SsiGauge` o placeholder métricas | Tap **Start** / preset |
| Alerta + Advisor | Banner `STICK-SLIP CRITICAL` o `RecommendationCard` | Tap **Stop simulation** |

---

## Estado Sprint 1 (baseline honesto)

| RNF | Estado | Nota |
|-----|--------|------|
| RNF-01 | Objetivo Sprint 3 | 3D lazy ayuda; medir tras optimizar shell |
| RNF-02 | Objetivo Sprint 3 | WS a 60 FPS puede competir en main thread |
| RNF-03 | En vigilancia | Shell Next 15 + React 19 cerca del límite; no incluir chunk 3D |
| RNF-04 | Aceptado deferido | Three.js inevitable > 200 KB en chunk propio |
| RNF-05 | Diseño TP5 | Wireframes móvil anotan 48 px |

---

## Conexión PP3 Sprint 3

Estos RNF son los que el despliegue final debe verificar. Sin números, la IA “optimiza” sin criterio. TP6 agrega los mismos comandos al pipeline GHA.

---

*Presupuestos rendimiento · ADI TP5 · Revisar al cambiar `src/ui/` bundle*
