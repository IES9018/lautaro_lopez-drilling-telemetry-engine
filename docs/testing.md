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
| Property | `tests/property/` | Hypothesis: SSI, Stribeck, RK4 orden, UKF **PSD numérica** (`λ > -1e-8`, no PD estricta) |
| Unit UI | `src/ui/src/**/*.test.ts(x)` | Gauges, AdvisorFeed, hooks |
| E2E UI | `src/ui/e2e/` | Cada botón/panel del dashboard + a11y + i18n ES/EN |

## E2E Playwright

- Config: [`src/ui/playwright.config.ts`](../src/ui/playwright.config.ts)
- Helpers: mock REST + `WebSocket` bridge (`e2e/_helpers/mockApi.ts`)
- **No requiere FastAPI** en local/CI
- Puerto **3100** (evita colisión con otros servicios en `:3000`)
- Specs: `dashboard`, `simulation-controls`, `ssi-alert`, `advisor-feed`, `accessibility`

## CI

Jobs en [`.github/workflows/ci.yml`](../.github/workflows/ci.yml):

- `openapi-lint` — Spectral sobre OpenAPI
- `python-tests` — pytest completo + mypy
- `security-tests` — `tests/security/` + `tests/property/`
- `ui-build` — typecheck + build + Vitest
- `e2e-playwright` — `npx playwright test` (+ artifact report on failure)
- `js-budget` — RNF-03 shell JS gzip (`scripts/check-js-budget.sh`); **non-blocking** si excede 200 KB (WARN + exit 0; vigilancia Sprint 1)
- `lighthouse-mobile` — RNF-01/02; `continue-on-error: true` (modo warn)

## Auditoría

Hallazgos A-008…A-010 y nota PSD en A-003: [`docs/auditoria/auditoria-sprint1.md`](auditoria/auditoria-sprint1.md).

## Última corrida local

Resultados del 2026-09-08: [`docs/resultados-tests-2026-09-08.md`](resultados-tests-2026-09-08.md).
