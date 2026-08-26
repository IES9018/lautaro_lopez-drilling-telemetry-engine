"""Tests de corrección fixed-lag MWD en el SimulationOrchestrator."""

from __future__ import annotations

import asyncio

import numpy as np

from src.engine.simulator.well_generator import (
    MwdTelemetrySample,
    default_simulator_config,
)
from src.pipeline.orchestration.simulation_orchestrator import (
    OrchestratorConfig,
    SimulationOrchestrator,
)


async def _run_until_mwd_correction(
    orch: SimulationOrchestrator,
    target_time_s: float,
) -> tuple[np.ndarray, int]:
    """Avanza ticks síncronos hasta ``target_time_s`` y espera correcciones MWD."""
    orch.start()
    dt = orch.config.dt_surface
    while orch._simulator.time_s < target_time_s:  # noqa: SLF001
        await orch._physics_tick(dt)  # noqa: SLF001
    if orch._correction_tasks:  # noqa: SLF001
        await asyncio.gather(*list(orch._correction_tasks), return_exceptions=True)
    x = np.array(orch._ukf.x, dtype=np.float64, copy=True)  # noqa: SLF001
    drops = orch.status.mwd_drops
    orch.stop()
    return x, drops


def test_mwd_fixed_lag_is_deterministic_and_no_drop_within_window() -> None:
    """Misma semilla → mismo estado tras corrección; sin drops si la ventana cubre el delay."""
    delay = 2.0
    sim_cfg = default_simulator_config(
        seed=99,
        mwd_interval_sec=1.0,
        acoustic_delay_sec=delay,
    )
    cfg = OrchestratorConfig(
        simulator_config=sim_cfg,
        dt_surface=0.01,
        buffer_window_sec=10.0,
        ssi_window_size=50,
    )

    orch_a = SimulationOrchestrator(config=cfg)
    x_a, drops_a = asyncio.run(_run_until_mwd_correction(orch_a, target_time_s=3.5))

    orch_b = SimulationOrchestrator(config=cfg)
    x_b, drops_b = asyncio.run(_run_until_mwd_correction(orch_b, target_time_s=3.5))

    assert drops_a == 0
    assert drops_b == 0
    np.testing.assert_allclose(x_a, x_b, rtol=0.0, atol=1e-12)
    assert orch_a.latest_broadcast is not None
    assert orch_a.latest_broadcast.ssi >= 0.0


def test_biased_mwd_fixed_lag_changes_ukf_state() -> None:
    """Un MWD artificialmente sesgado altera el estado vía fixed-lag replay."""
    delay = 1.5
    sim_cfg = default_simulator_config(
        seed=3,
        mwd_interval_sec=1.0,
        acoustic_delay_sec=delay,
    )
    cfg = OrchestratorConfig(
        simulator_config=sim_cfg,
        dt_surface=0.01,
        buffer_window_sec=10.0,
    )
    orch = SimulationOrchestrator(config=cfg)

    async def _drive() -> tuple[np.ndarray, np.ndarray, int]:
        orch.start()
        dt = cfg.dt_surface
        while orch._simulator.time_s < delay + 0.5:  # noqa: SLF001
            await orch._physics_tick(dt)  # noqa: SLF001
        if orch._correction_tasks:  # noqa: SLF001
            await asyncio.gather(*list(orch._correction_tasks), return_exceptions=True)

        x_before = np.array(orch._ukf.x, dtype=np.float64, copy=True)  # noqa: SLF001
        biased = MwdTelemetrySample(
            timestamp="2026-08-25T12:00:01Z",
            acoustic_delay_s=delay,
            rpm_downhole=0.0,  # sesgo fuerte vs. bit girando
            torque_downhole_knm=50.0,
            wob_kn=80.0,
            origin_time_s=1.0,
        )
        await orch._apply_mwd_correction(biased)  # noqa: SLF001
        x_after = np.array(orch._ukf.x, dtype=np.float64, copy=True)  # noqa: SLF001
        drops = orch.status.mwd_drops
        orch.stop()
        return x_before, x_after, drops

    x_before, x_after, drops = asyncio.run(_drive())
    assert drops == 0
    assert not np.allclose(x_before, x_after, atol=1e-9)


def test_mwd_older_than_window_is_dropped() -> None:
    """MWD cuyo origen es más viejo que el journal → drop (sin excepción)."""
    sim_cfg = default_simulator_config(
        seed=1,
        mwd_interval_sec=20.0,
        acoustic_delay_sec=20.0,
    )
    cfg = OrchestratorConfig(
        simulator_config=sim_cfg,
        dt_surface=0.01,
        buffer_window_sec=1.0,  # ventana corta
    )
    orch = SimulationOrchestrator(config=cfg)

    async def _drive() -> int:
        orch.start()
        for _ in range(5):
            await orch._physics_tick(cfg.dt_surface)  # noqa: SLF001
        stale = MwdTelemetrySample(
            timestamp="2026-08-25T11:00:00Z",
            acoustic_delay_s=20.0,
            rpm_downhole=10.0,
            torque_downhole_knm=1.0,
            wob_kn=80.0,
            origin_time_s=0.0,  # más viejo que lo retenido tras pocos ticks? 
            # Tras 5 ticks el journal empieza en ~0.01; origin 0.0 aún puede alinear.
            # Usar origen negativo imposible — usar origen muy anterior vía clear:
        )
        orch._buffer.clear()  # noqa: SLF001
        await orch._apply_mwd_correction(stale)  # noqa: SLF001
        drops = orch.status.mwd_drops
        orch.stop()
        return drops

    assert asyncio.run(_drive()) == 1
