"""Energía mecánica torsional lumped — helper solo para property tests (QA).

Contraste SPEC §5.3:

    E = 1/2 Σ_i I_i ω_i² + 1/2 θᵀ K θ

con estado interleaved [θ_0, ω_0, …, θ_{N-1}, ω_{N-1}].
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from src.engine.physics.drillstring_fem import (
    DrillstringParameters,
    build_stiffness_matrix,
)


def torsional_mechanical_energy(
    state: NDArray[np.float64],
    params: DrillstringParameters,
) -> float:
    """Energía cinética + potencial elástica torsional de la sarta lumped."""
    n = params.n_nodes
    expected = 2 * n
    if state.shape != (expected,):
        msg = f"state must have shape ({expected},), got {state.shape}"
        raise ValueError(msg)

    theta = state[0::2]
    omega = state[1::2]
    kinetic = 0.5 * float(np.dot(params.inertia * omega, omega))
    k_mat = build_stiffness_matrix(params.stiffness)
    potential = 0.5 * float(theta @ (k_mat @ theta))
    return kinetic + potential
