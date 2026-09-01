# Arquitectura — documentación

Diagramas C4, contratos API y modelo matemático del Drilling Telemetry Engine.

## Contrato OpenAPI (API-first — ADI TP4)

| Artefacto | Ubicación |
|-----------|-----------|
| OpenAPI 3.0.3 | [`api-contracts.yaml`](api-contracts.yaml) |
| Implementación FastAPI | `src/pipeline/api/` |
| SSOT declarativo | [`SPEC.md`](../../SPEC.md) §1.4 y §4 |

### Validación del contrato (obligatorio antes del PR)

```bash
npx --yes @redocly/cli lint docs/arquitectura/api-contracts.yaml
```

El archivo debe pasar sin errores. Alternativa con Docker:

```bash
docker run --rm -v "$PWD/docs/arquitectura:/work" redocly/cli lint api-contracts.yaml
```

### Endpoints críticos (5 — journeys TP3)

| # | Operación | Journey |
|---|-----------|---------|
| 1 | `GET /ws/telemetry` (WebSocket) | Monitoreo continuo gemelo 3D |
| 2 | `POST /api/v1/simulation/start` | Arranque demo stick-slip |
| 3 | `POST /api/v1/simulation/stop` | Mitigación / pausa demo |
| 4 | `POST /api/v1/simulation/preset` | Selección escenario |
| 5 | `GET /api/v1/advisor/recommendations` | Lectura SOP tras alerta |

**Regla de cambio:** primero `api-contracts.yaml`, luego código (arnés v3 en `.cursor/rules/governance.mdc`).

## Otros documentos

| Documento | Descripción |
|-----------|-------------|
| [`C4-contexto.md`](C4-contexto.md) | Vista de contexto |
| [`C4-contenedores.md`](C4-contenedores.md) | Vista de contenedores |
| [`DIAGRAMAS_C4.md`](DIAGRAMAS_C4.md) | Índice C4 |
| [`MODELO_MATEMATICO.md`](MODELO_MATEMATICO.md) | FEM, SSI, UKF |
| [`presupuestos-rendimiento.md`](presupuestos-rendimiento.md) | RNF LCP/INP/JS (ADI TP5) |
| [`lighthouserc.mobile.json`](lighthouserc.mobile.json) | Config Lighthouse CI móvil |
| [`offline-sync.md`](offline-sync.md) | Non-Goal offline (ADI TP5) |
