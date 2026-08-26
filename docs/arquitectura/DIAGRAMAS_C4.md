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
