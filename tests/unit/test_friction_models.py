"""Tests unitarios del modelo Stribeck regularizado."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray
from src.engine.physics.friction_models import (
    StribeckParameters,
    stribeck_friction_torque,
)


def _default_params() -> StribeckParameters:
    return StribeckParameters(
        t_coulomb=50.0,
        t_static=80.0,
        gamma=0.05,
        omega_eps=1e-3,
        c_viscous=2.0,
    )


def test_stribeck_odd_symmetry() -> None:
    """T_bit(-ω) == -T_bit(ω) (función impar)."""
    params = _default_params()
    rng = np.random.default_rng(42)
    omega: NDArray[np.float64] = rng.uniform(-200.0, 200.0, size=64)
    torque = stribeck_friction_torque(omega, params)
    torque_neg = stribeck_friction_torque(-omega, params)
    np.testing.assert_allclose(torque_neg, -torque, rtol=1e-12, atol=1e-12)


def test_stribeck_zero_at_rest() -> None:
    """En reposo el torque regularizado es exactamente 0."""
    params = _default_params()
    omega = np.array([0.0], dtype=np.float64)
    torque = stribeck_friction_torque(omega, params)
    assert torque.shape == (1,)
    assert torque[0] == 0.0


def test_stribeck_high_speed_asymptotic() -> None:
    """A |ω| grande: T ≈ sign(ω)·T_c + c_v·ω (término Stribeck ≈ 0)."""
    params = _default_params()
    omega = np.array([1.0e4, -1.0e4], dtype=np.float64)
    torque = stribeck_friction_torque(omega, params)
    expected = np.sign(omega) * params.t_coulomb + params.c_viscous * omega
    # residual Stribeck: (T_s-T_c)·exp(-γ|ω|) → 0; tanh → ±1
    np.testing.assert_allclose(torque, expected, rtol=1e-9, atol=1e-9)


def test_stribeck_rejects_negative_coulomb() -> None:
    with pytest.raises(ValueError, match="t_coulomb"):
        StribeckParameters(
            t_coulomb=-1.0,
            t_static=1.0,
            gamma=1.0,
            omega_eps=1e-3,
            c_viscous=0.0,
        )


def test_stribeck_rejects_static_below_coulomb() -> None:
    with pytest.raises(ValueError, match="t_static"):
        StribeckParameters(
            t_coulomb=10.0,
            t_static=5.0,
            gamma=1.0,
            omega_eps=1e-3,
            c_viscous=0.0,
        )


def test_stribeck_rejects_nonpositive_gamma() -> None:
    with pytest.raises(ValueError, match="gamma"):
        StribeckParameters(
            t_coulomb=1.0,
            t_static=2.0,
            gamma=0.0,
            omega_eps=1e-3,
            c_viscous=0.0,
        )


def test_stribeck_rejects_nonpositive_omega_eps() -> None:
    with pytest.raises(ValueError, match="omega_eps"):
        StribeckParameters(
            t_coulomb=1.0,
            t_static=2.0,
            gamma=1.0,
            omega_eps=-0.1,
            c_viscous=0.0,
        )


def test_stribeck_scalar_and_vector_shapes() -> None:
    params = _default_params()
    scalar = stribeck_friction_torque(np.array(3.0, dtype=np.float64), params)
    assert scalar.shape == ()
    matrix = stribeck_friction_torque(
        np.ones((2, 3), dtype=np.float64),
        params,
    )
    assert matrix.shape == (2, 3)
