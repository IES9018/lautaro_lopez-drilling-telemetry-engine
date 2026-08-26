# INSTRUCTIONS.md — Runbook operativo de agentes

**Proyecto:** `lautaro_lopez-drilling-telemetry-engine`  
**Institución:** IES 9-018 · Práctica Profesionalizante III (PP3) · Ciclo 2026  
**Profesor:** Paulo Alvarez  
**Sprint 1:** 24 ago – 18 sep 2026  

Este documento es el runbook diario. Las restricciones duras viven en [`.cursor/rules/`](.cursor/rules/) (rules de Cursor). La especificación técnica SSOT vive en [`SPEC.md`](SPEC.md).

---

## 1. Árbol de carpetas

```
drilling-telemetry-engine/
├── .cursor/rules/                 # Cursor rules (enforcement por dominio)
├── INSTRUCTIONS.md                # Este runbook
├── SPEC.md                        # SSOT técnico
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/                 # ci.yml + security.yml
├── pyproject.toml                 # Tooling Python (mypy/ruff/pytest/bandit)
├── Dockerfile                     # Runtime FastAPI (cuando exista create_app)
├── docker-compose.yml             # api + redis
├── docs/
│   ├── adr/                       # Architecture Decision Records
│   ├── arquitectura/              # Diagramas
│   ├── auditoria/                 # Auditoría crítica de código IA
│   │   └── auditoria-sprint1.md
│   └── contratos/                 # JSON Schemas versionados
├── src/
│   ├── engine/                    # Physics Engine (Python)
│   │   ├── physics/               # Onda torsional, Stribeck, espacio de estados
│   │   ├── kalman/                # UKF
│   │   └── simulator/             # Integrador RK4 y escenarios
│   ├── pipeline/                  # Ingest / Buffer / API (Python)
│   │   ├── ingest/
│   │   ├── buffer/
│   │   └── api/
│   ├── advisor/                   # LLM Advisor (Python)
│   │   └── prompts/
│   └── ui/                        # Gemelo digital (Next.js / Three.js — TypeScript)
├── tests/
│   ├── unit/
│   ├── property/                  # Hypothesis
│   └── integration/
```

Notas:

- `src/ui/` **no** es paquete Python (sin `__init__.py`); es frontend TypeScript.
- `docs/arquitectura/` y `docs/contratos/` pueden usar `.gitkeep` hasta que haya artefactos.

---

## 2. Git Flow (obligatorio)

```
feature/<tema>  →  PR → develop  →  PR → main
```

- Push directo a `main` y `develop`: **prohibido**.
- Features abren PR **siempre** contra `develop`.
- Solo un PR de release (`develop` → `main`) cierra el sprint o un hito estable.

### Convención de ramas

| Patrón | Dominio | Ejemplo |
|--------|---------|---------|
| `feature/physics-<tema>` | Physics Engine | `feature/physics-rk4-integrator` |
| `feature/kalman-<tema>` | UKF | `feature/kalman-ukf-sigma-points` |
| `feature/pipeline-<tema>` | Data Pipeline | `feature/pipeline-redis-ingest` |
| `feature/advisor-<tema>` | LLM Advisor | `feature/advisor-ssi-trigger` |
| `feature/ui-<tema>` | Digital Twin UI | `feature/ui-torsional-mesh` |
| `feature/test-<tema>` | QA | `feature/test-rk4-convergence` |
| `feature/docs-<tema>` | Audit/Docs | `feature/docs-sprint1-audit` |
| `fix/<tema>` | Hotfix vía develop | `fix/ukf-covariance-psd` |

### Commits convencionales

Usar únicamente: `feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `test:`.

Ejemplos:

```text
feat: implement RK4 step for lumped torsional string
test: add Hypothesis invariants for energy conservation
docs: register AI hallucination fix on Stribeck exponent
```

---

## 3. Dominios de agentes (uso diario)

| Label sugerido | Agente | Escribe en | Lee |
|----------------|--------|------------|-----|
| `domain:physics` | Physics Engine Agent | `src/engine/**` | `SPEC.md`, `tests/` (solo lectura) |
| `domain:pipeline` | Data Pipeline Agent | `src/pipeline/**` | contratos, SPEC |
| `domain:advisor` | Advisor/LLM Agent | `src/advisor/**` | eventos SSI, SPEC |
| `domain:ui` | Digital Twin/Frontend Agent | `src/ui/**` | contratos WebSocket |
| `domain:qa` | QA/Testing Agent | `tests/**` | todo el repo |
| `domain:docs` | Audit/Docs Agent | `docs/**`, `.github/**` | todo el repo |

**Regla:** un PR = un dominio. Cross-domain solo con justificación y aprobación del alumno.

Mapeo Sprint 1 (issues):

| Prioridad Sprint 1 | Dominio | Entregable típico |
|--------------------|---------|-------------------|
| P0 | docs | Gobernanza, SPEC, plantillas (este entregable) |
| P1 | physics | Modelo de espacio de estados + RK4 |
| P1 | kalman/physics | UKF + SSI |
| P2 | pipeline | Ingest + buffer Redis Streams |
| P2 | pipeline/api | Broadcast WebSocket 60 FPS |
| P3 | ui | Visualización torsional 3D |
| P3 | advisor | Trigger SSI > 1.0 → SOP |
| Continuo | qa | Cobertura ≥ 85%, Hypothesis, estabilidad numérica |

---

## 4. Checklist previo a abrir un PR

Completar **antes** de solicitar revisión:

1. **Rama:** `feature/<tema>` desde `develop` actualizado.
2. **Dominio:** un solo dominio (o cross-domain justificado).
3. **Lint:** sin errores (`ruff` / ESLint según stack).
4. **Tipado:** `mypy --strict` (Python) y/o `tsc --noEmit` (UI) sin errores.
5. **Tests:** `pytest` verde; cobertura de producción ≥ **85%**.
6. **Property tests:** si toca física/UKF/contratos, Hypothesis actualizado.
7. **Estabilidad numérica:** si toca RK4/UKF, tests de orden/PSD presentes.
8. **Secretos:** ningún credential en el diff.
9. **SAST:** Bandit (y Semgrep si aplica) sin hallazgos críticos.
10. **Auditoría IA:** si hubo generación de fórmulas/constantes, fila en [`docs/auditoria/auditoria-sprint1.md`](docs/auditoria/auditoria-sprint1.md).
11. **SPEC:** cambios de contrato o modelo reflejados en `SPEC.md` y `docs/contratos/`.
12. **Plantilla de PR:** checklist de [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) completa.

---

## 5. Tooling y CI local

Instalación editable (Python 3.11–3.12):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Calidad / tests (equivalente a `.github/workflows/ci.yml`)

```bash
ruff check src tests
ruff format --check src tests
mypy
pytest                      # unit + integration + property; gate cov >= 85%
pytest tests/property -q
bandit -r src -ll           # equivalente a security.yml
```

Frontend (solo si existe `src/ui/package.json`; el job CI es condicional):

```bash
cd src/ui && npm ci && npm run typecheck && npm test && npm run build
```

### Docker Compose

```bash
# Redis ya usable (pipeline consumirá REDIS_URL más adelante)
docker compose up redis

# API: requiere src.pipeline.api.app:create_app (dominio pipeline)
docker compose up --build api
```

Semillas y determinismo:

- Tests numéricos: `numpy.random.default_rng(seed)` con seed fija documentada.
- No depender de relojes de sistema en aserciones (inyectar reloj / timestamps sintéticos).

---

## 6. Flujo recomendado por agente

### Physics Engine Agent

1. Leer sección de modelo físico en `SPEC.md`.
2. Implementar solo en `src/engine/{physics,kalman,simulator}/`.
3. Pedir al QA Agent (o crear en el mismo PR de dominio physics si es mínimo) tests de unidad + Hypothesis + convergencia.
4. Registrar cualquier corrección de fórmula en auditoría.

### Data Pipeline Agent

1. Alinear payloads a JSON Schema de `SPEC.md` / `docs/contratos/`.
2. Validar en ingest; no confiar en MWD crudo.
3. Redis Streams + API/WebSocket sin tocar el núcleo físico.

### QA/Testing Agent

1. Leer código de producción; **escribir solo** en `tests/`.
2. Mantener invariantes: energía (sin fricción), límites físicos, PSD de covarianza UKF.
3. Fallar el job si cobertura < 85%.

### Audit/Docs Agent

1. Mantener `SPEC.md`, contratos, PR template y `auditoria-sprint1.md`.
2. No introducir lógica ejecutable en `src/`.

---

## 7. Referencias cruzadas

| Documento | Rol |
|-----------|-----|
| [`.cursor/rules/`](.cursor/rules/) | Enforcement Cursor: dominios, tipado, Git Flow, cajas negras |
| [`SPEC.md`](SPEC.md) | SSOT: física, arquitectura, contratos, testing, riesgos |
| [`docs/auditoria/auditoria-sprint1.md`](docs/auditoria/auditoria-sprint1.md) | Registro de alucinaciones / correcciones IA |
| [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) | Checklist de merge |

---

## 8. Evaluación (rúbrica institucional)

| Criterio | Peso |
|----------|------|
| Implementación / Calidad | 40% |
| Testing | 20% |
| Seguridad (SAST) | 15% |
| Gestión (Git / PRs) | 15% |
| Documentación / Auditoría crítica de IA | 10% |

Todo trabajo de agentes debe ser auditable frente a esta rúbrica.
