# Arnés de agente IA (Cursor)

Equivalente al `.opencoderules` de OpenCode para este proyecto. La cátedra ADI acepta el arnés nativo de Cursor: **`.cursor/rules/*.mdc`** (formato moderno; `.cursorrules` en la raíz es legado).

**Arnés consolidado vFinal (ADI TP6):** [`.opencoderules`](../../.opencoderules) — alcance, estándares, prohibiciones, proceso y ADRs en un solo archivo.

Referencia institucional: [entornos-de-desarrollo.md](https://github.com/IES9018/proyecto-adi-2026/blob/main/entornos-de-desarrollo.md) · Runbook: [`INSTRUCTIONS.md`](../../INSTRUCTIONS.md) · SSOT: [`SPEC.md`](../../SPEC.md) v6.0.0

## Archivos del arnés (Cursor — por dominio)

| Archivo | Rol |
|---------|-----|
| [`governance.mdc`](governance.mdc) | Siempre activo — SSOT, Git Flow, dominios, prohibiciones globales |
| [`python-strict.mdc`](python-strict.mdc) | Tipado `mypy --strict` en Python |
| [`physics-engine.mdc`](physics-engine.mdc) | RK4/UKF/FEM — sin cajas negras |
| [`data-pipeline.mdc`](data-pipeline.mdc) | Ingest, buffer, API, contratos |
| [`advisor-llm.mdc`](advisor-llm.mdc) | Advisor event-driven, SOP |
| [`ui-digital-twin.mdc`](ui-digital-twin.mdc) | Next.js / R3F / TypeScript strict |
| [`testing-qa.mdc`](testing-qa.mdc) | Cobertura ≥85%, Hypothesis, invariantes |
| [`docs-audit.mdc`](docs-audit.mdc) | SPEC, ADRs, auditoría IA |

## Resumen vFinal (sin duplicar `.opencoderules`)

### Alcance permitido

- Escritura restringida por dominio (`governance.mdc`).
- Un PR = un dominio (cross-domain solo con justificación).

### Estándares obligatorios

- Python: `mypy --strict` · UI: TypeScript `strict` · Tests: pytest + CI verde.
- OpenAPI lint en CI · API-first antes de código.

### Prohibiciones

- Ver sección 3 de [`.opencoderules`](../../.opencoderules) (secrets, cajas negras, deps sin ADR, CI rojo en merge).

### Proceso

- Git Flow · CHANGELOG · tag SemVer · postmortem en `docs/postmortem-cuatrimestre.md`.
