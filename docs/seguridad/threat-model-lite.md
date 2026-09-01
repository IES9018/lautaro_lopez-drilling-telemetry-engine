# Threat model lite — STRIDE sobre API pública

**Proyecto:** Drilling Telemetry Engine · ADI TP4  
**Alcance:** 5 endpoints críticos en [`api-contracts.yaml`](../arquitectura/api-contracts.yaml)  
**Metodología:** STRIDE simplificada (Spoofing, Tampering, Repudiation, Information disclosure, Denial of Service, Elevation of privilege)

**Personas de ataque consideradas:** operador no autorizado en red de rig, script automatizado externo, insider con token robado, agente IA que genera endpoints sin contrato.

---

## Superficie de ataque

| # | Endpoint | Método | Datos sensibles |
|---|----------|--------|-----------------|
| E1 | `/ws/telemetry` | WebSocket | Estado UKF, SSI, alertas, SOP |
| E2 | `/api/v1/simulation/start` | POST | Control del simulador |
| E3 | `/api/v1/simulation/stop` | POST | Control del simulador |
| E4 | `/api/v1/simulation/preset` | POST | Escenario stick-slip |
| E5 | `/api/v1/advisor/recommendations` | GET | Historial SOP / snapshot operativo |

Auth declarada: `BearerAuth` JWT en OpenAPI. **Sprint 1:** enforcement parcial (WS público en dev); mitigaciones abajo incluyen roadmap PP3.

---

## Tabla de amenazas

| ID | STRIDE | Amenaza concreta | Endpoint(s) | Mitigación | Dónde se aplica |
|----|--------|------------------|-------------|------------|-----------------|
| T-01 | **Spoofing** | Cliente WS sin identidad se conecta a `/ws/telemetry` y recibe telemetría operativa como si fuera operador legitimo | E1 | JWT en handshake (query `token` o cookie) + validación en `ConnectionManager.connect`; rechazar sin credencial en prod | `src/pipeline/api/connection_manager.py` · middleware FastAPI · regla arnés secrets |
| T-02 | **Tampering** | Body malicioso en `POST /simulation/preset` con `preset` fuera de enum o campos extra para explotar deserialización | E4, E2 | `additionalProperties: false` en OpenAPI; Pydantic `extra=forbid` en `SetPresetRequestDTO` / `StartSimulationRequestDTO`; 400 en borde | `api-contracts.yaml` schemas · `src/pipeline/api/schemas/requests.py` · arnés validación borde |
| T-03 | **Repudiation** | Operador detiene simulación durante incidente y no queda trazabilidad de quién ejecutó Stop | E3 | Log estructurado con `user_id` del JWT, timestamp, IP en cada POST simulation; correlación con `frame_id` | Middleware auth + logger pipeline · Sprint 2 audit log |
| T-04 | **Information disclosure** | `GET /advisor/recommendations?limit=200` expone historial SOP completo a usuario sin rol supervisor | E5 | JWT con claim `role`; autorización por endpoint; default `limit=50`; 401 sin token en prod | Router `advisor.py` · OpenAPI `security: BearerAuth` |
| T-05 | **Denial of Service** | Flood de conexiones WS o POST start/stop sin rate limit satura loops `physics-loop` / `broadcast-loop` | E1, E2, E3 | Límite conexiones por IP en `ConnectionManager`; rate limit REST (ej. slowapi); timeout en WS idle | `connection_manager.py` · capa API · infra futura (reverse proxy) |
| T-06 | **Elevation** | Token JWT de solo lectura (monitor) usado para `POST /simulation/start` y alterar estado del pozo simulado | E2, E4 | Claims `scopes: simulation:write` vs `telemetry:read`; dependency FastAPI `require_scope` | Middleware auth Sprint 2 · documentado en OpenAPI scopes futuro |
| T-07 | **Tampering** | Inyección en query `limit` negativo o enorme para forzar cómputo O(n) en historial | E5 | OpenAPI `minimum: 1`, `maximum: 200`; FastAPI `Query(ge=1, le=200)` ya aplicado | `src/pipeline/api/routers/advisor.py` línea `limit` |
| T-08 | **Information disclosure** | Error 500 con stack trace Python hacia cliente REST | E2–E5 | Handler global devuelve `ErrorResponse` genérico; detalle solo en logs servidor | FastAPI exception handlers · RF-12 |

*(Tabla incluye 8 amenazas; consigna exige ≥ 5.)*

---

## Mitigaciones transversales (arnés v3)

| Regla arnés | Amenazas cubiertas |
|-------------|-------------------|
| PROHIBIDO hardcodear secrets/tokens | T-01, T-04, T-06 |
| OBLIGATORIO validar/sanear entrada en borde | T-02, T-07 |
| OBLIGATORIO endpoint nuevo en `api-contracts.yaml` primero | Evita superficie desconocida (todas) |

Ubicación: [`.cursor/rules/governance.mdc`](../../.cursor/rules/governance.mdc) (equivalente institucional a `.opencoderules`).

---

## Gaps aceptados Sprint 1

| Gap | Razón | Plan |
|-----|-------|------|
| JWT no enforced en dev | NG-08 MVP académico | Sprint 2 + evaluación Seguridad 15% |
| Sin rate limit global | Prioridad núcleo físico | ADR + middleware antes de demo PP3 |
| WS sin backpressure contractual | Drop-oldest en cola ya implementado | Documentado en `ConnectionManager` |

---

## Trazabilidad journeys TP3

| Journey | Endpoints expuestos | Amenazas principales |
|---------|---------------------|----------------------|
| Monitoreo continuo | E1 | T-01, T-05, T-08 |
| Respuesta stick-slip + SOP | E2, E3, E4, E5, E1 | T-02, T-03, T-04, T-06 |

---

*Threat model lite · ADI TP4 · Revisar al cambiar `api-contracts.yaml`*
