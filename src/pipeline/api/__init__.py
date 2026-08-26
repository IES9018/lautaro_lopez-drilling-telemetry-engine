"""API FastAPI del pipeline."""

from src.pipeline.api.app import create_app
from src.pipeline.api.connection_manager import ConnectionManager

__all__ = [
    "ConnectionManager",
    "create_app",
]
