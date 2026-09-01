# Arnés de agente IA (Cursor)

Equivalente al `.opencoderules` de OpenCode para este proyecto. La cátedra ADI acepta el arnés nativo de Cursor: **`.cursor/rules/*.mdc`** (formato moderno; `.cursorrules` en la raíz es legado).

Referencia institucional: [entornos-de-desarrollo.md](https://github.com/IES9018/proyecto-adi-2026/blob/main/entornos-de-desarrollo.md) · Runbook: [`INSTRUCTIONS.md`](../../INSTRUCTIONS.md) · SSOT: [`SPEC.md`](../../SPEC.md)

## Archivos del arnés

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

## Contenido mínimo ADI (tres secciones)

### Alcance permitido

- Escritura restringida por dominio (`governance.mdc`): Physics → `src/engine/**`, Pipeline → `src/pipeline/**`, Advisor → `src/advisor/**`, UI → `src/ui/**`, QA → `tests/**`, Docs → `docs/**`, `.github/**`, `.cursor/rules/**`.
- Un PR = un dominio (cross-domain solo con justificación).

### Estándares obligatorios

- Python: type hints completos, `mypy --strict` (`python-strict.mdc`).
- UI: TypeScript `strict` (`ui-digital-twin.mdc`).
- Tests: cobertura ≥85%, Hypothesis en física/UKF (`testing-qa.mdc`).
- Commits convencionales; Git Flow `feature/*` → `develop` → `main` (`governance.mdc`).

### Prohibiciones

- Código de relleno no alineado a `SPEC.md`.
- Cajas negras para RK4/UKF; `eval`/pickle sobre telemetría.
- Secretos hardcodeados; cambiar contratos sin actualizar `SPEC.md` / `docs/contratos/`.
- Dependencias o servicios externos sin ADR aprobado (arnés v2 — ADI TP2).
- Endpoints REST/WS sin entrada previa en `api-contracts.yaml` (arnés v3 — ADI TP4).
- Push directo a `main` / `develop`.
