"""DTO de telemetría MWD — contrato ``mwd.telemetry.v1``."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MwdTelemetryDTO(BaseModel):
    """Muestra MWD validada (SPEC §4.2).

    Attributes
    ----------
    timestamp : datetime
        Instantánea UTC del origen de la medición.
    acoustic_delay_s : float
        Retardo acústico mud-pulse [s], ∈ [15, 45].
    rpm_downhole : float
        RPM de fondo [rpm], ≥ 0.
    torque_downhole_knm : float
        Torque de fondo [kN·m].
    wob_kn : float
        Weight on Bit [kN], ≥ 0.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    acoustic_delay_s: float = Field(ge=15.0, le=45.0)
    rpm_downhole: float = Field(ge=0.0)
    torque_downhole_knm: float
    wob_kn: float = Field(ge=0.0)
