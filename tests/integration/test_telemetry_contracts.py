"""Tests de contratos JSON Schema y DTOs Pydantic v2."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.engine.simulator.well_generator import (
    MwdTelemetrySample,
    SurfaceTelemetrySample,
    WellSimulator,
    default_simulator_config,
)
from src.pipeline.api.schemas.adapters import mwd_sample_to_dto, surface_sample_to_dto
from src.pipeline.api.schemas.broadcast import TelemetryStreamBroadcastDTO, UkfStateDTO
from src.pipeline.api.schemas.mwd_telemetry import MwdTelemetryDTO
from src.pipeline.api.schemas.surface_telemetry import SurfaceTelemetryDTO
from src.pipeline.ingest.schema_validation import (
    SchemaValidationError,
    load_schema,
    validate_payload,
)


def test_surface_dto_rejects_negative_rpm() -> None:
    with pytest.raises(ValidationError):
        SurfaceTelemetryDTO(
            timestamp=datetime.now(tz=UTC),
            hookload_kn=800.0,
            rpm_surface=-1.0,
            torque_surface_knm=10.0,
            standpipe_pressure_kpa=15000.0,
        )


def test_surface_dto_rejects_negative_hookload() -> None:
    with pytest.raises(ValidationError):
        SurfaceTelemetryDTO(
            timestamp=datetime.now(tz=UTC),
            hookload_kn=-0.1,
            rpm_surface=100.0,
            torque_surface_knm=10.0,
            standpipe_pressure_kpa=15000.0,
        )


def test_surface_dto_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        SurfaceTelemetryDTO.model_validate(
            {
                "timestamp": "2026-08-25T12:00:00Z",
                "hookload_kn": 800.0,
                "rpm_surface": 100.0,
                "torque_surface_knm": 10.0,
                "standpipe_pressure_kpa": 15000.0,
                "extra_field": 1,
            }
        )


def test_mwd_dto_rejects_negative_wob() -> None:
    with pytest.raises(ValidationError):
        MwdTelemetryDTO(
            timestamp=datetime.now(tz=UTC),
            acoustic_delay_s=20.0,
            rpm_downhole=50.0,
            torque_downhole_knm=5.0,
            wob_kn=-1.0,
        )


def test_mwd_dto_rejects_delay_out_of_range() -> None:
    with pytest.raises(ValidationError):
        MwdTelemetryDTO(
            timestamp=datetime.now(tz=UTC),
            acoustic_delay_s=10.0,
            rpm_downhole=50.0,
            torque_downhole_knm=5.0,
            wob_kn=80.0,
        )


def test_json_schema_accepts_valid_surface_payload() -> None:
    schema = load_schema("surface_telemetry")
    payload: dict[str, object] = {
        "timestamp": "2026-08-25T12:00:00Z",
        "hookload_kn": 800.0,
        "rpm_surface": 100.0,
        "torque_surface_knm": 10.0,
        "standpipe_pressure_kpa": 15000.0,
    }
    validate_payload(payload, schema)


def test_json_schema_rejects_invalid_surface_payload() -> None:
    schema = load_schema("surface_telemetry")
    payload: dict[str, object] = {
        "timestamp": "2026-08-25T12:00:00Z",
        "hookload_kn": -1.0,
        "rpm_surface": 100.0,
        "torque_surface_knm": 10.0,
        "standpipe_pressure_kpa": 15000.0,
    }
    with pytest.raises(SchemaValidationError):
        validate_payload(payload, schema)


def test_json_schema_accepts_valid_mwd_and_broadcast() -> None:
    mwd_schema = load_schema("mwd_telemetry")
    validate_payload(
        {
            "timestamp": "2026-08-25T12:00:00Z",
            "acoustic_delay_s": 20.0,
            "rpm_downhole": 40.0,
            "torque_downhole_knm": 4.0,
            "wob_kn": 80.0,
        },
        mwd_schema,
    )
    broadcast_schema = load_schema("telemetry_stream_broadcast")
    validate_payload(
        {
            "timestamp": "2026-08-25T12:00:00Z",
            "frame_id": 1,
            "ukf_state": {
                "theta_rad": [0.0, 0.1],
                "omega_rad_s": [10.0, 9.0],
                "rpm_bit_est": 85.9,
                "torque_bit_est_knm": 3.2,
            },
            "torsional_deformation_rad": [0.0, 0.1],
            "ssi": 0.2,
            "alert_level": "normal",
        },
        broadcast_schema,
    )


def test_adapters_from_simulator_samples() -> None:
    sim = WellSimulator(default_simulator_config(seed=7, acoustic_delay_sec=20.0))
    sim.step(0.01, 120.0, 80.0)
    surface = sim.get_surface_telemetry()
    dto = surface_sample_to_dto(surface)
    assert dto.rpm_surface >= 0.0
    assert dto.hookload_kn >= 0.0

    sample = MwdTelemetrySample(
        timestamp="2026-08-25T12:00:20Z",
        acoustic_delay_s=20.0,
        rpm_downhole=10.0,
        torque_downhole_knm=2.0,
        wob_kn=80.0,
        origin_time_s=20.0,
    )
    mwd_dto = mwd_sample_to_dto(sample)
    assert mwd_dto.acoustic_delay_s == 20.0


def test_surface_adapter_from_dataclass() -> None:
    sample = SurfaceTelemetrySample(
        timestamp="2026-08-25T12:00:00Z",
        hookload_kn=800.0,
        rpm_surface=100.0,
        torque_surface_knm=10.0,
        standpipe_pressure_kpa=15000.0,
    )
    dto = surface_sample_to_dto(sample)
    assert dto.rpm_surface == 100.0


def test_pydantic_serialization_under_high_frequency_load() -> None:
    """Smoke: serializar ≥1000 frames sin fallar (sin asertar contra reloj)."""
    base = TelemetryStreamBroadcastDTO(
        timestamp=datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC),
        frame_id=0,
        ukf_state=UkfStateDTO(
            theta_rad=[0.0, 0.1, 0.2],
            omega_rad_s=[12.0, 11.0, 10.0],
            rpm_bit_est=95.5,
            torque_bit_est_knm=3.1,
        ),
        torsional_deformation_rad=[0.0, 0.1, 0.2],
        ssi=0.15,
        alert_level="normal",
    )
    payloads: list[str] = []
    for i in range(1200):
        frame = base.model_copy(update={"frame_id": i})
        payloads.append(frame.model_dump_json())
    assert len(payloads) == 1200
    assert '"frame_id":1199' in payloads[-1]
