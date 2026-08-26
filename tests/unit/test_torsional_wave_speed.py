"""Validación de velocidad de onda torsional c_s = sqrt(G / ρ)."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.engine.physics.drillstring_fem import (
    BitFrictionCoefficients,
    DrillstringParameters,
    build_state_derivative,
    build_uniform_drillstring,
)
from src.engine.physics.integrators import rk4_step


def _arrival_time(
    *,
    n_nodes: int,
    density: float,
    shear_modulus: float,
    length: float,
    omega_step: float,
    threshold: float,
) -> float:
    c_s = float(np.sqrt(shear_modulus / density))
    dx = length / float(n_nodes - 1)
    # CFL-ish: pasos suficientemente chicos para modos altos ~ c_s/dx
    dt = 0.05 * dx / c_s
    t_theory = length / c_s
    t_max = 2.5 * t_theory

    base = build_uniform_drillstring(
        n_nodes=n_nodes,
        density_kg_m3=density,
        shear_modulus_pa=shear_modulus,
        polar_moment_of_inertia_m4=1.0e-5,
        total_length_m=length,
        nodal_damping_coeff=0.0,
        top_drive_damping=1.0,  # placeholder; se reescala abajo
        bit_radius_m=0.1,
    )
    # Tiempo característico de tracking ~ 0.02 · T_transit (no rígido vs dt)
    c_drive = float(base.inertia[0]) / (0.02 * t_theory)
    params = DrillstringParameters(
        n_nodes=base.n_nodes,
        inertia=base.inertia,
        stiffness=base.stiffness,
        damping=base.damping,
        top_drive_damping=c_drive,
        bit_radius_m=base.bit_radius_m,
    )
    friction = BitFrictionCoefficients(
        mu_static=0.0,
        mu_coulomb=0.0,
        gamma=1.0,
        omega_eps=1e-3,
        c_viscous=0.0,
    )
    state_deriv = build_state_derivative(params, friction)

    def deriv(t_: float, y: NDArray[np.float64]) -> NDArray[np.float64]:
        return state_deriv(t_, y, omega_step, 0.0)

    y = np.zeros(2 * n_nodes, dtype=np.float64)
    t = 0.0
    while t < t_max:
        y = rk4_step(deriv, t, y, dt)
        t += dt
        if not np.all(np.isfinite(y)):
            msg = f"non-finite state at t={t} (dt={dt}, N={n_nodes})"
            raise AssertionError(msg)
        if abs(float(y[-1])) >= threshold:
            return t
    msg = f"bit omega never reached threshold {threshold} within t_max={t_max}"
    raise AssertionError(msg)


def test_wave_transit_time_matches_theoretical_speed() -> None:
    """Tiempo de arribo ≈ L / c_s con c_s = sqrt(G/ρ); mejora al subir N."""
    density = 7850.0
    shear_modulus = 8.0e10
    length = 1000.0
    c_s = float(np.sqrt(shear_modulus / density))
    t_theory = length / c_s

    omega_step = 1.0
    threshold = 0.05 * omega_step

    t_coarse = _arrival_time(
        n_nodes=40,
        density=density,
        shear_modulus=shear_modulus,
        length=length,
        omega_step=omega_step,
        threshold=threshold,
    )
    t_fine = _arrival_time(
        n_nodes=80,
        density=density,
        shear_modulus=shear_modulus,
        length=length,
        omega_step=omega_step,
        threshold=threshold,
    )

    err_coarse = abs(t_coarse - t_theory) / t_theory
    err_fine = abs(t_fine - t_theory) / t_theory

    # Cadena discreta: tolerancia amplia (~30%) documentada en MODELO_MATEMATICO.md
    assert err_fine < 0.30, (
        f"relative error {err_fine:.3f} >= 0.30 "
        f"(t_fine={t_fine:.4f}, t_theory={t_theory:.4f})"
    )
    assert err_fine <= err_coarse + 1.0e-12, (
        f"refinement worsened error: coarse={err_coarse:.4f}, fine={err_fine:.4f}"
    )
