"""Orquestador Simulator + UKF + TimeSyncBuffer + broadcast consolidado."""

from __future__ import annotations

import asyncio
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from src.engine.kalman.sigma_points import SigmaPointParameters, compute_sigma_points
from src.engine.kalman.ssi_calculator import StickSlipRegime, compute_ssi
from src.engine.kalman.ukf_estimator import UnscentedKalmanFilter
from src.engine.physics.drillstring_fem import StateDerivativeFn, build_state_derivative
from src.advisor.llm_diagnostics import (
    DeterministicMockLLMProvider,
    DrillingAdvisor,
)
from src.advisor.schemas import AdvisorIncidentSnapshot
from src.engine.simulator.well_generator import (
    MwdTelemetrySample,
    ScenarioName,
    SimulatorConfig,
    WellSimulator,
    default_simulator_config,
)
from src.pipeline.api.advisor_store import (
    AdvisorHistoryStore,
    AdvisorRecommendationRecordDTO,
)
from src.pipeline.api.schemas.broadcast import (
    AlertLevel,
    TelemetryStreamBroadcastDTO,
    UkfStateDTO,
)
from src.pipeline.api.schemas.requests import OrchestratorStatusDTO
from src.pipeline.buffer.time_sync_buffer import TimeSyncBuffer, UkfJournalEntry
from src.pipeline.orchestration.measurement_models import (
    build_mwd_h_fn,
    build_surface_h_fn,
)

if TYPE_CHECKING:
    from src.pipeline.api.connection_manager import ConnectionManager

_RAD_S_TO_RPM = 60.0 / (2.0 * np.pi)
_RPM_TO_RAD_S = 2.0 * np.pi / 60.0


@dataclass(frozen=True, slots=True)
class OrchestratorConfig:
    """Configuración del orquestador de simulación / streaming.

    Parameters
    ----------
    simulator_config : SimulatorConfig
        Config del ``WellSimulator``.
    dt_surface : float
        Paso del loop físico / telemetría de superficie [s] (p. ej. 0.01 → 100 Hz).
    broadcast_fps : float
        Tasa objetivo de emisión WebSocket [Hz] (p. ej. 60).
    buffer_window_sec : float
        Ventana del journal fixed-lag [s] (≥ max acoustic delay).
    ssi_window_size : int
        Muestras de ω_bit para el SSI.
    u_top_rpm : float
        RPM de referencia del top-drive.
    wob_kn : float
        Weight on Bit nominal [kN].
    r_surface_diag : tuple[float, float]
        Diagonal de R para medición de superficie [rpm², (kN·m)²].
    r_mwd_diag : tuple[float, float]
        Diagonal de R para medición MWD [rpm², (kN·m)²].
    process_noise_scale : float
        Escala de Q = scale · I.
    """

    simulator_config: SimulatorConfig
    dt_surface: float = 0.01
    broadcast_fps: float = 60.0
    buffer_window_sec: float = 45.0
    ssi_window_size: int = 200
    u_top_rpm: float = 120.0
    wob_kn: float = 80.0
    r_surface_diag: tuple[float, float] = (4.0, 1.0)
    r_mwd_diag: tuple[float, float] = (16.0, 2.0)
    process_noise_scale: float = 1.0e-3


def _regime_to_alert(regime: StickSlipRegime) -> AlertLevel:
    if regime is StickSlipRegime.NORMAL:
        return "normal"
    if regime is StickSlipRegime.WARNING:
        return "warning"
    return "critical"


def _default_orchestrator_config() -> OrchestratorConfig:
    # Acoustic delay must be in [15, 45] for MWD DTO contract.
    sim = default_simulator_config(
        seed=42,
        mwd_interval_sec=20.0,
        acoustic_delay_sec=20.0,
    )
    return OrchestratorConfig(simulator_config=sim)


@dataclass
class SimulationOrchestrator:
    """Conecta simulador, UKF, journal fixed-lag y estado de broadcast.

    Parameters
    ----------
    config : OrchestratorConfig
        Configuración inmutable del orquestador.
    """

    config: OrchestratorConfig = field(default_factory=_default_orchestrator_config)
    advisor: DrillingAdvisor | None = None
    advisor_store: AdvisorHistoryStore | None = None
    connections: ConnectionManager | None = None
    _simulator: WellSimulator = field(init=False, repr=False)
    _ukf: UnscentedKalmanFilter = field(init=False, repr=False)
    _state_derivative: StateDerivativeFn = field(init=False, repr=False)
    _buffer: TimeSyncBuffer = field(init=False, repr=False)
    _r_surface: NDArray[np.float64] = field(init=False, repr=False)
    _r_mwd: NDArray[np.float64] = field(init=False, repr=False)
    _omega_window: deque[float] = field(init=False, repr=False)
    _running: bool = field(default=False, init=False, repr=False)
    _frame_id: int = field(default=0, init=False, repr=False)
    _mwd_drops: int = field(default=0, init=False, repr=False)
    _latest_broadcast: TelemetryStreamBroadcastDTO | None = field(
        default=None, init=False, repr=False
    )
    _state_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _correction_tasks: set[asyncio.Task[None]] = field(
        default_factory=set, init=False, repr=False
    )
    _advisor_tasks: set[asyncio.Task[None]] = field(
        default_factory=set, init=False, repr=False
    )
    _last_surface_rpm: float = field(default=0.0, init=False, repr=False)
    _last_torque_surface_knm: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._simulator = WellSimulator(self.config.simulator_config)
        n_nodes = self.config.simulator_config.drillstring_params.n_nodes
        n_state = 2 * n_nodes
        self._state_derivative = build_state_derivative(
            self.config.simulator_config.drillstring_params,
            self._simulator._friction_coeffs,  # noqa: SLF001 — mismo preset activo
        )
        sigma = SigmaPointParameters(n=n_state, alpha=1.0e-3, beta=2.0, kappa=0.0)
        x0 = np.zeros(n_state, dtype=np.float64)
        p0 = np.eye(n_state, dtype=np.float64) * 1.0e-4
        q0 = np.eye(n_state, dtype=np.float64) * self.config.process_noise_scale
        self._ukf = UnscentedKalmanFilter(
            initial_state=x0,
            initial_covariance=p0,
            process_noise=q0,
            state_derivative=self._state_derivative,
            sigma_params=sigma,
        )
        max_entries = int(
            math.ceil(self.config.buffer_window_sec / self.config.dt_surface)
        ) + 16
        self._buffer = TimeSyncBuffer(
            window_sec=self.config.buffer_window_sec,
            max_entries=max_entries,
        )
        self._r_surface = np.diag(
            np.asarray(self.config.r_surface_diag, dtype=np.float64)
        )
        self._r_mwd = np.diag(np.asarray(self.config.r_mwd_diag, dtype=np.float64))
        self._omega_window = deque(maxlen=self.config.ssi_window_size)
        self._correction_tasks = set()
        self._advisor_tasks = set()
        if self.advisor is None:
            self.advisor = DrillingAdvisor(provider=DeterministicMockLLMProvider())
        if self.advisor_store is None:
            self.advisor_store = AdvisorHistoryStore()

    def _rebuild_derivative(self) -> None:
        self._state_derivative = build_state_derivative(
            self.config.simulator_config.drillstring_params,
            self._simulator._friction_coeffs,  # noqa: SLF001
        )
        self._ukf.state_derivative = self._state_derivative

    def start(self, preset: ScenarioName | None = None) -> None:
        """Arranca el loop físico (idempotente si ya está running)."""
        if preset is not None:
            self.set_preset(preset)
        if self._running:
            return
        self._simulator.reset()
        self._buffer.clear()
        self._omega_window.clear()
        self._frame_id = 0
        self._mwd_drops = 0
        n_state = self._ukf.sigma_params.n
        self._ukf.x = np.zeros(n_state, dtype=np.float64)
        self._ukf.p = np.eye(n_state, dtype=np.float64) * 1.0e-4
        self._ukf._predicted_sigma_points = None  # noqa: SLF001
        self._latest_broadcast = None
        self._running = True
        if self.advisor_store is not None:
            self.advisor_store.clear()
        if self.advisor is not None:
            self.advisor._in_incident = False  # noqa: SLF001
            self.advisor._last_emitted_monotonic = None  # noqa: SLF001

    def stop(self) -> None:
        """Detiene el loop físico."""
        self._running = False

    def set_preset(self, preset: ScenarioName) -> None:
        """Cambia el preset del simulador y reconstruye la dinámica UKF."""
        self._simulator.load_preset(preset)
        self._rebuild_derivative()

    @property
    def status(self) -> OrchestratorStatusDTO:
        """Estado operativo expuesto por la API REST."""
        return OrchestratorStatusDTO(
            running=self._running,
            preset=self._simulator.scenario,
            sim_time_s=float(self._simulator.time_s),
            mwd_drops=self._mwd_drops,
        )

    @property
    def latest_broadcast(self) -> TelemetryStreamBroadcastDTO | None:
        """Último frame consolidado (o ``None`` si aún no hay)."""
        return self._latest_broadcast

    @property
    def is_running(self) -> bool:
        """``True`` si el loop físico está activo."""
        return self._running

    async def run_physics_loop(self) -> None:
        """Loop a ``dt_surface`` mientras ``running``; cancela con ``CancelledError``."""
        dt = self.config.dt_surface
        try:
            while True:
                if self._running:
                    await self._physics_tick(dt)
                await asyncio.sleep(dt)
        except asyncio.CancelledError:
            raise

    async def run_broadcast_loop(self, connections: ConnectionManager) -> None:
        """Emite el último estado consolidado a ~``broadcast_fps``."""
        period = 1.0 / self.config.broadcast_fps
        try:
            while True:
                payload = self._latest_broadcast
                if self._running and payload is not None:
                    await connections.broadcast(payload)
                await asyncio.sleep(period)
        except asyncio.CancelledError:
            raise

    async def _physics_tick(self, dt: float) -> None:
        u_rpm = self.config.u_top_rpm
        wob = self.config.wob_kn
        u_top = u_rpm * _RPM_TO_RAD_S
        drive = self.config.simulator_config.drillstring_params.top_drive_damping

        step = self._simulator.step(dt, u_rpm, wob)
        surface = self._simulator.get_surface_telemetry()
        self._last_surface_rpm = float(surface.rpm_surface)
        self._last_torque_surface_knm = float(surface.torque_surface_knm)
        z_surface = np.asarray(
            [surface.rpm_surface, surface.torque_surface_knm],
            dtype=np.float64,
        )
        h_surface = build_surface_h_fn(u_top, drive)

        async with self._state_lock:
            self._ukf.predict(dt, u_top, wob)
            self._ukf.update(z_surface, h_surface, self._r_surface)
            x_copy = np.array(self._ukf.x, dtype=np.float64, copy=True)
            p_copy = np.array(self._ukf.p, dtype=np.float64, copy=True)

        await self._buffer.record(
            UkfJournalEntry(
                timestamp_s=step.time_s,
                state=x_copy,
                covariance=p_copy,
                dt=dt,
                u_top_rad_s=u_top,
                wob_kn=wob,
                z_surface=z_surface,
                r_surface=self._r_surface,
            )
        )

        for mwd in self._simulator.get_available_mwd_telemetry(step.time_s):
            task = asyncio.create_task(self._apply_mwd_correction(mwd))
            self._correction_tasks.add(task)
            task.add_done_callback(self._correction_tasks.discard)

        await self._refresh_broadcast(x_copy, step.time_s)

    async def _refresh_broadcast(
        self,
        state: NDArray[np.float64],
        time_s: float,
    ) -> None:
        n_nodes = self.config.simulator_config.drillstring_params.n_nodes
        theta = [float(state[2 * i]) for i in range(n_nodes)]
        omega = [float(state[2 * i + 1]) for i in range(n_nodes)]
        omega_bit = omega[-1]
        self._omega_window.append(omega_bit)

        rpm_bit = max(0.0, omega_bit * _RAD_S_TO_RPM)
        h_mwd = build_mwd_h_fn(
            self.config.wob_kn,
            self.config.simulator_config.drillstring_params.bit_radius_m,
            self._simulator._friction_coeffs,  # noqa: SLF001
        )
        z_bit = h_mwd(state)
        torque_bit = float(z_bit[1])

        if len(self._omega_window) >= 2:
            window = np.asarray(list(self._omega_window), dtype=np.float64)
            omega_nom = max(abs(float(np.mean(window))), 1.0e-3)
            ssi_result = compute_ssi(window, omega_nom)
            ssi_val = max(0.0, float(ssi_result.ssi))
            alert = _regime_to_alert(ssi_result.regime)
        else:
            ssi_val = 0.0
            alert = "normal"

        # Deformación torsional relativa al nodo de superficie.
        deformation = [t - theta[0] for t in theta]
        start = self._simulator._start_utc  # noqa: SLF001
        ts = start + timedelta(seconds=float(time_s))
        self._frame_id += 1
        broadcast = TelemetryStreamBroadcastDTO(
            timestamp=ts,
            frame_id=self._frame_id,
            ukf_state=UkfStateDTO(
                theta_rad=theta,
                omega_rad_s=omega,
                rpm_bit_est=rpm_bit,
                torque_bit_est_knm=torque_bit,
            ),
            torsional_deformation_rad=deformation,
            ssi=ssi_val,
            alert_level=alert,
        )
        self._latest_broadcast = broadcast

        snapshot = AdvisorIncidentSnapshot(
            timestamp=ts,
            surface_rpm=max(0.0, self._last_surface_rpm),
            estimated_bit_rpm=rpm_bit,
            wob_kn=self.config.wob_kn,
            ssi=ssi_val,
            regime=alert,
            torque_contrast=self._last_torque_surface_knm - torque_bit,
        )
        task = asyncio.create_task(self._maybe_trigger_advisor(snapshot))
        self._advisor_tasks.add(task)
        task.add_done_callback(self._advisor_tasks.discard)

    async def _maybe_trigger_advisor(
        self,
        snapshot: AdvisorIncidentSnapshot,
    ) -> None:
        """Evalúa el Advisor sin bloquear el tick físico; emite REST/WS si hay rec."""
        if self.advisor is None:
            return
        recommendation = await self.advisor.evaluate_telemetry(snapshot)
        if recommendation is None:
            return
        record = AdvisorRecommendationRecordDTO(
            recommendation=recommendation,
            triggered_at=snapshot.timestamp,
            snapshot=snapshot,
        )
        if self.advisor_store is not None:
            self.advisor_store.append(record)
        if self.connections is not None:
            await self.connections.broadcast_advisor(record)

    def _replay_fixed_lag(
        self,
        mwd: MwdTelemetrySample,
        anchor_state: NDArray[np.float64],
        anchor_cov: NDArray[np.float64],
        replay_entries: tuple[UkfJournalEntry, ...],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Ejecuta update MWD en el ancla y re-propaga el journal (CPU-bound)."""
        n = self._ukf.sigma_params.n
        ephemeral = UnscentedKalmanFilter(
            initial_state=anchor_state,
            initial_covariance=anchor_cov,
            process_noise=np.array(self._ukf.q, dtype=np.float64, copy=True),
            state_derivative=self._state_derivative,
            sigma_params=self._ukf.sigma_params,
            jitter=self._ukf.jitter,
        )
        # Segunda medición en el mismo instante: regenerar sigma del posterior.
        ephemeral._predicted_sigma_points = compute_sigma_points(  # noqa: SLF001
            ephemeral.x,
            ephemeral.p,
            ephemeral.sigma_params,
            jitter=ephemeral.jitter,
        )
        h_mwd = build_mwd_h_fn(
            float(mwd.wob_kn),
            self.config.simulator_config.drillstring_params.bit_radius_m,
            self._simulator._friction_coeffs,  # noqa: SLF001
        )
        z_mwd = np.asarray(
            [mwd.rpm_downhole, mwd.torque_downhole_knm],
            dtype=np.float64,
        )
        ephemeral.update(z_mwd, h_mwd, self._r_mwd)

        drive = self.config.simulator_config.drillstring_params.top_drive_damping
        for entry in replay_entries:
            ephemeral.predict(entry.dt, entry.u_top_rad_s, entry.wob_kn)
            if entry.z_surface is not None and entry.r_surface is not None:
                h_s = build_surface_h_fn(entry.u_top_rad_s, drive)
                ephemeral.update(entry.z_surface, h_s, entry.r_surface)

        assert ephemeral.x.shape == (n,)
        return (
            np.array(ephemeral.x, dtype=np.float64, copy=True),
            np.array(ephemeral.p, dtype=np.float64, copy=True),
        )

    async def _apply_mwd_correction(self, mwd: MwdTelemetrySample) -> None:
        """Fixed-lag smoothing: alinea MWD, rejuega journal y swap del filtro vivo."""
        alignment = await self._buffer.align(mwd.origin_time_s)
        if alignment is None:
            self._mwd_drops += 1
            return

        x_corr, p_corr = await asyncio.to_thread(
            self._replay_fixed_lag,
            mwd,
            alignment.anchor.state,
            alignment.anchor.covariance,
            alignment.replay_entries,
        )
        async with self._state_lock:
            self._ukf.x = x_corr
            self._ukf.p = p_corr
            self._ukf._predicted_sigma_points = None  # noqa: SLF001


__all__ = [
    "OrchestratorConfig",
    "SimulationOrchestrator",
]
