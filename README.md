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
| Alumno / repo | `lautaro_lopez` · `IES9018/lautaro_lopez-drilling-telemetry-engine` |
| Sprint 1 | 24 ago – 18 sep 2026 |

## Estado del proyecto

**Fase actual:** foundation (gobernanza + SPEC + estructura de dominios).

| Entregable | Estado |
|------------|--------|
| `SPEC.md` (SSOT) | Listo |
| Cursor rules (`.cursor/rules/`) | Listo |
| ADR-001 stack tecnológico | Listo |
| Árbol modular `src/` + `tests/` | Listo |
| Tooling (`pyproject.toml`, CI) | Pendiente |
| Núcleo RK4 / UKF / SSI | Pendiente |
| Pipeline Redis + WebSocket | Pendiente |
| UI Three.js + LLM Advisor | Pendiente (P3) |

## Arquitectura (4 capas)

```text
Superficie 100 Hz ──┐
                    ├──► Ingest + Redis Streams ──► Physics Engine (RK4 + UKF + SSI)
MWD ~0.05 Hz ───────┘                                      │
                                                           ├──► FastAPI WebSocket ~60 FPS ──► Next.js / Three.js
                                                           └──► LLM Advisor (si SSI > 1.0) ──► SOP
```

Detalle: [`SPEC.md`](SPEC.md) · decisión de stack: [`docs/adr/ADR-001-stack-tecnologico.md`](docs/adr/ADR-001-stack-tecnologico.md)

## Stack

| Capa | Tecnología |
|------|------------|
| Núcleo | Python 3.12+, NumPy (RK4/UKF propios) |
| API / WS | FastAPI |
| Buffer | Redis Streams |
| UI | Next.js, Three.js, TypeScript strict |
| Calidad | mypy --strict, Ruff, pytest, Hypothesis, Bandit |

## Estructura

```text
src/engine/{physics,kalman,simulator}   # Physics Engine
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
| [`.cursor/rules/`](.cursor/rules/) | Enforcement por dominio |
| [`docs/auditoria/auditoria-sprint1.md`](docs/auditoria/auditoria-sprint1.md) | Auditoría crítica de código IA |
| [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) | Checklist de PR |

## Git Flow (obligatorio)

```text
feature/<tema>  →  PR → develop  →  PR → main
```

- Push directo a `main` y `develop` bloqueado.
- Commits convencionales: `feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `test:`.
- Un PR = un dominio siempre que sea posible.

## Desarrollo local

El scaffolding de dependencias se agrega en un paso posterior del Sprint 1. Cuando exista `pyproject.toml`:

```bash
# Calidad Python (esperado)
ruff check src tests
mypy --strict src
pytest --cov=src --cov-fail-under=85
bandit -r src -ll
```

Ver comandos y checklist completo en [`INSTRUCTIONS.md`](INSTRUCTIONS.md).

## Requerimientos funcionales (resumen)

- **RF-03…06** — Modelo Stribeck, RK4, UKF, SSI  
- **RF-01/02/10** — Ingest superficie + MWD + Redis Streams  
- **RF-08/09** — Broadcast WebSocket ~60 FPS + visualización 3D  
- **RF-07** — Advisor LLM si `SSI > 1.0`  
- **RF-11/12** — Cobertura ≥ 85%, Hypothesis, SAST, auditoría IA  

Lista completa y Non-Goals: [`SPEC.md` §1](SPEC.md).

## Licencia

Uso académico — PP3 IES 9-018 · Ciclo 2026.
