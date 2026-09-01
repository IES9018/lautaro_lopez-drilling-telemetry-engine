## Metadata

- **Título del PR:**
- **Dominio afectado:** `physics` | `pipeline` | `advisor` | `ui` | `qa` | `docs` | `cross-domain`
- **Issue / ticket vinculado:**
- **Sprint:** Sprint 1 (24 ago – 18 sep 2026)
- **Tipo de commit convencional predominante:** `feat` | `fix` | `docs` | `ci` | `chore` | `test`
- **Base branch:** `develop` (features) / `main` (solo release `develop` → `main`)

## Resumen

<!-- Qué cambia y por qué. Remitir a SPEC.md si afecta modelo, contratos o arquitectura. -->

## Checklist de calidad

- [ ] Lint sin errores (`ruff` / ESLint según dominio)
- [ ] Tipado estricto sin errores (`mypy --strict` y/o `tsc --noEmit`)
- [ ] Sin `# type: ignore` / `@ts-ignore` no justificados
- [ ] Sin código de relleno superfluo; alineado a `SPEC.md`
- [ ] Sin cajas negras físicas (RK4/UKF propios si aplica)

## Checklist de testing

- [ ] `pytest` pasa en local
- [ ] Cobertura de producción **≥ 85%** (`pytest-cov`)
- [ ] Tests unitarios actualizados / agregados
- [ ] Property tests (Hypothesis) si toca física, UKF, SSI o schemas
- [ ] Tests de estabilidad numérica si toca RK4 o UKF
- [ ] Tests de integración si toca ingest / buffer / API / WebSocket

## Checklist de seguridad (SAST)

- [ ] Bandit (y Semgrep si aplica) sin hallazgos **críticos**
- [ ] Sin secretos, API keys ni credenciales en el diff
- [ ] Payloads validados contra JSON Schema (`SPEC.md` / `docs/contratos/`)
- [ ] Si toca Advisor: prompts sin concatenar telemetría cruda no validada
- [ ] Dependencias nuevas auditadas (licencia + vulnerabilidades)

## Checklist de gestión (Git Flow)

- [ ] Rama `feature/<tema>` (o `fix/<tema>`) correcta
- [ ] PR apunta a la base correcta (`develop` para features / `main` para entregas ADI)
- [ ] No hay push directo a `main` ni `develop`
- [ ] Un dominio por PR (o cross-domain justificado abajo)
- [ ] Commits convencionales (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `test:`)
- [ ] **CI verde en el PR** — merge a `main` prohibido con pipeline rojo (`.github/workflows/ci.yml`)

### Justificación cross-domain (si aplica)

<!-- Obligatorio si el PR toca más de un dominio según .cursor/rules/ -->

## Checklist de auditoría de IA

- [ ] Este PR **incluye** código generado o asistido por IA
- [ ] Si incluye fórmulas / constantes / convergencia: registrado en `docs/auditoria/auditoria-sprint1.md`
- [ ] Ecuaciones contrastadas manualmente contra `SPEC.md`
- [ ] N/A — sin generación de IA en este PR

## Evidencia

<!-- Pegar salidas relevantes: cobertura, bandit, mypy, capturas, etc. -->

## Riesgos residuales

<!-- Qué queda pendiente o qué puede romperse -->
