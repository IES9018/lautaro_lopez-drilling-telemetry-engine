"""Tests unitarios del Unscented Kalman Filter."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

from src.engine.kalman.sigma_points import SigmaPointParameters
from src.engine.kalman.ukf_estimator import UnscentedKalmanFilter
from src.engine.physics.drillstring_fem import (
    BitFrictionCoefficients,
    StateDerivativeFn,
    build_state_derivative,
    build_uniform_drillstring,
)
from src.engine.physics.integrators import rk4_step


def _small_string_setup() -> tuple[
    UnscentedKalmanFilter,
    NDArray[np.float64],
    StateDerivativeFn,
]:
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
    omega0 = 8.0
    x0[1::2] = omega0
    p0 = np.eye(n, dtype=np.float64) * 0.5
    q = np.eye(n, dtype=np.float64) * 1e-3
    sigma_params = SigmaPointParameters(n=n, alpha=1e-3, beta=2.0, kappa=0.0)
    ukf = UnscentedKalmanFilter(
        initial_state=x0,
        initial_covariance=p0,
        process_noise=q,
        state_derivative=state_deriv,
        sigma_params=sigma_params,
    )
    return ukf, x0.copy(), state_deriv


def _h_surface_and_bit(state: NDArray[np.float64]) -> NDArray[np.float64]:
    """Observa ω_0 (superficie) y ω_{N-1} (broca)."""
    return np.array([state[1], state[-1]], dtype=np.float64)


def test_predict_preserves_symmetry_and_psd() -> None:
    ukf, _, _ = _small_string_setup()
    ukf.predict(dt=1e-3, u_top=8.0, wob=80.0)
    assert np.allclose(ukf.p, ukf.p.T)
    eig = np.linalg.eigvalsh(ukf.p)
    assert np.all(eig > -1e-8)


def test_update_preserves_symmetry_and_psd() -> None:
    ukf, _, _ = _small_string_setup()
    ukf.predict(dt=1e-3, u_top=8.0, wob=80.0)
    z = _h_surface_and_bit(ukf.x)
    r = np.eye(2, dtype=np.float64) * 0.1
    ukf.update(z, _h_surface_and_bit, r)
    assert np.allclose(ukf.p, ukf.p.T)
    eig = np.linalg.eigvalsh(ukf.p)
    assert np.all(eig > -1e-8)


def test_update_without_predict_raises() -> None:
    ukf, _, _ = _small_string_setup()
    with pytest.raises(RuntimeError, match="predict"):
        ukf.update(
            np.array([0.0, 0.0], dtype=np.float64),
            _h_surface_and_bit,
            np.eye(2, dtype=np.float64),
        )


def test_ukf_init_rejects_bad_shapes() -> None:
    ukf, _, state_deriv = _small_string_setup()
    n = ukf.sigma_params.n
    with pytest.raises(ValueError, match="initial_state"):
        UnscentedKalmanFilter(
            initial_state=np.zeros(n - 1, dtype=np.float64),
            initial_covariance=np.eye(n, dtype=np.float64),
            process_noise=np.eye(n, dtype=np.float64) * 1e-3,
            state_derivative=state_deriv,
            sigma_params=ukf.sigma_params,
        )
    with pytest.raises(ValueError, match="initial_covariance"):
        UnscentedKalmanFilter(
            initial_state=np.zeros(n, dtype=np.float64),
            initial_covariance=np.eye(n - 1, dtype=np.float64),
            process_noise=np.eye(n, dtype=np.float64) * 1e-3,
            state_derivative=state_deriv,
            sigma_params=ukf.sigma_params,
        )
    with pytest.raises(ValueError, match="process_noise"):
        UnscentedKalmanFilter(
            initial_state=np.zeros(n, dtype=np.float64),
            initial_covariance=np.eye(n, dtype=np.float64),
            process_noise=np.eye(n - 1, dtype=np.float64) * 1e-3,
            state_derivative=state_deriv,
            sigma_params=ukf.sigma_params,
        )
    with pytest.raises(ValueError, match="jitter"):
        UnscentedKalmanFilter(
            initial_state=np.zeros(n, dtype=np.float64),
            initial_covariance=np.eye(n, dtype=np.float64),
            process_noise=np.eye(n, dtype=np.float64) * 1e-3,
            state_derivative=state_deriv,
            sigma_params=ukf.sigma_params,
            jitter=-1.0,
        )
    with pytest.raises(ValueError, match="dt"):
        ukf.predict(dt=0.0, u_top=1.0, wob=0.0)


def test_update_rejects_bad_z_and_r() -> None:
    ukf, _, _ = _small_string_setup()
    ukf.predict(dt=1e-3, u_top=8.0, wob=50.0)
    with pytest.raises(ValueError, match="r must have shape"):
        ukf.update(
            np.array([1.0, 2.0], dtype=np.float64),
            _h_surface_and_bit,
            np.eye(3, dtype=np.float64),
        )
    with pytest.raises(ValueError, match="1-D"):
        ukf.update(
            np.array([[1.0, 2.0]], dtype=np.float64),
            _h_surface_and_bit,
            np.eye(2, dtype=np.float64),
        )


def test_update_rejects_bad_h_fn_output() -> None:
    ukf, _, _ = _small_string_setup()
    ukf.predict(dt=1e-3, u_top=8.0, wob=50.0)

    def bad_h(_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.array([1.0, 2.0, 3.0], dtype=np.float64)

    with pytest.raises(ValueError, match="h_fn output"):
        ukf.update(
            np.array([1.0, 2.0], dtype=np.float64),
            bad_h,
            np.eye(2, dtype=np.float64),
        )


def test_bit_omega_estimation_under_stick_slip_with_noise() -> None:
    ukf, x_true, state_deriv = _small_string_setup()

    def deriv(t: float, y: NDArray[np.float64]) -> NDArray[np.float64]:
        return state_deriv(t, y, 8.0, 120.0)

    dt = 2e-3
    n_steps = 250
    rng = np.random.default_rng(42)
    noise_std = 1.5
    r = np.eye(2, dtype=np.float64) * (noise_std**2)

    true_bit: list[float] = []
    est_bit: list[float] = []
    meas_bit: list[float] = []

    y = x_true.copy()
    for _ in range(n_steps):
        y = rk4_step(deriv, 0.0, y, dt)
        z_clean = _h_surface_and_bit(y)
        z_noisy = z_clean + rng.normal(0.0, noise_std, size=2)

        ukf.predict(dt=dt, u_top=8.0, wob=120.0)
        ukf.update(z_noisy, _h_surface_and_bit, r)

        true_bit.append(float(y[-1]))
        est_bit.append(float(ukf.x[-1]))
        meas_bit.append(float(z_noisy[1]))

    true_arr = np.asarray(true_bit, dtype=np.float64)
    est_arr = np.asarray(est_bit, dtype=np.float64)
    meas_arr = np.asarray(meas_bit, dtype=np.float64)

    half = n_steps // 2
    rmse_est = float(np.sqrt(np.mean((est_arr[half:] - true_arr[half:]) ** 2)))
    rmse_meas = float(np.sqrt(np.mean((meas_arr[half:] - true_arr[half:]) ** 2)))
    assert rmse_est < rmse_meas, (
        f"filter RMSE {rmse_est:.4f} should be < measurement RMSE {rmse_meas:.4f}"
    )


def test_consistency_error_within_three_sigma() -> None:
    ukf, x_true, state_deriv = _small_string_setup()

    def deriv(t: float, y: NDArray[np.float64]) -> NDArray[np.float64]:
        return state_deriv(t, y, 8.0, 100.0)

    dt = 2e-3
    n_steps = 200
    rng = np.random.default_rng(123)
    noise_std = 0.8
    r = np.eye(2, dtype=np.float64) * (noise_std**2)

    inside = 0
    y = x_true.copy()
    bit_idx = -1
    for _ in range(n_steps):
        y = rk4_step(deriv, 0.0, y, dt)
        z_noisy = _h_surface_and_bit(y) + rng.normal(0.0, noise_std, size=2)
        ukf.predict(dt=dt, u_top=8.0, wob=100.0)
        ukf.update(z_noisy, _h_surface_and_bit, r)

        err = abs(float(ukf.x[bit_idx]) - float(y[bit_idx]))
        sigma = float(np.sqrt(max(ukf.p[bit_idx, bit_idx], 0.0)))
        if err <= 3.0 * sigma + 1e-12:
            inside += 1

    fraction = inside / n_steps
    assert fraction >= 0.90, f"3-sigma consistency fraction {fraction:.3f} < 0.90"
