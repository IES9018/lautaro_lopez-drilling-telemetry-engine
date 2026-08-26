"""DTO de broadcast WebSocket — contrato ``broadcast.state.v1``."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AlertLevel = Literal["normal", "warning", "critical"]


class UkfStateDTO(BaseModel):
    """Estado estimado por el UKF para el gemelo digital.

    Attributes
    ----------
    theta_rad : list[float]
        Ángulos nodales estimados [rad].
    omega_rad_s : list[float]
        Velocidades angulares nodales estimadas [rad/s].
    rpm_bit_est : float
        RPM estimada en broca [rpm], ≥ 0.
    torque_bit_est_knm : float
        Torque estimado en broca [kN·m].
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    theta_rad: list[float]
    omega_rad_s: list[float]
    rpm_bit_est: float = Field(ge=0.0)
    torque_bit_est_knm: float


class TelemetryStreamBroadcastDTO(BaseModel):
    """Frame consolidado emitido a ~60 FPS (SPEC §4.3).

    Attributes
    ----------
    timestamp : datetime
        Instantánea UTC del frame.
    frame_id : int
        Contador monotónico de frames, ≥ 0.
    ukf_state : UkfStateDTO
        Estado torsional estimado.
    torsional_deformation_rad : list[float]
        Deformación torsional nodal relativa a superficie [rad].
    ssi : float
        Stick-Slip Severity Index, ≥ 0.
    alert_level : {"normal", "warning", "critical"}
        Régimen derivado del SSI en el Physics Engine.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    frame_id: int = Field(ge=0)
    ukf_state: UkfStateDTO
    torsional_deformation_rad: list[float]
    ssi: float = Field(ge=0.0)
    alert_level: AlertLevel
