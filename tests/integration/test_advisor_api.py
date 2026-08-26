"""Tests de integración Advisor ↔ API / WebSocket."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from src.advisor.llm_diagnostics import DeterministicMockLLMProvider, DrillingAdvisor
from src.advisor.schemas import AdvisorIncidentSnapshot
from src.engine.simulator.well_generator import default_simulator_config
from src.pipeline.api.app import create_app
from src.pipeline.api.advisor_store import AdvisorHistoryStore
from src.pipeline.api.connection_manager import ConnectionManager
from src.pipeline.orchestration.simulation_orchestrator import (
    OrchestratorConfig,
    SimulationOrchestrator,
)


def _critical_snapshot() -> AdvisorIncidentSnapshot:
    return AdvisorIncidentSnapshot(
        timestamp=datetime(2026, 8, 25, 12, 0, 1, tzinfo=UTC),
        surface_rpm=120.0,
        estimated_bit_rpm=5.0,
        wob_kn=90.0,
        ssi=1.8,
        regime="critical",
        torque_contrast=4.0,
    )


def _make_client() -> tuple[TestClient, SimulationOrchestrator, AdvisorHistoryStore]:
    sim = default_simulator_config(seed=11, acoustic_delay_sec=20.0)
    store = AdvisorHistoryStore()
    advisor = DrillingAdvisor(
        provider=DeterministicMockLLMProvider(),
        cooldown_sec=0.0,
    )
    orch = SimulationOrchestrator(
        config=OrchestratorConfig(
            simulator_config=sim,
            dt_surface=0.01,
            broadcast_fps=60.0,
            ssi_window_size=50,
            u_top_rpm=120.0,
            wob_kn=100.0,
        ),
        advisor=advisor,
        advisor_store=store,
    )
    orch.set_preset("severe_stick_slip")
    connections = ConnectionManager(queue_maxsize=4)
    orch.connections = connections
    app = create_app(
        orchestrator=orch,
        connections=connections,
        advisor=advisor,
        advisor_store=store,
    )
    return TestClient(app), orch, store


def test_recommendations_endpoint_after_critical_ssi() -> None:
    client, orch, store = _make_client()

    async def _drive() -> None:
        orch.start(preset="severe_stick_slip")
        await orch._maybe_trigger_advisor(_critical_snapshot())  # noqa: SLF001
        orch.stop()

    with client:
        asyncio.run(_drive())
        response = client.get("/api/v1/advisor/recommendations")
        assert response.status_code == 200
        body = response.json()
        assert len(body) >= 1
        rec = body[0]["recommendation"]
        assert rec["incident_type"] in (
            "stick_slip",
            "over_torque",
            "transient_choke",
            "unknown",
        )
        assert 0.0 <= rec["target_wob_kn"] <= 200.0
        assert 0.0 <= rec["target_rpm"] <= 220.0
        assert len(store) >= 1


def test_websocket_receives_advisor_recommendation_envelope() -> None:
    client, orch, _store = _make_client()
    with client:
        client.post(
            "/api/v1/simulation/start",
            json={"preset": "severe_stick_slip"},
        )
        with client.websocket_connect("/ws/telemetry") as ws:
            # Disparar advisor en el event loop del TestClient (mismas colas WS).
            client.portal.call(orch._maybe_trigger_advisor, _critical_snapshot())
            found = False
            for _ in range(30):
                try:
                    raw = ws.receive()
                except Exception:  # noqa: BLE001
                    break
                if raw.get("bytes"):
                    payload = json.loads(raw["bytes"].decode("utf-8"))
                elif raw.get("text"):
                    payload = json.loads(raw["text"])
                else:
                    continue
                assert isinstance(payload, dict)
                if payload.get("type") == "advisor_recommendation":
                    data = payload["data"]
                    assert isinstance(data, dict)
                    assert "recommendation" in data
                    found = True
                    break
            assert found is True
            ws.close()
        client.post("/api/v1/simulation/stop")
