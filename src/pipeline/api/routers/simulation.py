"""Endpoints REST de control del simulador."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.pipeline.api.schemas.requests import (
    OrchestratorStatusDTO,
    SetPresetRequestDTO,
    StartSimulationRequestDTO,
)
from src.pipeline.orchestration.simulation_orchestrator import SimulationOrchestrator

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


def _orchestrator(request: Request) -> SimulationOrchestrator:
    return request.app.state.orchestrator  # type: ignore[no-any-return]


@router.post("/start", response_model=OrchestratorStatusDTO)
async def start_simulation(
    body: StartSimulationRequestDTO,
    request: Request,
) -> OrchestratorStatusDTO:
    """Arranca el loop físico; opcionalmente carga un preset."""
    orch = _orchestrator(request)
    orch.start(preset=body.preset)
    return orch.status


@router.post("/stop", response_model=OrchestratorStatusDTO)
async def stop_simulation(request: Request) -> OrchestratorStatusDTO:
    """Detiene el loop físico."""
    orch = _orchestrator(request)
    orch.stop()
    return orch.status


@router.post("/preset", response_model=OrchestratorStatusDTO)
async def set_preset(
    body: SetPresetRequestDTO,
    request: Request,
) -> OrchestratorStatusDTO:
    """Cambia el preset del ``WellSimulator``."""
    orch = _orchestrator(request)
    orch.set_preset(body.preset)
    return orch.status


@router.get("/status", response_model=OrchestratorStatusDTO)
async def simulation_status(request: Request) -> OrchestratorStatusDTO:
    """Consulta el estado del orquestador."""
    return _orchestrator(request).status
