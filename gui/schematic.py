"""
schematic.py
============
Renders the 5 equivalent-circuit diagrams (a)–(e) from Nagashima 2014
as an SVG, with calculated component values annotated inline.

All drawing is pure SVG strings — no external dependencies beyond PyQt5.
"""
from __future__ import annotations
from .widgets import eng
from .style   import BG, PANEL, TEAL, TEXT, MUTED, GREEN, ACCENT, BORDER, YELLOW

# ── colour shortcuts ─────────────────────────────────────────────────────────
C_WIRE  = "#a0a8c8"
C_COMP  = "#7c6af7"
C_VAL   = "#43d98c"
C_LABEL = "#c8cce0"
C_BOX   = "#23233a"
C_TITLE = "#4ecdc4"

def _svg_open(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>')

def _svg_close(): return '</svg>'

def _text(x, y, txt, color=C_LABEL, size=9, anchor="middle", bold=False):
    fw = "bold" if bold else "normal"
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-family="Consolas,monospace" text-anchor="{anchor}" '
            f'font-weight="{fw}">{txt}</text>')

def _line(x1,y1,x2,y2,col=C_WIRE,w=1.2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"/>'

def _rect(x,y,w,h,fill=C_BOX,stroke=C_COMP,sw=1):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="2"/>'

def _box(x,y,w,h,label,val="",col=C_COMP):
    s  = _rect(x,y,w,h,fill=C_BOX,stroke=col)
    cx = x+w/2; cy = y+h/2
    s += _text(cx, cy+3, label, col, 8, bold=True)
    if val:
        s += _text(cx, y+h+10, val, C_VAL, 8)
    return s

def _inductor(x,y,horiz=True,label="",val=""):
    """Draw a 3-bump inductor symbol."""
    s = ""
    if horiz:
        bumps = 3; bw = 7; bh = 5
        for i in range(bumps):
            cx = x + i*bw + bw/2
            s += f'<path d="M {x+i*bw},{y} A {bw/2},{bh} 0 0 1 {x+(i+1)*bw},{y}" fill="none" stroke="{C_COMP}" stroke-width="1.3"/>'
        s += _line(x-6,y,x,y); s += _line(x+bumps*bw,y,x+bumps*bw+6,y)
        if label: s += _text(x+bumps*bw/2, y-7, label, C_COMP, 8)
        if val:   s += _text(x+bumps*bw/2, y+14, val,   C_VAL,  8)
    else:
        bumps = 3; bw = 7; bh = 5
        for i in range(bumps):
            cy = y + i*bw + bw/2
            s += f'<path d="M {x},{y+i*bw} A {bh},{bw/2} 0 0 1 {x},{y+(i+1)*bw}" fill="none" stroke="{C_COMP}" stroke-width="1.3"/>'
        s += _line(x,y-6,x,y); s += _line(x,y+bumps*bw,x,y+bumps*bw+6)
        if label: s += _text(x+16, y+bumps*bw/2+3, label, C_COMP, 8, "start")
        if val:   s += _text(x+16, y+bumps*bw/2+14, val, C_VAL, 8, "start")
    return s

def _capacitor(x,y,horiz=True,label="",val=""):
    """Draw a capacitor symbol."""
    s = ""
    gap = 3
    if horiz:
        s += _line(x-6,y,x,y); s += _line(x+gap*2,y,x+gap*2+6,y)
        s += _line(x,y-8,x,y+8,C_COMP,2); s += _line(x+gap*2,y-8,x+gap*2,y+8,C_COMP,2)
        if label: s += _text(x+gap, y-12, label, C_COMP, 8)
        if val:   s += _text(x+gap, y+18, val, C_VAL, 8)
    else:
        s += _line(x,y-6,x,y); s += _line(x,y+gap*2,x,y+gap*2+6)
        s += _line(x-8,y,x+8,y,C_COMP,2); s += _line(x-8,y+gap*2,x+8,y+gap*2,C_COMP,2)
        if label: s += _text(x+12, y+gap, label, C_COMP, 8, "start")
        if val:   s += _text(x+12, y+gap+10, val, C_VAL, 8, "start")
    return s

def _resistor(x,y,horiz=True,label="",val=""):
    """Draw a resistor (zigzag)."""
    s = ""
    if horiz:
        s += _line(x-6,y,x,y); s += _line(x+24,y,x+30,y)
        pts = f"{x},  {y}"
        zz = [(x+2,y-4),(x+5,y+4),(x+8,y-4),(x+11,y+4),(x+14,y-4),(x+17,y+4),(x+20,y-4),(x+22,y)]
        pts = f"M {x},{y} " + " ".join(f"L {a},{b}" for a,b in zz)
        s += f'<path d="{pts}" fill="none" stroke="{C_COMP}" stroke-width="1.3"/>'
        if label: s += _text(x+12, y-11, label, C_COMP, 8)
        if val:   s += _text(x+12, y+16, val, C_VAL, 8)
    else:
        s += _line(x,y-6,x,y); s += _line(x,y+24,x,y+30)
        zz = [(x-4,y+2),(x+4,y+5),(x-4,y+8),(x+4,y+11),(x-4,y+14),(x+4,y+17),(x-4,y+20),(x,y+22)]
        pts = f"M {x},{y} " + " ".join(f"L {a},{b}" for a,b in zz)
        s += f'<path d="{pts}" fill="none" stroke="{C_COMP}" stroke-width="1.3"/>'
        if label: s += _text(x+12, y+12, label, C_COMP, 8, "start")
        if val:   s += _text(x+12, y+22, val, C_VAL, 8, "start")
    return s

def _mosfet(x,y,label=""):
    """Simple N-MOSFET symbol."""
    s  = _line(x,y,x,y+28,C_COMP,1.5)        # drain-source line
    s += _line(x-8,y+4,x,y+4,C_WIRE)           # drain
    s += _line(x-8,y+24,x,y+24,C_WIRE)         # source
    s += _line(x-8,y+14,x-4,y+14,C_COMP,1.5)   # gate
    s += _line(x-4,y+6,x-4,y+22,C_COMP,2)      # gate bar
    # arrow
    s += f'<polygon points="{x-1},{y+14} {x-6},{y+11} {x-6},{y+17}" fill="{C_COMP}"/>'
    if label: s += _text(x+6, y+16, label, C_COMP, 8, "start")
    return s

def _diode(x,y,label=""):
    s  = _line(x,y-6,x,y)
    s += _line(x,y+12,x,y+18)
    s += f'<polygon points="{x},{y} {x-7},{y+12} {x+7},{y+12}" fill="{C_COMP}" stroke="{C_COMP}" stroke-width="1"/>'
    s += _line(x-7,y+12,x+7,y+12,C_COMP,2)
    if label: s += _text(x+10, y+8, label, C_COMP, 8, "start")
    return s

def _gnd(x,y):
    s  = _line(x,y,x,y+6)
    s += _line(x-8,y+6,x+8,y+6,C_WIRE,1.5)
    s += _line(x-5,y+9,x+5,y+9,C_WIRE,1)
    s += _line(x-2,y+12,x+2,y+12,C_WIRE,1)
    return s

def _vdd(x,y,label="VDD"):
    s  = _line(x,y,x,y+6)
    s += _line(x-8,y,x+8,y,C_WIRE,1.5)
    s += _text(x,y-5,label,TEAL,9)
    return s

def _dot(x,y):
    return f'<circle cx="{x}" cy="{y}" r="2.5" fill="{C_WIRE}"/>'

def _panel_box(x,y,w,h,title):
    s  = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{BORDER}" stroke-width="1" rx="4" stroke-dasharray="4,2"/>'
    s += _text(x+w/2, y+10, title, MUTED, 8)
    return s

# ── per-diagram builders ──────────────────────────────────────────────────────

def _diagram_a(r, ox, oy):
    """System overview (a)."""
    s = _text(ox+185, oy+12, "(a) System Overview", C_TITLE, 9, bold=True)
    # VDD rail
    s += _vdd(ox+20, oy+20)
    # S2
    s += _mosfet(ox+40, oy+26, "S₂")
    # S1
    s += _mosfet(ox+40, oy+60, "S₁")
    # CS2
    s += _capacitor(ox+55, oy+30, False, "CS₂",  eng(r.get("CS1"),"F") if r else "")
    # CS1
    s += _capacitor(ox+55, oy+64, False, "CS₁",  eng(r.get("CS1"),"F") if r else "")
    # C0
    s += _capacitor(ox+75, oy+48, True, "C₀",   eng(r.get("C0"),"F") if r else "")
    # Xp/Cp
    s += _capacitor(ox+95, oy+48, True, "Cp",   eng(r.get("Cp"),"F") if r else "")
    # L1
    s += _inductor(ox+115, oy+58, True, "L₁",  eng(r.get("L1"),"H") if r else "")
    # M coupling arrow
    s += _line(ox+155, oy+30, ox+175, oy+30, TEAL)
    s += _text(ox+165, oy+26, "M", TEAL, 8)
    # L2
    s += _inductor(ox+175, oy+58, True, "L₂",  eng(r.get("L2"),"H") if r else "")
    # C2
    s += _capacitor(ox+200, oy+48, True, "C₂",  eng(r.get("C2"),"F") if r else "")
    # Diode
    s += _diode(ox+220, oy+42, "D")
    # CD
    s += _capacitor(ox+235, oy+48, True, "C_D",  eng(r.get("CD"),"F") if r else "")
    # Lf
    s += _inductor(ox+255, oy+35, True, "Lf", "")
    # Cf
    s += _capacitor(ox+285, oy+48, True, "Cf", "")
    # RL
    s += _resistor(ox+305, oy+40, False, "RL", eng(r.get("RL"),"Ω") if r else "")
    # ground
    s += _gnd(ox+20, oy+92)
    s += _gnd(ox+330, oy+80)
    # boxes
    s += _panel_box(ox+5,  oy+16, 115, 85, "Class-DE Inverter")
    s += _panel_box(ox+130,oy+16, 100, 85, "Resonant Inductive Coupling")
    s += _panel_box(ox+240,oy+16, 100, 85, "Class-E Rectifier")
    return s

def _diagram_b(r, ox, oy):
    """Equivalent circuit of rectifier (b) — with CD and filter."""
    s = _text(ox+100, oy+12, "(b) Rectifier Equivalent", C_TITLE, 9, bold=True)
    # Vind source
    s += f'<circle cx="{ox+20}" cy="{oy+50}" r="12" fill="none" stroke="{C_COMP}" stroke-width="1.2"/>'
    s += _text(ox+20, oy+52, "~", C_COMP, 10)
    s += _text(ox+20, oy+68, "Vind", MUTED, 8)
    # RL2 (wire resistance)
    s += _resistor(ox+40, oy+34, True, "RL₂", eng(r.get("RL2"),"Ω") if r else "")
    # C2
    s += _capacitor(ox+75, oy+34, True, "C₂", eng(r.get("C2"),"F") if r else "")
    # Lf
    s += _inductor(ox+110, oy+34, True, "Lf", "")
    # wires
    s += _line(ox+32, oy+38, ox+40, oy+38)
    s += _line(ox+105,oy+38, ox+110,oy+38)
    # Diode branch
    s += _diode(ox+148, oy+28, "D")
    # CD
    s += _capacitor(ox+160, oy+34, True, "C_D", eng(r.get("CD"),"F") if r else "")
    # Cf
    s += _capacitor(ox+180, oy+34, True, "Cf", "")
    # RL
    s += _resistor(ox+200, oy+30, False, "RL", "")
    s += _text(ox+206, oy+60, f"Vo={eng(r.get('Vo'),'V')}" if r else "Vo", C_VAL, 8)
    s += _gnd(ox+20, oy+66); s += _gnd(ox+215, oy+72)
    # Zsec label
    s += _text(ox+80, oy+80, "← Zsec", MUTED, 8)
    return s

def _diagram_c(r, ox, oy):
    """Rectifier as input impedance (c)."""
    s = _text(ox+100, oy+12, "(c) Rectifier as Zi", C_TITLE, 9, bold=True)
    s += f'<circle cx="{ox+20}" cy="{oy+50}" r="12" fill="none" stroke="{C_COMP}" stroke-width="1.2"/>'
    s += _text(ox+20, oy+52, "~", C_COMP, 10)
    s += _text(ox+20, oy+68, "Vind", MUTED, 8)
    s += _resistor(ox+40, oy+34, True, "RL₂", eng(r.get("RL2"),"Ω") if r else "")
    s += _capacitor(ox+75, oy+34, True, "C₂", eng(r.get("C2"),"F") if r else "")
    s += _capacitor(ox+110,oy+34, True, "Ci",  eng(r.get("Ci"),"F") if r else "")
    s += _resistor(ox+148, oy+30, False, "Ri",  eng(r.get("Ri"),"Ω") if r else "")
    s += _line(ox+32, oy+38, ox+40, oy+38)
    s += _gnd(ox+20, oy+66); s += _gnd(ox+162, oy+72)
    s += _text(ox+80, oy+80, "← Zrec", MUTED, 8)
    return s

def _diagram_d(r, ox, oy):
    """Inverter with reflected impedance (d)."""
    s = _text(ox+160, oy+12, "(d) Reflected Impedance Model", C_TITLE, 9, bold=True)
    s += _vdd(ox+20, oy+20)
    s += _mosfet(ox+40, oy+26, "S₂")
    s += _mosfet(ox+40, oy+60, "S₁")
    s += _capacitor(ox+55, oy+30, False, "CS₂", eng(r.get("CS1"),"F") if r else "")
    s += _capacitor(ox+55, oy+64, False, "CS₁", eng(r.get("CS1"),"F") if r else "")
    s += _capacitor(ox+75, oy+48, True,  "C₀",  eng(r.get("C0"),"F") if r else "")
    s += _capacitor(ox+95, oy+48, True,  "Cp",  eng(r.get("Cp"),"F") if r else "")
    # (1-k²)L1
    s += _inductor(ox+115, oy+38, True, "(1-k²)L₁", eng((1-(r.get("k_used",0))**2)*r.get("L1",0),"H") if r else "")
    # k²L1
    s += _inductor(ox+150, oy+38, True, "k²L₁", "")
    # Reflected Zeq box
    s += _rect(ox+185, oy+30, 55, 30, fill=PANEL, stroke=TEAL)
    s += _text(ox+212, oy+42, "Zeq", TEAL, 8, bold=True)
    s += _text(ox+212, oy+52, f"Req={eng(r.get('Req'),'Ω')}" if r else "", C_VAL, 7)
    s += _gnd(ox+20, oy+92)
    # Zout label
    s += _text(ox+110, oy+80, "← Zout", MUTED, 8)
    return s

def _diagram_e(r, ox, oy):
    """Reduced class-DE inverter (e)."""
    s = _text(ox+130, oy+12, "(e) Simplified Inverter", C_TITLE, 9, bold=True)
    s += _vdd(ox+20, oy+20)
    s += _mosfet(ox+40, oy+26, "S₂")
    s += _mosfet(ox+40, oy+60, "S₁")
    s += _capacitor(ox+55, oy+30, False, "CS₂", eng(r.get("CS1"),"F") if r else "")
    s += _capacitor(ox+55, oy+64, False, "CS₁", eng(r.get("CS1"),"F") if r else "")
    s += _capacitor(ox+75, oy+48, True,  "C₀",  eng(r.get("C0"),"F") if r else "")
    # Lout
    s += _inductor(ox+100, oy+38, True, "Lout", eng(r.get("Xout",0)/(2*3.14159*r.get("freq",1e6)),"H") if r else "")
    # Rout
    s += _resistor(ox+140, oy+34, False, "Rout", eng(r.get("Rout"),"Ω") if r else "")
    s += _gnd(ox+20, oy+92); s += _gnd(ox+155, oy+80)
    return s


# ── public API ────────────────────────────────────────────────────────────────

def build_schematic_svg(results: dict | None, width=760, height=530) -> str:
    """
    Build a complete SVG string showing all 5 sub-circuits with
    annotated component values from *results* (None → blank labels).
    """
    r = results
    s = _svg_open(width, height)

    # Title
    s += _text(width//2, 18, "WPT System — Circuit Diagrams with Computed Values",
               TEAL, 11, bold=True)

    # Layout: (a) top full width; (b)(c) middle; (d)(e) bottom
    pad = 8; dh = 105  # diagram height
    dw2 = (width - 3*pad) // 2   # half-width diagram

    # (a) full width
    s += _rect(pad, 24, width-2*pad, dh, fill=PANEL, stroke=BORDER)
    s += _diagram_a(r, pad+6, 26)

    # (b) left
    s += _rect(pad, 24+dh+pad, dw2, dh, fill=PANEL, stroke=BORDER)
    s += _diagram_b(r, pad+6, 24+dh+pad+2)

    # (c) right
    s += _rect(pad*2+dw2, 24+dh+pad, dw2, dh, fill=PANEL, stroke=BORDER)
    s += _diagram_c(r, pad*2+dw2+6, 24+dh+pad+2)

    # (d) left
    y3 = 24 + 2*(dh+pad)
    s += _rect(pad, y3, dw2, dh, fill=PANEL, stroke=BORDER)
    s += _diagram_d(r, pad+6, y3+2)

    # (e) right
    s += _rect(pad*2+dw2, y3, dw2, dh, fill=PANEL, stroke=BORDER)
    s += _diagram_e(r, pad*2+dw2+6, y3+2)

    # No-results overlay
    if r is None:
        s += (f'<rect x="0" y="0" width="{width}" height="{height}" '
              f'fill="{BG}" opacity="0.55"/>')
        s += _text(width//2, height//2,
                   "Run calculation to annotate values", MUTED, 13)

    s += _svg_close()
    return s
