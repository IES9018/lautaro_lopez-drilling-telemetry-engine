"""Modelo de espacio de estados de la sarta torsional discretizada (lumped / FEM 1D)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.engine.physics.friction_models import (
    StribeckParameters,
    stribeck_friction_torque,
)

StateDerivativeFn = Callable[
    [float, NDArray[np.float64], float, float],
    NDArray[np.float64],
]


@dataclass(frozen=True, slots=True)
class DrillstringParameters:
    """Parámetros lumped de una sarta torsional de N nodos.

    Attributes:
        n_nodes: Número de nodos N (≥ 2).
        inertia: Inercias nodales I_i [kg·m²], shape (N,), > 0.
        stiffness: Rigideces de segmento k_i [N·m/rad], shape (N-1,), > 0.
        damping: Amortiguamiento viscoso nodal c_i [N·m·s/rad], shape (N,), ≥ 0.
        top_drive_damping: Ganancia de control de velocidad c_drive [N·m·s/rad], > 0.
        bit_radius_m: Radio efectivo de broca [m], > 0.
    """

    n_nodes: int
    inertia: NDArray[np.float64]
    stiffness: NDArray[np.float64]
    damping: NDArray[np.float64]
    top_drive_damping: float
    bit_radius_m: float

    def __post_init__(self) -> None:
        inertia = np.array(self.inertia, dtype=np.float64, copy=True)
        stiffness = np.array(self.stiffness, dtype=np.float64, copy=True)
        damping = np.array(self.damping, dtype=np.float64, copy=True)
        object.__setattr__(self, "inertia", inertia)
        object.__setattr__(self, "stiffness", stiffness)
        object.__setattr__(self, "damping", damping)

        if self.n_nodes < 2:
            msg = f"n_nodes must be >= 2, got {self.n_nodes}"
            raise ValueError(msg)
        if inertia.shape != (self.n_nodes,):
            msg = (
                f"inertia must have shape ({self.n_nodes},), "
                f"got {inertia.shape}"
            )
            raise ValueError(msg)
        if stiffness.shape != (self.n_nodes - 1,):
            msg = (
                f"stiffness must have shape ({self.n_nodes - 1},), "
                f"got {stiffness.shape}"
            )
            raise ValueError(msg)
        if damping.shape != (self.n_nodes,):
            msg = (
                f"damping must have shape ({self.n_nodes},), "
                f"got {damping.shape}"
            )
            raise ValueError(msg)
        if np.any(inertia <= 0.0):
            msg = "inertia elements must be > 0"
            raise ValueError(msg)
        if np.any(stiffness <= 0.0):
            msg = "stiffness elements must be > 0"
            raise ValueError(msg)
        if np.any(damping < 0.0):
            msg = "damping elements must be >= 0"
            raise ValueError(msg)
        if self.top_drive_damping <= 0.0:
            msg = f"top_drive_damping must be > 0, got {self.top_drive_damping}"
            raise ValueError(msg)
        if self.bit_radius_m <= 0.0:
            msg = f"bit_radius_m must be > 0, got {self.bit_radius_m}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BitFrictionCoefficients:
    """Coeficientes adimensionales / viscosos para fricción broca-roca vía WOB."""

    mu_static: float
    mu_coulomb: float
    gamma: float
    omega_eps: float
    c_viscous: float

    def __post_init__(self) -> None:
        if self.mu_coulomb < 0.0:
            msg = f"mu_coulomb must be >= 0, got {self.mu_coulomb}"
            raise ValueError(msg)
        if self.mu_static < self.mu_coulomb:
            msg = (
                f"mu_static must be >= mu_coulomb "
                f"({self.mu_static} < {self.mu_coulomb})"
            )
            raise ValueError(msg)
        if self.gamma <= 0.0:
            msg = f"gamma must be > 0, got {self.gamma}"
            raise ValueError(msg)
        if self.omega_eps <= 0.0:
            msg = f"omega_eps must be > 0, got {self.omega_eps}"
            raise ValueError(msg)
        if self.c_viscous < 0.0:
            msg = f"c_viscous must be >= 0, got {self.c_viscous}"
            raise ValueError(msg)


def build_uniform_drillstring(
    n_nodes: int,
    density_kg_m3: float,
    shear_modulus_pa: float,
    polar_moment_of_inertia_m4: float,
    total_length_m: float,
    nodal_damping_coeff: float,
    top_drive_damping: float,
    bit_radius_m: float,
) -> DrillstringParameters:
    """Construye una sarta uniforme a partir de propiedades continuas.

    Discretización (SPEC §2.1 / §2.2):

        dx = L / (N - 1)
        I_i = ρ · J · dx
        k_i = G · J / dx
    """
    if n_nodes < 2:
        msg = f"n_nodes must be >= 2, got {n_nodes}"
        raise ValueError(msg)
    if density_kg_m3 <= 0.0:
        msg = f"density_kg_m3 must be > 0, got {density_kg_m3}"
        raise ValueError(msg)
    if shear_modulus_pa <= 0.0:
        msg = f"shear_modulus_pa must be > 0, got {shear_modulus_pa}"
        raise ValueError(msg)
    if polar_moment_of_inertia_m4 <= 0.0:
        msg = (
            "polar_moment_of_inertia_m4 must be > 0, "
            f"got {polar_moment_of_inertia_m4}"
        )
        raise ValueError(msg)
    if total_length_m <= 0.0:
        msg = f"total_length_m must be > 0, got {total_length_m}"
        raise ValueError(msg)
    if nodal_damping_coeff < 0.0:
        msg = f"nodal_damping_coeff must be >= 0, got {nodal_damping_coeff}"
        raise ValueError(msg)

    dx = total_length_m / float(n_nodes - 1)
    i_node = density_kg_m3 * polar_moment_of_inertia_m4 * dx
    k_seg = shear_modulus_pa * polar_moment_of_inertia_m4 / dx

    inertia = np.full(n_nodes, i_node, dtype=np.float64)
    stiffness = np.full(n_nodes - 1, k_seg, dtype=np.float64)
    damping = np.full(n_nodes, nodal_damping_coeff, dtype=np.float64)

    return DrillstringParameters(
        n_nodes=n_nodes,
        inertia=inertia,
        stiffness=stiffness,
        damping=damping,
        top_drive_damping=top_drive_damping,
        bit_radius_m=bit_radius_m,
    )


def bit_stribeck_parameters(
    wob_kn: float,
    bit_radius_m: float,
    coeffs: BitFrictionCoefficients,
) -> StribeckParameters:
    """Mapea WOB [kN] y coeficientes de fricción a ``StribeckParameters``.

    T_c = μ_c · WOB_N · r_bit
    T_s = μ_s · WOB_N · r_bit
    con WOB_N = wob_kn · 1000.
    """
    if wob_kn < 0.0:
        msg = f"wob_kn must be >= 0, got {wob_kn}"
        raise ValueError(msg)
    if bit_radius_m <= 0.0:
        msg = f"bit_radius_m must be > 0, got {bit_radius_m}"
        raise ValueError(msg)

    wob_n = wob_kn * 1000.0
    t_coulomb = coeffs.mu_coulomb * wob_n * bit_radius_m
    t_static = coeffs.mu_static * wob_n * bit_radius_m
    return StribeckParameters(
        t_coulomb=t_coulomb,
        t_static=t_static,
        gamma=coeffs.gamma,
        omega_eps=coeffs.omega_eps,
        c_viscous=coeffs.c_viscous,
    )


def build_stiffness_matrix(stiffness: NDArray[np.float64]) -> NDArray[np.float64]:
    """Ensambla la matriz de rigidez tridiagonal simétrica K ∈ R^{N×N}.

    Para segmentos k_0 … k_{N-2}:

        K[i, i]     += k_{i-1} + k_i  (bordes: un solo vecino)
        K[i, i+1]   = K[i+1, i] = -k_i
    """
    n_seg = int(stiffness.shape[0])
    n_nodes = n_seg + 1
    k_mat = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    for i in range(n_seg):
        k_i = float(stiffness[i])
        k_mat[i, i] += k_i
        k_mat[i + 1, i + 1] += k_i
        k_mat[i, i + 1] -= k_i
        k_mat[i + 1, i] -= k_i
    return k_mat


def build_damping_matrix(damping: NDArray[np.float64]) -> NDArray[np.float64]:
    """Ensambla la matriz de amortiguamiento diagonal C = diag(c_i)."""
    return np.diag(np.asarray(damping, dtype=np.float64))


def build_state_derivative(
    params: DrillstringParameters,
    friction_coeffs: BitFrictionCoefficients,
) -> StateDerivativeFn:
    """Factory de ``state_derivative(t, state, u_top, wob)``.

    Estado interleaved: ``[θ_0, ω_0, …, θ_{N-1}, ω_{N-1}]``.

    Ecuaciones (por nodo):

        θ̇_i = ω_i
        I_i ω̇_i = -(K θ)_i - (C ω)_i + T_ext,i

    con T_ext,0 = c_drive (u_top - ω_0) y
    T_ext,N-1 = -T_bit(ω_{N-1}; WOB) (Stribeck regularizado).
    """
    n = params.n_nodes
    k_mat = build_stiffness_matrix(params.stiffness)
    c_mat = build_damping_matrix(params.damping)
    inertia = np.asarray(params.inertia, dtype=np.float64)
    c_drive = params.top_drive_damping
    r_bit = params.bit_radius_m

    def state_derivative(
        _t: float,
        state: NDArray[np.float64],
        u_top: float,
        wob: float,
    ) -> NDArray[np.float64]:
        state_arr = np.asarray(state, dtype=np.float64)
        if state_arr.shape != (2 * n,):
            msg = f"state must have shape ({2 * n},), got {state_arr.shape}"
            raise ValueError(msg)

        theta = state_arr[0::2]
        omega = state_arr[1::2]

        t_int = -(k_mat @ theta)
        t_damp = c_mat @ omega
        t_ext = np.zeros(n, dtype=np.float64)
        t_ext[0] += c_drive * (u_top - float(omega[0]))

        stribeck = bit_stribeck_parameters(wob, r_bit, friction_coeffs)
        omega_bit = np.asarray(omega[-1], dtype=np.float64)
        t_friction = float(stribeck_friction_torque(omega_bit, stribeck))
        t_ext[-1] -= t_friction

        omega_dot = (t_int - t_damp + t_ext) / inertia

        result = np.empty(2 * n, dtype=np.float64)
        result[0::2] = omega
        result[1::2] = omega_dot
        return result

    return state_derivative
