"""
physics
=======
Analytical models for the RIC-WPT system.

Modules
-------
constants   : Physical constants (MU0, RHO_COPPER)
coil_model  : CoilModel — Nagaoka inductance, Dowell ESR, Neumann coupling
wpt_design  : WPTDesigner — full analytical design procedure (Nagashima 2014)
"""

from .constants  import MU0, RHO_COPPER
from .coil_model import CoilModel, CoilResult
from .wpt_design import WPTDesigner, DesignInputs, DesignResults

__all__ = [
    "MU0", "RHO_COPPER",
    "CoilModel", "CoilResult",
    "WPTDesigner", "DesignInputs", "DesignResults",
]
