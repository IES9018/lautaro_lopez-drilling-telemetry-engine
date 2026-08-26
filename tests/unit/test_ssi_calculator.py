"""Tests unitarios del calculador de Stick-Slip Severity Index (SSI)."""

from __future__ import annotations

import numpy as np
import pytest

from src.engine.kalman.ssi_calculator import (
    StickSlipRegime,
    classify_regime,
    compute_ssi,
)


def test_ssi_constant_omega_is_zero_and_normal() -> None:
    window = np.full(64, 10.0, dtype=np.float64)
    result = compute_ssi(window, omega_nominal=10.0)
    assert result.ssi == 0.0
    assert result.regime == StickSlipRegime.NORMAL
    assert result.window_size == 64


def test_ssi_harmonic_matches_closed_form() -> None:
    omega_nominal = 20.0
    amplitude = 5.0
    t = np.linspace(0.0, 1.0, 1001, dtype=np.float64)
    window = omega_nominal + amplitude * np.sin(2.0 * np.pi * t)
    result = compute_ssi(window, omega_nominal=omega_nominal)
    expected = amplitude / omega_nominal
    np.testing.assert_allclose(result.ssi, expected, rtol=1e-3, atol=1e-3)
    assert result.regime == StickSlipRegime.NORMAL


def test_ssi_extreme_stick_slip_is_critical() -> None:
    # stick ≈ 0, slip ≈ 40; nominal 10 ⇒ SSI = 40/(2*10) = 2.0
    window = np.array([0.0, 0.0, 40.0, 40.0], dtype=np.float64)
    result = compute_ssi(window, omega_nominal=10.0)
    assert result.ssi > 1.0
    assert result.regime == StickSlipRegime.CRITICAL_STICK_SLIP


def test_ssi_regime_thresholds_boundaries() -> None:
    # SSI = (max-min)/(2*nom). Para SSI=0.5: rango = nom.
    # Para SSI=1.0: rango = 2*nom.
    omega_nominal = 10.0
    window_half = np.array([5.0, 15.0], dtype=np.float64)  # rango 10 → SSI 0.5
    window_one = np.array([0.0, 20.0], dtype=np.float64)  # rango 20 → SSI 1.0
    window_crit = np.array([0.0, 20.1], dtype=np.float64)

    r_half = compute_ssi(window_half, omega_nominal)
    r_one = compute_ssi(window_one, omega_nominal)
    r_crit = compute_ssi(window_crit, omega_nominal)

    assert r_half.ssi == pytest.approx(0.5)
    assert r_half.regime == StickSlipRegime.WARNING
    assert r_one.ssi == pytest.approx(1.0)
    assert r_one.regime == StickSlipRegime.WARNING
    assert r_crit.ssi > 1.0
    assert r_crit.regime == StickSlipRegime.CRITICAL_STICK_SLIP


def test_classify_regime_direct() -> None:
    assert classify_regime(0.0) == StickSlipRegime.NORMAL
    assert classify_regime(0.49) == StickSlipRegime.NORMAL
    assert classify_regime(0.5) == StickSlipRegime.WARNING
    assert classify_regime(1.0) == StickSlipRegime.WARNING
    assert classify_regime(1.01) == StickSlipRegime.CRITICAL_STICK_SLIP


def test_ssi_rejects_empty_window() -> None:
    with pytest.raises(ValueError, match="empty"):
        compute_ssi(np.array([], dtype=np.float64), 1.0)


def test_ssi_rejects_nonpositive_nominal() -> None:
    window = np.array([1.0, 2.0], dtype=np.float64)
    with pytest.raises(ValueError, match="omega_nominal"):
        compute_ssi(window, 0.0)
    with pytest.raises(ValueError, match="omega_nominal"):
        compute_ssi(window, -1.0)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_ssi_rejects_nan_or_inf_in_window(bad: float) -> None:
    window = np.array([1.0, bad], dtype=np.float64)
    with pytest.raises(ValueError, match="finite"):
        compute_ssi(window, 1.0)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_ssi_rejects_nan_or_inf_nominal(bad: float) -> None:
    window = np.array([1.0, 2.0], dtype=np.float64)
    with pytest.raises(ValueError, match="finite"):
        compute_ssi(window, bad)


def test_classify_regime_rejects_nan() -> None:
    with pytest.raises(ValueError, match="finite"):
        classify_regime(float("nan"))
