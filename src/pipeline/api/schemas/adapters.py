"""Adaptadores entre dataclasses del simulador y DTOs Pydantic v2."""

from __future__ import annotations

from datetime import datetime

from src.engine.simulator.well_generator import MwdTelemetrySample, SurfaceTelemetrySample
from src.pipeline.api.schemas.mwd_telemetry import MwdTelemetryDTO
from src.pipeline.api.schemas.surface_telemetry import SurfaceTelemetryDTO


def _parse_iso_utc(value: str) -> datetime:
    """Parsea ISO-8601 con sufijo ``Z`` a ``datetime`` aware."""
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def surface_sample_to_dto(sample: SurfaceTelemetrySample) -> SurfaceTelemetryDTO:
    """Convierte ``SurfaceTelemetrySample`` → ``SurfaceTelemetryDTO``.

    Parameters
    ----------
    sample : SurfaceTelemetrySample
        Muestra del simulador (puede incluir ruido).

    Returns
    -------
    SurfaceTelemetryDTO
        DTO validado (rangos físicos ≥ 0).
    """
    return SurfaceTelemetryDTO(
        timestamp=_parse_iso_utc(sample.timestamp),
        hookload_kn=max(0.0, float(sample.hookload_kn)),
        rpm_surface=max(0.0, float(sample.rpm_surface)),
        torque_surface_knm=float(sample.torque_surface_knm),
        standpipe_pressure_kpa=max(0.0, float(sample.standpipe_pressure_kpa)),
    )


def mwd_sample_to_dto(sample: MwdTelemetrySample) -> MwdTelemetryDTO:
    """Convierte ``MwdTelemetrySample`` → ``MwdTelemetryDTO``.

    Parameters
    ----------
    sample : MwdTelemetrySample
        Paquete MWD liberado tras el retardo acústico.

    Returns
    -------
    MwdTelemetryDTO
        DTO validado (``acoustic_delay_s`` ∈ [15, 45], RPM/WOB ≥ 0).
    """
    delay = float(sample.acoustic_delay_s)
    # Clamp al rango de contrato si el simulador usa delay de demo < 15 s.
    delay_clamped = min(45.0, max(15.0, delay))
    return MwdTelemetryDTO(
        timestamp=_parse_iso_utc(sample.timestamp),
        acoustic_delay_s=delay_clamped,
        rpm_downhole=max(0.0, float(sample.rpm_downhole)),
        torque_downhole_knm=float(sample.torque_downhole_knm),
        wob_kn=max(0.0, float(sample.wob_kn)),
    )


__all__ = [
    "mwd_sample_to_dto",
    "surface_sample_to_dto",
]
