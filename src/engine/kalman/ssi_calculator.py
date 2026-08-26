"""Stick-Slip Severity Index (SSI) — cálculo determinista sobre ventana."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray


class StickSlipRegime(str, Enum):
    """Régimen operativo según SSI (SPEC §2.6)."""

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL_STICK_SLIP = "critical_stick_slip"


@dataclass(frozen=True, slots=True)
class SSIResult:
    """Resultado del cálculo de SSI sobre una ventana de ω_bit."""

    ssi: float
    regime: StickSlipRegime
    omega_max: float
    omega_min: float
    omega_nominal: float
    window_size: int


def classify_regime(ssi: float) -> StickSlipRegime:
    """Clasifica el régimen Stick-Slip a partir del valor de SSI.

    - SSI < 0.5 → NORMAL
    - 0.5 ≤ SSI ≤ 1.0 → WARNING
    - SSI > 1.0 → CRITICAL_STICK_SLIP
    """
    if not np.isfinite(ssi):
        msg = f"ssi must be finite, got {ssi}"
        raise ValueError(msg)
    if ssi < 0.5:
        return StickSlipRegime.NORMAL
    if ssi <= 1.0:
        return StickSlipRegime.WARNING
    return StickSlipRegime.CRITICAL_STICK_SLIP


def compute_ssi(
    omega_window: NDArray[np.float64],
    omega_nominal: float,
) -> SSIResult:
    """Calcula SSI = (ω_max − ω_min) / (2 · ω_nominal) sobre la ventana.

    Raises:
        ValueError: ventana vacía, ω_nominal ≤ 0, o valores no finitos.
    """
    window = np.asarray(omega_window, dtype=np.float64)
    if window.size == 0:
        msg = "omega_window must not be empty"
        raise ValueError(msg)
    if not np.all(np.isfinite(window)):
        msg = "omega_window must contain only finite values"
        raise ValueError(msg)
    if not np.isfinite(omega_nominal):
        msg = f"omega_nominal must be finite, got {omega_nominal}"
        raise ValueError(msg)
    if omega_nominal <= 0.0:
        msg = f"omega_nominal must be > 0, got {omega_nominal}"
        raise ValueError(msg)

    omega_max = float(np.max(window))
    omega_min = float(np.min(window))
    ssi = (omega_max - omega_min) / (2.0 * omega_nominal)
    regime = classify_regime(ssi)
    return SSIResult(
        ssi=ssi,
        regime=regime,
        omega_max=omega_max,
        omega_min=omega_min,
        omega_nominal=omega_nominal,
        window_size=int(window.size),
    )
