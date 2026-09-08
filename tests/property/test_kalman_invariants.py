"""Property tests — invariantes UKF (Hypothesis)."""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st
from numpy.typing import NDArray

from src.engine.kalman.sigma_points import SigmaPointParameters
from src.engine.kalman.ukf_estimator import UnscentedKalmanFilter
from src.engine.physics.drillstring_fem import (
    BitFrictionCoefficients,
    build_state_derivative,
    build_uniform_drillstring,
)


def _make_ukf(n_nodes: int = 4) -> UnscentedKalmanFilter:
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
    state_deriv = build_state_derivative(params, friction)
    n = 2 * n_nodes
    x0 = np.zeros(n, dtype=np.float64)
    x0[1::2] = 8.0
    p0 = np.eye(n, dtype=np.float64) * 0.5
    q = np.eye(n, dtype=np.float64) * 1e-3
    sigma_params = SigmaPointParameters(n=n, alpha=1e-3, beta=2.0, kappa=0.0)
    return UnscentedKalmanFilter(
        initial_state=x0,
        initial_covariance=p0,
        process_noise=q,
        state_derivative=state_deriv,
        sigma_params=sigma_params,
    )


def _h_surface_and_bit(state: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.array([state[1], state[-1]], dtype=np.float64)


def _is_symmetric_psd(p: NDArray[np.float64], tol: float = 1e-8) -> bool:
    if not np.allclose(p, p.T, atol=tol):
        return False
    eig = np.linalg.eigvalsh(p)
    return bool(np.all(eig > -tol))


@given(
    dt=st.floats(min_value=5e-4, max_value=5e-3, allow_nan=False, allow_infinity=False),
    u_top=st.floats(min_value=1.0, max_value=20.0, allow_nan=False, allow_infinity=False),
    wob=st.floats(min_value=10.0, max_value=150.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, deadline=None)
def test_predict_preserves_symmetry_and_psd(
    dt: float,
    u_top: float,
    wob: float,
) -> None:
    ukf = _make_ukf()
    ukf.predict(dt=dt, u_top=u_top, wob=wob)
    assert _is_symmetric_psd(ukf.p)
    assert np.all(np.isfinite(ukf.x))
    assert np.all(np.isfinite(ukf.p))


@given(
    noise_scale=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=30, deadline=None)
def test_update_preserves_symmetry_and_psd(noise_scale: float) -> None:
    ukf = _make_ukf()
    ukf.predict(dt=1e-3, u_top=8.0, wob=80.0)
    z = _h_surface_and_bit(ukf.x) + noise_scale * np.array([0.1, -0.05])
    r = np.eye(2, dtype=np.float64) * 0.1
    ukf.update(z, _h_surface_and_bit, r)
    assert _is_symmetric_psd(ukf.p)
    assert np.all(np.isfinite(ukf.x))


@given(
    steps=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=15, deadline=None)
def test_predict_update_loop_keeps_finite_state(steps: int) -> None:
    ukf = _make_ukf()
    r = np.eye(2, dtype=np.float64) * 0.05
    for _ in range(steps):
        ukf.predict(dt=1e-3, u_top=10.0, wob=70.0)
        z = _h_surface_and_bit(ukf.x)
        ukf.update(z, _h_surface_and_bit, r)
        assert _is_symmetric_psd(ukf.p)
        assert np.all(np.isfinite(ukf.x))
