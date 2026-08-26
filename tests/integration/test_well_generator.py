"""Tests de integración del generador de telemetría sintética."""

from __future__ import annotations

import numpy as np
import pytest
from src.engine.simulator.well_generator import (
    NoiseConfig,
    SimulatorConfig,
    WellSimulator,
    default_simulator_config,
)


def test_reproducibility_with_fixed_seed() -> None:
    cfg = default_simulator_config(
        seed=99, acoustic_delay_sec=5.0, mwd_interval_sec=2.0
    )
    sim_a = WellSimulator(cfg)
    sim_b = WellSimulator(cfg)
    sim_a.load_preset("normal")
    sim_b.load_preset("normal")

    surfaces_a = []
    surfaces_b = []
    for _ in range(50):
        sim_a.step(0.01, u_top_rpm=80.0, wob_kn=60.0)
        sim_b.step(0.01, u_top_rpm=80.0, wob_kn=60.0)
        surfaces_a.append(sim_a.get_surface_telemetry())
        surfaces_b.append(sim_b.get_surface_telemetry())

    for a, b in zip(surfaces_a, surfaces_b, strict=True):
        assert a.timestamp == b.timestamp
        assert a.rpm_surface == b.rpm_surface
        assert a.torque_surface_knm == b.torque_surface_knm
        assert a.hookload_kn == b.hookload_kn
        assert a.standpipe_pressure_kpa == b.standpipe_pressure_kpa


def test_acoustic_delay_no_mwd_before_delay() -> None:
    delay = 15.0
    interval = 5.0
    cfg = default_simulator_config(
        seed=7,
        acoustic_delay_sec=delay,
        mwd_interval_sec=interval,
        dt_internal=1e-3,
    )
    sim = WellSimulator(cfg)
    sim.load_preset("normal")

    dt = 0.01
    t_end = delay + interval + 1.0
    n_steps = int(round(t_end / dt))
    for _i in range(n_steps):
        sim.step(dt, u_top_rpm=70.0, wob_kn=50.0)
        t = sim.time_s
        packets = sim.get_available_mwd_telemetry(t)
        for pkt in packets:
            # Ningún paquete disponible antes de origin + delay
            assert pkt.origin_time_s + delay <= t + 1e-9
            assert pkt.acoustic_delay_s == delay

    # Antes de que expire el primer retardo, la cola no debe liberar nada
    sim2 = WellSimulator(cfg)
    sim2.load_preset("normal")
    early_end = delay - 0.5
    for _ in range(int(round(early_end / dt))):
        sim2.step(dt, u_top_rpm=70.0, wob_kn=50.0)
        assert sim2.get_available_mwd_telemetry(sim2.time_s) == []


def test_severe_stick_slip_bit_reaches_near_zero_rpm() -> None:
    cfg = default_simulator_config(seed=11, dt_internal=1e-3, mwd_interval_sec=50.0)
    sim = WellSimulator(cfg)
    sim.load_preset("severe_stick_slip")

    # Condición inicial: rotación rígida cerca del setpoint
    n = cfg.drillstring_params.n_nodes
    omega0 = 60.0 * (2.0 * np.pi / 60.0)
    state = np.zeros(2 * n, dtype=np.float64)
    state[1::2] = omega0
    sim._state = state  # noqa: SLF001 — condición inicial controlada en test de integración

    dt = 0.01
    u_top_rpm = 60.0
    wob_kn = 180.0
    bit_rpms: list[float] = []
    duration_s = 25.0
    for _ in range(int(round(duration_s / dt))):
        result = sim.step(dt, u_top_rpm=u_top_rpm, wob_kn=wob_kn)
        bit_rpms.append(result.rpm_bit_true)

    bit_arr = np.asarray(bit_rpms, dtype=np.float64)
    # Stick cíclico: la broca debe caer cerca de 0 RPM al menos una vez
    assert float(np.min(np.abs(bit_arr))) < 1.0, (
        f"min |rpm_bit|={float(np.min(np.abs(bit_arr))):.3f} expected < 1"
    )
    # Y también recuperarse (slip) — rango amplio
    assert float(np.max(bit_arr) - np.min(bit_arr)) > 20.0


def test_surface_requires_step_first() -> None:
    sim = WellSimulator(default_simulator_config(seed=1))
    with pytest.raises(RuntimeError, match="step"):
        sim.get_surface_telemetry()


def test_unknown_preset_raises() -> None:
    sim = WellSimulator(default_simulator_config(seed=1))
    with pytest.raises(ValueError, match="unknown scenario"):
        sim.load_preset("not_a_real_scenario")  # type: ignore[arg-type]


def test_noise_and_config_validation() -> None:
    with pytest.raises(ValueError, match="rpm_surface_std"):
        NoiseConfig(
            rpm_surface_std=-1.0,
            torque_surface_knm_std=0.0,
            hookload_kn_std=0.0,
            standpipe_pressure_kpa_std=0.0,
            rpm_downhole_std=0.0,
            torque_downhole_knm_std=0.0,
            wob_kn_std=0.0,
        )
    base = default_simulator_config(seed=1)
    with pytest.raises(ValueError, match="dt_internal"):
        SimulatorConfig(
            drillstring_params=base.drillstring_params,
            friction_coeffs=base.friction_coeffs,
            dt_internal=0.0,
            noise_config=base.noise_config,
            mwd_interval_sec=1.0,
            acoustic_delay_sec=1.0,
            seed=1,
        )
    with pytest.raises(ValueError, match="mwd_interval"):
        SimulatorConfig(
            drillstring_params=base.drillstring_params,
            friction_coeffs=base.friction_coeffs,
            dt_internal=1e-3,
            noise_config=base.noise_config,
            mwd_interval_sec=0.0,
            acoustic_delay_sec=1.0,
            seed=1,
        )
    with pytest.raises(ValueError, match="acoustic_delay"):
        SimulatorConfig(
            drillstring_params=base.drillstring_params,
            friction_coeffs=base.friction_coeffs,
            dt_internal=1e-3,
            noise_config=base.noise_config,
            mwd_interval_sec=1.0,
            acoustic_delay_sec=-1.0,
            seed=1,
        )


def test_step_rejects_bad_args_and_reset() -> None:
    sim = WellSimulator(default_simulator_config(seed=3))
    with pytest.raises(ValueError, match="dt"):
        sim.step(0.0, 10.0, 1.0)
    with pytest.raises(ValueError, match="wob"):
        sim.step(0.01, 10.0, -1.0)
    with pytest.raises(ValueError, match="current_time"):
        sim.get_available_mwd_telemetry(-0.1)
    sim.step(0.01, 50.0, 40.0)
    sim.reset()
    assert sim.time_s == 0.0
    assert sim.get_available_mwd_telemetry(0.0) == []


def test_transient_choke_preset_loads() -> None:
    sim = WellSimulator(default_simulator_config(seed=5))
    sim.load_preset("transient_choke")
    assert sim.scenario == "transient_choke"
    result = sim.step(0.01, u_top_rpm=90.0, wob_kn=70.0)
    assert result.time_s > 0.0
    tel = sim.get_surface_telemetry()
    assert tel.rpm_surface >= 0.0
