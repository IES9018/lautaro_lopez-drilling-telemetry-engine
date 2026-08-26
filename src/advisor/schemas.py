"""Esquemas Pydantic del Advisor LLM (entrada de incidente / salida SOP)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Duplicado intencional de pipeline AlertLevel para evitar import circular
# advisor → pipeline.api → advisor (aislamiento de dominios / A-006).
AlertLevel = Literal["normal", "warning", "critical"]
IncidentType = Literal["stick_slip", "over_torque", "transient_choke", "unknown"]
SeverityLevel = Literal["warning", "critical"]

# Límites operativos seguros (supuesto Sprint 1; documentado en A-006).
SAFE_WOB_RANGE_KN: tuple[float, float] = (0.0, 200.0)
SAFE_RPM_RANGE: tuple[float, float] = (0.0, 220.0)

_MAX_ACTION_LEN = 200


class AdvisorIncidentSnapshot(BaseModel):
    """Snapshot contextual inmutable del incidente (features tipados).

    Attributes
    ----------
    timestamp : datetime
        Instantánea UTC del snapshot.
    surface_rpm : float
        RPM de superficie [rpm], ≥ 0.
    estimated_bit_rpm : float
        RPM estimada en broca [rpm], ≥ 0.
    wob_kn : float
        Weight on Bit [kN], ≥ 0.
    ssi : float
        Stick-Slip Severity Index, ≥ 0.
    regime : AlertLevel
        Régimen derivado del SSI (`normal` / `warning` / `critical`).
    torque_contrast : float
        Contraste de torque superficie − fondo [kN·m].
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    surface_rpm: float = Field(ge=0.0)
    estimated_bit_rpm: float = Field(ge=0.0)
    wob_kn: float = Field(ge=0.0)
    ssi: float = Field(ge=0.0)
    regime: AlertLevel
    torque_contrast: float


class AdvisorRecommendation(BaseModel):
    """Recomendación operativa estructurada (salida del LLM / mock).

    Attributes
    ----------
    incident_type : IncidentType
        Clasificación del incidente.
    severity_level : SeverityLevel
        Severidad operativa.
    physical_root_cause : str
        Causa raíz física (≤ 500 chars).
    immediate_actions : list[str]
        Acciones inmediatas (1–6), cada una ≤ 200 chars.
    target_wob_kn : float
        WOB objetivo [kN] dentro de ``SAFE_WOB_RANGE_KN``.
    target_rpm : float
        RPM objetivo [rpm] dentro de ``SAFE_RPM_RANGE``.
    rationale : str
        Justificación breve (≤ 800 chars).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_type: IncidentType
    severity_level: SeverityLevel
    physical_root_cause: str = Field(max_length=500)
    immediate_actions: list[str] = Field(min_length=1, max_length=6)
    target_wob_kn: float = Field(
        ge=SAFE_WOB_RANGE_KN[0],
        le=SAFE_WOB_RANGE_KN[1],
    )
    target_rpm: float = Field(
        ge=SAFE_RPM_RANGE[0],
        le=SAFE_RPM_RANGE[1],
    )
    rationale: str = Field(max_length=800)

    @field_validator("immediate_actions")
    @classmethod
    def _bounded_action_length(cls, actions: list[str]) -> list[str]:
        for action in actions:
            if len(action) > _MAX_ACTION_LEN:
                msg = (
                    f"immediate_actions entries must be <= {_MAX_ACTION_LEN} chars, "
                    f"got {len(action)}"
                )
                raise ValueError(msg)
        return actions


__all__ = [
    "SAFE_RPM_RANGE",
    "SAFE_WOB_RANGE_KN",
    "AdvisorIncidentSnapshot",
    "AdvisorRecommendation",
    "AlertLevel",
    "IncidentType",
    "SeverityLevel",
]
