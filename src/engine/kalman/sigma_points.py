"""Generador de puntos sigma (esquema de Van der Merwe) para el UKF."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class SigmaPointParameters:
    """Parámetros del esquema de Van der Merwe.

    Attributes:
        n: Dimensión del estado (n = 2N), ≥ 1.
        alpha: Escala de spread, 0 < α ≤ 1.
        beta: Incorporación de conocimiento previo (β = 2 óptimo para Gaussianas).
        kappa: Parámetro secundario (típicamente 0 o 3 − n).
    """

    n: int
    alpha: float
    beta: float
    kappa: float

    @property
    def lambda_(self) -> float:
        """λ = α²(n + κ) − n."""
        return self.alpha**2 * (self.n + self.kappa) - self.n

    def __post_init__(self) -> None:
        if self.n < 1:
            msg = f"n must be >= 1, got {self.n}"
            raise ValueError(msg)
        if not (0.0 < self.alpha <= 1.0):
            msg = f"alpha must satisfy 0 < alpha <= 1, got {self.alpha}"
            raise ValueError(msg)
        if self.beta < 0.0:
            msg = f"beta must be >= 0, got {self.beta}"
            raise ValueError(msg)
        n_plus_lambda = float(self.n) + self.lambda_
        if n_plus_lambda <= 0.0:
            msg = (
                f"n + lambda must be > 0, got {n_plus_lambda} "
                f"(n={self.n}, lambda={self.lambda_})"
            )
            raise ValueError(msg)


def compute_sigma_weights(
    params: SigmaPointParameters,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Pesos Wm (media) y Wc (covarianza), shape (2n+1,).

    Wm[0] = λ/(n+λ)
    Wc[0] = λ/(n+λ) + (1 − α² + β)
    Wm[i] = Wc[i] = 1/(2(n+λ)),  i = 1..2n
    """
    n = params.n
    n_plus_lambda = float(n) + params.lambda_
    n_sigma = 2 * n + 1
    wm = np.empty(n_sigma, dtype=np.float64)
    wc = np.empty(n_sigma, dtype=np.float64)
    wm[0] = params.lambda_ / n_plus_lambda
    wc[0] = wm[0] + (1.0 - params.alpha**2 + params.beta)
    weight = 1.0 / (2.0 * n_plus_lambda)
    wm[1:] = weight
    wc[1:] = weight
    return wm, wc


def _cholesky_with_jitter(
    matrix: NDArray[np.float64],
    jitter: float,
    max_attempts: int,
) -> NDArray[np.float64]:
    """Cholesky con regularización εI y backoff exponencial si no es PSD."""
    if jitter < 0.0:
        msg = f"jitter must be >= 0, got {jitter}"
        raise ValueError(msg)
    if max_attempts < 1:
        msg = f"max_attempts must be >= 1, got {max_attempts}"
        raise ValueError(msg)

    n = int(matrix.shape[0])
    working = np.array(matrix, dtype=np.float64, copy=True)
    scale = jitter
    for attempt in range(max_attempts):
        try:
            return np.linalg.cholesky(working)
        except np.linalg.LinAlgError:
            if attempt == max_attempts - 1:
                break
            working = matrix + scale * np.eye(n, dtype=np.float64)
            scale *= 2.0
    msg = (
        f"Cholesky failed after {max_attempts} jitter attempts "
        f"(final scale={scale / 2.0})"
    )
    raise ValueError(msg)


def compute_sigma_points(
    mean: NDArray[np.float64],
    covariance: NDArray[np.float64],
    params: SigmaPointParameters,
    jitter: float = 1e-9,
    max_jitter_attempts: int = 5,
) -> NDArray[np.float64]:
    """Genera 2n+1 puntos sigma, shape (2n+1, n).

    σ⁰ = μ
    σ^{i+1} = μ + L[:, i],  σ^{n+i+1} = μ − L[:, i]
    con L Lᵀ = (n+λ) P_sym, P_sym = ½(P + Pᵀ).
    """
    mean_arr = np.asarray(mean, dtype=np.float64)
    cov_arr = np.asarray(covariance, dtype=np.float64)
    n = params.n
    if mean_arr.shape != (n,):
        msg = f"mean must have shape ({n},), got {mean_arr.shape}"
        raise ValueError(msg)
    if cov_arr.shape != (n, n):
        msg = f"covariance must have shape ({n}, {n}), got {cov_arr.shape}"
        raise ValueError(msg)

    p_sym = 0.5 * (cov_arr + cov_arr.T)
    n_plus_lambda = float(n) + params.lambda_
    scaled = n_plus_lambda * p_sym
    chol = _cholesky_with_jitter(scaled, jitter=jitter, max_attempts=max_jitter_attempts)

    n_sigma = 2 * n + 1
    sigma = np.empty((n_sigma, n), dtype=np.float64)
    sigma[0] = mean_arr
    for i in range(n):
        col = chol[:, i]
        sigma[i + 1] = mean_arr + col
        sigma[n + i + 1] = mean_arr - col
    return sigma
