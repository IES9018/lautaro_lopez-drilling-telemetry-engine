# Resultados de ejecución de tests

**Fecha:** 2026-09-08 21:48 (UTC-3)  
**Commit:** `ce2b34e` — `test: e2e playwright, security suite y property hypothesis`  
**Rama:** `feature/test-round-complete`  
**Host:** Linux vivobook · Python 3.14.5 · Node v25.9.0 · Chromium (Playwright)

---

## Resumen ejecutivo

| Suite | Comando | Resultado | Duración |
|-------|---------|-----------|----------|
| Backend completo (pytest) | `.venv/bin/python -m pytest tests/ -q` | **154 passed**, 1 warning | ~12.0 s |
| Security + property | `.venv/bin/python -m pytest tests/security/ tests/property/ -q` | **26 passed**, 1 warning | ~2.3 s |
| UI unit (Vitest) | `cd src/ui && npm test` | **10 passed** (5 files) | ~2.4 s |
| UI E2E (Playwright) | `cd src/ui && npx playwright test` | **17 passed, 1 failed** (luego flake) | ~43.3 s |
| UI E2E retry SSI | `npx playwright test e2e/ssi-alert.spec.ts` | **3 passed** | ~17.3 s |

**Total estable (sin flake):** 154 + 10 + 18 = **182 tests** verdes en reintento del E2E afectado.

---

## 1. Backend — pytest

### Totales por carpeta (colección)

| Carpeta | Tests colectados |
|---------|------------------|
| `tests/unit/` | 90 |
| `tests/integration/` | 38 |
| `tests/security/` | 20 |
| `tests/property/` | 6 |
| **Total** | **154** |

### Resultado

```text
154 passed, 1 warning in 11.97s
```

**Warning:** `StarletteDeprecationWarning` — `httpx` con `starlette.testclient` deprecado; sugerencia instalar `httpx2` (no bloqueante).

### Security + property (subset)

```text
26 passed, 1 warning in 2.25s
```

Cubre:

- Escaneo de secretos hardcodeados / `os.environ` LLM / sin `eval`/`pickle` en pipeline
- Input hardening REST (extra fields, JSON inválido, `limit` fuera de rango)
- Headers / 500 sin traceback
- Hypothesis: SSI ≥ 0, Stribeck imparidad, RK4 ~orden 4, UKF P PSD

---

## 2. Frontend unit — Vitest

```text
Test Files  5 passed (5)
Tests       10 passed (10)
Duration    2.40s
```

| Archivo | Tests |
|---------|-------|
| `src/lib/wsEnvelope.test.ts` | 3 |
| `src/hooks/useTelemetryStream.test.ts` | 1 |
| `src/components/telemetry/SsiGauge.test.tsx` | 2 |
| `src/components/advisor/AdvisorFeed.test.tsx` | 2 |
| `src/components/telemetry/SimulationControls.test.tsx` | 2 |

---

## 3. Frontend E2E — Playwright (Chromium, puerto 3100)

### Primera corrida (suite completa)

```text
18 tests
17 passed
1 failed
~43.3s
```

**Fallo:**

| Spec | Error |
|------|--------|
| `e2e/ssi-alert.spec.ts` › *pushing CRITICAL after NORMAL updates the zone* | Esperaba `ssi-zone` = `CRITICAL`; permaneció en `NORMAL` (timeout 15 s). El bridge `__dtePushWs` no actualizó el gauge a tiempo (flake de timing / throttle 33 ms del stream). |

### Reintento aislado del archivo SSI

```text
e2e/ssi-alert.spec.ts — 3 passed in 17.3s
```

Incluye el caso *pushing CRITICAL after NORMAL* → **pasó** en el reintento. Se clasifica como **flake intermitente**, no regresión estable.

### Specs E2E (cobertura)

| Spec | Casos | Estado 1ª corrida |
|------|-------|-------------------|
| `dashboard.spec.ts` | 4 | OK |
| `simulation-controls.spec.ts` | 4 | OK |
| `ssi-alert.spec.ts` | 3 | 2 OK · 1 flake |
| `advisor-feed.spec.ts` | 3 | OK |
| `accessibility.spec.ts` | 4 | OK |

---

## 4. Conclusión

| Criterio | Veredicto |
|----------|-----------|
| Backend (unit/integration/security/property) | **Verde** — 154/154 |
| UI unit | **Verde** — 10/10 |
| UI E2E | **Verde con flake** — 17/18 en 1ª corrida; 18/18 tras reintento SSI |
| Bloqueante para merge | No — flake documentado (A-008 / throttle WS mock); CI con `retries: 1` mitiga |

### Acciones sugeridas (opcionales)

1. Endurecer el test flake: esperar `connection-badge` Live + `waitForTimeout(50)` antes de `pushTelemetry`, o desactivar throttle en modo test.
2. Sustituir `httpx` de TestClient por `httpx2` cuando Starlette lo exija.
3. Re-correr E2E en CI del PR #16 y adjuntar artifact si vuelve a fallar.

---

## 5. Comandos usados

```bash
.venv/bin/python -m pytest tests/ -q --tb=line
.venv/bin/python -m pytest tests/security/ tests/property/ -q --tb=line
cd src/ui && npm test
cd src/ui && npx playwright test --reporter=line
cd src/ui && npx playwright test e2e/ssi-alert.spec.ts --reporter=line
```

Referencia de estrategia: [`docs/testing.md`](testing.md).
