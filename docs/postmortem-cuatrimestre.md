# Postmortem lite — cuatrimestre ADI 2026

**Proyecto:** `lautaro_lopez-drilling-telemetry-engine`  
**Alumno:** lautaro_lopez · IES 9-018 · Prof. Paulo Alvarez  
**Período:** TP1–TP6 (ago–nov 2026)  
**Evidencia ampliada:** [`docs/auditoria/auditoria-sprint1.md`](auditoria/auditoria-sprint1.md)

---

## Tabla de incidentes con IA (≥ 3)

| # | Incidente | Qué generó mal la IA | Cómo se detectó | Qué capa lo previene a futuro | Evidencia |
|---|-----------|----------------------|-----------------|------------------------------|-----------|
| 1 | **UKF `update` reutiliza sigma points propagados** sin regenerar desde \((x^-,P^-)\) | El agente Physics eligió reuso Van der Merwe sin documentar; riesgo de covarianza no PSD si se mezcla con otra variante | Tests `test_predict_preserves_symmetry_and_psd`, `test_consistency_error_within_three_sigma` + revisión humana contra SPEC §2.5 | **SPEC** §2.5 + **auditoría** A-003 + **arnés** physics-engine (sin caja negra) + **CI** pytest | [auditoria A-003](auditoria/auditoria-sprint1.md#a-003) · `tests/unit/test_ukf_estimator.py` |
| 2 | **Re-render React a 60 FPS** en dashboard (gauges + 3D) | UI agent montó estado React por frame WS saturando main thread | Revisión humana de arquitectura cliente + Vitest `useTelemetryStream` + auditoría A-007 | **ADR-004** stack UI + **arnés** ui-digital-twin + **tests** Vitest en CI | [auditoria A-007](auditoria/auditoria-sprint1.md#a-007) · commits UI en `src/ui/` |
| 3 | **OpenAPI `preset` nullable junto a `$ref`** inválido para Redocly | Al generar `api-contracts.yaml` en TP4, la IA usó `nullable` como sibling de `$ref` | **Lint OpenAPI** (`@redocly/cli`) — error `nullable-type-sibling` antes del merge | **Arnés v3** API-first + **CI** job `openapi-lint` + **SPEC** §1.4 | Commit [644ce2a](https://github.com/IES9018/lautaro_lopez-drilling-telemetry-engine/commit/644ce2a) · PR [#13](https://github.com/IES9018/lautaro_lopez-drilling-telemetry-engine/pull/13) |
| 4 | **Dependencia Redis / tooling sin ADR** propuesta en rama infra | Agente infra añadió `pyproject.toml`, Docker, Redis compose sin ADR-003 actualizado en el mismo PR | Revisión humana gobernanza v2 (TP2): regla anti-deps sin ADR | **Arnés v2** governance.mdc + **ADR-003** buffer in-memory + **SPEC** ARCH-05 | Rama `feature/infra-tooling-and-property-tests` (no mergeada a main; RF-10 diferido) |
| 5 | **Advisor acoplado al tick 100 Hz** (latencia LLM bloqueante) | IA inicial conectó llamada LLM síncrona al loop físico | Diseño event-driven + tests debounce; auditoría A-006 | **ADR-002** capas + **arnés** advisor-llm + **tests** `test_advisor.py` | [auditoria A-006](auditoria/auditoria-sprint1.md#a-006) · `tests/integration/test_advisor_api.py` |

---

## Docker — Non-Goal justificado

**No Dockerfile en v0.1.0.** Desarrollo local con venv + `npm ci`; CI instala deps en runner. Docker multi-stage quedó en rama infra no mergeada. **Condición de reapertura:** despliegue PP3 Sprint 3 en contenedor único API+UI.

---

## Reflexión (5 líneas)

Arrancaría con **SPEC + OpenAPI vacío** el mismo día uno, no después del código: el incidente OpenAPI y los endpoints “imaginados” costaron un PR entero. **CI mínimo** (lint contrato + pytest) en TP1 habría atrapado regresiones antes de acumular 128 tests. Consolidar **un solo arnés** (`.opencoderules`) temprano reduce reglas duplicadas entre TP1–TP4. Para física/UKF, **test de invariante antes de merge** es más barato que auditoría posterior. La IA acelera scaffolding pero **no sustituye** la trazabilidad ADR ↔ SPEC ↔ CI; el postmortem es la evidencia de ese proceso.

---

*Postmortem lite · ADI TP6 · v0.1.0*
