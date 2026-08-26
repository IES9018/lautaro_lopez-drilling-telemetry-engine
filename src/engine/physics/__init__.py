"""API pública del subpaquete physics."""

from .drillstring_fem import (
    BitFrictionCoefficients,
    DrillstringParameters,
    bit_stribeck_parameters,
    build_damping_matrix,
    build_state_derivative,
    build_stiffness_matrix,
    build_uniform_drillstring,
)
from .friction_models import StribeckParameters, stribeck_friction_torque
from .integrators import rk4_step

__all__ = [
    "BitFrictionCoefficients",
    "DrillstringParameters",
    "StribeckParameters",
    "bit_stribeck_parameters",
    "build_damping_matrix",
    "build_state_derivative",
    "build_stiffness_matrix",
    "build_uniform_drillstring",
    "rk4_step",
    "stribeck_friction_torque",
]
