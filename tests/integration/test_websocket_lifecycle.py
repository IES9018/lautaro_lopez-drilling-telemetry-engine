"""Tests del ciclo de vida WebSocket ``/ws/telemetry`` (envelope discriminado)."""

from __future__ import annotations

import json
import time

from fastapi.testclient import TestClient

from src.engine.simulator.well_generator import default_simulator_config
from src.pipeline.api.app import create_app
from src.pipeline.api.connection_manager import ConnectionManager
from src.pipeline.api.schemas.broadcast import TelemetryStreamBroadcastDTO
from src.pipeline.ingest.schema_validation import load_schema, validate_payload
from src.pipeline.orchestration.simulation_orchestrator import (
    OrchestratorConfig,
    SimulationOrchestrator,
)


def _make_app() -> tuple[TestClient, ConnectionManager, SimulationOrchestrator]:
    sim = default_simulator_config(seed=5, acoustic_delay_sec=20.0)
    orch = SimulationOrchestrator(
        config=OrchestratorConfig(
            simulator_config=sim,
            dt_surface=0.01,
            broadcast_fps=60.0,
        )
    )
    connections = ConnectionManager(queue_maxsize=2)
    app = create_app(orchestrator=orch, connections=connections)
    client = TestClient(app)
    return client, connections, orch


def _parse_ws_message(raw: dict[str, object]) -> dict[str, object] | None:
    if raw.get("bytes"):
        payload_obj: object = json.loads(raw["bytes"].decode("utf-8"))  # type: ignore[union-attr]
    elif raw.get("text"):
        payload_obj = json.loads(raw["text"])  # type: ignore[arg-type]
    else:
        return None
    if not isinstance(payload_obj, dict):
        return None
    return payload_obj


def test_websocket_receives_valid_broadcast_frames() -> None:
    client, connections, orch = _make_app()
    schema = load_schema("telemetry_stream_broadcast")
    with client:
        client.post("/api/v1/simulation/start", json={"preset": "normal"})
        with client.websocket_connect("/ws/telemetry") as ws:
            time.sleep(0.15)
            frames: list[dict[str, object]] = []
            for _ in range(10):
                raw = ws.receive()
                envelope = _parse_ws_message(raw)
                if envelope is None:
                    continue
                if envelope.get("type") != "telemetry_frame":
                    continue
                data = envelope.get("data")
                assert isinstance(data, dict)
                frames.append(data)
                validate_payload(data, schema)
                dto = TelemetryStreamBroadcastDTO.model_validate(data)
                assert dto.ssi >= 0.0
                assert dto.alert_level in ("normal", "warning", "critical")
                if len(frames) >= 3:
                    break
            assert len(frames) >= 1
            assert orch.latest_broadcast is not None
            ws.close()
        client.post("/api/v1/simulation/stop")
        time.sleep(0.05)
        assert len(connections) == 0


def test_disconnect_clears_connection_manager() -> None:
    client, connections, _orch = _make_app()
    with client:
        with client.websocket_connect("/ws/telemetry") as ws:
            assert len(connections) == 1
            ws.close()
        time.sleep(0.05)
        assert len(connections) == 0


def test_stop_halts_new_frame_ids() -> None:
    client, _connections, orch = _make_app()
    with client:
        client.post("/api/v1/simulation/start", json={})
        time.sleep(0.3)
        client.post("/api/v1/simulation/stop")
        time.sleep(0.15)
        frame_before = orch.latest_broadcast.frame_id if orch.latest_broadcast else 0
        time.sleep(0.2)
        frame_after = orch.latest_broadcast.frame_id if orch.latest_broadcast else 0
        assert frame_after == frame_before
        assert orch.is_running is False
