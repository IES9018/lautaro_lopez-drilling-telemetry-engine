# Drilling Telemetry Engine

Motor de estimación de estado en tiempo real y gemelo digital para monitoreo de perforación petrolera profunda (Upstream Oil & Gas). Detecta y diagnostica **Stick-Slip** (inestabilidad torsional de la broca) fusionando telemetría de superficie (100 Hz) con MWD de fondo (~0.05 Hz, retardo acústico 15–45 s).

> No es un CRUD web: es un sistema soft real-time con núcleo numérico determinista (RK4 + UKF propios), streaming y visualización 3D.

## Contexto académico

| Campo | Valor |
|-------|-------|
| Asignatura PP3 | Práctica Profesionalizante III (PP3) |
| Asignatura ADI | Arquitectura y Diseño de Interfaces (3° año) |
| Institución | IES 9-018 |
| Ciclo | 2026 |
| Profesor | Paulo Alvarez |
| Alumno / repo | `lautaro_lopez` · [`IES9018/lautaro_lopez-drilling-telemetry-engine`](https://github.com/IES9018/lautaro_lopez-drilling-telemetry-engine) |
| Sprint 1 (PP3) | 24 ago – 18 sep 2026 |
| Entorno de desarrollo | **Cursor** |
| Arnés IA | [`.cursor/rules/*.mdc`](.cursor/rules/) (índice en [`.cursor/rules/README.md`](.cursor/rules/README.md)) |
| Consignas ADI | [`IES9018/proyecto-adi-2026`](https://github.com/IES9018/proyecto-adi-2026) |

## Entrega ADI — TP1 (SDD y arneses)

| Entregable TP1 | Ubicación en este repo |
|----------------|------------------------|
| Especificación declarativa | [`SPEC.md`](SPEC.md) — RF-01…13, Non-Goals, contratos |
| ADR stack tecnológico | [`docs/adr/ADR-001-stack-tecnologico.md`](docs/adr/ADR-001-stack-tecnologico.md) |
| Arnés de agente IA | [`.cursor/rules/`](.cursor/rules/) + [`INSTRUCTIONS.md`](INSTRUCTIONS.md) |
| Evidencia de entrega | PR `feature/tp1-sdd` → `main` (checklist en plantilla de PR) |

## Entrega ADI — TP2 (Arquitectura visible)

| Entregable TP2 | Ubicación en este repo |
|----------------|------------------------|
| C4 contexto | [`docs/arquitectura/C4-contexto.md`](docs/arquitectura/C4-contexto.md) |
| C4 contenedores | [`docs/arquitectura/C4-contenedores.md`](docs/arquitectura/C4-contenedores.md) |
| ADR estilo arquitectónico | [`docs/adr/ADR-002-estilo-arquitectonico.md`](docs/adr/ADR-002-estilo-arquitectonico.md) |
| ADR persistencia / buffer | [`docs/adr/ADR-003-persistencia.md`](docs/adr/ADR-003-persistencia.md) |
| SPEC v2 (restricciones + changelog) | [`SPEC.md`](SPEC.md) §1.5 |
| Arnés v2 (regla anti-deps sin ADR) | [`.cursor/rules/governance.mdc`](.cursor/rules/governance.mdc) |
| Evidencia de entrega | PR `feature/tp2-arquitectura` → `main` |

## Entrega ADI — TP3 (Diseño HCI)

| Entregable TP3 | Ubicación en este repo |
|----------------|------------------------|
| Personas + user journeys (Mermaid) | [`docs/diseno/usuarios.md`](docs/diseno/usuarios.md) |
| Wireframes pantallas críticas (baja fidelidad) | [`docs/diseno/wireframes/`](docs/diseno/wireframes/) |
| Auditoría heurística Nielsen (10 + correcciones) | [`docs/diseno/auditoria-heuristica.md`](docs/diseno/auditoria-heuristica.md) |
| ADR stack UI | [`docs/adr/ADR-004-stack-ui.md`](docs/adr/ADR-004-stack-ui.md) |
| SPEC v3 (Gherkin UI + accesibilidad + changelog) | [`SPEC.md`](SPEC.md) §1.2.1 |
| Evidencia de entrega | PR `feature/tp3-hci` → `main` |

## Entrega ADI — TP4 (API-first y web segura)

| Entregable TP4 | Ubicación en este repo |
|----------------|------------------------|
| Contrato OpenAPI 3.x (5 endpoints críticos) | [`docs/arquitectura/api-contracts.yaml`](docs/arquitectura/api-contracts.yaml) |
| Validación lint (Redocly) | [`docs/arquitectura/README.md`](docs/arquitectura/README.md) |
| ADR estrategia web | [`docs/adr/ADR-005-estrategia-web.md`](docs/adr/ADR-005-estrategia-web.md) |
| Threat model lite STRIDE | [`docs/seguridad/threat-model-lite.md`](docs/seguridad/threat-model-lite.md) |
| Arnés v3 (reglas seguridad) | [`.cursor/rules/governance.mdc`](.cursor/rules/governance.mdc) |
| SPEC v4 (schemas OpenAPI + changelog) | [`SPEC.md`](SPEC.md) §1.4 |
| Evidencia de entrega | PR `feature/tp4-api-first` → `main` |

## Entrega ADI — TP5 (Estrategia mobile)

| Entregable TP5 | Ubicación en este repo |
|----------------|------------------------|
| ADR estrategia mobile (matriz decisión) | [`docs/adr/ADR-006-estrategia-mobile.md`](docs/adr/ADR-006-estrategia-mobile.md) |
| Presupuestos rendimiento (LCP, INP, JS) | [`docs/arquitectura/presupuestos-rendimiento.md`](docs/arquitectura/presupuestos-rendimiento.md) |
| Lighthouse CI config móvil | [`docs/arquitectura/lighthouserc.mobile.json`](docs/arquitectura/lighthouserc.mobile.json) |
| Offline Non-Goal justificado | [`docs/arquitectura/offline-sync.md`](docs/arquitectura/offline-sync.md) |
| Wireframes móvil (&lt; 400 px) | [`docs/diseno/wireframes/*-mobile.md`](docs/diseno/wireframes/) |
| SPEC v5 (RNF-01…05 + changelog) | [`SPEC.md`](SPEC.md) §1.6 |
| Script presupuesto JS (CI TP6) | [`scripts/check-js-budget.sh`](scripts/check-js-budget.sh) |
| Evidencia de entrega | PR `feature/tp5-mobile` → `main` |

## Estado del proyecto

**Fase actual:** Physics + UKF + simulador + pipeline + **gemelo digital 3D** (Sprint 1 en curso).

| Entregable | Estado |
|------------|--------|
| `SPEC.md` (SSOT) + RF / Non-Goals | Listo |
| Cursor rules (`.cursor/rules/`) | Listo |
| ADR-001 stack tecnológico | Listo |
| Stribeck regularizado + RK4 | Listo |
| Drillstring FEM (espacio de estados) | Listo |
| SSI calculator | Listo |
| UKF (sigma points Van der Merwe + predict/update) | Listo |
| Simulador de pozo (`well_generator`) + retardo MWD | Listo |
| Contratos JSON Schema + DTOs Pydantic v2 | Listo |
| TimeSyncBuffer + fixed-lag MWD | Listo |
| FastAPI WebSocket ~60 FPS + REST control | Listo |
| LLM Advisor (debounce + mock provider + SOP) | Listo |
| UI Next.js / R3F digital twin + gauges + AdvisorFeed | Listo |
| Tests unitarios + integración; cobertura ≥85% pipeline/advisor | Listo |
| `MODELO_MATEMATICO.md` + `DIAGRAMAS_C4.md` + auditoría (A-001…A-007) | Listo |
| Tooling (`pyproject.toml`, CI) | Pendiente |
| Redis Streams (RF-10) | Diferido (buffer in-memory Sprint 1) |

**Rama de trabajo reciente:** `feature/ui-3d-digital-twin` → PR a `develop`.

## Arquitectura (4 capas)

```text
Superficie 100 Hz ──┐
                    ├──► Ingest (JSON Schema + Pydantic) ──► TimeSyncBuffer ──► UKF + SSI
MWD ~0.05 Hz ───────┘         │                                    │
                              │                                    ├──► FastAPI WebSocket ~60 FPS
                              └── fixed-lag replay (retardo) ──────┘
```

Detalle: [`SPEC.md`](SPEC.md) · C4: [`docs/arquitectura/DIAGRAMAS_C4.md`](docs/arquitectura/DIAGRAMAS_C4.md) · matemáticas: [`docs/arquitectura/MODELO_MATEMATICO.md`](docs/arquitectura/MODELO_MATEMATICO.md)

## Núcleo implementado

### Physics Engine (`src/engine/`)

| Módulo | Rol |
|--------|-----|
| `physics/friction_models.py` | Fricción Stribeck regularizada (`tanh`) |
| `physics/integrators.py` | Paso RK4 determinista |
| `physics/drillstring_fem.py` | Sarta lumped N nodos + `state_derivative` |
| `kalman/ssi_calculator.py` | Stick-Slip Severity Index + regímenes |
| `kalman/sigma_points.py` | Sigma points Van der Merwe + Cholesky/jitter |
| `kalman/ukf_estimator.py` | UKF `predict` / `update` sobre la dinámica FEM |
| `simulator/well_generator.py` | Ground truth + ruido + retardo acústico MWD |

### Data Pipeline (`src/pipeline/`)

| Módulo | Rol |
|--------|-----|
| `ingest/schema_validation.py` | Validación JSON Schema (`docs/contratos/`) |
| `api/schemas/*` | DTOs Pydantic v2 (`Surface` / `Mwd` / `Broadcast`) |
| `buffer/time_sync_buffer.py` | Journal circular fixed-lag O(1) |
| `orchestration/*` | Orquestador Simulator+UKF+SSI + `h(x)` |
| `api/app.py` | FastAPI lifespan + REST + `/ws/telemetry` |

## Stack

| Capa | Tecnología |
|------|------------|
| Núcleo | Python 3.12+, NumPy (RK4/UKF propios) |
| API / WS | FastAPI + WebSockets ~60 FPS |
| Buffer | TimeSyncBuffer in-memory (Redis diferido) |
| UI | Next.js 15, React Three Fiber, TypeScript strict (`src/ui/`) |
| Calidad | mypy --strict, pytest, coverage; Ruff/Bandit pendientes en CI |

## Estructura

```text
src/engine/{physics,kalman,simulator}   # Physics Engine + UKF/SSI
src/pipeline/{ingest,buffer,api,orchestration}
src/advisor/prompts                     # LLM Advisor
src/ui/                                 # Gemelo digital (TypeScript)
tests/{unit,property,integration}
docs/{adr,arquitectura,auditoria,contratos}
.cursor/rules/                          # Gobernanza para agentes Cursor
```

## Documentación clave

| Documento | Rol |
|-----------|-----|
| [`SPEC.md`](SPEC.md) | Especificación SSOT (RF, Non-Goals, física, contratos) |
| [`INSTRUCTIONS.md`](INSTRUCTIONS.md) | Runbook operativo (Git Flow, checklist PR, comandos) |
| [`docs/arquitectura/MODELO_MATEMATICO.md`](docs/arquitectura/MODELO_MATEMATICO.md) | Ecuaciones FEM, SSI, UKF |
| [`docs/arquitectura/DIAGRAMAS_C4.md`](docs/arquitectura/DIAGRAMAS_C4.md) | Contexto / contenedores / streaming |
| [`docs/auditoria/auditoria-sprint1.md`](docs/auditoria/auditoria-sprint1.md) | Auditoría crítica de código IA |
| [`docs/contratos/`](docs/contratos/) | JSON Schema canónicos |
| [`.cursor/rules/`](.cursor/rules/) | Enforcement por dominio |

## Git Flow (obligatorio)

```text
feature/<tema>  →  PR → develop  →  PR → main
```

- Push directo a `main` y `develop` bloqueado.
- Commits convencionales: `feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `test:`.
- Un PR = un dominio siempre que sea posible.

## Desarrollo local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest tests/ -q
.venv/bin/mypy --strict src/pipeline src/engine
# Cobertura (evitar pytest-cov en Python 3.14; usar coverage run):
.venv/bin/coverage run --source=src -m pytest tests/ -q
.venv/bin/coverage report -m --include='src/pipeline/*'
```

## Requerimientos funcionales (resumen)

| ID | Descripción | Sprint 1 |
|----|-------------|----------|
| RF-03…06 | Stribeck, RK4, UKF, SSI | Hecho |
| RF-01/02/08 | Ingest schemas + WebSocket 60 FPS | Hecho (pipeline) |
| RF-11/12 | Tests, tipado, auditoría IA | En curso |
| RF-10 | Redis Streams | Diferido (buffer in-memory) |
| RF-09 | UI 3D | Pendiente (P3) |
| RF-07 | Advisor LLM si `SSI > 1.0` | Pendiente (P3) |

Lista completa y Non-Goals: [`SPEC.md` §1](SPEC.md).

## Licencia

Uso académico — PP3 IES 9-018 · Ciclo 2026.
