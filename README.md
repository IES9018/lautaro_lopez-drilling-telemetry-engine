# Drilling Telemetry Engine

Motor de estimación de estado en tiempo real y gemelo digital para monitoreo de perforación petrolera profunda (Upstream Oil & Gas). Detecta y diagnostica **Stick-Slip** (inestabilidad torsional de la broca) fusionando telemetría de superficie (100 Hz) con MWD de fondo (~0.05 Hz, retardo acústico 15–45 s).

> No es un CRUD web: es un sistema soft real-time con núcleo numérico determinista (RK4 + UKF propios), streaming y visualización 3D.

## Contexto académico

| Campo | Valor |
|-------|-------|
| Asignatura | Práctica Profesionalizante III (PP3) |
| Institución | IES 9-018 |
| Ciclo | 2026 |
| Profesor | Paulo Alvarez |
| Alumno / repo | `lautaro_lopez` · [`IES9018/lautaro_lopez-drilling-telemetry-engine`](https://github.com/IES9018/lautaro_lopez-drilling-telemetry-engine) |
| Sprint 1 | 24 ago – 18 sep 2026 |

## Estado del proyecto

**Fase actual:** núcleo Physics Engine + estimación UKF (Sprint 1 en curso).

| Entregable | Estado |
|------------|--------|
| `SPEC.md` (SSOT) + RF / Non-Goals | Listo |
| Cursor rules (`.cursor/rules/`) | Listo |
| ADR-001 stack tecnológico | Listo |
| Stribeck regularizado + RK4 | Listo |
| Drillstring FEM (espacio de estados) | Listo |
| SSI calculator | Listo |
| UKF (sigma points Van der Merwe + predict/update) | Listo |
| Tests unitarios (71) + cobertura 100% en módulos core | Listo |
| `MODELO_MATEMATICO.md` + auditoría IA (A-001…A-003) | Listo |
| Tooling (`pyproject.toml`, CI) | Pendiente |
| Pipeline Redis + WebSocket | Pendiente |
| UI Three.js + LLM Advisor | Pendiente (P3) |

**Rama de trabajo reciente:** `feature/kalman-ukf-estimator` → PR a `develop`.

## Arquitectura (4 capas)

```text
Superficie 100 Hz ──┐
                    ├──► Ingest + Redis Streams ──► Physics Engine (RK4 + UKF + SSI)
MWD ~0.05 Hz ───────┘                                      │
                                                           ├──► FastAPI WebSocket ~60 FPS ──► Next.js / Three.js
                                                           └──► LLM Advisor (si SSI > 1.0) ──► SOP
```

Detalle: [`SPEC.md`](SPEC.md) · matemáticas: [`docs/arquitectura/MODELO_MATEMATICO.md`](docs/arquitectura/MODELO_MATEMATICO.md) · stack: [`docs/adr/ADR-001-stack-tecnologico.md`](docs/adr/ADR-001-stack-tecnologico.md)

## Núcleo implementado (`src/engine/`)

| Módulo | Rol |
|--------|-----|
| `physics/friction_models.py` | Fricción Stribeck regularizada (`tanh`) |
| `physics/integrators.py` | Paso RK4 determinista |
| `physics/drillstring_fem.py` | Sarta lumped N nodos + `state_derivative` |
| `kalman/ssi_calculator.py` | Stick-Slip Severity Index + regímenes |
| `kalman/sigma_points.py` | Sigma points Van der Merwe + Cholesky/jitter |
| `kalman/ukf_estimator.py` | UKF `predict` / `update` sobre la dinámica FEM |

## Stack

| Capa | Tecnología |
|------|------------|
| Núcleo | Python 3.12+, NumPy (RK4/UKF propios) |
| API / WS | FastAPI (pendiente) |
| Buffer | Redis Streams (pendiente) |
| UI | Next.js, Three.js, TypeScript strict (pendiente) |
| Calidad | mypy --strict, pytest, coverage; Ruff/Bandit pendientes en CI |

## Estructura

```text
src/engine/{physics,kalman,simulator}   # Physics Engine + UKF/SSI
src/pipeline/{ingest,buffer,api}        # Ingest / Redis / FastAPI
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
| [`docs/auditoria/auditoria-sprint1.md`](docs/auditoria/auditoria-sprint1.md) | Auditoría crítica de código IA |
| [`.cursor/rules/`](.cursor/rules/) | Enforcement por dominio |
| [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) | Checklist de PR |

## Git Flow (obligatorio)

```text
feature/<tema>  →  PR → develop  →  PR → main
```

- Push directo a `main` y `develop` bloqueado.
- Commits convencionales: `feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `test:`.
- Un PR = un dominio siempre que sea posible.

## Desarrollo local

Con el venv del repo (cuando exista `.venv`):

```bash
python3 -m venv .venv
.venv/bin/pip install numpy pytest coverage mypy

.venv/bin/python -m pytest tests/unit -q
.venv/bin/mypy --strict src/engine
# Cobertura (evitar pytest-cov en Python 3.14; usar coverage run):
.venv/bin/coverage run --source=src -m pytest tests/unit -q
.venv/bin/coverage report -m --include='src/engine/*'
```

El scaffolding formal (`pyproject.toml`, Ruff, Bandit, CI) se agrega en un paso posterior del Sprint 1. Checklist completo: [`INSTRUCTIONS.md`](INSTRUCTIONS.md).

## Requerimientos funcionales (resumen)

| ID | Descripción | Sprint 1 |
|----|-------------|----------|
| RF-03…06 | Stribeck, RK4, UKF, SSI | Hecho (núcleo) |
| RF-11/12 | Tests, tipado, auditoría IA | En curso |
| RF-01/02/10 | Ingest + Redis Streams | Pendiente |
| RF-08/09 | WebSocket 60 FPS + UI 3D | Pendiente (P3) |
| RF-07 | Advisor LLM si `SSI > 1.0` | Pendiente (P3) |

Lista completa y Non-Goals: [`SPEC.md` §1](SPEC.md).

## Licencia

Uso académico — PP3 IES 9-018 · Ciclo 2026.
