"""Routers FastAPI del pipeline."""

from src.pipeline.api.routers.simulation import router as simulation_router
from src.pipeline.api.routers.telemetry_ws import router as telemetry_ws_router

__all__ = [
    "simulation_router",
    "telemetry_ws_router",
]
