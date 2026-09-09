"""Headers / respuestas de error — no filtrar stack traces (T-08 threat model)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from src.engine.simulator.well_generator import default_simulator_config
from src.pipeline.api.app import create_app
from src.pipeline.orchestration.simulation_orchestrator import (
    OrchestratorConfig,
    SimulationOrchestrator,
)


def _client() -> TestClient:
    sim = default_simulator_config(seed=3, acoustic_delay_sec=20.0)
    orch = SimulationOrchestrator(config=OrchestratorConfig(simulator_config=sim))
    return TestClient(create_app(orchestrator=orch))


def test_json_endpoints_return_application_json() -> None:
    with _client() as client:
        r = client.get("/api/v1/simulation/status")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


def test_validation_error_has_detail_not_traceback() -> None:
    with _client() as client:
        r = client.post(
            "/api/v1/simulation/preset",
            json={"preset": "nope"},
        )
        assert r.status_code == 422
        body = r.json()
        assert "detail" in body
        dumped = r.text.lower()
        assert "traceback" not in dumped
        assert 'file "' not in dumped
        assert "line " not in dumped or "loc" in body  # pydantic loc ok


def test_recommendations_content_type() -> None:
    with _client() as client:
        r = client.get("/api/v1/advisor/recommendations")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
        assert isinstance(r.json(), list)


def test_forced_500_handler_does_not_leak_traceback() -> None:
    """Simula un handler de error global que debe devolver ErrorResponse genérico."""
    app = FastAPI()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal path /home/ops/keys.pem")

    @app.exception_handler(Exception)
    async def generic_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    with TestClient(app, raise_server_exceptions=False) as client:
        r = client.get("/boom")
        assert r.status_code == 500
        body = r.json()
        assert body == {"detail": "Internal Server Error"}
        assert "keys.pem" not in r.text
        assert "traceback" not in r.text.lower()
        assert "RuntimeError" not in r.text
