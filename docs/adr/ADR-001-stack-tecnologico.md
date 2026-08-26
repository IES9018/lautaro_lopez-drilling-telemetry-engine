# ADR-001 — Stack tecnológico

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-08-25 |
| **Sprint** | Sprint 1 (PP3 · IES 9-018 · Ciclo 2026) |
| **Proyecto** | `lautaro_lopez-drilling-telemetry-engine` |
| **Decisores** | lautaro_lopez (alumno) · contraste contra [`SPEC.md`](../../SPEC.md) |
| **Dominios impactados** | `src/engine/`, `src/pipeline/`, `src/advisor/`, `src/ui/`, `tests/` |
| **Relacionado** | [`.cursor/rules/`](../../.cursor/rules/) · [`INSTRUCTIONS.md`](../../INSTRUCTIONS.md) |

---

## Contexto del problema técnico

El sistema no es un CRUD: es un **motor de estimación de estado en soft real-time** para Stick-Slip en perforación profunda, con:

1. **Núcleo numérico determinista** — espacio de estados torsional 1D, fricción Stribeck, integrador **RK4** y **UKF** implementados en código propio (sin cajas negras de simulación/filtrado).
2. **Disparidad de telemetría** — superficie a **100 Hz** (&lt; 50 ms) vs MWD a **~0.05 Hz** con retardo acústico 15–45 s; hace falta un buffer de streaming confiable entre ingest, motor y API.
3. **Gemelo digital** — broadcast del estado estimado a ~**60 FPS** vía WebSocket y visualización de deformación torsional **3D**.
4. **Advisor asíncrono** — disparo por evento `SSI > 1.0` hacia un LLM que traduce a SOP (capa secundaria, no bloqueante del lazo numérico).
5. **Restricciones académicas / de gobernanza** — tipado estricto, cobertura ≥ 85%, Hypothesis, SAST, separación modular por dominio para futuros Cloud Agents, Git Flow institucional.

Se necesita un stack que:

- Exponga álgebra lineal vectorizada y tipado listo para `mypy --strict`.
- Soporte HTTP/WebSocket async de baja fricción.
- Ofrezca streams durables/livianos para desacoplar productores y consumidores.
- Permita UI 3D moderna con TypeScript `strict`.
- No oculte la física detrás de frameworks opacos (RF / Non-Goals del SPEC).

---

## Decisión tomada

Adoptar el siguiente stack como **baseline tecnológico del proyecto**:

| Capa | Tecnología | Rol |
|------|------------|-----|
| Lenguaje núcleo | **Python 3.12+** | Physics Engine, Pipeline, Advisor |
| Cálculo vectorizado | **NumPy** (+ SciPy solo para álgebra lineal puntual) | RK4, Stribeck, UKF, SSI — implementación propia |
| Tipado / calidad | **mypy --strict**, **Ruff**, **pytest**, **pytest-cov**, **Hypothesis**, **Bandit** | Tipado, lint, tests, property/estabilidad, SAST |
| API / streaming out | **FastAPI** + WebSockets | Broadcast `broadcast.state.v1` ~60 FPS |
| Buffer | **Redis Streams** | Ingest superficie/MWD → consumidores (motor / API) |
| Frontend gemelo | **Next.js** + **Three.js** + **TypeScript strict** | Visualización torsional 3D en `src/ui/` |
| Contratos | **JSON Schema** (draft 2020-12) | `surface.telemetry.v1`, `mwd.telemetry.v1`, `broadcast.state.v1` |
| Advisor | Cliente LLM vía API (proveedor configurable por env) + prompts versionados | Activación por `SSI > 1.0`; no acoplado al paso RK4/UKF |

**Principio no negociable:** RK4 y UKF se escriben en código determinista del repo; NumPy/SciPy son primitivas numéricas, no un simulador/filtro “todo en uno”.

---

## Alternativas descartadas

### Alternativa A — MATLAB / Simulink (+ export a runtime)

**Propuesta:** modelar sarta y UKF en Simulink; desplegar con MATLAB Runtime o codegen.

| Criterio objetivo | Evaluación |
|-------------------|------------|
| Transparencia del algoritmo (auditoría PP3 / IA) | **Falla** — la física queda encapsulada en bloques propietarios; dificulta contraste línea-a-línea con `SPEC.md`. |
| Git Flow + CI open en GitHub (IES9018) | **Falla** — licencias costosas, runners no estándar, peor encaje con PRs/SAST Python. |
| Separación modular para Cloud Agents | **Falla** — monolito de modelo gráfico, no carpetas `src/engine|pipeline|ui`. |
| Costo / reproducibilidad estudiantil | **Falla** — dependencia de licencia. |
| WebSocket 60 FPS + Next.js | **Parcial** — posible vía glue code, pero stack híbrido frágil. |

**Descarte:** incompatible con exigencia de implementación propia auditable y con el modelo operativo de agentes por dominio.

### Alternativa B — Stack JVM (Kotlin/Java + Spring WebFlux) + ND4J / EJML + React

**Propuesta:** pipeline reactivo en JVM; álgebra con ND4J/EJML; UI en React (sin Next) o Kotlin/JS.

| Criterio objetivo | Evaluación |
|-------------------|------------|
| Ecosistema numérico científico + Hypothesis-like | **Débil** — menos maduro que NumPy + Hypothesis para property tests de física en contexto académico. |
| Velocidad de prototipado del UKF/RK4 | **Débil** — más boilerplate; curva más alta para PP3 en 1 sprint. |
| FastAPI-equivalente async + schemas | **Aceptable** — WebFlux/Ktor cubren WebSocket, pero mayor complejidad operativa. |
| Tipado estricto | **Fuerte** — JVM tipado estático sólido. |
| Alineación con SPEC ya declarado (Python/NumPy) | **Falla** — forzaría reescritura de SSOT y contratos de tooling. |

**Descarte:** tipado atractivo, pero peor densidad científica y mayor fricción para el núcleo numérico + tests de propiedad en el horizonte del Sprint 1.

### Alternativa C — Node.js end-to-end (TypeScript + TensorFlow.js / numeric.js) + Socket.IO + Vue

**Propuesta:** un solo lenguaje (TS) para motor, API y UI.

| Criterio objetivo | Evaluación |
|-------------------|------------|
| Unificación de lenguaje | **Fuerte**. |
| Calidad de BLAS/vectorización para UKF denso | **Débil** frente a NumPy maduro. |
| Determinismo y ecosistema de tests numéricos | **Débil** — Hypothesis + numpy.testing son el estándar de facto aquí. |
| Riesgo de “caja negra” (TF.js como filtro) | **Alto** — contradice Non-Goal NG-07 / `.cursor/rules/physics-engine.mdc`. |
| Three.js / UI | **Fuerte** — pero no justifica mover el núcleo físico a JS. |

**Descarte:** conviene TypeScript **solo en `src/ui/`**; el núcleo de estimación permanece en Python.

### Alternativa D — gRPC + Apache Kafka + C++ (Eigen) + Unity

**Propuesta:** máximo rendimiento industrial.

| Criterio objetivo | Evaluación |
|-------------------|------------|
| Latencia / throughput | **Fuerte**. |
| Complejidad operativa (Kafka + C++ + Unity) | **Falla** para MVP académico Sprint 1. |
| Curva de aprendizaje y rúbrica (testing 20%, docs 10%) | **Falla** — consumo de tiempo en infra, no en física auditable. |
| Gemelo 3D web (Next/Three) vs Unity | Unity sobra para broadcast browser 60 FPS del alcance PP3. |

**Descarte:** over-engineering respecto a RF/Non-Goals del Sprint 1. Redis Streams + FastAPI cubren el desacople necesario sin cluster Kafka.

---

## Criterios de decisión (resumen)

| Criterio | Peso relativo | Ganador |
|----------|---------------|---------|
| Implementación propia y auditable de RK4/UKF | Crítico | Python + NumPy |
| Tipado estricto + SAST + cobertura ≥ 85% | Alto | mypy / Ruff / pytest / Bandit |
| Buffer desacoplado superficie/MWD → motor/API | Alto | Redis Streams |
| Broadcast WebSocket ~60 FPS | Alto | FastAPI |
| Visualización torsional 3D en browser | Medio (P3) | Next.js + Three.js |
| Complejidad operativa en Sprint 1 | Alto | Stack propuesto (vs Kafka/C++/Unity/MATLAB) |
| Aislamiento de dominios para Cloud Agents | Alto | Carpetas `src/*` + contratos JSON Schema |

---

## Consecuencias

### Positivas

- Alineación directa con `SPEC.md` (capas Physics / Pipeline / Twin / Advisor).
- Física y filtrado **inspeccionables** en review y en `docs/auditoria/auditoria-sprint1.md`.
- Buen encaje con property-based testing (Hypothesis) y tests de convergencia numérica.
- Desacople ingest ↔ motor ↔ UI vía Redis Streams + contratos versionados.
- Frontend TS strict separado (`src/ui/` sin `__init__.py`), listo para agente Digital Twin.
- Stack familiar en entorno académico; CI GitHub Actions viable sin runtimes propietarios.

### Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| GIL / latencia Python en lazo 100 Hz + UKF denso | Media | Vectorizar NumPy; perfilar; acotar \(N\) nodos en Sprint 1; aislar hot path; no bloquear WebSocket con LLM |
| Drift de schemas entre Python y TypeScript | Media | JSON Schema como SSOT; validar en ingest; generar o tipar a mano contratos en UI |
| Operación Redis (disponibilidad local/CI) | Media | Redis en Docker Compose; tests de integración con testcontainers o fake stream en unit |
| Alcance creep del Advisor LLM | Media | Non-Goal NG-04: evento + prompts primero; proveedor vía env; nunca en el paso RK4 |
| Dependencias vulnerables (npm/pip) | Media | Pin de versiones; `pip-audit` / `npm audit` en CI; Bandit en `src/` |
| Tentación de librerías “filtro mágico” | Alta | Enforcement en `.cursor/rules/`; rechazo en PR review |

### Seguimiento

- Materializar lockfiles (`pyproject.toml`, `package.json`) en un PR `chore`/`ci` posterior del Sprint 1.
- Versionar schemas en `docs/contratos/*.schema.json` cuando se implemente ingest.
- Revisar este ADR si se cambia el buffer (p. ej. NATS) o el runtime del motor (extensiones Cython/Rust) — requeriría **ADR-002+**.

---

## Referencias

- [`SPEC.md`](../../SPEC.md) — RF-01…RF-13, Non-Goals, arquitectura en 4 capas, contratos.
- [`.cursor/rules/`](../../.cursor/rules/) — prohibición de cajas negras; tipado estricto; dominios.
- Nygard, M. — *Documenting Architecture Decisions* (plantilla ADR).
