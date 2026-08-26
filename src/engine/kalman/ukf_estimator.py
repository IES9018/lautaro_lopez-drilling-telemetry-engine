"""Unscented Kalman Filter (UKF) para estimación de estado de la sarta."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from src.engine.kalman.sigma_points import (
    SigmaPointParameters,
    compute_sigma_points,
    compute_sigma_weights,
)
from src.engine.physics.drillstring_fem import StateDerivativeFn
from src.engine.physics.integrators import rk4_step


class UnscentedKalmanFilter:
    """UKF con propagación RK4 sobre la dinámica de ``drillstring_fem``.

    El método ``update`` reutiliza los sigma points propagados por ``predict``
    (variante Van der Merwe; ver auditoría A-003).
    """

    def __init__(
        self,
        initial_state: NDArray[np.float64],
        initial_covariance: NDArray[np.float64],
        process_noise: NDArray[np.float64],
        state_derivative: StateDerivativeFn,
        sigma_params: SigmaPointParameters,
        jitter: float = 1e-9,
    ) -> None:
        n = sigma_params.n
        x0 = np.asarray(initial_state, dtype=np.float64)
        p0 = np.asarray(initial_covariance, dtype=np.float64)
        q0 = np.asarray(process_noise, dtype=np.float64)

        if x0.shape != (n,):
            msg = f"initial_state must have shape ({n},), got {x0.shape}"
            raise ValueError(msg)
        if p0.shape != (n, n):
            msg = f"initial_covariance must have shape ({n}, {n}), got {p0.shape}"
            raise ValueError(msg)
        if q0.shape != (n, n):
            msg = f"process_noise must have shape ({n}, {n}), got {q0.shape}"
            raise ValueError(msg)
        if jitter < 0.0:
            msg = f"jitter must be >= 0, got {jitter}"
            raise ValueError(msg)

        self.sigma_params = sigma_params
        self.state_derivative = state_derivative
        self.jitter = jitter
        self.x: NDArray[np.float64] = np.array(x0, dtype=np.float64, copy=True)
        self.p: NDArray[np.float64] = 0.5 * (p0 + p0.T)
        self.q: NDArray[np.float64] = 0.5 * (q0 + q0.T)
        self._predicted_sigma_points: NDArray[np.float64] | None = None

    def predict(self, dt: float, u_top: float, wob: float) -> None:
        """Predicción: propaga sigma points con RK4 y reconstruye media/covarianza."""
        if dt <= 0.0:
            msg = f"dt must be > 0, got {dt}"
            raise ValueError(msg)

        sigma = compute_sigma_points(
            self.x,
            self.p,
            self.sigma_params,
            jitter=self.jitter,
        )
        wm, wc = compute_sigma_weights(self.sigma_params)
        n_sigma = sigma.shape[0]
        n = self.sigma_params.n
        propagated = np.empty((n_sigma, n), dtype=np.float64)

        def deriv(t: float, y: NDArray[np.float64]) -> NDArray[np.float64]:
            return self.state_derivative(t, y, u_top, wob)

        for i in range(n_sigma):
            propagated[i] = rk4_step(deriv, 0.0, sigma[i], dt)

        x_pred = wm @ propagated
        diffs = propagated - x_pred
        p_pred = (diffs.T * wc) @ diffs + self.q
        p_pred = 0.5 * (p_pred + p_pred.T)

        self.x = np.asarray(x_pred, dtype=np.float64)
        self.p = np.asarray(p_pred, dtype=np.float64)
        self._predicted_sigma_points = propagated

    def update(
        self,
        z: NDArray[np.float64],
        h_fn: Callable[[NDArray[np.float64]], NDArray[np.float64]],
        r: NDArray[np.float64],
    ) -> None:
        """Corrección: proyecta sigma points al espacio de medición y actualiza."""
        if self._predicted_sigma_points is None:
            msg = "call predict() before update()"
            raise RuntimeError(msg)

        z_arr = np.asarray(z, dtype=np.float64)
        r_arr = np.asarray(r, dtype=np.float64)
        if z_arr.ndim != 1:
            msg = f"z must be 1-D, got shape {z_arr.shape}"
            raise ValueError(msg)
        m = int(z_arr.shape[0])
        if r_arr.shape != (m, m):
            msg = f"r must have shape ({m}, {m}), got {r_arr.shape}"
            raise ValueError(msg)

        sigma = self._predicted_sigma_points
        wm, wc = compute_sigma_weights(self.sigma_params)
        n_sigma = sigma.shape[0]

        z0 = np.asarray(h_fn(sigma[0]), dtype=np.float64)
        if z0.shape != (m,):
            msg = f"h_fn output must have shape ({m},), got {z0.shape}"
            raise ValueError(msg)

        z_sigma = np.empty((n_sigma, m), dtype=np.float64)
        z_sigma[0] = z0
        for i in range(1, n_sigma):
            z_sigma[i] = np.asarray(h_fn(sigma[i]), dtype=np.float64)

        z_pred = wm @ z_sigma
        dz = z_sigma - z_pred
        dx = sigma - self.x
        p_zz = (dz.T * wc) @ dz + 0.5 * (r_arr + r_arr.T)
        p_xz = (dx.T * wc) @ dz
        k_gain = np.linalg.solve(p_zz, p_xz.T).T
        innovation = z_arr - z_pred
        self.x = self.x + k_gain @ innovation
        p_new = self.p - k_gain @ p_zz @ k_gain.T
        self.p = 0.5 * (p_new + p_new.T)
        self._predicted_sigma_points = None
