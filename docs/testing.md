# Estrategia de testing

Documentación operativa de la pirámide de pruebas (SPEC §5).

## Comandos rápidos

```bash
# Backend (154+ tests: unit + integration + security + property)
.venv/bin/python -m pytest tests/ -q

# Solo seguridad + property
.venv/bin/python -m pytest tests/security/ tests/property/ -q

# Frontend unit (Vitest)
cd src/ui && npm test

# Frontend E2E (Playwright — Chromium, puerto 3100, mocks REST/WS)
cd src/ui && npm run test:e2e
```

## Capas

| Capa | Ruta | Qué cubre |
|------|------|-----------|
| Unit Python | `tests/unit/` | Física, UKF, Advisor |
| Integration | `tests/integration/` | FastAPI REST/WS, buffer, contratos |
| Security | `tests/security/` | Secretos, hardening de input, headers/traceback |
| Property | `tests/property/` | Hypothesis: SSI, Stribeck, RK4 orden, UKF PSD |
| Unit UI | `src/ui/src/**/*.test.ts(x)` | Gauges, AdvisorFeed, hooks |
| E2E UI | `src/ui/e2e/` | Cada botón/panel del dashboard + a11y |

## E2E Playwright

- Config: [`src/ui/playwright.config.ts`](../src/ui/playwright.config.ts)
- Helpers: mock REST + `WebSocket` bridge (`e2e/_helpers/mockApi.ts`)
- **No requiere FastAPI** en local/CI
- Puerto **3100** (evita colisión con otros servicios en `:3000`)
- Specs: `dashboard`, `simulation-controls`, `ssi-alert`, `advisor-feed`, `accessibility`

## CI

Jobs en [`.github/workflows/ci.yml`](../.github/workflows/ci.yml):

- `python-tests` — pytest completo + mypy
- `security-tests` — `tests/security/` + `tests/property/`
- `ui-build` — typecheck + build + Vitest
- `e2e-playwright` — `npx playwright test` (+ artifact report on failure)

## Auditoría

Hallazgo **A-008** (puerto E2E / mock WS): [`docs/auditoria/auditoria-sprint1.md`](auditoria/auditoria-sprint1.md).

## Última corrida local

Resultados del 2026-09-08: [`docs/resultados-tests-2026-09-08.md`](resultados-tests-2026-09-08.md).
