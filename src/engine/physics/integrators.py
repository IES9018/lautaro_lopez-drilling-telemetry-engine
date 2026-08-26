"""Integradores numéricos deterministas para el Physics Engine."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

DerivFn = Callable[[float, NDArray[np.float64]], NDArray[np.float64]]


def rk4_step(
    deriv_fn: DerivFn,
    t: float,
    y: NDArray[np.float64],
    dt: float,
) -> NDArray[np.float64]:
    """Un paso de Runge–Kutta de 4º orden (RK4).

    Integra ``ẏ = f(t, y)`` sin mutar ``y``:

        k1 = f(t, y)
        k2 = f(t + dt/2, y + dt/2 · k1)
        k3 = f(t + dt/2, y + dt/2 · k2)
        k4 = f(t + dt, y + dt · k3)
        y_next = y + dt/6 · (k1 + 2·k2 + 2·k3 + k4)

    Args:
        deriv_fn: Función de derivadas ``f(t, y)``.
        t: Tiempo actual.
        y: Estado en ``t`` (no se modifica).
        dt: Paso temporal.

    Returns:
        Nuevo estado en ``t + dt`` (array nuevo ``float64``).
    """
    y0: NDArray[np.float64] = np.array(y, dtype=np.float64, copy=True)

    k1 = np.asarray(deriv_fn(t, y0), dtype=np.float64)
    k2 = np.asarray(
        deriv_fn(t + 0.5 * dt, y0 + 0.5 * dt * k1),
        dtype=np.float64,
    )
    k3 = np.asarray(
        deriv_fn(t + 0.5 * dt, y0 + 0.5 * dt * k2),
        dtype=np.float64,
    )
    k4 = np.asarray(
        deriv_fn(t + dt, y0 + dt * k3),
        dtype=np.float64,
    )

    return y0 + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
