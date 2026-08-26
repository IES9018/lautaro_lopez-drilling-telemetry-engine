"""Property tests: invariantes de energía mecánica (SPEC §5.3)."""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st
from numpy.typing import NDArray
from src.engine.physics.drillstring_fem import (
    BitFrictionCoefficients,
    DrillstringParameters,
    build_state_derivative,
    build_uniform_drillstring,
)
from src.engine.physics.integrators import rk4_step

from tests.property._torsional_energy import torsional_mechanical_energy

# Tolerancia numérica RK4 para dE/dt estimado en un paso (J/s).
_DE_DT_EPS = 1.0e-4


def _base_params(
    n_nodes: int = 4,
) -> tuple[DrillstringParameters, BitFrictionCoefficients]:
    params = build_uniform_drillstring(
        n_nodes=n_nodes,
        density_kg_m3=7850.0,
        shear_modulus_pa=8.0e10,
        polar_moment_of_inertia_m4=1.0e-5,
        total_length_m=200.0,
        nodal_damping_coeff=5.0,
        top_drive_damping=500.0,
        bit_radius_m=0.1,
    )
    friction = BitFrictionCoefficients(
        mu_static=0.45,
        mu_coulomb=0.15,
        gamma=0.08,
        omega_eps=1e-2,
        c_viscous=0.5,
    )
    return params, friction


@given(
    data=st.data(),
)
@settings(max_examples=50, deadline=None, derandomize=True)
def test_mechanical_energy_dissipation_free_rotation(data: st.DataObject) -> None:
    """Con u_top=wob=0, (E(t+dt)-E(t))/dt <= eps_num para estados válidos."""
    params, friction = _base_params(n_nodes=4)
    n = params.n_nodes
    state_deriv = build_state_derivative(params, friction)

    def deriv(t: float, y: NDArray[np.float64]) -> NDArray[np.float64]:
        # Rotación libre: sin inyección externa de potencia.
        return state_deriv(t, y, 0.0, 0.0)

    theta = data.draw(
        st.lists(
            st.floats(-0.5, 0.5, allow_nan=False, allow_infinity=False),
            min_size=n,
            max_size=n,
        )
    )
    omega = data.draw(
        st.lists(
            st.floats(-20.0, 20.0, allow_nan=False, allow_infinity=False),
            min_size=n,
            max_size=n,
        )
    )
    state = np.empty(2 * n, dtype=np.float64)
    state[0::2] = np.asarray(theta, dtype=np.float64)
    state[1::2] = np.asarray(omega, dtype=np.float64)

    dt = 1.0e-3
    e0 = torsional_mechanical_energy(state, params)
    state_next: NDArray[np.float64] = rk4_step(deriv, 0.0, state, dt)
    e1 = torsional_mechanical_energy(state_next, params)
    d_e_dt = (e1 - e0) / dt
    assert d_e_dt <= _DE_DT_EPS, f"dE/dt={d_e_dt:.6e} exceeded eps={_DE_DT_EPS}"
