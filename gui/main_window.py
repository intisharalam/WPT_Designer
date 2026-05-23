"""
main_window.py  —  Compact, feature-rich MainWindow for WPT Designer.

New in this version
-------------------
* Independent primary / secondary coil inputs (radio toggle)
* Direct L1 / L2 override (same pattern as k override)
* LPF cutoff frequency displayed
* Circuit diagram tab with annotated SVGs
* Tighter, cleaner layout throughout
"""
from __future__ import annotations
import math

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QScrollArea,
    QSplitter, QTabWidget, QTextEdit, QStatusBar, QCheckBox,
    QRadioButton, QButtonGroup, QFrame, QSizePolicy,
)
from PyQt5.QtCore  import Qt
from PyQt5.QtGui   import QDoubleValidator
from PyQt5.QtSvg   import QSvgWidget

from .style   import (STYLESHEET, ACCENT, TEAL, TEXT, MUTED,
                       GREEN, RED, YELLOW, BORDER, BG, PANEL, ORANGE)
from .widgets import InputRow, OutputRow, SectionLabel, eng
from .worker  import DesignWorker
from .schematic import build_schematic_svg

# ── paper defaults ────────────────────────────────────────────────────────────
D = {
    "freq":"1e6","VDD":"48","Po":"5","RL":"50","Ds":"0.25","Dd":"0.5",
    "D_coil":"0.155","N":"10","d_wire":"0.001","h_coil":"0.01","d_sep":"0.10",
    "Lf":"300e-6","Cf":"47e-6","k":"0.0725",
    "L1":"35.4e-6","RL1":"1.36","L2":"35.4e-6","RL2":"1.36",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RIC-WPT Designer  |  Class-DE + Class-E  |  Nagashima 2014")
        self.setMinimumSize(930, 330)
        self._worker = None
        self._last_results = None
        self._build()
        self.setStyleSheet(STYLESHEET)

    # ═══════════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════════════

    def _build(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(10,8,10,6); root.setSpacing(6)
        root.addLayout(self._title_bar())

        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self._left_panel())
        sp.addWidget(self._right_panel())
        sp.setSizes([480, 700])
        root.addWidget(sp, stretch=1)

        self._sb = QStatusBar(); self.setStatusBar(self._sb)
        self._sb.showMessage("Ready — enter parameters and press Calculate")

    # ── title ─────────────────────────────────────────────────────────

    def _title_bar(self):
        h = QHBoxLayout()
        t1 = QLabel("RIC-WPT Designer")
        t1.setStyleSheet(f"color:{ACCENT};font-size:17px;font-weight:bold;")
        t2 = QLabel("Class-DE Inverter  ·  Class-E Rectifier  ·  Nagashima, Wei, Sekiya — IEEE 2014")
        t2.setStyleSheet(f"color:{MUTED};font-size:11px;")
        h.addWidget(t1); h.addSpacing(10); h.addWidget(t2); h.addStretch()
        return h

    # ── LEFT panel ────────────────────────────────────────────────────

    def _left_panel(self):
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setMinimumWidth(465)
        w = QWidget(); ll = QVBoxLayout(w)
        ll.setContentsMargins(6,4,6,4); ll.setSpacing(6)

        ll.addWidget(self._grp_operating())
        ll.addWidget(self._grp_coils())
        ll.addWidget(self._grp_filter())
        ll.addStretch()
        ll.addLayout(self._btn_row())
        sc.setWidget(w)
        return sc

    def _grp_operating(self):
        g = QGroupBox("Operating Conditions"); v = QVBoxLayout(g); v.setSpacing(2)
        self.i_freq = InputRow("Frequency  f",         D["freq"],  "Hz",  "1 MHz in paper")
        self.i_vdd  = InputRow("DC Supply  VDD",       D["VDD"],   "V",   "48 V in paper")
        self.i_po   = InputRow("Output Power  Po",     D["Po"],    "W",   "5 W in paper")
        self.i_rl   = InputRow("Load Resistance  RL",  D["RL"],    "Ω",   "50 Ω in paper")
        self.i_ds   = InputRow("Switch Duty  Ds",      D["Ds"],    "",    "0.25 → class-DE")
        self.i_dd   = InputRow("Diode Duty  Dd",       D["Dd"],    "",    "0.5 → class-E")
        for r in [self.i_freq,self.i_vdd,self.i_po,self.i_rl,self.i_ds,self.i_dd]:
            v.addWidget(r)
        return g

    def _grp_coils(self):
        g = QGroupBox("Coil Parameters"); v = QVBoxLayout(g); v.setSpacing(3)

        # ── Identical / Different radio ──────────────────────────────
        rb_row = QHBoxLayout(); rb_row.setSpacing(14)
        self.rb_identical = QRadioButton("Identical coils")
        self.rb_different = QRadioButton("Different coils")
        self.rb_identical.setChecked(True)
        self._coil_grp = QButtonGroup(); self._coil_grp.addButton(self.rb_identical)
        self._coil_grp.addButton(self.rb_different)
        rb_row.addWidget(self.rb_identical); rb_row.addWidget(self.rb_different)
        rb_row.addStretch()
        v.addLayout(rb_row)

        # ── L override ───────────────────────────────────────────────
        self.chk_L = QCheckBox("Override L (skip Nagaoka)")
        self.chk_L.setStyleSheet(f"color:{YELLOW};font-size:11px;")
        v.addWidget(self.chk_L)

        # ── L override fields (primary) ──────────────────────────────
        self._l1_override_widget = QWidget()
        lo1 = QVBoxLayout(self._l1_override_widget); lo1.setContentsMargins(0,0,0,0); lo1.setSpacing(2)
        lo1.addWidget(SectionLabel("PRIMARY  —  Override Values"))
        self.i_L1  = InputRow("Self-inductance  L₁",  D["L1"],  "H",  "Direct override")
        self.i_RL1 = InputRow("AC ESR  RL₁",           D["RL1"], "Ω",  "Direct override")
        lo1.addWidget(self.i_L1); lo1.addWidget(self.i_RL1)
        self._l1_override_widget.setVisible(False)
        v.addWidget(self._l1_override_widget)

        # ── L2 override fields (secondary, only when different) ──────
        self._l2_override_widget = QWidget()
        lo2 = QVBoxLayout(self._l2_override_widget); lo2.setContentsMargins(0,0,0,0); lo2.setSpacing(2)
        lo2.addWidget(SectionLabel("SECONDARY  —  Override Values"))
        self.i_L2  = InputRow("Self-inductance  L₂",  D["L2"],  "H",  "Direct override")
        self.i_RL2 = InputRow("AC ESR  RL₂",           D["RL2"], "Ω",  "Direct override")
        lo2.addWidget(self.i_L2); lo2.addWidget(self.i_RL2)
        self._l2_override_widget.setVisible(False)
        v.addWidget(self._l2_override_widget)

        # ── Geometry — primary ───────────────────────────────────────
        self._geo_primary = QWidget()
        gp = QVBoxLayout(self._geo_primary); gp.setContentsMargins(0,0,0,0); gp.setSpacing(2)
        gp.addWidget(SectionLabel("PRIMARY COIL GEOMETRY"))
        self.i_dc1   = InputRow("Coil Diameter  D",    D["D_coil"],  "m",  "15.5 cm")
        self.i_n1    = InputRow("Turns  N",            D["N"],       "",   "10 turns")
        self.i_dw1   = InputRow("Wire Diameter  d_w",  D["d_wire"],  "m",  "1 mm")
        self.i_hc1   = InputRow("Winding Height  h",   D["h_coil"],  "m",  "1 cm")
        for r in [self.i_dc1,self.i_n1,self.i_dw1,self.i_hc1]: gp.addWidget(r)
        v.addWidget(self._geo_primary)

        # ── Geometry — secondary (hidden when identical) ─────────────
        self._geo_secondary = QWidget()
        gs = QVBoxLayout(self._geo_secondary); gs.setContentsMargins(0,0,0,0); gs.setSpacing(2)
        gs.addWidget(SectionLabel("SECONDARY COIL GEOMETRY"))
        self.i_dc2   = InputRow("Coil Diameter  D",    D["D_coil"],  "m")
        self.i_n2    = InputRow("Turns  N",            D["N"],       "")
        self.i_dw2   = InputRow("Wire Diameter  d_w",  D["d_wire"],  "m")
        self.i_hc2   = InputRow("Winding Height  h",   D["h_coil"],  "m")
        for r in [self.i_dc2,self.i_n2,self.i_dw2,self.i_hc2]: gs.addWidget(r)
        self._geo_secondary.setVisible(False)
        v.addWidget(self._geo_secondary)

        # ── Separation ───────────────────────────────────────────────
        self.i_dsep = InputRow("Coil Separation  d",   D["d_sep"], "m", "10 cm")
        v.addWidget(self.i_dsep)

        # ── k override ───────────────────────────────────────────────
        k_row = QHBoxLayout(); k_row.setSpacing(6)
        self.chk_k = QCheckBox("Override  k:")
        self.chk_k.setFixedWidth(110)
        self.i_k_field = QLineEdit(D["k"]); self.i_k_field.setFixedWidth(80)
        self.i_k_field.setValidator(QDoubleValidator()); self.i_k_field.setEnabled(False)
        self.chk_k.toggled.connect(self.i_k_field.setEnabled)
        note = QLabel("(Neumann underestimates k for helical coils)")
        note.setStyleSheet(f"color:{MUTED};font-size:10px;font-style:italic;")
        k_row.addSpacing(4); k_row.addWidget(self.chk_k); k_row.addWidget(self.i_k_field)
        k_row.addWidget(note); k_row.addStretch()
        v.addLayout(k_row)

        # ── wire up toggles ──────────────────────────────────────────
        self.rb_different.toggled.connect(self._on_coil_mode)
        self.chk_L.toggled.connect(self._on_L_override)

        return g

    def _grp_filter(self):
        g = QGroupBox("Output Low-Pass Filter  Lf–Cf"); v = QVBoxLayout(g); v.setSpacing(2)
        self.i_lf = InputRow("Inductance  Lf",  D["Lf"], "H")
        self.i_cf = InputRow("Capacitance  Cf", D["Cf"], "F")
        v.addWidget(self.i_lf); v.addWidget(self.i_cf)
        return g

    def _btn_row(self):
        h = QHBoxLayout(); h.setSpacing(8)
        self.btn_calc = QPushButton("Calculate"); self.btn_calc.setObjectName("calc_btn")
        self.btn_rst  = QPushButton("↺  Reset"); self.btn_rst.setObjectName("rst_btn")
        self.btn_calc.clicked.connect(self._on_calc)
        self.btn_rst.clicked.connect(self._on_reset)
        h.addWidget(self.btn_calc); h.addWidget(self.btn_rst); h.addStretch()
        return h

    # ── RIGHT panel ───────────────────────────────────────────────────

    def _right_panel(self):
        rw = QWidget(); rl = QVBoxLayout(rw); rl.setContentsMargins(6,4,6,4); rl.setSpacing(4)
        tabs = QTabWidget(); rl.addWidget(tabs, stretch=1)

        tabs.addTab(self._tab_coil(),       "Coil")
        tabs.addTab(self._tab_rectifier(),  "Rectifier")
        tabs.addTab(self._tab_inverter(),   "Inverter")
        tabs.addTab(self._tab_schematic(),  "Schematic")
        tabs.addTab(self._tab_log(),        "Log")
        return rw

    def _tab_coil(self):
        t = QWidget(); v = QVBoxLayout(t); v.setSpacing(3)
        g = QGroupBox("Computed Coil Parameters"); gl = QVBoxLayout(g); gl.setSpacing(1)
        self.o_L1      = OutputRow("L₁  (primary)",          "H")
        self.o_L2      = OutputRow("L₂  (secondary)",        "H")
        self.o_RL1     = OutputRow("RL₁  AC ESR primary",    "Ω")
        self.o_RL2     = OutputRow("RL₂  AC ESR secondary",  "Ω")
        self.o_k_calc  = OutputRow("k  Neumann analytical",  "")
        self.o_k_used  = OutputRow("k  used in design",      "")
        self.o_delta   = OutputRow("Skin depth  δ",          "mm")
        for r in [self.o_L1,self.o_L2,self.o_RL1,self.o_RL2,
                  self.o_k_calc,self.o_k_used,self.o_delta]: gl.addWidget(r)
        v.addWidget(g); v.addStretch(); return t

    def _tab_rectifier(self):
        t = QWidget(); v = QVBoxLayout(t); v.setSpacing(3)
        g = QGroupBox("Class-E Rectifier"); gl = QVBoxLayout(g); gl.setSpacing(1)
        self.o_phid  = OutputRow("Phase shift  φd",       "°")
        self.o_CD    = OutputRow("Shunt cap  C_D",        "F")
        self.o_Ri    = OutputRow("Input resistance  Ri",  "Ω")
        self.o_Ci    = OutputRow("Input cap  Ci",         "F")
        self.o_C2    = OutputRow("Resonant cap  C₂",      "F")
        self.o_I2    = OutputRow("Input current  I₂",     "A")
        self.o_Vind  = OutputRow("Induced voltage  Vind", "V")
        self.o_VDmax = OutputRow("Max diode voltage",     "V")
        self.o_Vo    = OutputRow("Output voltage  Vo",    "V")
        self.o_Io    = OutputRow("Output current  Io",    "A")
        for r in [self.o_phid,self.o_CD,self.o_Ri,self.o_Ci,self.o_C2,
                  self.o_I2,self.o_Vind,self.o_VDmax,self.o_Vo,self.o_Io]:
            gl.addWidget(r)
        v.addWidget(g); v.addStretch(); return t

    def _tab_inverter(self):
        t = QWidget(); v = QVBoxLayout(t); v.setSpacing(3)
        g = QGroupBox("Class-DE Inverter"); gl = QVBoxLayout(g); gl.setSpacing(1)
        self.o_Req  = OutputRow("Reflected resistance  Req",  "Ω")
        self.o_Xeq  = OutputRow("Reflected reactance  Xeq",  "Ω")
        self.o_I1   = OutputRow("TX coil current  I₁",        "A")
        self.o_Rout = OutputRow("Optimal load  Rout",         "Ω")
        self.o_Xp   = OutputRow("Transform reactance  Xp",    "Ω")
        self.o_Cp   = OutputRow("Transform cap  Cp",          "F")
        self.o_Xout = OutputRow("Output reactance  Xout",     "Ω")
        self.o_Q    = OutputRow("Loaded Q",                    "")
        self.o_C0   = OutputRow("Series resonant cap  C₀",    "F")
        self.o_CS1  = OutputRow("Shunt caps  CS1 = CS2",      "F")
        self.o_fc   = OutputRow("LPF cutoff  fc",             "Hz")
        for r in [self.o_Req,self.o_Xeq,self.o_I1,self.o_Rout,self.o_Xp,
                  self.o_Cp,self.o_Xout,self.o_Q,self.o_C0,self.o_CS1,self.o_fc]:
            gl.addWidget(r)
        v.addWidget(g); v.addStretch(); return t

    def _tab_schematic(self):
        t = QWidget(); v = QVBoxLayout(t); v.setContentsMargins(0,0,0,0)
        self._svg_widget = QSvgWidget()
        self._svg_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._refresh_schematic()
        v.addWidget(self._svg_widget)
        return t

    def _tab_log(self):
        t = QWidget(); v = QVBoxLayout(t)
        self._log = QTextEdit(); self._log.setReadOnly(True)
        self._log.setPlaceholderText("Full design summary appears here after calculation...")
        v.addWidget(self._log); return t

    # ═══════════════════════════════════════════════════════════════════
    #  TOGGLE HANDLERS
    # ═══════════════════════════════════════════════════════════════════

    def _on_coil_mode(self, different: bool):
        self._geo_secondary.setVisible(different)
        # L2 override only shown when different AND L-override checked
        self._l2_override_widget.setVisible(different and self.chk_L.isChecked())

    def _on_L_override(self, checked: bool):
        self._l1_override_widget.setVisible(checked)
        different = self.rb_different.isChecked()
        self._l2_override_widget.setVisible(checked and different)
        # geometry hidden when overriding L
        self._geo_primary.setVisible(not checked)
        self._geo_secondary.setVisible(not checked and different)
        # sep still shown always
        self.i_dsep.setVisible(not checked)

    # ═══════════════════════════════════════════════════════════════════
    #  SLOTS
    # ═══════════════════════════════════════════════════════════════════

    def _on_calc(self):
        self.btn_calc.setEnabled(False)
        self._reset_outputs()
        self._sb.showMessage("Calculating…")
        try:
            p = self._collect()
        except ValueError as e:
            self._sb.showMessage(f"Input error: {e}")
            self.btn_calc.setEnabled(True)
            return
        self._worker = DesignWorker(p)
        self._worker.finished_ok.connect(self._on_result)
        self._worker.finished_err.connect(self._on_error)
        self._worker.finished.connect(lambda: self.btn_calc.setEnabled(True))
        self._worker.start()

    def _on_result(self, r: dict):
        self._last_results = r
        k_diff = (r["k_calc"] is not None and
                  abs(r["k_calc"] - r["k_used"]) > 1e-6)

        # Coil
        self.o_L1.set_value(r["L1"])
        self.o_L2.set_value(r["L2"])
        self.o_RL1.set_value(r["RL1"])
        self.o_RL2.set_value(r["RL2"])
        if r["k_calc"] is not None:
            self.o_k_calc.set_value(r["k_calc"], warn=k_diff)
        else:
            self.o_k_calc._v.setText("(overridden)")
            self.o_k_calc._v.setStyleSheet(f"color:{MUTED};font-family:monospace;font-size:11px;")
        self.o_k_used.set_value(r["k_used"])
        if r["delta_mm"] is not None:
            self.o_delta.set_value(r["delta_mm"])

        # Rectifier
        self.o_phid.set_value(r["phi_d_deg"])
        self.o_CD.set_value(r["CD"]); self.o_Ri.set_value(r["Ri"])
        self.o_Ci.set_value(r["Ci"]); self.o_C2.set_value(r["C2"])
        self.o_I2.set_value(r["I2"]); self.o_Vind.set_value(r["Vind"])
        self.o_VDmax.set_value(r["VDmax"])
        self.o_Vo.set_value(r["Vo"]); self.o_Io.set_value(r["Io"])

        # Inverter
        self.o_Req.set_value(r["Req"]); self.o_Xeq.set_value(r["Xeq"])
        self.o_I1.set_value(r["I1"]); self.o_Rout.set_value(r["Rout"])
        self.o_Xp.set_value(r["Xp"])
        if r["Cp"]: self.o_Cp.set_value(r["Cp"])
        self.o_Xout.set_value(r["Xout"]); self.o_Q.set_value(r["Q"])
        self.o_C0.set_value(r["C0"]); self.o_CS1.set_value(r["CS1"])
        self.o_fc.set_value(r["fc"])

        self._refresh_schematic()
        self._write_log(r)
        msg = "✓  Design complete"
        if k_diff:
            msg += "  ⚠  k override active"
        self._sb.showMessage(msg)

    def _on_error(self, msg: str):
        self._sb.showMessage(f"✗  {msg}")
        self._log.setHtml(f'<span style="color:{RED}"><b>Error:</b> {msg}</span>')

    def _on_reset(self):
        rows = {
            self.i_freq:D["freq"], self.i_vdd:D["VDD"], self.i_po:D["Po"],
            self.i_rl:D["RL"],     self.i_ds:D["Ds"],   self.i_dd:D["Dd"],
            self.i_dc1:D["D_coil"],self.i_n1:D["N"],    self.i_dw1:D["d_wire"],
            self.i_hc1:D["h_coil"],self.i_dc2:D["D_coil"],self.i_n2:D["N"],
            self.i_dw2:D["d_wire"],self.i_hc2:D["h_coil"],self.i_dsep:D["d_sep"],
            self.i_lf:D["Lf"],     self.i_cf:D["Cf"],
            self.i_L1:D["L1"],     self.i_RL1:D["RL1"],
            self.i_L2:D["L2"],     self.i_RL2:D["RL2"],
        }
        for row, val in rows.items(): row.set_text(val)
        self.rb_identical.setChecked(True)
        self.chk_L.setChecked(False)
        self.chk_k.setChecked(False)
        self.i_k_field.setText(D["k"])
        self._last_results = None
        self._reset_outputs()
        self._refresh_schematic()
        self._sb.showMessage("Reset to paper values — Nagashima et al. 2014")

    # ═══════════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════════

    def _collect(self) -> dict:
        fv = lambda row: row.value()
        p = dict(
            freq=fv(self.i_freq), VDD=fv(self.i_vdd), Po=fv(self.i_po),
            RL=fv(self.i_rl),     Ds=fv(self.i_ds),   Dd=fv(self.i_dd),
            Lf=fv(self.i_lf),     Cf=fv(self.i_cf),
            identical_coils=self.rb_identical.isChecked(),
            d_sep=fv(self.i_dsep) if not self.chk_L.isChecked() else 0.1,
        )
        # Coil geometry
        if not self.chk_L.isChecked():
            p.update(N1=int(fv(self.i_n1)), D_coil1=fv(self.i_dc1),
                     d_wire1=fv(self.i_dw1), h_coil1=fv(self.i_hc1))
            if not p["identical_coils"]:
                p.update(N2=int(fv(self.i_n2)), D_coil2=fv(self.i_dc2),
                         d_wire2=fv(self.i_dw2), h_coil2=fv(self.i_hc2))
        # L overrides
        if self.chk_L.isChecked():
            p["L1_override"]  = fv(self.i_L1)
            p["RL1_override"] = fv(self.i_RL1)
            if not p["identical_coils"]:
                p["L2_override"]  = fv(self.i_L2)
                p["RL2_override"] = fv(self.i_RL2)
        # k override
        if self.chk_k.isChecked():
            p["k_override"] = float(self.i_k_field.text())
        return p

    def _reset_outputs(self):
        for v in vars(self).values():
            if isinstance(v, OutputRow): v.reset()
        self._log.clear()

    def _refresh_schematic(self):
        # pass collected results + freq for Lout calculation
        r = None
        if self._last_results:
            r = dict(self._last_results)
            try: r["freq"] = self.i_freq.value()
            except: pass
            try: r["RL"] = self.i_rl.value()
            except: pass
        svg = build_schematic_svg(r, width=680, height=520)
        self._svg_widget.load(svg.encode("utf-8"))

    # ── HTML log ──────────────────────────────────────────────────────

    def _write_log(self, r: dict):
        def tr(lb, v, u=""):
            return (f'<tr>'
                    f'<td style="color:{MUTED};padding-right:14px;white-space:nowrap;">{lb}</td>'
                    f'<td style="color:{GREEN};font-family:monospace;">{eng(v,u)}</td></tr>')

        k_warn = ""
        if r["k_calc"] is not None and abs(r["k_calc"]-r["k_used"]) > 1e-6:
            k_warn = (f'<p style="color:{YELLOW};font-size:10px;">'
                      f'⚠ Neumann k={r["k_calc"]:.4f} — override k={r["k_used"]:.4f}</p>')

        cp_row = tr("Xp → Cp", r["Cp"], "F") if r["Cp"] else ""
        html = f"""
<style>body{{background:{BG};color:{TEXT};font-family:Consolas,monospace;font-size:11px;}}
h3{{color:{TEAL};margin:8px 0 3px 0;border-bottom:1px solid {BORDER};padding-bottom:2px;}}
</style>
<h3>▶ Coil</h3>{k_warn}<table>
{tr("L₁",r["L1"],"H")}{tr("L₂",r["L2"],"H")}
{tr("RL₁ (ESR)",r["RL1"],"Ω")}{tr("RL₂ (ESR)",r["RL2"],"Ω")}
{tr("k calc",r["k_calc"]) if r["k_calc"] else ""}{tr("k used",r["k_used"])}
{tr("δ skin depth",r["delta_mm"]*1e-3,"m") if r["delta_mm"] else ""}
</table>
<h3>▶ Class-E Rectifier  (Eqs. 3–10, 22)</h3><table>
{tr("φd",r["phi_d_deg"],"°")}{tr("CD (Eq.3)",r["CD"],"F")}
{tr("Ri (Eq.5)",r["Ri"],"Ω")}{tr("Ci (Eq.4)",r["Ci"],"F")}
{tr("C₂ (Eq.7)",r["C2"],"F")}{tr("I₂ (Eq.8)",r["I2"],"A")}
{tr("Vind (Eq.10)",r["Vind"],"V")}{tr("VDmax (Eq.22)",r["VDmax"],"V")}
{tr("Vo",r["Vo"],"V")}{tr("Io",r["Io"],"A")}
</table>
<h3>▶ Class-DE Inverter  (Eqs. 12–21)</h3><table>
{tr("Req (Eq.12)",r["Req"],"Ω")}{tr("Xeq (Eq.13)",r["Xeq"],"Ω")}
{tr("I₁ (Eq.14)",r["I1"],"A")}{tr("Rout (Eq.17)",r["Rout"],"Ω")}
{tr("Xp (Eq.18)",r["Xp"],"Ω")}{cp_row}
{tr("Xout (Eq.16)",r["Xout"],"Ω")}{tr("Q (Eq.19)",r["Q"])}
{tr("C₀ (Eq.20)",r["C0"],"F")}{tr("CS (Eq.21)",r["CS1"],"F")}
{tr("LPF cutoff fc",r["fc"],"Hz")}
</table>
<p style="color:{MUTED};font-size:9px;margin-top:8px;">
Ref: Nagashima, Wei, Sekiya — IEEE IECON 2014 |
Coil: Nagaoka(L) · Dowell(ESR) · Neumann(k)</p>"""
        self._log.setHtml(html)
