"""
worker.py  —  Background QThread for coil model + WPT design calculations.
"""
from __future__ import annotations
import math
from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal
from physics.coil_model import CoilModel
from physics.wpt_design  import WPTDesigner, DesignInputs


class DesignWorker(QThread):
    finished_ok  = pyqtSignal(dict)
    finished_err = pyqtSignal(str)

    def __init__(self, params: dict, parent=None):
        super().__init__(parent)
        self._p = params

    def run(self):
        try:    self.finished_ok.emit(self._compute())
        except Exception as e: self.finished_err.emit(str(e))

    def _compute(self) -> dict:
        p = self._p

        # ── Coil parameters ──────────────────────────────────────────
        # Primary
        if p.get("L1_override") is not None:
            L1   = p["L1_override"]
            RL1  = p["RL1_override"]
            k_calc_primary = None
            delta_mm = None
        else:
            c1 = CoilModel(N=p["N1"], D_coil=p["D_coil1"], d_wire=p["d_wire1"],
                           h_coil=p["h_coil1"], freq=p["freq"]).compute(p["d_sep"])
            L1  = c1.L; RL1 = c1.R_ac
            delta_mm = c1.skin_depth_mm

        # Secondary
        if p.get("L2_override") is not None:
            L2  = p["L2_override"]
            RL2 = p["RL2_override"]
        else:
            if p["identical_coils"]:
                # reuse primary coil result
                if p.get("L1_override") is not None:
                    L2 = L1; RL2 = RL1
                else:
                    L2 = c1.L; RL2 = c1.R_ac
            else:
                c2 = CoilModel(N=p["N2"], D_coil=p["D_coil2"], d_wire=p["d_wire2"],
                               h_coil=p["h_coil2"], freq=p["freq"]).compute(p["d_sep"])
                L2 = c2.L; RL2 = c2.R_ac
                if delta_mm is None:
                    delta_mm = c2.skin_depth_mm

        # k
        if p.get("k_override") is not None:
            k_calc = None
            k_used = p["k_override"]
        else:
            # compute analytically from primary coil (need c1)
            if p.get("L1_override") is None:
                k_calc = c1.k
            else:
                k_calc = None
            k_used = k_calc if k_calc is not None else 0.0

        if delta_mm is None:
            from physics.constants import RHO_COPPER, MU0
            delta_mm = math.sqrt(RHO_COPPER / (math.pi * p["freq"] * MU0)) * 1e3

        # LPF cutoff
        fc = 1.0 / (2.0 * math.pi * math.sqrt(p["Lf"] * p["Cf"]))

        # ── Design ───────────────────────────────────────────────────
        inp = DesignInputs(
            freq=p["freq"], VDD=p["VDD"], Po=p["Po"], RL=p["RL"],
            Ds=p["Ds"], Dd=p["Dd"],
            L1=L1, L2=L2, RL1=RL1, RL2=RL2, k=k_used,
            Lf=p["Lf"], Cf=p["Cf"],
        )
        d   = WPTDesigner(inp).run()
        rec = d.rectifier; inv = d.inverter

        return dict(
            L1=L1, L2=L2, RL1=RL1, RL2=RL2,
            k_calc=k_calc, k_used=k_used, delta_mm=delta_mm, fc=fc,
            phi_d_deg=rec.phi_d_deg, CD=rec.CD, Ri=rec.Ri, Ci=rec.Ci,
            C2=rec.C2, L_series_H=rec.L_series_H,
            I2=rec.I2, Vind=rec.Vind, VDmax=rec.VDmax, Vo=rec.Vo, Io=rec.Io,
            Req=inv.Req, Xeq=inv.Xeq, I1=inv.I1, Rout=inv.Rout,
            Xp=inv.Xp, Cp=inv.Cp, Xout=inv.Xout, Q=inv.Q,
            C0=inv.C0, CS1=inv.CS1, CS2=inv.CS2,
        )
