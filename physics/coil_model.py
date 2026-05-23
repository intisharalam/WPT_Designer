"""
CoilModel
=========
Analytical models for a single-layer helical coil:

  - Self-inductance  : Nagaoka coefficient  (Ref [11] in paper)
  - AC winding ESR   : Dowell's equation    (Ref [12] in paper)
  - Mutual inductance: Neumann's formula    (Ref [12] in paper)
  - Coupling coeff   : k = M / L

Reference
---------
Nagashima, Wei, Sekiya — IEEE IECON 2014
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.special import ellipk, ellipe

from .constants import MU0, RHO_COPPER


# ─────────────────────────────────────────────────────────────────────────────
#  Data container for coil results
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CoilResult:
    """Holds all computed coil parameters."""
    L:         float   # Self-inductance (H)
    R_ac:      float   # AC ESR via Dowell (Ω)
    M:         float   # Mutual inductance with identical coaxial partner (H)
    k:         float   # Coupling coefficient M/L (dimensionless)
    skin_depth_mm: float  # Skin depth at operating frequency (mm)


# ─────────────────────────────────────────────────────────────────────────────
#  CoilModel
# ─────────────────────────────────────────────────────────────────────────────

class CoilModel:
    """
    Computes self-inductance, AC ESR, and coupling coefficient for a
    single-layer helical coil.

    Parameters
    ----------
    N        : number of turns
    D_coil   : coil diameter (m)  — centre-to-centre across winding
    d_wire   : wire diameter (m)
    h_coil   : winding axial length (m)
    freq     : operating frequency (Hz)
    """

    def __init__(
        self,
        N:       int,
        D_coil:  float,
        d_wire:  float,
        h_coil:  float,
        freq:    float,
    ) -> None:
        self.N      = N
        self.radius = D_coil / 2.0
        self.d_wire = d_wire
        self.h_coil = h_coil
        self.freq   = freq

    # ── public API ────────────────────────────────────────────────────

    def compute(self, d_separation: float) -> CoilResult:
        """
        Compute all coil parameters for a pair of identical coaxial coils
        separated by *d_separation* metres (centre-to-centre).

        Returns a :class:`CoilResult`.
        """
        L    = self._self_inductance()
        R_ac = self._dowell_esr()
        M    = self._neumann_M(d_separation)
        k    = M / L
        delta_mm = self._skin_depth() * 1e3
        return CoilResult(L=L, R_ac=R_ac, M=M, k=k, skin_depth_mm=delta_mm)

    # ── private: Nagaoka self-inductance ──────────────────────────────

    def _nagaoka_kL(self) -> float:
        """
        Nagaoka correction coefficient K_L for a finite solenoid.

        K_L = (4 / 3π) · (1/√(1−k²)) · [(1−k²)/k² · K(k) − (1−2k²)/k² · E(k) − k]

        where k = 1 / √(1 + (h / 2r)²)
        and K(k), E(k) are complete elliptic integrals of 1st and 2nd kind.
        """
        ratio = self.h_coil / (2.0 * self.radius)
        kn    = 1.0 / math.sqrt(1.0 + ratio ** 2)
        k2    = kn ** 2
        Kk    = float(ellipk(k2))
        Ek    = float(ellipe(k2))
        KL = (4.0 / (3.0 * math.pi)) * (1.0 / math.sqrt(1.0 - k2)) * (
            ((1.0 - k2) / k2) * Kk
            - ((1.0 - 2.0 * k2) / k2) * Ek
            - kn
        )
        return KL

    def _self_inductance(self) -> float:
        """
        L = μ₀ · N² · π · r² / h · K_L    (H)
        """
        KL = self._nagaoka_kL()
        return MU0 * self.N ** 2 * math.pi * self.radius ** 2 / self.h_coil * KL

    # ── private: Dowell ESR ───────────────────────────────────────────

    def _skin_depth(self) -> float:
        """δ = √(ρ / (π f μ₀))  in metres."""
        return math.sqrt(RHO_COPPER / (math.pi * self.freq * MU0))

    def _dowell_esr(self) -> float:
        """
        AC winding resistance for a single-layer coil via Dowell's equation.

        Round wire is converted to an equivalent foil of thickness
        h_eq = d_wire · √π / 2 (Dowell approximation).

        For a single layer (M=1) the proximity-effect term vanishes and:
            F_R = Δ · (sinh 2Δ + sin 2Δ) / (cosh 2Δ − cos 2Δ)
        where Δ = h_eq / δ.
        """
        # DC resistance
        wire_length = self.N * 2.0 * math.pi * self.radius
        A_wire      = math.pi * (self.d_wire / 2.0) ** 2
        R_dc        = RHO_COPPER * wire_length / A_wire

        delta = self._skin_depth()
        h_eq  = self.d_wire * math.sqrt(math.pi) / 2.0
        Delta = h_eq / delta

        if Delta < 1e-6:          # low-frequency limit → DC resistance
            return R_dc

        s2D = math.sinh(2 * Delta)
        c2D = math.cosh(2 * Delta)
        si2D = math.sin(2 * Delta)
        co2D = math.cos(2 * Delta)

        F_R = Delta * (s2D + si2D) / (c2D - co2D)
        return R_dc * F_R

    # ── private: Neumann mutual inductance ────────────────────────────

    def _neumann_M(self, d_sep: float) -> float:
        """
        Mutual inductance between two identical coaxial N-turn coils
        separated by *d_sep*, via the Neumann elliptic-integral formula:

            M_single = μ₀ · a / π · [(2/m − m)·K(m) − (2/m)·E(m)]

            M_total  = N² · M_single

        where  m = √(4a² / (4a² + d²))

        **Note:** This thin-ring approximation underestimates k for
        real helical coils.  Use the manual-override field in the GUI
        when a measured value is available.
        """
        a   = self.radius
        m2  = 4.0 * a ** 2 / (4.0 * a ** 2 + d_sep ** 2)
        m   = math.sqrt(m2)
        Km  = float(ellipk(m2))
        Em  = float(ellipe(m2))
        M1  = MU0 * a / math.pi * ((2.0 / m - m) * Km - (2.0 / m) * Em)
        return self.N ** 2 * M1
