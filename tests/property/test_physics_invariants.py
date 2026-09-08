"""Property tests — invariantes físicos (Hypothesis)."""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st
from numpy.typing import NDArray

from src.engine.kalman.ssi_calculator import compute_ssi
from src.engine.physics.friction_models import (
    StribeckParameters,
    stribeck_friction_torque,
)
from src.engine.physics.integrators import rk4_step


@given(
    omega_max=st.floats(min_value=-500.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    omega_min=st.floats(min_value=-500.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    omega_nominal=st.floats(min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=80, deadline=None)
def test_ssi_always_non_negative(
    omega_max: float,
    omega_min: float,
    omega_nominal: float,
) -> None:
    hi = max(omega_max, omega_min)
    lo = min(omega_max, omega_min)
    window = np.array([lo, (lo + hi) / 2.0, hi], dtype=np.float64)
    result = compute_ssi(window, omega_nominal)
    assert result.ssi >= 0.0
    assert np.isfinite(result.ssi)


@given(
    omega=st.floats(
        min_value=-50.0,
        max_value=50.0,
        allow_nan=False,
        allow_infinity=False,
    ),
)
@settings(max_examples=60, deadline=None)
def test_stribeck_is_odd_and_zero_at_rest(omega: float) -> None:
    params = StribeckParameters(
        t_coulomb=1000.0,
        t_static=1500.0,
        gamma=0.1,
        omega_eps=1e-2,
        c_viscous=0.5,
    )
    zero = stribeck_friction_torque(np.array([0.0], dtype=np.float64), params)
    assert float(zero[0]) == 0.0

    if abs(omega) < 1e-12:
        return

    t_pos = stribeck_friction_torque(np.array([omega], dtype=np.float64), params)
    t_neg = stribeck_friction_torque(np.array([-omega], dtype=np.float64), params)
    assert np.isclose(float(t_pos[0]), -float(t_neg[0]), rtol=1e-9, atol=1e-9)


def _harmonic_deriv(
    _t: float,
    y: NDArray[np.float64],
    *,
    omega0: float,
) -> NDArray[np.float64]:
    return np.array([y[1], -(omega0**2) * y[0]], dtype=np.float64)


@given(
    dt_scale=st.sampled_from([1.0, 0.5, 0.25]),
)
@settings(max_examples=10, deadline=None)
def test_rk4_global_error_scales_near_order_four(dt_scale: float) -> None:
    """Error global ~ O(dt^4): ratio entre dt y dt/2 cerca de 16."""
    omega0 = 2.0 * np.pi
    t_end = 0.5
    y0 = np.array([1.0, 0.0], dtype=np.float64)
    y_exact = np.array(
        [np.cos(omega0 * t_end), -omega0 * np.sin(omega0 * t_end)],
        dtype=np.float64,
    )

    def integrate(dt: float) -> NDArray[np.float64]:
        y = y0.copy()
        t = 0.0
        n_steps = int(round(t_end / dt))

        def deriv(t_: float, state: NDArray[np.float64]) -> NDArray[np.float64]:
            return _harmonic_deriv(t_, state, omega0=omega0)

        for _ in range(n_steps):
            y = rk4_step(deriv, t, y, dt)
            t += dt
        return y

    dt_coarse = 1.0e-2 * dt_scale
    # Asegurar horizonte exacto.
    n = max(2, int(round(t_end / dt_coarse)))
    dt_coarse = t_end / n
    dt_fine = dt_coarse / 2.0

    err_c = float(np.linalg.norm(integrate(dt_coarse) - y_exact))
    err_f = float(np.linalg.norm(integrate(dt_fine) - y_exact))
    assert err_c > 0.0
    assert err_f > 0.0
    ratio = err_c / err_f
    # Orden 4 → ratio ≈ 16; tolerancia amplia ante redondeo.
    assert ratio > 8.0
