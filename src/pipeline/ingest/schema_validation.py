"""Validación de payloads contra JSON Schema canónicos (`docs/contratos/`)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

SchemaName = Literal[
    "surface_telemetry",
    "mwd_telemetry",
    "telemetry_stream_broadcast",
]

_CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "docs" / "contratos"

_SCHEMA_FILES: dict[SchemaName, str] = {
    "surface_telemetry": "surface_telemetry.json",
    "mwd_telemetry": "mwd_telemetry.json",
    "telemetry_stream_broadcast": "telemetry_stream_broadcast.json",
}


class SchemaValidationError(ValueError):
    """Payload rechazado por el JSON Schema canónico."""


@lru_cache(maxsize=8)
def load_schema(name: SchemaName) -> dict[str, object]:
    """Carga un schema JSON desde ``docs/contratos/``.

    Parameters
    ----------
    name : SchemaName
        Identificador del contrato (sin extensión).

    Returns
    -------
    dict[str, object]
        Documento JSON Schema (draft 2020-12).

    Raises
    ------
    FileNotFoundError
        Si el archivo del contrato no existe.
    """
    filename = _SCHEMA_FILES[name]
    path = _CONTRACTS_DIR / filename
    if not path.is_file():
        msg = f"schema file not found: {path}"
        raise FileNotFoundError(msg)
    with path.open(encoding="utf-8") as handle:
        raw: object = json.load(handle)
    if not isinstance(raw, dict):
        msg = f"schema root must be an object, got {type(raw).__name__}"
        raise TypeError(msg)
    typed: dict[str, object] = raw
    return typed


def validate_payload(payload: dict[str, object], schema: dict[str, object]) -> None:
    """Valida ``payload`` contra ``schema`` (``additionalProperties: false``).

    Parameters
    ----------
    payload : dict[str, object]
        Documento a validar.
    schema : dict[str, object]
        JSON Schema cargado con :func:`load_schema`.

    Raises
    ------
    SchemaValidationError
        Si el payload no cumple el schema.
    """
    validator = Draft202012Validator(schema)
    try:
        validator.validate(payload)
    except JsonSchemaValidationError as exc:
        msg = f"schema validation failed: {exc.message}"
        raise SchemaValidationError(msg) from exc


__all__ = [
    "SchemaName",
    "SchemaValidationError",
    "load_schema",
    "validate_payload",
]
