"""Tests unitarios del generador de puntos sigma (Van der Merwe)."""

from __future__ import annotations

import numpy as np
import pytest
from src.engine.kalman.sigma_points import (
    SigmaPointParameters,
    _cholesky_with_jitter,
    compute_sigma_points,
    compute_sigma_weights,
)


def _default_params(n: int = 4) -> SigmaPointParameters:
    return SigmaPointParameters(n=n, alpha=1e-3, beta=2.0, kappa=0.0)


def test_weights_shape_and_sum() -> None:
    params = _default_params(3)
    wm, wc = compute_sigma_weights(params)
    assert wm.shape == (2 * 3 + 1,)
    assert wc.shape == (2 * 3 + 1,)
    np.testing.assert_allclose(wm.sum(), 1.0, atol=1e-12)


@pytest.mark.parametrize("n", [1, 2, 4, 8])
def test_sigma_points_shape(n: int) -> None:
    params = _default_params(n)
    mean = np.zeros(n, dtype=np.float64)
    cov = np.eye(n, dtype=np.float64)
    sigma = compute_sigma_points(mean, cov, params)
    assert sigma.shape == (2 * n + 1, n)


def test_sigma_points_mean_recovery() -> None:
    params = _default_params(4)
    rng = np.random.default_rng(7)
    mean = rng.normal(size=4)
    a = rng.normal(size=(4, 4))
    cov = a @ a.T + np.eye(4)
    sigma = compute_sigma_points(mean, cov, params)
    wm, _ = compute_sigma_weights(params)
    recovered = wm @ sigma
    np.testing.assert_allclose(recovered, mean, atol=1e-10)


def test_sigma_points_covariance_recovery_linear() -> None:
    """Transformada unscented lineal: cov reconstruida ≈ P original."""
    params = SigmaPointParameters(n=3, alpha=1.0, beta=2.0, kappa=0.0)
    mean = np.array([1.0, -2.0, 0.5], dtype=np.float64)
    cov = np.array(
        [
            [2.0, 0.3, 0.1],
            [0.3, 1.5, -0.2],
            [0.1, -0.2, 0.8],
        ],
        dtype=np.float64,
    )
    sigma = compute_sigma_points(mean, cov, params)
    wm, wc = compute_sigma_weights(params)
    x_hat = wm @ sigma
    diffs = sigma - x_hat
    p_rec = (diffs.T * wc) @ diffs
    np.testing.assert_allclose(p_rec, cov, rtol=1e-9, atol=1e-9)


def test_cholesky_jitter_recovers_near_singular_covariance() -> None:
    params = _default_params(3)
    mean = np.zeros(3, dtype=np.float64)
    # Covarianza simétrica con autovalor ligeramente negativo (drift numérico)
    cov = np.array(
        [
            [1.0, 0.99, 0.98],
            [0.99, 1.0, 0.99],
            [0.98, 0.99, 1.0],
        ],
        dtype=np.float64,
    )
    eig = np.linalg.eigvalsh(cov)
    cov_bad = cov - (abs(float(eig.min())) + 1e-8) * np.eye(3)
    sigma = compute_sigma_points(mean, cov_bad, params, jitter=1e-6)
    assert np.all(np.isfinite(sigma))


def test_cholesky_with_jitter_rejects_bad_args() -> None:
    mat = np.eye(2, dtype=np.float64)
    with pytest.raises(ValueError, match="jitter"):
        _cholesky_with_jitter(mat, jitter=-1.0, max_attempts=3)
    with pytest.raises(ValueError, match="max_attempts"):
        _cholesky_with_jitter(mat, jitter=1e-9, max_attempts=0)


def test_cholesky_with_jitter_fails_after_attempts() -> None:
    # Matriz definitivamente no PSD (autovalores muy negativos)
    mat = -np.eye(2, dtype=np.float64) * 1e3
    with pytest.raises(ValueError, match="Cholesky failed"):
        _cholesky_with_jitter(mat, jitter=1e-12, max_attempts=2)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"n": 0, "alpha": 0.5, "beta": 2.0, "kappa": 0.0}, "n must"),
        ({"n": 2, "alpha": 0.0, "beta": 2.0, "kappa": 0.0}, "alpha"),
        ({"n": 2, "alpha": 1.5, "beta": 2.0, "kappa": 0.0}, "alpha"),
        ({"n": 2, "alpha": 0.5, "beta": -1.0, "kappa": 0.0}, "beta"),
        ({"n": 2, "alpha": 1e-3, "beta": 0.0, "kappa": -3.0}, "n \\+ lambda"),
    ],
)
def test_rejects_invalid_alpha_beta_kappa(
    kwargs: dict[str, float | int],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        SigmaPointParameters(
            n=int(kwargs["n"]),
            alpha=float(kwargs["alpha"]),
            beta=float(kwargs["beta"]),
            kappa=float(kwargs["kappa"]),
        )


def test_rejects_shape_mismatch() -> None:
    params = _default_params(3)
    with pytest.raises(ValueError, match="mean"):
        compute_sigma_points(
            np.zeros(2, dtype=np.float64),
            np.eye(3, dtype=np.float64),
            params,
        )
    with pytest.raises(ValueError, match="covariance"):
        compute_sigma_points(
            np.zeros(3, dtype=np.float64),
            np.eye(2, dtype=np.float64),
            params,
        )
