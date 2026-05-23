# RIC-WPT Designer

An analytical design tool for a **Resonant Inductively Coupled Wireless Power Transfer** system using a **Class-DE inverter** (transmitter) and **Class-E rectifier** (receiver). All component values are computed from closed-form equations — no simulation required.

Based on:
> T. Nagashima, X. Wei, H. Sekiya — *"Analytical Design Procedure for Resonant Inductively Coupled Wireless Power Transfer System With Class-DE Inverter and Class-E Rectifier"*, IEEE IECON 2014.

---

## Screenshot

![RIC-WPT Designer GUI](img/GUI_pic.png)

---

## Features

- **Full analytical design** — solves all 22 paper equations in sequence; results appear instantly
- **Coil parameter calculation** — self-inductance via Nagaoka coefficient, AC ESR via Dowell's equation, coupling coefficient via Neumann's formula
- **Identical or independent coils** — toggle between a shared geometry for both coils or separate primary / secondary inputs
- **Direct L override** — bypass Nagaoka and enter L₁, L₂, RL₁, RL₂ directly (useful when you have measured or datasheet values)
- **k override** — enter a measured coupling coefficient to replace the Neumann analytical estimate (which underestimates k for helical coils)
- **LPF cutoff frequency** — displays `fc = 1 / (2π√(Lf·Cf))` alongside the filter components
- **Circuit schematic tab** — all 5 equivalent-circuit diagrams from the paper rendered as SVG with computed values annotated inline
- **CRT terminal theme** — phosphor-green on near-black

---

## Installation

**Requirements:** Python 3.8+

```bash
pip install PyQt5 scipy
```

Then run:

```bash
python main.py
```

---

## Project Structure

```
WPT_Designer/
├── main.py                   ← Entry point
├── requirements.txt
├── img/
│   └── GUI_pic.png
│
├── physics/                  ← Pure maths, no GUI dependency
│   ├── constants.py          ← MU0, RHO_COPPER
│   ├── coil_model.py         ← CoilModel  (Nagaoka · Dowell · Neumann)
│   └── wpt_design.py         ← WPTDesigner (all paper equations)
│
└── gui/                      ← PyQt5 presentation layer
    ├── style.py              ← Colour palette + Qt stylesheet
    ├── widgets.py            ← InputRow, OutputRow, eng() SI formatter
    ├── worker.py             ← DesignWorker QThread
    ├── schematic.py          ← SVG circuit diagram renderer
    └── main_window.py        ← MainWindow with all tabs and slots
```

The `physics/` layer has **zero GUI imports** — you can use `CoilModel` and `WPTDesigner` headlessly in your own scripts.

---

## How to Use

### 1 — Operating Conditions
Enter your target system specifications in the top-left panel.

| Field | Description | Paper value |
|---|---|---|
| Frequency f | Operating frequency | 1 MHz |
| DC Supply VDD | Input DC voltage | 48 V |
| Output Power Po | Desired output power | 5 W |
| Load Resistance RL | Load at output | 50 Ω |
| Switch Duty Ds | Class-DE switch on-duty ratio | 0.25 |
| Diode Duty Dd | Class-E diode on-duty ratio | 0.5 |

### 2 — Coil Parameters

**Identical coils** (default) — one set of geometry fields applies to both primary and secondary.  
**Different coils** — separate geometry fields appear for each side.

| Field | Description | Paper value |
|---|---|---|
| Coil Diameter D | Centre-to-centre winding diameter | 155 mm |
| Turns N | Number of turns | 10 |
| Wire Diameter d_w | Bare wire diameter | 1 mm |
| Winding Height h | Axial length of winding | 10 mm |
| Coil Separation d | Centre-to-centre coil distance | 100 mm |

**Override L** — tick this to skip Nagaoka/Dowell and enter L and ESR directly.  
**Override k** — tick this to enter a measured coupling coefficient. The Neumann formula is shown for reference but typically underestimates k for real helical coils by a factor of ~3×.

### 3 — Output Filter
Standard Lf–Cf low-pass filter values. The cutoff frequency `fc` is displayed in the results.

### 4 — Calculate
Press **Calculate**. Results populate across four tabs on the right.

---

## Output Tabs

### Coil
Computed coil parameters — self-inductance, AC ESR, analytical k, k used in design, and skin depth at the operating frequency.

### Rectifier
All Class-E rectifier components from the paper:

| Output | Equation | Description |
|---|---|---|
| φd | Eq. 6 | Phase shift between input current and switch voltage |
| C_D | Eq. 3 | Shunt capacitance across the diode |
| Ri | Eq. 5 | Effective input resistance |
| Ci | Eq. 4 | Effective input capacitance |
| C₂ | Eq. 7 | Series resonant capacitor on the secondary |
| I₂ | Eq. 8 | Secondary RMS current |
| Vind | Eq. 10 | Induced voltage at resonance |
| VDmax | Eq. 22 | Maximum voltage across the diode |

### Inverter
All Class-DE inverter components:

| Output | Equation | Description |
|---|---|---|
| Req | Eq. 12 | Reflected resistance into primary |
| Xeq | Eq. 13 | Reflected reactance into primary |
| I₁ | Eq. 14 | Primary (TX coil) RMS current |
| Rout | Eq. 17 | Optimal load resistance |
| Xp / Cp | Eq. 18 | Impedance transform reactance / equivalent capacitor |
| Xout | Eq. 16 | Output reactance |
| Q | Eq. 19 | Loaded quality factor |
| C₀ | Eq. 20 | Primary series resonant capacitor |
| CS1 = CS2 | Eq. 21 | Switch shunt capacitors |
| fc | — | LPF cutoff frequency `1/(2π√(Lf·Cf))` |

### Schematic
Live SVG rendering of the five equivalent-circuit diagrams (a)–(e) from the paper, with all computed component values annotated directly on the schematic. Updates automatically after each calculation.

---

## Coil Model Notes

| Quantity | Method | Notes |
|---|---|---|
| Self-inductance L | Nagaoka coefficient | Accurate for single-layer solenoids; uses complete elliptic integrals |
| AC winding ESR | Dowell's equation | Single-layer approximation; accounts for skin effect via equivalent foil thickness |
| Coupling coefficient k | Neumann's formula | Thin-ring approximation — underestimates k for helical coils. Use override for measured values |

The paper's design example (coil diameter 155 mm, 10 turns, 1 mm wire, 10 mm height, 100 mm separation at 1 MHz) produces:

```
L₁ = L₂ = 35.35 µH     (paper: 35.4 µH)
RL₁ = RL₂ = 1.43 Ω     (paper: 1.36 Ω)
k (Neumann) = 0.023     (paper: 0.0725 — use override)
```

With k overridden to 0.0725 all Table I values reproduce to within 1–2%.

---

## Design Equations Reference

| Eq. | Quantity | Formula summary |
|---|---|---|
| 3 | CD | Shunt cap from Dd and RL |
| 4 | Ci | Rectifier input capacitance |
| 5 | Ri | `2·RL·sin²φd` |
| 6 | φd | `atan((1−cos2πDd) / (2π(1−Dd)+sin2πDd))` |
| 7 | C2 | Resonates L2 with Ci |
| 8 | I2 | `Io / (√2·sinφd)` |
| 10 | Vind | `I2·(RL2+Ri)` at resonance |
| 12 | Req | Primary reflected resistance |
| 13 | Xeq | Primary reflected reactance |
| 14 | I1 | `Vind / (ω·k·√(L1·L2))` |
| 17 | Rout | `VDD² / (2π²·Req·I1²)` |
| 18 | Xp | Quadratic solve from Eq. 15 |
| 16 | Xout | Output reactance via Xp, Xeq, Req |
| 19 | Q | `Xout / Rout` |
| 20 | C0 | `1 / (ω·Rout·(Q−π/2))` |
| 21 | CS1=CS2 | `1 / (2π·ω·Rout)` |
| 22 | VDmax | Maximum diode voltage |

---

## Reference

T. Nagashima, X. Wei, H. Sekiya,
*"Analytical Design Procedure for Resonant Inductively Coupled Wireless Power Transfer System With Class-DE Inverter and Class-E Rectifier"*,
Proceedings of the IEEE IECON 2014, pp. 611–616.