# Diagramas C4 — Drilling Telemetry Engine (Sprint 1)

**SSOT:** [`SPEC.md`](../../SPEC.md) · **Auditoría:** [`docs/auditoria/auditoria-sprint1.md`](../auditoria/auditoria-sprint1.md)

Este documento describe el flujo de datos de **streaming e ingesta** (`src/pipeline/`) y su relación con el Physics Engine.

---

## 1. Contexto (C4 nivel 1)

```mermaid
flowchart TB
  operator[DrillingEngineer]
  twin[DigitalTwinUI_NextThree]
  system[DrillingTelemetryEngine]
  synth[SyntheticWellSimulator]
  operator -->|monitor SSI alerts| twin
  twin -->|WebSocket 60FPS| system
  operator -->|REST start stop preset| system
  synth -->|surface 100Hz + MWD delayed| system
  system -->|broadcast.state.v1| twin
```

---

## 2. Contenedores (C4 nivel 2)

```mermaid
flowchart LR
  subgraph engine [PhysicsEngine]
    sim[WellSimulator]
    ukf[UnscentedKalmanFilter]
    ssi[SSICalculator]
  end
  subgraph pipeline [DataPipeline]
    ingest[SchemaValidation_Pydantic]
    buf[TimeSyncBuffer_fixedLag]
    orch[SimulationOrchestrator]
    api[FastAPI_WebSocket]
  end
  sim -->|SurfaceTelemetrySample| ingest
  sim -->|MwdTelemetrySample| orch
  ingest --> orch
  orch --> ukf
  ukf --> buf
  orch -->|MWD OOSM replay| buf
  ukf --> ssi
  ssi --> api
  orch --> api
```

**Nota de alcance (Sprint 1):** Redis Streams (RF-10) queda diferido; el buffer en memoria `deque` cubre la sincronización temporal MWD↔superficie para el fixed-lag smoothing.

---

## 3. Flujo de streaming (detalle)

```mermaid
flowchart LR
  WS100["WellSimulator step 100Hz"] --> SURF["surface telemetry + ruido"]
  WS100 --> MWDQ["cola MWD retardo acustico"]
  SURF --> ORC["SimulationOrchestrator"]
  MWDQ -->|"origin_time + delay <= now"| ORC
  ORC --> UKFP["UKF predict/update superficie"]
  UKFP --> BUF["TimeSyncBuffer journal"]
  MWDQ --> REPLAY["fixed-lag replay UKF efimero"]
  BUF --> REPLAY
  REPLAY -->|"swap corregido"| UKFP
  UKFP --> SSI["compute_ssi ventana omega_bit"]
  SSI --> STATE["TelemetryStreamBroadcastDTO"]
  STATE --> CM["ConnectionManager 60 FPS"]
  CM --> CLIENTS["Clientes WebSocket"]
  REST["REST /api/v1/simulation"] --> ORC
```

### Tasas

| Camino | Tasa | Contrato |
|--------|------|----------|
| Física / superficie | 100 Hz (`dt=0.01 s`) | `surface.telemetry.v1` |
| MWD | ~0.05 Hz + retardo 15–45 s | `mwd.telemetry.v1` |
| Broadcast gemelo | ~60 FPS | `broadcast.state.v1` |

### Contratos materializados

- [`docs/contratos/surface_telemetry.json`](../contratos/surface_telemetry.json)
- [`docs/contratos/mwd_telemetry.json`](../contratos/mwd_telemetry.json)
- [`docs/contratos/telemetry_stream_broadcast.json`](../contratos/telemetry_stream_broadcast.json)

### Backpressure WebSocket

Cada cliente tiene una `asyncio.Queue` acotada (`maxsize=2`, política *drop-oldest*). Un cliente lento no bloquea el broadcast ni acumula memoria ilimitada.

### Envelope WebSocket (wire format)

Los mensajes en `/ws/telemetry` usan un envelope discriminado:

```json
{"type": "telemetry_frame", "data": { /* broadcast.state.v1 */ }}
{"type": "advisor_recommendation", "data": { /* AdvisorRecommendationRecordDTO */ }}
```

---

## 4. Advisor LLM (Capa 4)

```mermaid
flowchart LR
  ORC["SimulationOrchestrator._refresh_broadcast"] -->|"ssi, regime, rpm, torque"| SNAP["AdvisorIncidentSnapshot"]
  SNAP --> ADV["DrillingAdvisor.evaluate_telemetry"]
  ADV -->|"cooldown ok"| SOP["drilling_sop prompts"]
  SOP --> PROV["LLMProviderProtocol.generate"]
  PROV --> ADV
  ADV -->|"AdvisorRecommendation valida"| HIST["AdvisorHistoryStore"]
  HIST --> REST["GET /api/v1/advisor/recommendations"]
  ADV --> BCAST["ConnectionManager.broadcast_advisor"]
  BCAST --> WS["/ws/telemetry envelope advisor_recommendation"]
  ADV -->|"suprimido o error"| NONE["None sin bloquear loop 100Hz"]
```

| Pieza | Rol |
|-------|-----|
| `src/advisor/schemas.py` | Snapshot / Recommendation tipados + límites seguros |
| `src/advisor/prompts/drilling_sop.py` | System/user prompts SOP + `sanitize_numeric` |
| `src/advisor/llm_diagnostics.py` | `DrillingAdvisor` + mock/adaptadores LLM |
| `src/pipeline/api/advisor_store.py` | Historial REST |
| Trigger | `SSI > 1.0`, fire-and-forget + cooldown 30 s |

El Advisor **no** bloquea el lazo RK4/UKF: se dispara con `asyncio.create_task` desde el tick de broadcast.
