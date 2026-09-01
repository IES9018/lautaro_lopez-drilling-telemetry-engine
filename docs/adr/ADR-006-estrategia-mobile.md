# ADR-006 — Estrategia mobile

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-08-31 |
| **Sprint / TP** | ADI TP5 · PP3 Sprint 1–3 |
| **Proyecto** | `lautaro_lopez-drilling-telemetry-engine` |
| **Decisores** | lautaro_lopez (alumno) · contraste contra [`SPEC.md`](../../SPEC.md) |
| **Dominios impactados** | `src/ui/` (responsive), sin app nativa nueva |
| **Relacionado** | [ADR-004](ADR-004-stack-ui.md) · [ADR-005](ADR-005-estrategia-web.md) · [`presupuestos-rendimiento.md`](../arquitectura/presupuestos-rendimiento.md) |

---

## Contexto

Personas TP3 (Martín — laptop sala de control; Claudia — tablet en cabina) necesitan consultar SSI y SOP en pantallas &lt; 400 px. El núcleo del producto es **WebSocket ~60 FPS** + **WebGL** (gemelo 3D). Hay que decidir: responsive web, PWA, nativa o híbrida — sin “responsive un domingo” sin criterios.

**Restricciones del contexto:**

- **1 desarrollador** + agentes IA por dominio.
- **PP3 cierre Sprint 1:** 18 sep 2026; despliegue verificable Sprint 3.
- **Stack fijado:** Next.js 15 + R3F en `src/ui/` (ADR-004/005).
- **Offline:** ver [`offline-sync.md`](../arquitectura/offline-sync.md) — Non-Goal para monitoreo live.

---

## Matriz de decisión

Criterios del **contexto real** del proyecto (no genéricos). Escala: ✅ favorable · ⚠️ parcial · ❌ desfavorable.

| Criterio | Responsive web (Next.js) | PWA (instalable + SW) | Nativa (Flutter / RN) | Híbrida (Capacitor) |
|----------|---------------------------|----------------------|-------------------------|---------------------|
| **Costo mantenimiento (1 persona)** | ✅ Un codebase TS/React ya existente; Tailwind breakpoints | ⚠️ + service worker, manifest, política de cache | ❌ Segundo stack (Dart/Kotlin/Swift), duplica UI 3D | ⚠️ Wrapper + sync web; debugging nativo extra |
| **Offline necesario?** | ⚠️ Solo lectura último frame (ver Non-Goal offline) | ✅ Cache shell + assets; **no** sustituye WS live | ✅ Almacenamiento local nativo | ⚠️ Similar PWA dentro WebView |
| **Acceso hardware** (sensores rig, SCADA) | ❌ No requerido (NG-02); browser API suficiente | ❌ Igual que web | ✅ Bluetooth/USB posible | ⚠️ Plugins Capacitor |
| **Tiempo hasta cierre PP3** | ✅ Grid responsive ya en `DashboardShell`; wireframes móvil TP5 | ⚠️ Sprint 2–3 si se prioriza instalación | ❌ Reescritura UI + bridge 3D | ❌ Build stores / signing fuera alcance académico |
| **Soft real-time WS ~60 FPS** | ✅ Cliente WS nativo ya integrado | ✅ Igual (conexión requerida) | ✅ Posible con sockets nativos | ⚠️ Capa WebView puede limitar |
| **3D WebGL (R3F)** | ✅ Ecosistema maduro; `dynamic(ssr:false)` | ✅ Mismo runtime | ❌ Reimplementar en Unity/Flame o WebView pesado | ⚠️ WebView = básicamente responsive |
| **Contrato API-first (TP4)** | ✅ Consume OpenAPI REST/WS sin cambios | ✅ Igual | ⚠️ Cliente HTTP nuevo | ✅ WebView reutiliza |
| **Presupuestos RNF medibles** | ✅ Lighthouse CI + source-map-explorer en Next | ✅ Lighthouse + SW metrics | ❌ Herramientas distintas (Perfetto, etc.) | ⚠️ Mezcla de métricas |

---

## Decisión tomada

**Responsive web mobile-first sobre el gemelo Next.js existente** (breakpoints Tailwind `md`/`lg`), con **PWA diferida** a post-Sprint 3 si offline de shell se justifica.

| Aspecto | Elección |
|---------|----------|
| Layout móvil (&lt; 400 px) | Columna única: Advisor/alerta → gauges → controles → 3D reducido |
| Instalación home screen | No en Sprint 1–2 (sin manifest obligatorio) |
| App nativa / Capacitor | No |
| Métricas | RNF-01…05 en SPEC §1.6 + [`presupuestos-rendimiento.md`](../arquitectura/presupuestos-rendimiento.md) |

---

## Consecuencias — qué NO vamos a poder hacer (antes de sufrirlo)

| Limitación | Impacto |
|------------|---------|
| **Sin app store** | Distribución vía URL en tablet del rig; sin push nativo iOS/Android. |
| **3D pesado en 4G** | Chunk Three.js lazy-loaded; LCP del shell debe cumplir presupuesto **sin** esperar WebGL. |
| **Sin offline operativo** | Sin red no hay UKF ni SSI live; ver Non-Goal offline. |
| **Sin integración SCADA nativa** | NG-02; responsive no abre WITSML en background. |
| **INP en canvas 3D** | Gestos touch en WebGL compiten con INP de botones; priorizar targets táctiles en controles REST. |
| **PWA offline completa** | Cache de SOP histórico posible en futuro; no prometido en PP3. |

---

## Alternativas descartadas (resumen)

- **PWA ahora:** beneficio marginal vs esfuerzo SW mientras el valor es stream live.
- **Nativa / híbrida:** costo 1 dev + 3D incompatible con plazo PP3.

---

## Trazabilidad

| Artefacto | Ubicación |
|-----------|-----------|
| Wireframes móvil | [`docs/diseno/wireframes/*-mobile.md`](../../docs/diseno/wireframes/) |
| Offline | [`docs/arquitectura/offline-sync.md`](../arquitectura/offline-sync.md) |
| RNF | [`SPEC.md`](../../SPEC.md) §1.6 |

---

*ADR-006 — Aceptado · ADI TP5*
