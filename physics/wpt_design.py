"""
WPTDesigner
===========
Implements the full analytical design procedure from:

    Nagashima, Wei, Sekiya —
    "Analytical Design Procedure for Resonant Inductively Coupled
     Wireless Power Transfer System With Class-DE Inverter and
     Class-E Rectifier", IEEE IECON 2014.

Equation numbers in comments correspond directly to the paper.

Design flow
-----------
1.  Secondary (rectifier) — Eqs. 3, 4, 5, 6, 7, 8, 10
2.  Coupling / reflected impedance — Eqs. 12, 13, 14
3.  Primary (inverter) — Eqs. 15–21
4.  Diode voltage check — Eq. 22

Note on C2 sign
---------------
When L is small (low ωL), Ci > 1/(ω²L) and Eq. 7 yields C2 < 0.
A negative C2 is physically valid: it means the secondary resonant
element is an INDUCTOR of value  L_series = 1 / (ω² |C2|)  placed
in series with L2.  RectifierResults.L_series_nH is set in that case.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Data containers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DesignInputs:
    """All user-supplied design parameters."""
    freq:   float          # Operating frequency  f  (Hz)
    VDD:    float          # DC supply voltage        (V)
    Po:     float          # Output power             (W)
    RL:     float          # Load resistance          (Ω)
    Ds:     float          # Switch on-duty ratio     (−)
    Dd:     float          # Diode on-duty ratio      (−)
    L1:     float          # Primary self-inductance  (H)
    L2:     float          # Secondary self-inductance(H)
    RL1:    float          # Primary AC ESR           (Ω)
    RL2:    float          # Secondary AC ESR         (Ω)
    k:      float          # Coupling coefficient     (−)
    Lf:     float          # Low-pass filter inductor (H)
    Cf:     float          # Low-pass filter capacitor(F)


@dataclass
class RectifierResults:
    """Class-E rectifier component values."""
    phi_d_deg:    float        # Phase shift φd              (degrees)
    CD:           float        # Shunt capacitance CD        (F)
    Ri:           float        # Input resistance Ri         (Ω)
    Ci:           float        # Input capacitance Ci        (F)
    C2:           float        # Series resonant cap C2      (F) — may be negative
    L_series_H:   Optional[float]  # Series inductor when C2<0  (H)
    I2:           float        # Input current I2 RMS        (A)
    Vind:         float        # Induced voltage             (V)
    Vo:           float        # DC output voltage           (V)
    Io:           float        # DC output current           (A)
    VDmax:        float        # Maximum diode voltage       (V)

    @property
    def c2_is_inductor(self) -> bool:
        """True when the secondary resonant element is inductive."""
        return self.C2 < 0


@dataclass
class InverterResults:
    """Class-DE inverter component values."""
    Req:   float
    Xeq:   float
    I1:    float
    Rout:  float
    Xp:    float
    Cp:    Optional[float]
    Xout:  float
    Q:     float
    C0:    float
    CS1:   float
    CS2:   float


@dataclass
class DesignResults:
    """Combined output of the full design procedure."""
    rectifier: RectifierResults
    inverter:  InverterResults
    delta_mm:  float


# ─────────────────────────────────────────────────────────────────────────────
#  WPTDesigner
# ─────────────────────────────────────────────────────────────────────────────

class WPTDesigner:
    """
    Executes the analytical design procedure of Nagashima et al. 2014.

    Usage
    -----
    >>> inputs  = DesignInputs(freq=1e6, VDD=48, Po=5, RL=50, ...)
    >>> results = WPTDesigner(inputs).run()
    """

    def __init__(self, inputs: DesignInputs) -> None:
        self._p = inputs
        self._w = 2.0 * math.pi * inputs.freq

    def run(self) -> DesignResults:
        rect = self._design_rectifier()
        inv  = self._design_inverter(rect)
        from .constants import RHO_COPPER, MU0
        delta_mm = math.sqrt(RHO_COPPER / (math.pi * self._p.freq * MU0)) * 1e3
        return DesignResults(rectifier=rect, inverter=inv, delta_mm=delta_mm)

    # ── rectifier ────────────────────────────────────────────────────

    def _design_rectifier(self) -> RectifierResults:
        p = self._p; w = self._w; Dd = p.Dd

        Vo = math.sqrt(p.Po * p.RL)
        Io = Vo / p.RL

        # Eq. 6
        phi_d = math.atan2(
            1.0 - math.cos(2.0 * math.pi * Dd),
            2.0 * math.pi * (1.0 - Dd) + math.sin(2.0 * math.pi * Dd),
        )

        # Eq. 3
        t1 = 1.0 - math.cos(2.0 * math.pi * Dd)
        t2 = -2.0 * math.pi**2 * (1.0 - Dd)**2
        t3 = (2.0*math.pi*(1.0-Dd) + math.sin(2.0*math.pi*Dd))**2 / t1
        CD = (t1 + t2 + t3) / (2.0 * math.pi * w * p.RL)

        # Eq. 5
        Ri = 2.0 * p.RL * math.sin(phi_d)**2

        # Eq. 4
        A = (
            math.pi*(1.0-Dd)
            + math.sin(2.0*math.pi*Dd)
            - 0.25*math.sin(4.0*math.pi*Dd)*math.cos(2.0*phi_d)
            - 0.50*math.sin(2.0*phi_d)*math.sin(2.0*math.pi*Dd)**2
            - 2.0*math.pi*(1.0-Dd)*math.sin(phi_d)*math.sin(2.0*math.pi*Dd-phi_d)
        )
        if abs(A) < 1e-30:
            raise ValueError("Ci denominator A ≈ 0. Check Dd.")
        Ci = math.pi * CD / A

        # Eq. 7  — C2 can be negative (inductive compensation required)
        denom_C2 = w**2 * p.L2 * Ci - 1.0
        if abs(denom_C2) < 1e-30:
            raise ValueError("C2 undefined — exact resonance. Adjust L2 or f.")
        C2 = Ci / denom_C2

        # Determine series inductor when C2 < 0
        L_series_H: Optional[float] = None
        if C2 < 0:
            L_series_H = 1.0 / (w**2 * abs(C2))

        # Eq. 8, 10
        I2   = Io / (math.sqrt(2.0) * math.sin(phi_d))
        Vind = I2 * (p.RL2 + Ri)

        # Eq. 22
        phi_r = math.atan(1.0 / (w * CD * p.RL))
        VDmax = (Vo / (w * CD * p.RL)) * (2.0*phi_r - math.pi + 2.0/math.tan(phi_r))

        return RectifierResults(
            phi_d_deg=math.degrees(phi_d),
            CD=CD, Ri=Ri, Ci=Ci, C2=C2,
            L_series_H=L_series_H,
            I2=I2, Vind=Vind, Vo=Vo, Io=Io, VDmax=VDmax,
        )

    # ── inverter ─────────────────────────────────────────────────────

    def _design_inverter(self, rect: RectifierResults) -> InverterResults:
        p = self._p; w = self._w
        Ri = rect.Ri; C2 = rect.C2; Ci = rect.Ci; Vind = rect.Vind

        C_sum  = C2 + Ci
        C_prod = C2 * Ci
        X_sec  = w*p.L2 - C_sum / (w*C_prod)
        S_denom = (p.RL2 + Ri)**2 + X_sec**2

        # Eq. 12, 13
        Req = p.RL1 + k2w2L1L2Ri(p.k, w, p.L1, p.L2, p.RL2+Ri, S_denom)
        Xeq = _Xeq(p.k, w, p.L1, p.L2, p.RL2+Ri, C_sum, C_prod, S_denom)

        # Eq. 14
        I1 = Vind / (w * p.k * math.sqrt(p.L1 * p.L2))

        # Eq. 17
        Rout = p.VDD**2 / (2.0 * math.pi**2 * Req * I1**2)

        # Eq. 18 via quadratic from Eq. 15
        Xp = _solve_Xp(Req, Xeq, Rout)

        # Eq. 16
        R2 = Req**2; XpXeq = Xp + Xeq
        Xout = (R2*Xp + Xp*Xeq*XpXeq) / (R2 + XpXeq**2)

        # Eq. 19
        Q = Xout / Rout

        # Eq. 20
        if (Q - math.pi/2.0) <= 0.0:
            raise ValueError(
                f"Loaded Q = {Q:.3f} ≤ π/2 ≈ {math.pi/2:.3f}. "
                "Try increasing VDD, reducing Po, or adjusting duty ratios."
            )
        C0 = 1.0 / (w * Rout * (Q - math.pi/2.0))

        # Eq. 21
        CS = 1.0 / (2.0 * math.pi * w * Rout)

        Cp = (-1.0 / (w * Xp)) if Xp < 0.0 else None

        return InverterResults(
            Req=Req, Xeq=Xeq, I1=I1, Rout=Rout,
            Xp=Xp, Cp=Cp, Xout=Xout, Q=Q, C0=C0, CS1=CS, CS2=CS,
        )


# ── module-level helpers (keeps class body readable) ─────────────────────────

def k2w2L1L2Ri(k, w, L1, L2, RL2pRi, Sd):
    return k**2 * w**2 * L1 * L2 * RL2pRi / Sd

def _Xeq(k, w, L1, L2, RL2pRi, C_sum, C_prod, Sd):
    return (
        k**2 * w * L1 * (RL2pRi**2 - L2*C_sum/C_prod + (C_sum/(w*C_prod))**2) / Sd
        + w*L1*(1.0 - k**2)
    )

def _solve_Xp(Req, Xeq, Rout):
    """
    Quadratic from Eq. 15:
      (Req-Rout)·Xp² − 2·Rout·Xeq·Xp − Rout·(Xeq²+Req²) = 0
    Returns larger-magnitude root (paper convention).
    """
    qa = Req - Rout
    qb = -2.0 * Rout * Xeq
    qc = -Rout * (Xeq**2 + Req**2)
    disc = qb**2 - 4.0*qa*qc
    if disc < 0:
        raise ValueError("No real Xp solution — discriminant < 0.")
    sq = math.sqrt(disc)
    Xp1 = (-qb + sq) / (2.0*qa)
    Xp2 = (-qb - sq) / (2.0*qa)
    return Xp1 if abs(Xp1) > abs(Xp2) else Xp2
