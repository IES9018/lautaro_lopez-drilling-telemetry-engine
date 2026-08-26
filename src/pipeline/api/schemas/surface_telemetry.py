"""DTO de telemetría de superficie — contrato ``surface.telemetry.v1``."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SurfaceTelemetryDTO(BaseModel):
    """Muestra de superficie validada (SPEC §4.1).

    Attributes
    ----------
    timestamp : datetime
        Instantánea UTC del sample.
    hookload_kn : float
        Hookload [kN], ≥ 0.
    rpm_surface : float
        RPM de top-drive [rpm], ≥ 0.
    torque_surface_knm : float
        Torque de superficie [kN·m].
    standpipe_pressure_kpa : float
        Presión de standpipe [kPa], ≥ 0.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    hookload_kn: float = Field(ge=0.0)
    rpm_surface: float = Field(ge=0.0)
    torque_surface_knm: float
    standpipe_pressure_kpa: float = Field(ge=0.0)
