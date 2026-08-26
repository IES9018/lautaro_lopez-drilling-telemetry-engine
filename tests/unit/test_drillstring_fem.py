"""Tests unitarios del modelo de sarta en espacio de estados."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

from src.engine.physics.drillstring_fem import (
    BitFrictionCoefficients,
    DrillstringParameters,
    bit_stribeck_parameters,
    build_damping_matrix,
    build_state_derivative,
    build_stiffness_matrix,
    build_uniform_drillstring,
)


def _friction_zero() -> BitFrictionCoefficients:
    return BitFrictionCoefficients(
        mu_static=0.0,
        mu_coulomb=0.0,
        gamma=1.0,
        omega_eps=1e-3,
        c_viscous=0.0,
    )


def _uniform_params(n_nodes: int) -> DrillstringParameters:
    return build_uniform_drillstring(
        n_nodes=n_nodes,
        density_kg_m3=7850.0,
        shear_modulus_pa=8.0e10,
        polar_moment_of_inertia_m4=1.0e-5,
        total_length_m=1000.0,
        nodal_damping_coeff=0.0,
        top_drive_damping=1.0e4,
        bit_radius_m=0.1,
    )


def test_dataclass_validation_rejects_bad_n_nodes() -> None:
    with pytest.raises(ValueError, match="n_nodes"):
        DrillstringParameters(
            n_nodes=1,
            inertia=np.array([1.0], dtype=np.float64),
            stiffness=np.array([], dtype=np.float64),
            damping=np.array([0.0], dtype=np.float64),
            top_drive_damping=1.0,
            bit_radius_m=0.1,
        )


def test_dataclass_validation_rejects_bad_inertia_shape() -> None:
    with pytest.raises(ValueError, match="inertia"):
        DrillstringParameters(
            n_nodes=2,
            inertia=np.array([1.0], dtype=np.float64),
            stiffness=np.array([1.0], dtype=np.float64),
            damping=np.array([0.0, 0.0], dtype=np.float64),
            top_drive_damping=1.0,
            bit_radius_m=0.1,
        )


def test_dataclass_validation_rejects_negative_inertia() -> None:
    with pytest.raises(ValueError, match="inertia"):
        DrillstringParameters(
            n_nodes=2,
            inertia=np.array([-1.0, 1.0], dtype=np.float64),
            stiffness=np.array([1.0], dtype=np.float64),
            damping=np.array([0.0, 0.0], dtype=np.float64),
            top_drive_damping=1.0,
            bit_radius_m=0.1,
        )


def test_bit_friction_coeffs_reject_static_below_coulomb() -> None:
    with pytest.raises(ValueError, match="mu_static"):
        BitFrictionCoefficients(
            mu_static=0.1,
            mu_coulomb=0.2,
            gamma=1.0,
            omega_eps=1e-3,
            c_viscous=0.0,
        )


@pytest.mark.parametrize("n_nodes", [2, 3, 5, 10])
def test_state_derivative_output_dimension(n_nodes: int) -> None:
    params = _uniform_params(n_nodes)
    deriv = build_state_derivative(params, _friction_zero())
    state = np.zeros(2 * n_nodes, dtype=np.float64)
    out = deriv(0.0, state, 1.0, 0.0)
    assert out.shape == (2 * n_nodes,)


def test_steady_state_torque_balance() -> None:
    """Rotación rígida a ω constante, wob=0, u_top=ω ⇒ ω̇ ≈ 0."""
    params = _uniform_params(5)
    deriv = build_state_derivative(params, _friction_zero())
    omega_common = 10.0
    state = np.zeros(2 * params.n_nodes, dtype=np.float64)
    state[1::2] = omega_common
    # θ_i iguales ⇒ Kθ = 0
    state[0::2] = 0.0
    out = deriv(0.0, state, omega_common, 0.0)
    omega_dot = out[1::2]
    np.testing.assert_allclose(omega_dot, 0.0, atol=1e-9)


def test_bit_friction_zero_at_zero_wob() -> None:
    coeffs = BitFrictionCoefficients(
        mu_static=0.4,
        mu_coulomb=0.2,
        gamma=0.05,
        omega_eps=1e-3,
        c_viscous=1.0,
    )
    params = bit_stribeck_parameters(0.0, 0.1, coeffs)
    assert params.t_coulomb == 0.0
    assert params.t_static == 0.0


def test_state_derivative_does_not_mutate_input() -> None:
    params = _uniform_params(4)
    deriv = build_state_derivative(params, _friction_zero())
    state = np.linspace(0.0, 1.0, 2 * params.n_nodes, dtype=np.float64)
    state_copy = state.copy()
    _ = deriv(0.0, state, 5.0, 10.0)
    np.testing.assert_array_equal(state, state_copy)


def test_build_stiffness_matrix_tridiagonal_symmetry() -> None:
    stiffness = np.array([2.0, 3.0, 4.0], dtype=np.float64)
    k_mat = build_stiffness_matrix(stiffness)
    assert k_mat.shape == (4, 4)
    np.testing.assert_allclose(k_mat, k_mat.T)
    assert k_mat[0, 0] == 2.0
    assert k_mat[0, 1] == -2.0
    assert k_mat[1, 1] == 2.0 + 3.0


def test_build_damping_matrix_diagonal() -> None:
    damping = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    c_mat = build_damping_matrix(damping)
    np.testing.assert_array_equal(c_mat, np.diag(damping))


def test_build_uniform_rejects_bad_density() -> None:
    with pytest.raises(ValueError, match="density"):
        build_uniform_drillstring(
            n_nodes=3,
            density_kg_m3=-1.0,
            shear_modulus_pa=1.0e10,
            polar_moment_of_inertia_m4=1e-5,
            total_length_m=100.0,
            nodal_damping_coeff=0.0,
            top_drive_damping=1.0,
            bit_radius_m=0.1,
        )


def test_bit_stribeck_rejects_negative_wob() -> None:
    with pytest.raises(ValueError, match="wob_kn"):
        bit_stribeck_parameters(-1.0, 0.1, _friction_zero())


def test_state_derivative_rejects_bad_state_shape() -> None:
    params = _uniform_params(3)
    deriv = build_state_derivative(params, _friction_zero())
    bad: NDArray[np.float64] = np.zeros(3, dtype=np.float64)
    with pytest.raises(ValueError, match="state"):
        deriv(0.0, bad, 1.0, 0.0)


def test_dataclass_validation_rejects_bad_stiffness_and_damping() -> None:
    with pytest.raises(ValueError, match="stiffness"):
        DrillstringParameters(
            n_nodes=2,
            inertia=np.array([1.0, 1.0], dtype=np.float64),
            stiffness=np.array([1.0, 1.0], dtype=np.float64),
            damping=np.array([0.0, 0.0], dtype=np.float64),
            top_drive_damping=1.0,
            bit_radius_m=0.1,
        )
    with pytest.raises(ValueError, match="damping"):
        DrillstringParameters(
            n_nodes=2,
            inertia=np.array([1.0, 1.0], dtype=np.float64),
            stiffness=np.array([1.0], dtype=np.float64),
            damping=np.array([0.0], dtype=np.float64),
            top_drive_damping=1.0,
            bit_radius_m=0.1,
        )


def test_dataclass_validation_rejects_nonpositive_fields() -> None:
    with pytest.raises(ValueError, match="stiffness"):
        DrillstringParameters(
            n_nodes=2,
            inertia=np.array([1.0, 1.0], dtype=np.float64),
            stiffness=np.array([0.0], dtype=np.float64),
            damping=np.array([0.0, 0.0], dtype=np.float64),
            top_drive_damping=1.0,
            bit_radius_m=0.1,
        )
    with pytest.raises(ValueError, match="damping"):
        DrillstringParameters(
            n_nodes=2,
            inertia=np.array([1.0, 1.0], dtype=np.float64),
            stiffness=np.array([1.0], dtype=np.float64),
            damping=np.array([-0.1, 0.0], dtype=np.float64),
            top_drive_damping=1.0,
            bit_radius_m=0.1,
        )
    with pytest.raises(ValueError, match="top_drive_damping"):
        DrillstringParameters(
            n_nodes=2,
            inertia=np.array([1.0, 1.0], dtype=np.float64),
            stiffness=np.array([1.0], dtype=np.float64),
            damping=np.array([0.0, 0.0], dtype=np.float64),
            top_drive_damping=0.0,
            bit_radius_m=0.1,
        )
    with pytest.raises(ValueError, match="bit_radius_m"):
        DrillstringParameters(
            n_nodes=2,
            inertia=np.array([1.0, 1.0], dtype=np.float64),
            stiffness=np.array([1.0], dtype=np.float64),
            damping=np.array([0.0, 0.0], dtype=np.float64),
            top_drive_damping=1.0,
            bit_radius_m=-0.1,
        )


def test_bit_friction_coeffs_all_rejects() -> None:
    with pytest.raises(ValueError, match="mu_coulomb"):
        BitFrictionCoefficients(
            mu_static=0.0,
            mu_coulomb=-0.1,
            gamma=1.0,
            omega_eps=1e-3,
            c_viscous=0.0,
        )
    with pytest.raises(ValueError, match="gamma"):
        BitFrictionCoefficients(
            mu_static=0.2,
            mu_coulomb=0.1,
            gamma=0.0,
            omega_eps=1e-3,
            c_viscous=0.0,
        )
    with pytest.raises(ValueError, match="omega_eps"):
        BitFrictionCoefficients(
            mu_static=0.2,
            mu_coulomb=0.1,
            gamma=1.0,
            omega_eps=0.0,
            c_viscous=0.0,
        )
    with pytest.raises(ValueError, match="c_viscous"):
        BitFrictionCoefficients(
            mu_static=0.2,
            mu_coulomb=0.1,
            gamma=1.0,
            omega_eps=1e-3,
            c_viscous=-1.0,
        )


def test_build_uniform_all_rejects() -> None:
    kwargs = {
        "n_nodes": 3,
        "density_kg_m3": 7850.0,
        "shear_modulus_pa": 8.0e10,
        "polar_moment_of_inertia_m4": 1e-5,
        "total_length_m": 100.0,
        "nodal_damping_coeff": 0.0,
        "top_drive_damping": 1.0,
        "bit_radius_m": 0.1,
    }
    with pytest.raises(ValueError, match="n_nodes"):
        build_uniform_drillstring(**{**kwargs, "n_nodes": 1})
    with pytest.raises(ValueError, match="shear_modulus"):
        build_uniform_drillstring(**{**kwargs, "shear_modulus_pa": 0.0})
    with pytest.raises(ValueError, match="polar_moment"):
        build_uniform_drillstring(**{**kwargs, "polar_moment_of_inertia_m4": -1.0})
    with pytest.raises(ValueError, match="total_length"):
        build_uniform_drillstring(**{**kwargs, "total_length_m": 0.0})
    with pytest.raises(ValueError, match="nodal_damping"):
        build_uniform_drillstring(**{**kwargs, "nodal_damping_coeff": -0.1})


def test_bit_stribeck_rejects_bad_radius() -> None:
    with pytest.raises(ValueError, match="bit_radius_m"):
        bit_stribeck_parameters(10.0, 0.0, _friction_zero())
