"""Data Pipeline — ingest, buffer temporal, FastAPI / WebSockets."""

from src.pipeline.api.app import create_app

__all__ = ["create_app"]
