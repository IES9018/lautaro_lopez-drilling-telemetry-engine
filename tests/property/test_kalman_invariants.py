"""Property tests: invariantes de covarianza UKF (simetría + PSD)."""

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

_EIG_FLOOR = -1.0e-8


def _h_surface_and_bit(state: NDArray[np.float64]) -> NDArray[np.float64]:
    """Observa ω_0 (superficie) y ω_{N-1} (broca)."""
    return np.array([state[1], state[-1]], dtype=np.float64)


def _small_ukf() -> UnscentedKalmanFilter:
    n_nodes = 4
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


@given(
    steps=st.integers(min_value=1, max_value=15),
    noise_scale=st.floats(1e-4, 1.0, allow_nan=False, allow_infinity=False),
    u_top=st.floats(0.0, 15.0, allow_nan=False, allow_infinity=False),
    wob=st.floats(0.0, 200.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, deadline=None, derandomize=True)
def test_ukf_covariance_psd_after_random_predict_update(
    steps: int,
    noise_scale: float,
    u_top: float,
    wob: float,
) -> None:
    """Tras K predict+update, eigvalsh(sym(P)) >= -1e-8."""
    ukf = _small_ukf()
    rng = np.random.default_rng(20260826)
    dt = 1.0e-3
    r = np.eye(2, dtype=np.float64) * 0.1

    for _ in range(steps):
        ukf.predict(dt=dt, u_top=u_top, wob=wob)
        noise = rng.normal(0.0, noise_scale, size=2).astype(np.float64)
        z = _h_surface_and_bit(ukf.x) + noise
        ukf.update(z, _h_surface_and_bit, r)

    p_sym = 0.5 * (ukf.p + ukf.p.T)
    assert np.allclose(ukf.p, ukf.p.T, atol=1e-10)
    eig = np.linalg.eigvalsh(p_sym)
    assert np.all(eig >= _EIG_FLOOR), f"min eigenvalue {float(eig.min()):.3e}"
