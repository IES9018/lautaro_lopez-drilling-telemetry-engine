"""Generador de telemetría sintética de pozo (ground truth + ruido + retardo MWD)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from src.engine.physics.drillstring_fem import (
    BitFrictionCoefficients,
    DrillstringParameters,
    StateDerivativeFn,
    bit_stribeck_parameters,
    build_state_derivative,
    build_uniform_drillstring,
)
from src.engine.physics.friction_models import stribeck_friction_torque
from src.engine.physics.integrators import rk4_step

ScenarioName = Literal["normal", "severe_stick_slip", "transient_choke"]

_RPM_TO_RAD_S = 2.0 * np.pi / 60.0
_RAD_S_TO_RPM = 60.0 / (2.0 * np.pi)
_N_M_TO_KN_M = 1.0e-3


@dataclass(frozen=True, slots=True)
class NoiseConfig:
    """Desviaciones estándar de ruido gaussiano por sensor.

    Parameters
    ----------
    rpm_surface_std : float
        σ de RPM de superficie [rpm].
    torque_surface_knm_std : float
        σ de torque de superficie [kN·m].
    hookload_kn_std : float
        σ de hookload [kN].
    standpipe_pressure_kpa_std : float
        σ de presión de standpipe [kPa].
    rpm_downhole_std : float
        σ de RPM de fondo [rpm].
    torque_downhole_knm_std : float
        σ de torque de fondo [kN·m].
    wob_kn_std : float
        σ de Weight on Bit reportado [kN].
    """

    rpm_surface_std: float
    torque_surface_knm_std: float
    hookload_kn_std: float
    standpipe_pressure_kpa_std: float
    rpm_downhole_std: float
    torque_downhole_knm_std: float
    wob_kn_std: float

    def __post_init__(self) -> None:
        for name, value in (
            ("rpm_surface_std", self.rpm_surface_std),
            ("torque_surface_knm_std", self.torque_surface_knm_std),
            ("hookload_kn_std", self.hookload_kn_std),
            ("standpipe_pressure_kpa_std", self.standpipe_pressure_kpa_std),
            ("rpm_downhole_std", self.rpm_downhole_std),
            ("torque_downhole_knm_std", self.torque_downhole_knm_std),
            ("wob_kn_std", self.wob_kn_std),
        ):
            if value < 0.0:
                msg = f"{name} must be >= 0, got {value}"
                raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class SimulatorConfig:
    """Configuración del simulador de pozo sintético.

    Parameters
    ----------
    drillstring_params : DrillstringParameters
        Parámetros lumped de la sarta.
    friction_coeffs : BitFrictionCoefficients
        Coeficientes de fricción broca-roca.
    dt_internal : float
        Paso de integración físico RK4 [s] (p. ej. 0.001 → 1000 Hz).
    noise_config : NoiseConfig
        σ por canal de telemetría.
    mwd_interval_sec : float
        Intervalo de muestreo MWD en origen [s] (p. ej. 20.0).
    acoustic_delay_sec : float
        Retardo acústico mud-pulse [s] (típicamente 15–45).
    seed : int
        Semilla para ``numpy.random.default_rng``.
    hookload_base_kn : float
        Hookload nominal sin ruido [kN].
    standpipe_base_kpa : float
        Presión de standpipe nominal sin ruido [kPa].
    """

    drillstring_params: DrillstringParameters
    friction_coeffs: BitFrictionCoefficients
    dt_internal: float
    noise_config: NoiseConfig
    mwd_interval_sec: float
    acoustic_delay_sec: float
    seed: int
    hookload_base_kn: float = 800.0
    standpipe_base_kpa: float = 15000.0

    def __post_init__(self) -> None:
        if self.dt_internal <= 0.0:
            msg = f"dt_internal must be > 0, got {self.dt_internal}"
            raise ValueError(msg)
        if self.mwd_interval_sec <= 0.0:
            msg = f"mwd_interval_sec must be > 0, got {self.mwd_interval_sec}"
            raise ValueError(msg)
        if self.acoustic_delay_sec < 0.0:
            msg = f"acoustic_delay_sec must be >= 0, got {self.acoustic_delay_sec}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class SimulationStepResult:
    """Estado ground-truth tras un avance de simulación.

    Parameters
    ----------
    time_s : float
        Tiempo de simulación [s] desde el arranque.
    state : NDArray[np.float64]
        Vector de estado interleaved ``[θ_0, ω_0, …]`` [rad, rad/s].
    rpm_surface_true : float
        RPM verdadera en nodo 0 [rpm].
    rpm_bit_true : float
        RPM verdadera en broca [rpm].
    torque_surface_knm_true : float
        Torque de accionamiento verdadero [kN·m].
    torque_bit_knm_true : float
        Torque de fricción en broca verdadero [kN·m].
    u_top_rad_s : float
        Referencia de top-drive aplicada [rad/s].
    wob_kn : float
        Weight on Bit aplicado [kN].
    """

    time_s: float
    state: NDArray[np.float64]
    rpm_surface_true: float
    rpm_bit_true: float
    torque_surface_knm_true: float
    torque_bit_knm_true: float
    u_top_rad_s: float
    wob_kn: float


@dataclass(frozen=True, slots=True)
class SurfaceTelemetrySample:
    """Muestra de telemetría de superficie (contrato ``surface.telemetry.v1``).

    Parameters
    ----------
    timestamp : str
        Instantánea UTC ISO-8601.
    hookload_kn : float
        Hookload [kN].
    rpm_surface : float
        RPM de superficie [rpm] (≥ 0 tras clip).
    torque_surface_knm : float
        Torque de superficie [kN·m].
    standpipe_pressure_kpa : float
        Presión de standpipe [kPa] (≥ 0 tras clip).
    """

    timestamp: str
    hookload_kn: float
    rpm_surface: float
    torque_surface_knm: float
    standpipe_pressure_kpa: float


@dataclass(frozen=True, slots=True)
class MwdTelemetrySample:
    """Muestra MWD disponible tras el retardo acústico (``mwd.telemetry.v1``).

    Parameters
    ----------
    timestamp : str
        UTC ISO-8601 del instante de **origen** de la medición.
    acoustic_delay_s : float
        Retardo acústico aplicado [s].
    rpm_downhole : float
        RPM de fondo [rpm] (≥ 0 tras clip).
    torque_downhole_knm : float
        Torque de fondo [kN·m].
    wob_kn : float
        Weight on Bit [kN].
    origin_time_s : float
        Tiempo de simulación de origen [s] (trazabilidad de retardo).
    """

    timestamp: str
    acoustic_delay_s: float
    rpm_downhole: float
    torque_downhole_knm: float
    wob_kn: float
    origin_time_s: float


@dataclass(frozen=True, slots=True)
class _PendingMwd:
    """Paquete MWD en cola hasta que expire el retardo acústico."""

    origin_time_s: float
    rpm_downhole_true: float
    torque_downhole_knm_true: float
    wob_kn_true: float


@dataclass
class WellSimulator:
    """Simulador de pozo: física RK4 + telemetría ruidosa + retardo MWD.

    Parameters
    ----------
    config : SimulatorConfig
        Configuración inmutable del escenario.
    """

    config: SimulatorConfig
    _time_s: float = field(default=0.0, init=False, repr=False)
    _state: NDArray[np.float64] = field(init=False, repr=False)
    _state_derivative: StateDerivativeFn = field(init=False, repr=False)
    _rng: np.random.Generator = field(init=False, repr=False)
    _last_step: SimulationStepResult | None = field(default=None, init=False, repr=False)
    _pending_mwd: list[_PendingMwd] = field(default_factory=list, init=False, repr=False)
    _next_mwd_origin_s: float = field(init=False, repr=False)
    _start_utc: datetime = field(init=False, repr=False)
    _friction_coeffs: BitFrictionCoefficients = field(init=False, repr=False)
    _scenario: ScenarioName = field(default="normal", init=False, repr=False)

    def __post_init__(self) -> None:
        n = self.config.drillstring_params.n_nodes
        self._friction_coeffs = self.config.friction_coeffs
        self._state = np.zeros(2 * n, dtype=np.float64)
        self._rng = np.random.default_rng(self.config.seed)
        self._start_utc = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)
        self._pending_mwd = []
        self._next_mwd_origin_s = self.config.mwd_interval_sec
        self._rebuild_derivative()

    def _rebuild_derivative(self) -> None:
        self._state_derivative = build_state_derivative(
            self.config.drillstring_params,
            self._friction_coeffs,
        )

    def load_preset(self, scenario: ScenarioName) -> None:
        """Carga coeficientes de fricción / condiciones de un escenario nombrado.

        Parameters
        ----------
        scenario : {"normal", "severe_stick_slip", "transient_choke"}
            Preset operativo.
        """
        if scenario == "normal":
            self._friction_coeffs = BitFrictionCoefficients(
                mu_static=0.25,
                mu_coulomb=0.18,
                gamma=0.05,
                omega_eps=1e-2,
                c_viscous=1.0,
            )
        elif scenario == "severe_stick_slip":
            self._friction_coeffs = BitFrictionCoefficients(
                mu_static=0.65,
                mu_coulomb=0.12,
                gamma=0.04,
                omega_eps=5e-3,
                c_viscous=0.2,
            )
        elif scenario == "transient_choke":
            self._friction_coeffs = BitFrictionCoefficients(
                mu_static=0.40,
                mu_coulomb=0.20,
                gamma=0.06,
                omega_eps=1e-2,
                c_viscous=0.8,
            )
        else:
            msg = f"unknown scenario: {scenario}"
            raise ValueError(msg)
        self._scenario = scenario
        self._rebuild_derivative()

    def reset(self, seed: int | None = None) -> None:
        """Reinicia estado, reloj y colas MWD.

        Parameters
        ----------
        seed : int or None
            Si se indica, reemplaza el RNG; si no, reutiliza ``config.seed``.
        """
        n = self.config.drillstring_params.n_nodes
        self._time_s = 0.0
        self._state = np.zeros(2 * n, dtype=np.float64)
        self._last_step = None
        self._pending_mwd = []
        self._next_mwd_origin_s = self.config.mwd_interval_sec
        use_seed = self.config.seed if seed is None else seed
        self._rng = np.random.default_rng(use_seed)

    def step(
        self,
        dt: float,
        u_top_rpm: float,
        wob_kn: float,
    ) -> SimulationStepResult:
        """Avanza la física ``dt`` segundos con subpasos ``dt_internal``.

        Parameters
        ----------
        dt : float
            Horizonte a integrar [s] (p. ej. 0.01 s para 100 Hz).
        u_top_rpm : float
            RPM de referencia del top-drive [rpm].
        wob_kn : float
            Weight on Bit [kN], ≥ 0.

        Returns
        -------
        SimulationStepResult
            Ground truth al final del intervalo.
        """
        if dt <= 0.0:
            msg = f"dt must be > 0, got {dt}"
            raise ValueError(msg)
        if wob_kn < 0.0:
            msg = f"wob_kn must be >= 0, got {wob_kn}"
            raise ValueError(msg)

        u_top = float(u_top_rpm) * _RPM_TO_RAD_S
        dt_int = self.config.dt_internal
        # A-004: si dt no es múltiplo exacto de dt_internal, se usa n_sub = round(dt/dt_int)
        # y sub_dt = dt/n_sub (conserva el horizonte dt a costa de un paso ligeramente distinto).
        n_sub = max(1, int(round(dt / dt_int)))
        sub_dt = dt / float(n_sub)

        def deriv(t: float, y: NDArray[np.float64]) -> NDArray[np.float64]:
            return self._state_derivative(t, y, u_top, wob_kn)

        y = self._state
        t_local = self._time_s
        for _ in range(n_sub):
            y = rk4_step(deriv, t_local, y, sub_dt)
            t_local += sub_dt

        self._state = y
        self._time_s = t_local

        omega_0 = float(y[1])
        omega_bit = float(y[-1])
        c_drive = self.config.drillstring_params.top_drive_damping
        torque_surface_nm = c_drive * (u_top - omega_0)
        stribeck = bit_stribeck_parameters(
            wob_kn,
            self.config.drillstring_params.bit_radius_m,
            self._friction_coeffs,
        )
        torque_bit_nm = float(
            stribeck_friction_torque(
                np.asarray(omega_bit, dtype=np.float64),
                stribeck,
            )
        )

        result = SimulationStepResult(
            time_s=self._time_s,
            state=np.array(y, dtype=np.float64, copy=True),
            rpm_surface_true=omega_0 * _RAD_S_TO_RPM,
            rpm_bit_true=omega_bit * _RAD_S_TO_RPM,
            torque_surface_knm_true=torque_surface_nm * _N_M_TO_KN_M,
            torque_bit_knm_true=torque_bit_nm * _N_M_TO_KN_M,
            u_top_rad_s=u_top,
            wob_kn=wob_kn,
        )
        self._last_step = result
        self._maybe_enqueue_mwd(result)
        return result

    def _maybe_enqueue_mwd(self, result: SimulationStepResult) -> None:
        while result.time_s + 1e-15 >= self._next_mwd_origin_s:
            self._pending_mwd.append(
                _PendingMwd(
                    origin_time_s=self._next_mwd_origin_s,
                    rpm_downhole_true=result.rpm_bit_true,
                    torque_downhole_knm_true=result.torque_bit_knm_true,
                    wob_kn_true=result.wob_kn,
                )
            )
            self._next_mwd_origin_s += self.config.mwd_interval_sec

    def get_surface_telemetry(self) -> SurfaceTelemetrySample:
        """Telemetría de superficie con ruido gaussiano (≈100 Hz si ``step``=0.01 s).

        Returns
        -------
        SurfaceTelemetrySample
            Lectura ruidosa alineada a ``surface.telemetry.v1``.
        """
        if self._last_step is None:
            msg = "call step() before get_surface_telemetry()"
            raise RuntimeError(msg)
        noise = self.config.noise_config
        step = self._last_step
        rpm = step.rpm_surface_true + float(self._rng.normal(0.0, noise.rpm_surface_std))
        torque = step.torque_surface_knm_true + float(
            self._rng.normal(0.0, noise.torque_surface_knm_std)
        )
        hook = self.config.hookload_base_kn - step.wob_kn + float(
            self._rng.normal(0.0, noise.hookload_kn_std)
        )
        spp = self.config.standpipe_base_kpa + float(
            self._rng.normal(0.0, noise.standpipe_pressure_kpa_std)
        )
        return SurfaceTelemetrySample(
            timestamp=self._iso_utc(step.time_s),
            hookload_kn=hook,
            rpm_surface=max(0.0, rpm),
            torque_surface_knm=torque,
            standpipe_pressure_kpa=max(0.0, spp),
        )

    def get_available_mwd_telemetry(
        self,
        current_time: float,
    ) -> list[MwdTelemetrySample]:
        """Devuelve paquetes MWD cuyo retardo acústico ya expiró.

        Parameters
        ----------
        current_time : float
            Tiempo de simulación del receptor [s].

        Returns
        -------
        list of MwdTelemetrySample
            Paquetes liberados (se remueven de la cola interna).
        """
        if current_time < 0.0:
            msg = f"current_time must be >= 0, got {current_time}"
            raise ValueError(msg)

        delay = self.config.acoustic_delay_sec
        noise = self.config.noise_config
        ready: list[MwdTelemetrySample] = []
        remaining: list[_PendingMwd] = []
        for pending in self._pending_mwd:
            arrival = pending.origin_time_s + delay
            if arrival <= current_time + 1e-15:
                rpm = pending.rpm_downhole_true + float(
                    self._rng.normal(0.0, noise.rpm_downhole_std)
                )
                torque = pending.torque_downhole_knm_true + float(
                    self._rng.normal(0.0, noise.torque_downhole_knm_std)
                )
                wob = pending.wob_kn_true + float(self._rng.normal(0.0, noise.wob_kn_std))
                ready.append(
                    MwdTelemetrySample(
                        timestamp=self._iso_utc(pending.origin_time_s),
                        acoustic_delay_s=delay,
                        rpm_downhole=max(0.0, rpm),
                        torque_downhole_knm=torque,
                        wob_kn=wob,
                        origin_time_s=pending.origin_time_s,
                    )
                )
            else:
                remaining.append(pending)
        self._pending_mwd = remaining
        return ready

    def _iso_utc(self, time_s: float) -> str:
        instant = self._start_utc + timedelta(seconds=float(time_s))
        return instant.isoformat().replace("+00:00", "Z")

    @property
    def time_s(self) -> float:
        """Tiempo de simulación actual [s]."""
        return self._time_s

    @property
    def scenario(self) -> ScenarioName:
        """Preset activo."""
        return self._scenario


def default_simulator_config(
    *,
    seed: int = 42,
    dt_internal: float = 1.0e-3,
    mwd_interval_sec: float = 20.0,
    acoustic_delay_sec: float = 20.0,
) -> SimulatorConfig:
    """Factory de configuración baseline para tests y demos.

    Parameters
    ----------
    seed : int
        Semilla RNG.
    dt_internal : float
        Paso RK4 [s].
    mwd_interval_sec : float
        Intervalo MWD [s].
    acoustic_delay_sec : float
        Retardo acústico [s].

    Returns
    -------
    SimulatorConfig
    """
    drillstring = build_uniform_drillstring(
        n_nodes=6,
        density_kg_m3=7850.0,
        shear_modulus_pa=8.0e10,
        polar_moment_of_inertia_m4=1.2e-5,
        total_length_m=1500.0,
        nodal_damping_coeff=8.0,
        top_drive_damping=800.0,
        bit_radius_m=0.108,
    )
    friction = BitFrictionCoefficients(
        mu_static=0.25,
        mu_coulomb=0.18,
        gamma=0.05,
        omega_eps=1e-2,
        c_viscous=1.0,
    )
    noise = NoiseConfig(
        rpm_surface_std=0.4,
        torque_surface_knm_std=0.05,
        hookload_kn_std=2.0,
        standpipe_pressure_kpa_std=50.0,
        rpm_downhole_std=1.0,
        torque_downhole_knm_std=0.08,
        wob_kn_std=1.5,
    )
    return SimulatorConfig(
        drillstring_params=drillstring,
        friction_coeffs=friction,
        dt_internal=dt_internal,
        noise_config=noise,
        mwd_interval_sec=mwd_interval_sec,
        acoustic_delay_sec=acoustic_delay_sec,
        seed=seed,
    )


# Re-export for callers that type-check against friction helpers.
__all__ = [
    "MwdTelemetrySample",
    "NoiseConfig",
    "SimulationStepResult",
    "SimulatorConfig",
    "SurfaceTelemetrySample",
    "WellSimulator",
    "default_simulator_config",
]
