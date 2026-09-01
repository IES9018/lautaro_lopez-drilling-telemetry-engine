# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/es/1.1.0/). Versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Added

- Nada pendiente para v0.1.0.

## [0.1.0] - 2026-08-31

Primera release académica congelada para defensa ADI / baseline PP3 Sprint 1.

### Added

- **Physics:** Stribeck regularizado, RK4, drillstring FEM lumped, UKF (sigma points Van der Merwe), SSI, `well_generator` con retardo MWD.
- **Pipeline:** FastAPI REST + WebSocket ~60 FPS, `TimeSyncBuffer`, orquestador simulación, validación JSON Schema.
- **Advisor:** LLM Advisor event-driven (mock determinista), SOP estructurado, historial REST.
- **UI:** Gemelo digital Next.js 15 + R3F, gauges SSI/RPM, `AdvisorFeed`, controles simulación.
- **Docs ADI:** SPEC v1→v6, ADR-001…006, C4, personas/journeys/wireframes (desktop + móvil), OpenAPI `api-contracts.yaml`, threat model, presupuestos RNF, postmortem.
- **Gobernanza:** Arnés Cursor (`.cursor/rules/`) + `.opencoderules` vFinal, auditoría A-001…A-007.
- **CI:** GitHub Actions — OpenAPI lint, pytest (128+), mypy strict, UI build/test, JS budget, Lighthouse móvil (opcional).

### Changed

- SPEC evolucionó por TP1–TP6 (RF, arquitectura, Gherkin UI, API-first, RNF mobile, congelado defensa).

### Security

- Threat model lite STRIDE; arnés v3 (secrets, validación borde, API-first).
- Bandit en pipeline `security.yml`.

[Unreleased]: https://github.com/IES9018/lautaro_lopez-drilling-telemetry-engine/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/IES9018/lautaro_lopez-drilling-telemetry-engine/releases/tag/v0.1.0
