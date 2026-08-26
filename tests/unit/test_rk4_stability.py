"""Tests de estabilidad numérica del integrador RK4."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from src.engine.physics.integrators import rk4_step


def _harmonic_deriv(
    _t: float,
    y: NDArray[np.float64],
    *,
    omega0: float,
) -> NDArray[np.float64]:
    """Oscilador armónico: q̈ = -ω0² q, estado y = [q, v]."""
    q = y[0]
    v = y[1]
    return np.array([v, -(omega0**2) * q], dtype=np.float64)


def _integrate_harmonic(
    *,
    omega0: float,
    t_end: float,
    dt: float,
    y0: NDArray[np.float64],
) -> NDArray[np.float64]:
    y = np.array(y0, dtype=np.float64, copy=True)
    t = 0.0
    n_steps = int(round(t_end / dt))

    def deriv(t_: float, state: NDArray[np.float64]) -> NDArray[np.float64]:
        return _harmonic_deriv(t_, state, omega0=omega0)

    for _ in range(n_steps):
        y = rk4_step(deriv, t, y, dt)
        t += dt
    return y


def test_rk4_does_not_mutate_input() -> None:
    y = np.array([1.0, 0.0], dtype=np.float64)
    y_copy = y.copy()

    def deriv(_t: float, state: NDArray[np.float64]) -> NDArray[np.float64]:
        return _harmonic_deriv(_t, state, omega0=1.0)

    _ = rk4_step(deriv, 0.0, y, 0.01)
    np.testing.assert_array_equal(y, y_copy)


def test_rk4_global_error_order_four() -> None:
    """El error global en t fijo debe escalar ~ O(dt^4)."""
    omega0 = 2.0 * np.pi
    t_end = 1.0
    y0 = np.array([1.0, 0.0], dtype=np.float64)

    # Solución exacta: q(t) = cos(ω0 t), v(t) = -ω0 sin(ω0 t)
    q_exact = np.cos(omega0 * t_end)
    v_exact = -omega0 * np.sin(omega0 * t_end)
    y_exact = np.array([q_exact, v_exact], dtype=np.float64)

    dt_coarse = 1.0e-2
    dt_fine = dt_coarse / 2.0

    y_coarse = _integrate_harmonic(
        omega0=omega0,
        t_end=t_end,
        dt=dt_coarse,
        y0=y0,
    )
    y_fine = _integrate_harmonic(
        omega0=omega0,
        t_end=t_end,
        dt=dt_fine,
        y0=y0,
    )

    err_coarse = float(np.linalg.norm(y_coarse - y_exact))
    err_fine = float(np.linalg.norm(y_fine - y_exact))
    assert err_coarse > 0.0
    assert err_fine > 0.0

    observed_order = np.log(err_coarse / err_fine) / np.log(2.0)
    # Orden teórico 4; tolerancia amplia por errores de redondeo / fase
    assert observed_order > 3.5, f"observed order {observed_order:.3f} < 3.5"


def test_rk4_energy_conservation_undamped() -> None:
    """En oscilador no amortiguado la energía se conserva con tolerancia O(dt^4)."""
    omega0 = 1.0
    t_end = 20.0
    dt = 1.0e-3
    y0 = np.array([1.0, 0.0], dtype=np.float64)

    def energy(state: NDArray[np.float64]) -> float:
        q, v = float(state[0]), float(state[1])
        return 0.5 * v * v + 0.5 * (omega0**2) * q * q

    e0 = energy(y0)
    y_end = _integrate_harmonic(omega0=omega0, t_end=t_end, dt=dt, y0=y0)
    e_end = energy(y_end)
    rel_drift = abs(e_end - e0) / e0
    # Con dt=1e-3 y T=20, el drift relativo de RK4 debe ser muy pequeño
    assert rel_drift < 1.0e-8, f"relative energy drift {rel_drift:.3e}"
