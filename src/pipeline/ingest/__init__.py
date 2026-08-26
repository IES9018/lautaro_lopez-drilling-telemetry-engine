"""Ingesta y validación de telemetría contra JSON Schema."""

from src.pipeline.ingest.schema_validation import (
    SchemaName,
    SchemaValidationError,
    load_schema,
    validate_payload,
)

__all__ = [
    "SchemaName",
    "SchemaValidationError",
    "load_schema",
    "validate_payload",
]
