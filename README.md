# 🔬 Hall Effect Measurement Studio (Single & Batch Analysis)

**Author:** Trung Pham  
**Laboratory:** SALD Laboratory (Spatial Atomic Layer Deposition Laboratory)  
**Institution:** Phenikaa University  
**License:** MIT  

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6%20%7C%20PyQtGraph-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/)

A high-performance, publication-grade desktop scientific application for real-time Hall effect measurement extraction, dynamic baseline drift subtraction, van der Pauw sheet resistance solving, and automated temperature-dependent electronic transport analysis.

---

## 🌟 Key Features

- **60+ FPS Interactive Plotting:** Hardware-accelerated Qt/OpenGL canvas with on-screen draggable boundary and pulse plateau regions with zero latency.
- **Dual Visual Modes:**
  - ☀️ **Light Lab Mode:** Crisp Nature/Science journal aesthetic with publication-ready styling.
  - 🌙 **Dark Cryo Mode:** Deep cryostat palette (`#0b0f19`) with high-contrast electric cyan active traces (`#38bdf8`) and coral red step indicators.
  - Seamless luxury slider switch between Sun and Moon modes.
- **1-Click Publication Figure Copy:** Instantly copy 300 DPI publication plots to the clipboard for direct pasting into PowerPoint, Word, or LaTeX documents.
- **Real-Time Crosshairs & Tracking:** Live readout (`t = XX.XX s | V = X.XXXX mV`) tracking the cursor over the plot canvas.
- **Dual Studio Architecture:**
  - **Tab 1: Single Calculation Studio:** Interactive manual inspection, spike removal, Savitzky-Golay filtering, baseline flattening, and session logging.
  - **Tab 2: Batch Calculation Studio:** Multi-file queue for temperature-dependent series (e.g. 10 K to 300 K), automatic van der Pauw matching ($R_h$ & $R_v$), progress tracking, and multi-parameter temperature dependence plots ($T$ vs $\mu$, $n$, $n_s$, $\rho$, $V_H$).
- **Integrated Numerical van der Pauw Solver:** High-precision root finding (Brent's method) for the transcendental van der Pauw equation:
  $$\exp\left(-\frac{\pi R_h}{R_s}\right) + \exp\left(-\frac{\pi R_v}{R_s}\right) = 1$$
- **Contact Asymmetry Cancellation:** Field-reversal subtraction eliminating Ohmic misalignment offset voltages ($V_{\text{offset}}$) and thermal EMF:
  $$V_{\text{H}} = \frac{\Delta V(+B) - \Delta V(-B)}{2}$$

---

## 📐 Physical Parameter Extraction Reference

| Physical Quantity | Formula | Common Units |
| :--- | :--- | :--- |
| **Sheet Hall Coefficient ($R_{\text{Hs}}$)** | $R_{\text{Hs}} = \frac{V_{\text{H}}}{I \cdot B}$ | $\Omega / \text{T}$ or $\text{m}^2/\text{C}$ |
| **Carrier Type** | $R_{\text{Hs}} < 0 \implies \text{n-type}$, $R_{\text{Hs}} > 0 \implies \text{p-type}$ | Electrons / Holes |
| **Sheet Carrier Density ($n_s$)** | $n_s = \frac{\|I \cdot B\|}{q \cdot \|V_{\text{H}}\|} = \frac{1}{q \cdot \|R_{\text{Hs}}\|}$ | $\text{cm}^{-2}$ |
| **Bulk Carrier Density ($n$)** | $n = \frac{n_s}{d}$ | $\text{cm}^{-3}$ |
| **Bulk Hall Coefficient ($R_{\text{H}}$)** | $R_{\text{H}} = R_{\text{Hs}} \cdot d$ | $\text{cm}^3/\text{C}$ |
| **Hall Mobility ($\mu$)** | $\mu = \frac{\|R_{\text{Hs}}\|}{R_s} \times 10^4 = \frac{1}{q \cdot n_s \cdot R_s}$ | $\text{cm}^2/(\text{V}\cdot\text{s})$ |
| **Bulk Resistivity ($\rho$)** | $\rho = R_s \cdot d$ | $\Omega\cdot\text{cm}$ |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or later
- PyQt6, pyqtgraph, pandas, numpy, scipy, openpyxl

```bash
pip install pyqt6 pyqtgraph pandas numpy scipy openpyxl
```

### Running the Application

```bash
# Launch Native Desktop Studio
python desktop_app.py

# Or double click on Windows
run_desktop.bat
```

---

## 🏛️ Citation & Attribution

If you use this software in your experimental research or publications, please cite:

```bibtex
@software{hall_effect_studio_2026,
  author = {Trung Pham},
  title = {Hall Effect Measurement Studio: High-Performance Transport Analysis},
  institution = {SALD Laboratory, Phenikaa University},
  year = {2026},
  url = {https://github.com/LuckyVNN/Hall-effect-Analyst}
}
```

**Laboratory Contact:**  
SALD Laboratory — Spatial Atomic Layer Deposition  
Phenikaa University, Hanoi, Vietnam
