"""
widgets.py  —  Compact reusable widgets: InputRow, OutputRow, SectionLabel, eng().
"""
from __future__ import annotations
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QDoubleValidator
from .style import MUTED, GREEN, YELLOW, BORDER, ACCENT, TEXT

_SI = [(1e9,"G"),(1e6,"M"),(1e3,"k"),(1.0,""),(1e-3,"m"),
       (1e-6,"μ"),(1e-9,"n"),(1e-12,"p")]

def eng(value, unit=""):
    if value is None: return "N/A"
    if value == 0.0:  return f"0 {unit}".strip()
    a = abs(value)
    for thr, pfx in _SI:
        if a >= thr:
            return f"{value/thr:.4g} {pfx}{unit}".strip()
    return f"{value:.4g} {unit}".strip()


def SectionLabel(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{ACCENT};font-size:9px;font-weight:bold;letter-spacing:1px;"
        f"padding:3px 0 1px 0;border-bottom:1px solid {BORDER};")
    return lbl


class InputRow(QWidget):
    """[label] [field] [unit]  — compact 12 px row."""
    LW = 185   # label width
    UW = 42    # unit width

    def __init__(self, label, default, unit="", tooltip="", width=105, parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self)
        h.setContentsMargins(0,1,0,1); h.setSpacing(5)

        lb = QLabel(label); lb.setFixedWidth(self.LW)
        lb.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        lb.setStyleSheet(f"color:{TEXT};font-size:11px;")
        if tooltip: lb.setToolTip(tooltip)

        self.field = QLineEdit(default); self.field.setFixedWidth(width)
        self.field.setValidator(QDoubleValidator())

        ul = QLabel(unit); ul.setFixedWidth(self.UW)
        ul.setStyleSheet(f"color:{MUTED};font-size:10px;")

        h.addWidget(lb); h.addWidget(self.field); h.addWidget(ul); h.addStretch()

    def value(self):
        try: return float(self.field.text().strip())
        except: raise ValueError(f"Cannot parse '{self.field.text()}'")

    def set_text(self, t): self.field.setText(t)


class OutputRow(QWidget):
    """[label] [value]  — compact read-only display row."""
    LW = 195
    VW = 130
    UW = 42

    def __init__(self, label, unit="", parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self)
        h.setContentsMargins(0,0,0,0); h.setSpacing(5)

        lb = QLabel(label); lb.setFixedWidth(self.LW)
        lb.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        lb.setStyleSheet(f"color:{MUTED};font-size:11px;")

        self._v = QLabel("—"); self._v.setFixedWidth(self.VW)
        self._v.setStyleSheet(
            f"color:{GREEN};font-weight:bold;font-family:monospace;font-size:11px;")

        ul = QLabel(unit); ul.setFixedWidth(self.UW)
        ul.setStyleSheet(f"color:{MUTED};font-size:10px;")

        h.addWidget(lb); h.addWidget(self._v); h.addWidget(ul); h.addStretch()

    def set_value(self, v, warn=False):
        c = YELLOW if warn else GREEN
        self._v.setText(eng(v))
        self._v.setStyleSheet(
            f"color:{c};font-weight:bold;font-family:monospace;font-size:11px;")

    def reset(self):
        self._v.setText("—")
        self._v.setStyleSheet(
            f"color:{GREEN};font-weight:bold;font-family:monospace;font-size:11px;")
