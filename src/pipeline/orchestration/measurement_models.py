"""Modelos de medición h(x) para el UKF (superficie y MWD).

Viven en el dominio pipeline para no modificar ``src/engine/physics``.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from src.engine.physics.drillstring_fem import (
    BitFrictionCoefficients,
    bit_stribeck_parameters,
)
from src.engine.physics.friction_models import stribeck_friction_torque

_RAD_S_TO_RPM = 60.0 / (2.0 * np.pi)
_N_M_TO_KN_M = 1.0e-3

MeasurementFn = Callable[[NDArray[np.float64]], NDArray[np.float64]]


def build_surface_h_fn(
    u_top_rad_s: float,
    drive_damping: float,
) -> MeasurementFn:
    """Construye ``h(x)`` de superficie: ``[rpm_0, torque_surface_knm]``.

    Parameters
    ----------
    u_top_rad_s : float
        Referencia de top-drive [rad/s].
    drive_damping : float
        ``c_drive`` [N·m·s/rad] del modelo de sarta.

    Returns
    -------
    MeasurementFn
        Función de medición sobre el estado interleaved.
    """

    def h_fn(state: NDArray[np.float64]) -> NDArray[np.float64]:
        arr = np.asarray(state, dtype=np.float64)
        omega_0 = float(arr[1])
        torque_nm = drive_damping * (u_top_rad_s - omega_0)
        return np.asarray(
            [omega_0 * _RAD_S_TO_RPM, torque_nm * _N_M_TO_KN_M],
            dtype=np.float64,
        )

    return h_fn


def build_mwd_h_fn(
    wob_kn: float,
    bit_radius_m: float,
    friction_coeffs: BitFrictionCoefficients,
) -> MeasurementFn:
    """Construye ``h(x)`` MWD: ``[rpm_bit, torque_bit_knm]``.

    Parameters
    ----------
    wob_kn : float
        Weight on Bit [kN], ≥ 0.
    bit_radius_m : float
        Radio efectivo de broca [m].
    friction_coeffs : BitFrictionCoefficients
        Coeficientes Stribeck (solo lectura del engine).

    Returns
    -------
    MeasurementFn
        Función de medición sobre el estado interleaved.
    """
    stribeck = bit_stribeck_parameters(wob_kn, bit_radius_m, friction_coeffs)

    def h_fn(state: NDArray[np.float64]) -> NDArray[np.float64]:
        arr = np.asarray(state, dtype=np.float64)
        omega_bit = float(arr[-1])
        torque_nm = float(
            stribeck_friction_torque(
                np.asarray(omega_bit, dtype=np.float64),
                stribeck,
            )
        )
        return np.asarray(
            [omega_bit * _RAD_S_TO_RPM, torque_nm * _N_M_TO_KN_M],
            dtype=np.float64,
        )

    return h_fn


__all__ = [
    "MeasurementFn",
    "build_mwd_h_fn",
    "build_surface_h_fn",
]
