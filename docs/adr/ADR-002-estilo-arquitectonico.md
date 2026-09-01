# ADR-002 — Estilo arquitectónico

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-08-31 |
| **Sprint / TP** | ADI TP2 · PP3 Sprint 1 |
| **Proyecto** | `lautaro_lopez-drilling-telemetry-engine` |
| **Decisores** | lautaro_lopez |
| **Relacionado** | [`ADR-001`](ADR-001-stack-tecnologico.md) · [`SPEC.md`](../../SPEC.md) · [`C4-contenedores.md`](../arquitectura/C4-contenedores.md) |

---

## Contexto del problema técnico

El sistema combina:

1. Lazo numérico **soft real-time** (~100 Hz física + UKF).
2. API **async** con WebSocket ~60 FPS.
3. Cliente **3D** en browser (Next.js).
4. Módulo **Advisor** asíncrono (no bloqueante).

Restricciones del proyecto:

- **Un desarrollador** (lautaro_lopez) en horizonte Sprint 1.
- Deadlines PP3 (Sprint 2 núcleo funcional oct 2026).
- Gobernanza por **dominios** para agentes IA (`.cursor/rules/`).
- No operar un cluster distribuido en IES 9-018.

Hay que elegir un estilo que permita evolucionar sin fragmentar el despliegue ni multiplicar repos/servicios.

---

## Decisión tomada

Adoptar un **monolito modular por dominio** con **separación de capas dentro de cada dominio**:

```text
src/
  engine/     # Physics — RK4, UKF, SSI, simulador (sin HTTP)
  pipeline/   # Ingest, buffer, orchestration, FastAPI
  advisor/    # LLM SOP (invocado por pipeline, sin HTTP propio)
  ui/         # Cliente Next.js (desacoplado, solo contratos WS/REST)
```

**Patrón principal:** modular monolith + **ports/adapters livianos** en pipeline (schemas Pydantic, `LLMProviderProtocol`, inyección en `create_app` para tests).

**Despliegue Sprint 1:** un proceso Python (FastAPI/uvicorn) + build estático o `next dev` para UI. No hay orquestador de microservicios.

---

## Alternativas descartadas

### Alternativa A — Microservicios (Physics / Pipeline / Advisor / UI-BFF)

| Criterio | Evaluación |
|----------|------------|
| Escalado independiente por servicio | **Fuerte** en producción industrial |
| Complejidad operativa (4 deploys, tracing, versionado contratos) | **Falla** — equipo de 1, plazo Sprint 1 |
| Latencia inter-servicio en lazo 100 Hz | **Riesgo alto** — UKF + simulador en el mismo tick |
| Aislamiento para Cloud Agents | **Parcial** — ya logrado con carpetas `src/*` sin microservicios |
| Costo de red/deserialización en hot path | **Negativo** para soft real-time |

**Descarte:** over-engineering; los dominios ya están aislados por paquetes y rules, no por procesos.

### Alternativa B — Serverless (AWS Lambda / Cloud Functions + API Gateway)

| Criterio | Evaluación |
|----------|------------|
| Costo inicial bajo | **Fuerte** |
| WebSocket 60 FPS + estado UKF persistente entre invocaciones | **Falla** — cold start y estado de filtro incompatible |
| RK4 loop 100 Hz sostenido | **Falla** — no es workload serverless típico |
| Hosting académico IES9018 / Docker local | **Falla** — dependencia cloud no requerida |

**Descarte:** incompatible con lazo numérico continuo y broadcast WS.

### Alternativa C — Arquitectura hexagonal estricta con bounded contexts en repos separados

| Criterio | Evaluación |
|----------|------------|
| Separación conceptual clara | **Fuerte** |
| Múltiples repos / versionado cruzado | **Falla** — fricción Git Flow y PRs cross-domain |
| Encaje con SPEC monorepo `src/` | **Débil** — ya definido en gobernanza PP3 |

**Descarte:** hexagonal **dentro** de cada dominio es válido; multi-repo no aporta en Sprint 1.

---

## Criterios de decisión (resumen)

| Criterio | Ganador |
|----------|---------|
| Un desarrollador, un deploy Python | Monolito modular |
| Hot path 100 Hz UKF + RK4 | Proceso único, sin RPC |
| Aislamiento agentes IA | Carpetas + `.cursor/rules/` |
| UI 3D en browser | Cliente separado (Next.js) |
| Evolución futura a Redis/microservicios | ADR nuevo sin reescribir núcleo |

---

## Consecuencias

### Positivas

- Un `docker compose up` levanta API + Redis sin service mesh.
- Tests de integración cubren orchestrator + UKF en un solo proceso.
- PRs por dominio alineados a gobernanza PP3.
- C4 contenedores legible: un runtime Python + browser.

### Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Acoplamiento accidental entre dominios | Rules de dominio; pipeline no altera fórmulas |
| Monolito crece y CI lento | `pyproject.toml`, jobs CI paralelos; dominios en PRs chicos |
| Escalado horizontal futuro | ADR-002 puede superseded si RF-10 exige workers Redis |

### Seguimiento

- Si se extrae Physics a worker separado → **ADR-007+** con métricas de latencia.
- Diagramas C4 actualizados en [`C4-contenedores.md`](../arquitectura/C4-contenedores.md).

---

## Referencias

- [`SPEC.md`](../../SPEC.md) — RF-13 gobernanza modular.
- [`C4-contexto.md`](../arquitectura/C4-contexto.md) · [`C4-contenedores.md`](../arquitectura/C4-contenedores.md).
- Martin, R. — *Clean Architecture* (modular monolith vs microservices).
