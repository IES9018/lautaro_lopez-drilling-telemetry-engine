"""Hardening de entrada en el borde REST (OpenAPI / Pydantic)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.engine.simulator.well_generator import default_simulator_config
from src.pipeline.api.app import create_app
from src.pipeline.orchestration.simulation_orchestrator import (
    OrchestratorConfig,
    SimulationOrchestrator,
)


def _client() -> TestClient:
    sim = default_simulator_config(seed=7, acoustic_delay_sec=20.0)
    orch = SimulationOrchestrator(config=OrchestratorConfig(simulator_config=sim))
    return TestClient(create_app(orchestrator=orch))


def test_oversized_preset_string_rejected() -> None:
    with _client() as client:
        r = client.post(
            "/api/v1/simulation/preset",
            json={"preset": "x" * 10_000},
        )
        assert r.status_code == 422


def test_extra_fields_rejected_on_preset() -> None:
    with _client() as client:
        r = client.post(
            "/api/v1/simulation/preset",
            json={"preset": "normal", "__admin": True},
        )
        assert r.status_code == 422


def test_extra_fields_rejected_on_start() -> None:
    with _client() as client:
        r = client.post(
            "/api/v1/simulation/start",
            json={"preset": "normal", "inject": "payload"},
        )
        assert r.status_code == 422


def test_invalid_json_body_returns_422() -> None:
    with _client() as client:
        r = client.post(
            "/api/v1/simulation/start",
            content=b"{not-json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422


def test_limit_below_min_rejected() -> None:
    with _client() as client:
        r = client.get("/api/v1/advisor/recommendations?limit=0")
        assert r.status_code == 422


def test_limit_above_max_rejected() -> None:
    with _client() as client:
        r = client.get("/api/v1/advisor/recommendations?limit=9999")
        assert r.status_code == 422


def test_start_with_null_preset_ok() -> None:
    with _client() as client:
        r = client.post("/api/v1/simulation/start", json={"preset": None})
        assert r.status_code == 200
        assert r.json()["running"] is True
        client.post("/api/v1/simulation/stop")


def test_start_empty_body_ok() -> None:
    with _client() as client:
        r = client.post("/api/v1/simulation/start", json={})
        assert r.status_code == 200
        client.post("/api/v1/simulation/stop")


def test_sql_injection_like_preset_rejected() -> None:
    with _client() as client:
        r = client.post(
            "/api/v1/simulation/preset",
            json={"preset": "normal; DROP TABLE wells--"},
        )
        assert r.status_code == 422
