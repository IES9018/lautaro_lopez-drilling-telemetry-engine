"""Modelos de fricción torsional broca-roca (Stribeck regularizado)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class StribeckParameters:
    """Parámetros del modelo de fricción Stribeck regularizado.

    Formulación (SPEC §2.3, variante regularizada en ω=0):

        T_bit(ω) = [T_c + (T_s - T_c) · exp(-γ · |ω|)] · tanh(ω / ω_ε) + c_v · ω

    Attributes:
        t_coulomb: Torque Coulomb dinámico T_c [N·m], ≥ 0.
        t_static: Torque estático T_s [N·m], ≥ t_coulomb.
        gamma: Coeficiente de decaimiento Stribeck γ [s/rad], > 0.
        omega_eps: Escala de regularización ω_ε [rad/s], > 0.
        c_viscous: Coeficiente viscoso c_v [N·m·s/rad].
    """

    t_coulomb: float
    t_static: float
    gamma: float
    omega_eps: float
    c_viscous: float

    def __post_init__(self) -> None:
        if self.t_coulomb < 0.0:
            msg = f"t_coulomb must be >= 0, got {self.t_coulomb}"
            raise ValueError(msg)
        if self.t_static < self.t_coulomb:
            msg = (
                f"t_static must be >= t_coulomb "
                f"({self.t_static} < {self.t_coulomb})"
            )
            raise ValueError(msg)
        if self.gamma <= 0.0:
            msg = f"gamma must be > 0, got {self.gamma}"
            raise ValueError(msg)
        if self.omega_eps <= 0.0:
            msg = f"omega_eps must be > 0, got {self.omega_eps}"
            raise ValueError(msg)


def stribeck_friction_torque(
    omega: NDArray[np.float64],
    params: StribeckParameters,
) -> NDArray[np.float64]:
    """Torque de fricción Stribeck regularizado, vectorizado.

    Args:
        omega: Velocidades angulares [rad/s], shape arbitraria.
        params: Parámetros inmutables del modelo.

    Returns:
        Torque T_bit(ω) [N·m], misma shape que ``omega``.
    """
    omega_arr: NDArray[np.float64] = np.asarray(omega, dtype=np.float64)
    magnitude = params.t_coulomb + (params.t_static - params.t_coulomb) * np.exp(
        -params.gamma * np.abs(omega_arr)
    )
    regularized = magnitude * np.tanh(omega_arr / params.omega_eps)
    return regularized + params.c_viscous * omega_arr
