"""
style.py  —  Colour palette and Qt stylesheet.
"""

BG     = "#0a0f0a"   # near-black with green tint
PANEL  = "#0d140d"   # slightly lighter dark green
PANEL2 = "#0b110b"
ACCENT = "#00ff41"   # phosphor green
TEAL   = "#00cc33"   # dimmer phosphor
TEXT   = "#00ff41"   # full bright phosphor green
MUTED  = "#005c18"   # dim phosphor (inactive text)
GREEN  = "#00ff41"   # values — same phosphor
RED    = "#ff4400"   # amber-red for errors
YELLOW = "#aaff00"   # yellow-green phosphor
ORANGE = "#88ff00"
BORDER = "#003d12"   # very dim green border
DARK   = "#060c06"   # input field background
DARKER = "#040804"   # log background

STYLESHEET = f"""
QMainWindow,QWidget{{
    background:{BG};color:{TEXT};
    font-family:'Segoe UI','Inter',sans-serif;font-size:12px;}}

QGroupBox{{
    background:{PANEL};border:1px solid {BORDER};border-radius:6px;
    margin-top:12px;padding:6px 8px 8px 8px;font-weight:bold;color:{TEAL};
    font-size:11px;}}
QGroupBox::title{{
    subcontrol-origin:margin;left:8px;padding:0 5px;
    color:{TEAL};font-size:11px;}}

QLineEdit{{
    background:{DARK};border:1px solid {BORDER};border-radius:4px;
    padding:3px 6px;color:{TEXT};selection-background-color:{ACCENT};
    font-size:12px;}}
QLineEdit:focus{{border:1px solid {ACCENT};}}
QLineEdit:disabled{{background:#0e0e18;color:{MUTED};}}

QCheckBox{{color:{TEXT};spacing:5px;font-size:11px;}}
QCheckBox::indicator{{
    width:14px;height:14px;border:1px solid {BORDER};
    border-radius:3px;background:{DARK};}}
QCheckBox::indicator:checked{{background:{ACCENT};border-color:{ACCENT};}}

QLabel{{color:{TEXT};background:transparent;}}

QPushButton#calc_btn{{
    background:{MUTED};color:white;border:none;border-radius:6px;
    padding:8px 22px;font-size:13px;font-weight:bold;min-width:120px;}}
QPushButton#calc_btn:hover{{background:RED;}}
QPushButton#calc_btn:pressed{{background:TEAL;}}

QPushButton#rst_btn{{
    background:transparent;color:{MUTED};border:1px solid {BORDER};
    border-radius:6px;padding:8px 14px;font-size:12px;}}
QPushButton#rst_btn:hover{{color:{TEXT};border-color:{ACCENT};}}

QScrollArea{{border:none;background:{BG};}}

QTabWidget::pane{{
    background:{PANEL};border:1px solid {BORDER};border-radius:6px;}}
QTabBar::tab{{
    background:{BG};color:{MUTED};padding:6px 14px;
    border-top-left-radius:5px;border-top-right-radius:5px;
    margin-right:2px;font-size:11px;}}
QTabBar::tab:selected{{background:{PANEL};color:{TEAL};font-weight:bold;}}

QTextEdit{{
    background:{DARKER};border:1px solid {BORDER};border-radius:5px;
    color:{TEXT};font-family:'Consolas','Courier New',monospace;
    font-size:11px;padding:6px;}}

QStatusBar{{background:{PANEL};color:{MUTED};font-size:10px;}}
QSplitter::handle{{background:{BORDER};width:1px;}}

QRadioButton{{color:{TEXT};spacing:5px;font-size:11px;}}
QRadioButton::indicator{{
    width:13px;height:13px;border:1px solid {BORDER};
    border-radius:7px;background:{DARK};}}
QRadioButton::indicator:checked{{
    background:{ACCENT};border:3px solid {DARK};
    outline:1px solid {ACCENT};}}
"""
