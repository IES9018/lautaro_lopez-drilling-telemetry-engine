"""Prompts SOP de perforación (versionados) — anti prompt-injection."""

from __future__ import annotations

import math
from typing import Final

from src.advisor.schemas import (
    SAFE_RPM_RANGE,
    SAFE_WOB_RANGE_KN,
    AdvisorIncidentSnapshot,
    AdvisorRecommendation,
)

SOP_PROMPT_VERSION: Final[str] = "v1"

_ALLOWED_REGIMES: Final[frozenset[str]] = frozenset({"normal", "warning", "critical"})


def sanitize_numeric(value: float, name: str) -> str:
    """Rechaza NaN/Inf y formatea a decimal fijo.

    Parameters
    ----------
    value : float
        Valor numérico a interpolar en el prompt.
    name : str
        Nombre del campo (para mensajes de error).

    Returns
    -------
    str
        Representación decimal fija (6 decimales).

    Raises
    ------
    ValueError
        Si ``value`` no es finito.
    """
    if not math.isfinite(value):
        msg = f"{name} must be finite, got {value!r}"
        raise ValueError(msg)
    return f"{float(value):.6f}"


def build_system_prompt() -> str:
    """Directivas SOP fijas para mitigación Stick-Slip / sobre-torque.

    Returns
    -------
    str
        System prompt versionado (sin datos de telemetría).
    """
    wob_lo, wob_hi = SAFE_WOB_RANGE_KN
    rpm_lo, rpm_hi = SAFE_RPM_RANGE
    return (
        f"You are a drilling operations advisor (SOP prompt {SOP_PROMPT_VERSION}). "
        "Diagnose Stick-Slip and over-torque using only the numeric features provided. "
        "Mitigation priorities: (1) reduce WOB to lower static friction load; "
        "(2) adjust surface RPM away from torsional resonance bands; "
        "(3) avoid sudden torque spikes; (4) do not invent SCADA actions outside SOP. "
        f"target_wob_kn MUST be in [{wob_lo}, {wob_hi}] kN; "
        f"target_rpm MUST be in [{rpm_lo}, {rpm_hi}] rpm. "
        "Respond with a single JSON object matching the response schema. "
        "Do not include markdown, commentary, or additional keys."
    )


def build_user_prompt(snapshot: AdvisorIncidentSnapshot) -> str:
    """Plantilla fija con placeholders numéricos sanitizados.

    Parameters
    ----------
    snapshot : AdvisorIncidentSnapshot
        Features tipados del incidente (sin JSON crudo).

    Returns
    -------
    str
        User prompt listo para el proveedor LLM.
    """
    regime = snapshot.regime
    if regime not in _ALLOWED_REGIMES:
        msg = f"regime must be one of {_ALLOWED_REGIMES}, got {regime!r}"
        raise ValueError(msg)

    surface = sanitize_numeric(snapshot.surface_rpm, "surface_rpm")
    bit = sanitize_numeric(snapshot.estimated_bit_rpm, "estimated_bit_rpm")
    wob = sanitize_numeric(snapshot.wob_kn, "wob_kn")
    ssi = sanitize_numeric(snapshot.ssi, "ssi")
    contrast = sanitize_numeric(snapshot.torque_contrast, "torque_contrast")

    return (
        "Incident features (SI-derived units in field names):\n"
        f"- surface_rpm: {surface}\n"
        f"- estimated_bit_rpm: {bit}\n"
        f"- wob_kn: {wob}\n"
        f"- ssi: {ssi}\n"
        f"- regime: {regime}\n"
        f"- torque_contrast_knm: {contrast}\n"
        "Produce the structured recommendation JSON now."
    )


def build_response_schema() -> dict[str, object]:
    """JSON Schema de salida (Structured Outputs / JSON mode).

    Returns
    -------
    dict[str, object]
        Schema derivado de ``AdvisorRecommendation``.
    """
    schema = AdvisorRecommendation.model_json_schema()
    return schema


__all__ = [
    "SOP_PROMPT_VERSION",
    "build_response_schema",
    "build_system_prompt",
    "build_user_prompt",
    "sanitize_numeric",
]
