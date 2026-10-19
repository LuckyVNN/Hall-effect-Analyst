"""
desktop_app.py - High-Performance Native Desktop Studio for Hall Effect Analysis.
Built with PyQt6 and PyQtGraph for 60+ FPS zero-latency plotting and direct
on-screen draggable region selection.

Elevation Features:
  - Tab 1: Single Calculation Studio (interactive on-plot draggable regions, live updates).
  - Tab 2: Batch Calculation Studio (multi-file processing, auto-parsing filenames,
    matching against van der Pauw Rh & Rv CSV/Excel file, temperature-dependence plots).
  - Elevated Log & Export View:
    * Select and delete single or multiple rows (misclick correction).
    * Column selector checkboard to customize exported parameters.
    * Direct Excel (.xlsx) and CSV export.
  - Complete 4-sided bounding boxes on all plots with external ribbon legends.
  - 2-Tab Info & Theory Reference dialog with complete formulas.
"""

import sys
import os
import glob
import re
import numpy as np
import pandas as pd
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

import hall_core

# Configure pyqtgraph for clean modern scientific plotting
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)

LIGHT_STYLE = """
QMainWindow {
    background-color: #f8fafc;
}
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    color: #0f172a;
}
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background: #ffffff;
    border-radius: 6px;
}
QTabBar::tab {
    font-size: 13px;
    font-weight: 600;
    padding: 8px 24px;
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #2563eb;
    color: #ffffff;
    border-color: #2563eb;
}
QGroupBox {
    font-size: 12px;
    font-weight: bold;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 10px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    background-color: #ffffff;
    color: #0f172a;
}
QScrollArea {
    border: none;
    background: transparent;
}
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #f1f5f9;
    selection-background-color: #e0e7ff;
    selection-color: #1e1b4b;
    font-size: 12px;
}
QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    font-weight: 600;
    font-size: 11px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    padding: 6px 8px;
}
QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 4px 8px;
    background: #ffffff;
    color: #0f172a;
    font-size: 12px;
}
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {
    border: 1.5px solid #2563eb;
}
QSplitter::handle {
    background-color: #cbd5e1;
    width: 5px;
    border-radius: 2px;
    margin: 1px;
}
QSplitter::handle:hover {
    background-color: #2563eb;
}
QProgressBar {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    text-align: center;
    background-color: #f1f5f9;
    font-weight: 600;
    font-size: 11px;
    color: #0f172a;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 5px;
}
QFrame#legend_bar {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
}
"""

DARK_STYLE = """
QMainWindow {
    background-color: #0b0f19;
}
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    color: #f1f5f9;
}
QTabWidget::pane {
    border: 1px solid #1e293b;
    background: #0f172a;
    border-radius: 6px;
}
QTabBar::tab {
    font-size: 13px;
    font-weight: 600;
    padding: 8px 24px;
    background: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #0284c7;
    color: #ffffff;
    border-color: #0284c7;
}
QGroupBox {
    font-size: 12px;
    font-weight: bold;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 10px;
    background-color: #131b2e;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    background-color: #131b2e;
    color: #38bdf8;
}
QScrollArea {
    border: none;
    background: transparent;
}
QTableWidget {
    background-color: #131b2e;
    border: 1px solid #334155;
    border-radius: 6px;
    gridline-color: #1e293b;
    selection-background-color: #0369a1;
    selection-color: #ffffff;
    color: #f1f5f9;
    font-size: 12px;
}
QHeaderView::section {
    background-color: #0f172a;
    color: #94a3b8;
    font-weight: 600;
    font-size: 11px;
    border: none;
    border-bottom: 2px solid #334155;
    padding: 6px 8px;
}
QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 4px 8px;
    background: #1e293b;
    color: #f1f5f9;
    font-size: 12px;
}
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {
    border: 1.5px solid #38bdf8;
}
QSplitter::handle {
    background-color: #334155;
    width: 5px;
    border-radius: 2px;
    margin: 1px;
}
QSplitter::handle:hover {
    background-color: #38bdf8;
}
QProgressBar {
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    background-color: #1e293b;
    font-weight: 600;
    font-size: 11px;
    color: #f1f5f9;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 5px;
}
QFrame#legend_bar {
    background-color: #131b2e;
    border: 1px solid #334155;
    border-radius: 6px;
}
"""

class ColumnSelectorDialog(QtWidgets.QDialog):
    """Checkboard dialog allowing users to choose exactly which columns to export."""
    def __init__(self, available_columns, selected_columns=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Parameters / Columns to Export")
        self.resize(380, 480)
        self.available_columns = available_columns
        self.selected_columns = set(selected_columns if selected_columns else available_columns)
        self.checkboxes = {}

        layout = QtWidgets.QVBoxLayout(self)

        lbl = QtWidgets.QLabel("Select which parameters to include in the exported CSV/Excel:")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(lbl)

        # Quick select buttons
        h_btn = QtWidgets.QHBoxLayout()
        btn_all = QtWidgets.QPushButton("Select All")
        btn_all.clicked.connect(self.select_all)
        btn_none = QtWidgets.QPushButton("Deselect All")
        btn_none.clicked.connect(self.deselect_all)
        h_btn.addWidget(btn_all)
        h_btn.addWidget(btn_none)
        layout.addLayout(h_btn)

        # Scroll area with checkboxes
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QtWidgets.QWidget()
        w_layout = QtWidgets.QVBoxLayout(widget)
        w_layout.setSpacing(6)

        for col in self.available_columns:
            chk = QtWidgets.QCheckBox(col)
            chk.setChecked(col in self.selected_columns)
            self.checkboxes[col] = chk
            w_layout.addWidget(chk)

        w_layout.addStretch()
        scroll.setWidget(widget)
        layout.addWidget(scroll)

        # Bottom buttons
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def select_all(self):
        for chk in self.checkboxes.values():
            chk.setChecked(True)

    def deselect_all(self):
        for chk in self.checkboxes.values():
            chk.setChecked(False)

    def get_selected(self):
        return [col for col, chk in self.checkboxes.items() if chk.isChecked()]


class HallDesktopApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hall Effect Measurement Studio (Single & Batch Analysis)")
        self.resize(1380, 880)

        # Single Studio State
        self.raw_t_full = None
        self.raw_v_full = None
        self.t_sec = None
        self.v_active = None
        self.active_filename = "None"
        self.measurement_log = []
        self.selected_export_cols = None

        # Batch Studio State
        self.batch_files_data = []  # list of dicts: {'path', 'filename', 'meta', 'status', 'regions', 'result'}
        self.vdp_df = None
        self.vdp_filepath = None
        self.batch_results = []     # list of dicts: computed physical quantities
        self.batch_current_idx = -1
        self.b_raw_t = None
        self.b_raw_v = None
        self.b_t_sec = None
        self.b_v_active = None
        self.b_active_meta = {}
        self.b_active_rh = 250.0
        self.b_active_rv = 250.0
        self.b_active_rs = 1133.09
        self.b_active_vdp_match = "Fallback"
        self.b_latest_res = None
        self.b_latest_v_hall = 0.0
        self.b_latest_phys = None

        # UI Polish & Theme State
        self.is_dark_theme = False
        self.all_metric_cards = []

        # Build UI
        self.init_ui()

        # Load first available CSV into Single Studio if present
        local_csvs = glob.glob(os.path.join(os.getcwd(), "*.csv"))
        if local_csvs and self.combo_files.count() > 0:
            self.load_file(self.combo_files.itemData(0))

    def init_ui(self):
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        root_layout = QtWidgets.QVBoxLayout(main_widget)
        root_layout.setContentsMargins(8, 6, 8, 8)
        root_layout.setSpacing(6)

        # Top Header Ribbon with Branding & Live Theme Switcher
        h_top = QtWidgets.QHBoxLayout()
        h_top.setContentsMargins(4, 2, 4, 2)

        lbl_app_logo = QtWidgets.QLabel("🔬 <b>Hall Effect Measurement Studio</b> <span style='font-size: 11px; color: #64748b;'>| Research & Batch Edition</span>")
        lbl_app_logo.setStyleSheet("font-size: 14px;")
        h_top.addWidget(lbl_app_logo)

        h_top.addStretch()

        self.btn_theme_toggle = QtWidgets.QPushButton("🌙 Dark Cryo Mode")
        self.btn_theme_toggle.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: 600;
                padding: 5px 14px;
                border-radius: 5px;
                border: 1px solid #cbd5e1;
                background: #f1f5f9;
                color: #1e293b;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        h_top.addWidget(self.btn_theme_toggle)

        btn_top_info = QtWidgets.QPushButton("ℹ️ Physical Reference")
        btn_top_info.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: 600;
                padding: 5px 12px;
                border-radius: 5px;
                border: 1px solid #cbd5e1;
                background: #f1f5f9;
                color: #1e293b;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        btn_top_info.clicked.connect(self.open_info_dialog)
        h_top.addWidget(btn_top_info)

        root_layout.addLayout(h_top)

        # Main Top Tabs: Single Studio vs Batch Processing
        self.main_tabs = QtWidgets.QTabWidget()

        # Tab 1: Single Calculation Studio
        tab_single = QtWidgets.QWidget()
        self.init_single_studio(tab_single)
        self.main_tabs.addTab(tab_single, "🔬 Single Calculation Studio")

        # Tab 2: Batch Calculation Studio
        tab_batch = QtWidgets.QWidget()
        self.init_batch_studio(tab_batch)
        self.main_tabs.addTab(tab_batch, "⚡ Batch Calculation Studio")

        root_layout.addWidget(self.main_tabs)

        # Initialize Default Theme
        self.apply_theme(False)

    # =========================================================================
    # TAB 1: SINGLE CALCULATION STUDIO
    # =========================================================================
    def init_single_studio(self, parent_widget):
        main_layout = QtWidgets.QVBoxLayout(parent_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)

        self.single_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # ----------------- LEFT CONTROL PANEL -----------------
        left_scroll = QtWidgets.QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(320)
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setSpacing(10)

        # 1. File Selection Group
        grp_file = QtWidgets.QGroupBox("1. Data File")
        f_layout = QtWidgets.QVBoxLayout(grp_file)

        h_file = QtWidgets.QHBoxLayout()
        self.combo_files = QtWidgets.QComboBox()
        h_file.addWidget(self.combo_files)

        btn_browse = QtWidgets.QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_file)
        h_file.addWidget(btn_browse)
        f_layout.addLayout(h_file)

        # Spike exclusion
        h_spike = QtWidgets.QHBoxLayout()
        h_spike.addWidget(QtWidgets.QLabel("Exclude Initial Points:"))
        self.spin_spike = QtWidgets.QSpinBox()
        self.spin_spike.setRange(0, 500)
        self.spin_spike.setValue(10)
        self.spin_spike.valueChanged.connect(self.update_data_pipeline)
        h_spike.addWidget(self.spin_spike)
        f_layout.addLayout(h_spike)

        left_layout.addWidget(grp_file)

        # 2. Experimental Parameters Group
        grp_params = QtWidgets.QGroupBox("2. Experimental Parameters")
        p_layout = QtWidgets.QFormLayout(grp_params)

        self.spin_b = QtWidgets.QDoubleSpinBox()
        self.spin_b.setRange(0.0001, 100.0)
        self.spin_b.setDecimals(4)
        self.spin_b.setValue(0.4264)
        self.spin_b.setSingleStep(0.01)
        self.spin_b.setSuffix(" T")
        self.spin_b.valueChanged.connect(self.recalculate_all)
        p_layout.addRow("Magnetic Field (B):", self.spin_b)

        h_curr = QtWidgets.QHBoxLayout()
        self.spin_curr = QtWidgets.QDoubleSpinBox()
        self.spin_curr.setRange(0.001, 10000.0)
        self.spin_curr.setDecimals(2)
        self.spin_curr.setValue(100.0)
        self.spin_curr.valueChanged.connect(self.recalculate_all)
        self.combo_curr_unit = QtWidgets.QComboBox()
        self.combo_curr_unit.addItems(["µA", "mA", "A"])
        self.combo_curr_unit.currentIndexChanged.connect(self.recalculate_all)
        h_curr.addWidget(self.spin_curr)
        h_curr.addWidget(self.combo_curr_unit)
        p_layout.addRow("Excitation Current (I):", h_curr)

        h_thick = QtWidgets.QHBoxLayout()
        self.spin_thick = QtWidgets.QDoubleSpinBox()
        self.spin_thick.setRange(0.1, 100000.0)
        self.spin_thick.setDecimals(1)
        self.spin_thick.setValue(20.0)
        self.spin_thick.valueChanged.connect(self.recalculate_all)
        self.combo_thick_unit = QtWidgets.QComboBox()
        self.combo_thick_unit.addItems(["nm", "µm", "mm", "cm"])
        self.combo_thick_unit.currentIndexChanged.connect(self.recalculate_all)
        h_thick.addWidget(self.spin_thick)
        h_thick.addWidget(self.combo_thick_unit)
        p_layout.addRow("Sample Thickness (d):", h_thick)

        left_layout.addWidget(grp_params)

        # 3. van der Pauw Sheet Resistance Group
        grp_vdp = QtWidgets.QGroupBox("3. Sheet Resistance (van der Pauw)")
        vdp_layout = QtWidgets.QFormLayout(grp_vdp)

        self.spin_rh = QtWidgets.QDoubleSpinBox()
        self.spin_rh.setRange(0.01, 1e7)
        self.spin_rh.setDecimals(2)
        self.spin_rh.setValue(250.0)
        self.spin_rh.setSuffix(" Ω")
        self.spin_rh.valueChanged.connect(self.recalculate_all)
        vdp_layout.addRow("R horizontal (Rh):", self.spin_rh)

        self.spin_rv = QtWidgets.QDoubleSpinBox()
        self.spin_rv.setRange(0.01, 1e7)
        self.spin_rv.setDecimals(2)
        self.spin_rv.setValue(250.0)
        self.spin_rv.setSuffix(" Ω")
        self.spin_rv.valueChanged.connect(self.recalculate_all)
        vdp_layout.addRow("R vertical (Rv):", self.spin_rv)

        self.lbl_solved_rs = QtWidgets.QLabel("Rs: 1133.09 Ω/□")
        self.lbl_solved_rs.setStyleSheet("font-weight: bold; color: #084298;")
        vdp_layout.addRow("Solved Rs:", self.lbl_solved_rs)

        self.lbl_vdp_ratio = QtWidgets.QLabel("Symmetry: 1.00")
        vdp_layout.addRow("Rh / Rv Ratio:", self.lbl_vdp_ratio)

        left_layout.addWidget(grp_vdp)

        # 4. Signal Preprocessing Group
        grp_prep = QtWidgets.QGroupBox("4. Signal Processing")
        prep_layout = QtWidgets.QVBoxLayout(grp_prep)

        self.chk_denoise = QtWidgets.QCheckBox("Enable Savitzky-Golay Filter")
        self.chk_denoise.setChecked(True)
        self.chk_denoise.toggled.connect(self.update_data_pipeline)
        prep_layout.addWidget(self.chk_denoise)

        h_win = QtWidgets.QHBoxLayout()
        h_win.addWidget(QtWidgets.QLabel("Filter Window (pts):"))
        self.spin_denoise_win = QtWidgets.QSpinBox()
        self.spin_denoise_win.setRange(5, 51)
        self.spin_denoise_win.setSingleStep(2)
        self.spin_denoise_win.setValue(15)
        self.spin_denoise_win.valueChanged.connect(self.update_data_pipeline)
        h_win.addWidget(self.spin_denoise_win)
        prep_layout.addLayout(h_win)

        self.chk_flatten = QtWidgets.QCheckBox("Flatten Baseline (Horizontal at 0V)")
        self.chk_flatten.setChecked(False)
        self.chk_flatten.toggled.connect(self.recalculate_all)
        prep_layout.addWidget(self.chk_flatten)

        left_layout.addWidget(grp_prep)

        # 5. Quick Pulse Preset Jump
        grp_preset = QtWidgets.QGroupBox("5. Pulse Presets")
        pr_layout = QtWidgets.QHBoxLayout(grp_preset)
        btn_p1 = QtWidgets.QPushButton("Pulse 1 (+B)")
        btn_p1.clicked.connect(lambda: self.apply_preset(10, 20, 35, 50, 65, 75))
        btn_p2 = QtWidgets.QPushButton("Pulse 2 (-B)")
        btn_p2.clicked.connect(lambda: self.apply_preset(65, 75, 90, 110, 125, 135))
        btn_p3 = QtWidgets.QPushButton("Pulse 3 (+B)")
        btn_p3.clicked.connect(lambda: self.apply_preset(125, 135, 150, 170, 185, 195))
        pr_layout.addWidget(btn_p1)
        pr_layout.addWidget(btn_p2)
        pr_layout.addWidget(btn_p3)
        left_layout.addWidget(grp_preset)

        left_layout.addStretch()
        left_scroll.setWidget(left_widget)
        self.single_splitter.addWidget(left_scroll)

        # ----------------- RIGHT PLOT & METRICS AREA -----------------
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        # Top instruction banner
        banner = QtWidgets.QLabel("💡 <b>Direct On-Screen Dragging:</b> Grab the border lines to resize or click & drag inside any shaded zone to move it. Live 60 FPS recalculation!")
        banner.setStyleSheet("background-color: #e8f4fd; color: #0c5460; padding: 6px 12px; border-radius: 5px; font-size: 12px;")
        right_layout.addWidget(banner)

        # Hardware-accelerated PlotWidget (60+ FPS)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('bottom', "Time", units='s')
        self.plot_widget.setLabel('left', "Voltage", units='mV')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Complete 4-sided bounding box (Upper and Right borderlines)
        self.plot_widget.showAxis('top')
        self.plot_widget.showAxis('right')
        axis_top = self.plot_widget.getAxis('top')
        axis_right = self.plot_widget.getAxis('right')
        axis_top.setStyle(showValues=False)
        axis_right.setStyle(showValues=False)
        axis_top.setPen(pg.mkPen('k', width=1.5))
        axis_right.setPen(pg.mkPen('k', width=1.5))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen('k', width=1.5))
        self.plot_widget.getAxis('left').setPen(pg.mkPen('k', width=1.5))

        # Real-time mouse coordinate tracking
        self.plot_widget.scene().sigMouseMoved.connect(self.on_single_plot_mouse_moved)

        # Curves
        self.curve_raw = self.plot_widget.plot(name="Raw Voltage", pen=pg.mkPen(color=(190, 190, 190, 140), width=1))
        self.curve_active = self.plot_widget.plot(name="Measured Voltage", pen=pg.mkPen(color='#1f77b4', width=2))
        self.curve_baseline = self.plot_widget.plot(name="Fitted Baseline Drift", pen=pg.mkPen(color='#e377c2', width=2.5, style=QtCore.Qt.PenStyle.DashLine))
        self.curve_delta = self.plot_widget.plot(name="ΔV Step (V_Hall)", pen=pg.mkPen(color='r', width=3), symbol='o', symbolSize=8, symbolBrush='r')

        # DRAGGABLE REGIONS (LinearRegionItem)
        self.region_b1 = pg.LinearRegionItem(values=[10.0, 20.0], brush=pg.mkBrush(44, 160, 44, 45), pen=pg.mkPen(44, 160, 44, 180, width=1.5))
        self.region_b1.sigRegionChanged.connect(self.on_region_dragged)
        self.plot_widget.addItem(self.region_b1)

        self.region_pulse = pg.LinearRegionItem(values=[35.0, 50.0], brush=pg.mkBrush(255, 127, 14, 60), pen=pg.mkPen(255, 127, 14, 220, width=2))
        self.region_pulse.sigRegionChanged.connect(self.on_region_dragged)
        self.plot_widget.addItem(self.region_pulse)

        self.region_b2 = pg.LinearRegionItem(values=[65.0, 75.0], brush=pg.mkBrush(44, 160, 44, 45), pen=pg.mkPen(44, 160, 44, 180, width=1.5))
        self.region_b2.sigRegionChanged.connect(self.on_region_dragged)
        self.plot_widget.addItem(self.region_b2)

        # External Ribbon Legend Bar (with 1-click copy & coordinate tracking)
        right_layout.addWidget(self.create_legend_bar(self.plot_widget, is_batch=False))
        right_layout.addWidget(self.plot_widget, stretch=5)

        # RESULTS DASHBOARD CARDS
        res_group = QtWidgets.QGroupBox("Live Physical Results (Updates Instantly on Drag)")
        res_layout = QtWidgets.QGridLayout(res_group)

        self.card_vh = self.create_metric_card("V_Hall (Step Height):", "-- mV", "-- µV")
        self.card_type = self.create_metric_card("Carrier Type:", "--", "Sign of RH")
        self.card_ns = self.create_metric_card("Sheet Density (ns):", "-- cm⁻²", "2D Density")
        self.card_n = self.create_metric_card("Bulk Density (n):", "-- cm⁻³", "3D Density")
        self.card_mu = self.create_metric_card("Hall Mobility (μ):", "-- cm²/V·s", "Transport Mobility")
        self.card_rho = self.create_metric_card("Resistivity (ρ):", "-- Ω·cm", "van der Pauw")

        res_layout.addWidget(self.card_vh["widget"], 0, 0)
        res_layout.addWidget(self.card_type["widget"], 0, 1)
        res_layout.addWidget(self.card_ns["widget"], 0, 2)
        res_layout.addWidget(self.card_n["widget"], 1, 0)
        res_layout.addWidget(self.card_mu["widget"], 1, 1)
        res_layout.addWidget(self.card_rho["widget"], 1, 2)

        right_layout.addWidget(res_group, stretch=2)

        # BOTTOM ACTION BAR (Save Run + Export + Info)
        h_bottom = QtWidgets.QHBoxLayout()
        btn_log_run = QtWidgets.QPushButton("💾 Log This Measurement to Summary")
        btn_log_run.setStyleSheet("font-size: 13px; font-weight: bold; background-color: #198754; color: white; padding: 8px 14px; border-radius: 5px;")
        btn_log_run.clicked.connect(self.log_current_run)
        h_bottom.addWidget(btn_log_run)

        btn_view_log = QtWidgets.QPushButton("📋 View / Export Session Table...")
        btn_view_log.setStyleSheet("font-size: 13px; font-weight: bold; background-color: #0d6efd; color: white; padding: 8px 14px; border-radius: 5px;")
        btn_view_log.clicked.connect(self.open_log_dialog)
        h_bottom.addWidget(btn_view_log)

        btn_info = QtWidgets.QPushButton("ℹ️ Info & Theory Reference")
        btn_info.setStyleSheet("font-size: 13px; font-weight: bold; background-color: #495057; color: white; padding: 8px 14px; border-radius: 5px;")
        btn_info.clicked.connect(self.open_info_dialog)
        h_bottom.addWidget(btn_info)

        right_layout.addLayout(h_bottom)
        self.single_splitter.addWidget(right_widget)
        self.single_splitter.setStretchFactor(0, 0)
        self.single_splitter.setStretchFactor(1, 1)
        self.single_splitter.setCollapsible(0, False)
        self.single_splitter.setCollapsible(1, False)
        self.single_splitter.setSizes([360, 1000])
        main_layout.addWidget(self.single_splitter)

        # Safely populate file combo now that all widgets exist
        self.combo_files.blockSignals(True)
        local_csvs = glob.glob(os.path.join(os.getcwd(), "*.csv"))
        for f in local_csvs:
            self.combo_files.addItem(os.path.basename(f), f)
        self.combo_files.blockSignals(False)
        self.combo_files.currentIndexChanged.connect(self.on_combo_file_changed)

    # =========================================================================
    # TAB 2: BATCH CALCULATION STUDIO
    # =========================================================================
    def init_batch_studio(self, parent_widget):
        batch_layout = QtWidgets.QVBoxLayout(parent_widget)
        batch_layout.setContentsMargins(4, 4, 4, 4)

        self.batch_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # ----------------- BATCH LEFT PANEL -----------------
        b_left_scroll = QtWidgets.QScrollArea()
        b_left_scroll.setWidgetResizable(True)
        b_left_scroll.setMinimumWidth(360)
        b_left_widget = QtWidgets.QWidget()
        b_left_layout = QtWidgets.QVBoxLayout(b_left_widget)
        b_left_layout.setSpacing(10)

        # 1. Hall Files Group
        grp_b_files = QtWidgets.QGroupBox("1. Input Hall Measurement Files")
        bf_layout = QtWidgets.QVBoxLayout(grp_b_files)

        h_bf_btns = QtWidgets.QHBoxLayout()
        btn_add_files = QtWidgets.QPushButton("📁 Add Hall Files...")
        btn_add_files.clicked.connect(self.batch_add_files)
        btn_add_folder = QtWidgets.QPushButton("📂 Add Folder...")
        btn_add_folder.clicked.connect(self.batch_add_folder)
        btn_clear_bf = QtWidgets.QPushButton("🗑️ Clear")
        btn_clear_bf.clicked.connect(self.batch_clear_files)

        h_bf_btns.addWidget(btn_add_files)
        h_bf_btns.addWidget(btn_add_folder)
        h_bf_btns.addWidget(btn_clear_bf)
        bf_layout.addLayout(h_bf_btns)

        # Table of staged Hall files (with Status column and interactive click)
        self.table_b_files = QtWidgets.QTableWidget()
        self.table_b_files.setColumnCount(6)
        self.table_b_files.setHorizontalHeaderLabels(["#", "Status", "Sample", "Temp (K)", "Current", "File Name"])
        self.table_b_files.setColumnWidth(0, 32)
        self.table_b_files.setColumnWidth(1, 105)
        self.table_b_files.setColumnWidth(2, 75)
        self.table_b_files.setColumnWidth(3, 75)
        self.table_b_files.setColumnWidth(4, 75)
        self.table_b_files.horizontalHeader().setStretchLastSection(True)
        self.table_b_files.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_b_files.cellClicked.connect(self.on_batch_file_cell_clicked)
        self.table_b_files.setFixedHeight(180)
        bf_layout.addWidget(self.table_b_files)

        self.lbl_b_file_count = QtWidgets.QLabel("0 files staged.")
        self.lbl_b_file_count.setStyleSheet("color: #6c757d; font-size: 11px;")
        bf_layout.addWidget(self.lbl_b_file_count)

        b_left_layout.addWidget(grp_b_files)

        # 2. van der Pauw Reference File Group
        grp_vdp_ref = QtWidgets.QGroupBox("2. van der Pauw Reference Sheet")
        vdp_ref_layout = QtWidgets.QVBoxLayout(grp_vdp_ref)

        h_vdp_btn = QtWidgets.QHBoxLayout()
        btn_load_vdp = QtWidgets.QPushButton("📂 Load vdP Sheet (.csv / .xlsx)...")
        btn_load_vdp.clicked.connect(self.batch_load_vdp_file)
        h_vdp_btn.addWidget(btn_load_vdp)
        vdp_ref_layout.addLayout(h_vdp_btn)

        self.lbl_vdp_status = QtWidgets.QLabel("No vdP reference file loaded.")
        self.lbl_vdp_status.setStyleSheet("color: #dc3545; font-size: 11px; font-weight: bold;")
        vdp_ref_layout.addWidget(self.lbl_vdp_status)

        # Mini preview of vdP reference table
        self.table_vdp_preview = QtWidgets.QTableWidget()
        self.table_vdp_preview.setColumnCount(3)
        self.table_vdp_preview.setHorizontalHeaderLabels(["Sample", "Rh (Ω)", "Rv (Ω)"])
        self.table_vdp_preview.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table_vdp_preview.setFixedHeight(105)
        vdp_ref_layout.addWidget(self.table_vdp_preview)

        # Fallback vdP parameters
        f_fallback = QtWidgets.QFormLayout()
        self.spin_b_fallback_rh = QtWidgets.QDoubleSpinBox()
        self.spin_b_fallback_rh.setRange(0.01, 1e7)
        self.spin_b_fallback_rh.setValue(250.0)
        self.spin_b_fallback_rh.setSuffix(" Ω")
        self.spin_b_fallback_rh.valueChanged.connect(self.on_batch_param_changed)
        f_fallback.addRow("Fallback Rh (if missing):", self.spin_b_fallback_rh)

        self.spin_b_fallback_rv = QtWidgets.QDoubleSpinBox()
        self.spin_b_fallback_rv.setRange(0.01, 1e7)
        self.spin_b_fallback_rv.setValue(250.0)
        self.spin_b_fallback_rv.setSuffix(" Ω")
        self.spin_b_fallback_rv.valueChanged.connect(self.on_batch_param_changed)
        f_fallback.addRow("Fallback Rv (if missing):", self.spin_b_fallback_rv)
        vdp_ref_layout.addLayout(f_fallback)

        b_left_layout.addWidget(grp_vdp_ref)

        # 3. Measurement & Analysis Defaults
        grp_b_defs = QtWidgets.QGroupBox("3. Batch Measurement Defaults")
        bdef_layout = QtWidgets.QFormLayout(grp_b_defs)

        self.spin_b_field = QtWidgets.QDoubleSpinBox()
        self.spin_b_field.setRange(0.0001, 100.0)
        self.spin_b_field.setDecimals(4)
        self.spin_b_field.setValue(0.4264)
        self.spin_b_field.setSuffix(" T")
        self.spin_b_field.valueChanged.connect(self.on_batch_param_changed)
        bdef_layout.addRow("Magnetic Field (B):", self.spin_b_field)

        self.spin_b_thick = QtWidgets.QDoubleSpinBox()
        self.spin_b_thick.setRange(0.1, 10000.0)
        self.spin_b_thick.setValue(20.0)
        self.spin_b_thick.setSuffix(" nm")
        self.spin_b_thick.valueChanged.connect(self.on_batch_param_changed)
        bdef_layout.addRow("Sample Thickness:", self.spin_b_thick)

        self.spin_b_spike = QtWidgets.QSpinBox()
        self.spin_b_spike.setRange(0, 200)
        self.spin_b_spike.setValue(10)
        self.spin_b_spike.valueChanged.connect(self.on_batch_prep_changed)
        bdef_layout.addRow("Exclude Initial Points:", self.spin_b_spike)

        self.chk_b_denoise = QtWidgets.QCheckBox("Apply Savitzky-Golay (Window 15)")
        self.chk_b_denoise.setChecked(True)
        self.chk_b_denoise.toggled.connect(self.on_batch_prep_changed)
        bdef_layout.addRow("Denoising:", self.chk_b_denoise)

        b_left_layout.addWidget(grp_b_defs)

        # Action Buttons in Left Panel
        self.btn_b_start_manual = QtWidgets.QPushButton("🎯 Step-Through Manual Queue (File 1)")
        self.btn_b_start_manual.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                background-color: #0d6efd;
                color: white;
                padding: 9px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
        """)
        self.btn_b_start_manual.clicked.connect(self.start_batch_manual_queue)
        b_left_layout.addWidget(self.btn_b_start_manual)

        h_auto_btns = QtWidgets.QHBoxLayout()
        self.btn_run_batch = QtWidgets.QPushButton("⚡ Auto-Process All (Bulk)")
        self.btn_run_batch.setStyleSheet("background-color: #198754; color: white; font-weight: bold; padding: 7px 10px; border-radius: 5px;")
        self.btn_run_batch.clicked.connect(self.run_batch_processing)
        h_auto_btns.addWidget(self.btn_run_batch)

        self.btn_auto_remaining = QtWidgets.QPushButton("⚡ Auto Pending")
        self.btn_auto_remaining.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; padding: 7px 10px; border-radius: 5px;")
        self.btn_auto_remaining.clicked.connect(self.auto_process_remaining_files)
        h_auto_btns.addWidget(self.btn_auto_remaining)
        b_left_layout.addLayout(h_auto_btns)

        b_left_layout.addStretch()
        b_left_scroll.setWidget(b_left_widget)
        self.batch_splitter.addWidget(b_left_scroll)

        # ----------------- BATCH RIGHT PANEL -----------------
        b_right_widget = QtWidgets.QWidget()
        b_right_layout = QtWidgets.QVBoxLayout(b_right_widget)
        b_right_layout.setContentsMargins(0, 0, 0, 0)
        b_right_layout.setSpacing(6)

        # Sub-tabs for Batch Studio:
        # 1. 🎯 Manual Extraction Studio (One-by-One Queue)
        # 2. 📋 Batch Results Table
        # 3. 📈 Temperature Dependence Plots
        self.b_sub_tabs = QtWidgets.QTabWidget()

        # =====================================================================
        # SUB-TAB 0: 🎯 MANUAL EXTRACTION STUDIO
        # =====================================================================
        sub_tab_manual = QtWidgets.QWidget()
        sm_layout = QtWidgets.QVBoxLayout(sub_tab_manual)
        sm_layout.setContentsMargins(2, 2, 2, 2)
        sm_layout.setSpacing(6)

        # Live Batch Extraction Progress Bar
        self.b_progress_bar = QtWidgets.QProgressBar()
        self.b_progress_bar.setRange(0, 1)
        self.b_progress_bar.setValue(0)
        self.b_progress_bar.setFormat("Batch Progress: 0 of 0 files completed (0%)")
        sm_layout.addWidget(self.b_progress_bar)

        # 1. Navigation & Quick Advance Header Bar
        h_nav = QtWidgets.QHBoxLayout()
        self.btn_b_prev = QtWidgets.QPushButton("◀ Prev File")
        self.btn_b_prev.clicked.connect(self.batch_manual_prev_file)
        self.btn_b_prev.setEnabled(False)
        h_nav.addWidget(self.btn_b_prev)

        self.btn_b_next = QtWidgets.QPushButton("Next File ▶")
        self.btn_b_next.clicked.connect(self.batch_manual_next_file)
        self.btn_b_next.setEnabled(False)
        h_nav.addWidget(self.btn_b_next)

        self.lbl_b_file_badge = QtWidgets.QLabel("No file loaded. Please add files on the left.")
        self.lbl_b_file_badge.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #0d6efd;
            background-color: #e7f1ff;
            padding: 6px 14px;
            border: 1px solid #b6d4fe;
            border-radius: 5px;
        """)
        h_nav.addWidget(self.lbl_b_file_badge, stretch=1)

        self.btn_b_save_next = QtWidgets.QPushButton("✅ Accept & Next File ▶ (Ctrl+Enter)")
        self.btn_b_save_next.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                background-color: #198754;
                color: white;
                padding: 8px 18px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #157347;
            }
        """)
        self.btn_b_save_next.setShortcut(QtGui.QKeySequence("Ctrl+Return"))
        self.btn_b_save_next.clicked.connect(self.batch_manual_save_and_next)
        h_nav.addWidget(self.btn_b_save_next)
        sm_layout.addLayout(h_nav)

        # 2. Experimental Metadata & Controls Sub-bar
        h_ctrls = QtWidgets.QHBoxLayout()
        self.lbl_b_meta_info = QtWidgets.QLabel("vdP: -- | Current: -- | Field: --")
        self.lbl_b_meta_info.setStyleSheet("font-size: 12px; color: #495057; padding: 2px 4px;")
        h_ctrls.addWidget(self.lbl_b_meta_info, stretch=1)

        lbl_jump = QtWidgets.QLabel("<b>Jump Preset:</b>")
        h_ctrls.addWidget(lbl_jump)
        btn_bp1 = QtWidgets.QPushButton("Pulse 1 (+B)")
        btn_bp1.clicked.connect(lambda: self.batch_apply_preset(10, 20, 35, 50, 65, 75))
        btn_bp2 = QtWidgets.QPushButton("Pulse 2 (-B)")
        btn_bp2.clicked.connect(lambda: self.batch_apply_preset(65, 75, 90, 110, 125, 135))
        btn_bp3 = QtWidgets.QPushButton("Pulse 3 (+B)")
        btn_bp3.clicked.connect(lambda: self.batch_apply_preset(125, 135, 150, 170, 185, 195))
        h_ctrls.addWidget(btn_bp1)
        h_ctrls.addWidget(btn_bp2)
        h_ctrls.addWidget(btn_bp3)

        self.combo_b_calc_mode = QtWidgets.QComboBox()
        self.combo_b_calc_mode.addItems([
            "Single Pulse (Current Region)",
            "Full 3-Pulse Sequence (+B / -B / +B)"
        ])
        self.combo_b_calc_mode.currentIndexChanged.connect(self.recalculate_batch_manual)
        h_ctrls.addWidget(self.combo_b_calc_mode)

        self.chk_b_flatten = QtWidgets.QCheckBox("Flatten Baseline")
        self.chk_b_flatten.setChecked(False)
        self.chk_b_flatten.toggled.connect(self.recalculate_batch_manual)
        h_ctrls.addWidget(self.chk_b_flatten)

        sm_layout.addLayout(h_ctrls)

        # 3. Interactive Plot Widget (60+ FPS)
        self.plot_b_manual = pg.PlotWidget()
        self.plot_b_manual.setLabel('bottom', "Time", units='s')
        self.plot_b_manual.setLabel('left', "Voltage", units='mV')
        self.plot_b_manual.showGrid(x=True, y=True, alpha=0.3)

        # Complete 4-sided bounding box
        self.plot_b_manual.showAxis('top')
        self.plot_b_manual.showAxis('right')
        axis_b_top = self.plot_b_manual.getAxis('top')
        axis_b_right = self.plot_b_manual.getAxis('right')
        axis_b_top.setStyle(showValues=False)
        axis_b_right.setStyle(showValues=False)
        axis_b_top.setPen(pg.mkPen('k', width=1.5))
        axis_b_right.setPen(pg.mkPen('k', width=1.5))
        self.plot_b_manual.getAxis('bottom').setPen(pg.mkPen('k', width=1.5))
        self.plot_b_manual.getAxis('left').setPen(pg.mkPen('k', width=1.5))

        # Real-time mouse coordinate tracking
        self.plot_b_manual.scene().sigMouseMoved.connect(self.on_batch_plot_mouse_moved)

        # Curves
        self.b_curve_raw = self.plot_b_manual.plot(name="Raw Voltage", pen=pg.mkPen(color=(190, 190, 190, 140), width=1))
        self.b_curve_active = self.plot_b_manual.plot(name="Measured Voltage", pen=pg.mkPen(color='#1f77b4', width=2))
        self.b_curve_baseline = self.plot_b_manual.plot(name="Fitted Drift Line", pen=pg.mkPen(color='#e377c2', width=2.5, style=QtCore.Qt.PenStyle.DashLine))
        self.b_curve_delta = self.plot_b_manual.plot(name="ΔV Step (V_Hall)", pen=pg.mkPen(color='r', width=3), symbol='o', symbolSize=8, symbolBrush='r')

        # Draggable Regions
        self.b_region_b1 = pg.LinearRegionItem(values=[10.0, 20.0], brush=pg.mkBrush(44, 160, 44, 45), pen=pg.mkPen(44, 160, 44, 180, width=1.5))
        self.b_region_b1.sigRegionChanged.connect(self.on_batch_manual_region_dragged)
        self.plot_b_manual.addItem(self.b_region_b1)

        self.b_region_pulse = pg.LinearRegionItem(values=[35.0, 50.0], brush=pg.mkBrush(255, 127, 14, 60), pen=pg.mkPen(255, 127, 14, 220, width=2))
        self.b_region_pulse.sigRegionChanged.connect(self.on_batch_manual_region_dragged)
        self.plot_b_manual.addItem(self.b_region_pulse)

        self.b_region_b2 = pg.LinearRegionItem(values=[65.0, 75.0], brush=pg.mkBrush(44, 160, 44, 45), pen=pg.mkPen(44, 160, 44, 180, width=1.5))
        self.b_region_b2.sigRegionChanged.connect(self.on_batch_manual_region_dragged)
        self.plot_b_manual.addItem(self.b_region_b2)

        # 4. External Ribbon Legend Bar (with 1-click copy & coordinate tracking)
        sm_layout.addWidget(self.create_legend_bar(self.plot_b_manual, is_batch=True))
        sm_layout.addWidget(self.plot_b_manual, stretch=5)

        # 5. Live Physical Results Cards
        b_res_group = QtWidgets.QGroupBox("Live Physical Results (Updates Instantly on Drag)")
        b_res_layout = QtWidgets.QGridLayout(b_res_group)

        self.b_card_vh = self.create_metric_card("V_Hall (Step Height):", "-- mV", "-- µV")
        self.b_card_type = self.create_metric_card("Carrier Type:", "--", "Sign of RH")
        self.b_card_ns = self.create_metric_card("Sheet Density (ns):", "-- cm⁻²", "2D Density")
        self.b_card_n = self.create_metric_card("Bulk Density (n):", "-- cm⁻³", "3D Density")
        self.b_card_mu = self.create_metric_card("Hall Mobility (μ):", "-- cm²/V·s", "Transport Mobility")
        self.b_card_rho = self.create_metric_card("Resistivity (ρ):", "-- Ω·cm", "van der Pauw")

        b_res_layout.addWidget(self.b_card_vh["widget"], 0, 0)
        b_res_layout.addWidget(self.b_card_type["widget"], 0, 1)
        b_res_layout.addWidget(self.b_card_ns["widget"], 0, 2)
        b_res_layout.addWidget(self.b_card_n["widget"], 1, 0)
        b_res_layout.addWidget(self.b_card_mu["widget"], 1, 1)
        b_res_layout.addWidget(self.b_card_rho["widget"], 1, 2)

        sm_layout.addWidget(b_res_group, stretch=2)

        self.b_sub_tabs.addTab(sub_tab_manual, "🎯 Manual Extraction Studio")

        # =====================================================================
        # SUB-TAB 1: 📋 BATCH RESULTS TABLE
        # =====================================================================
        sub_tab_table = QtWidgets.QWidget()
        st_layout = QtWidgets.QVBoxLayout(sub_tab_table)

        self.table_b_results = QtWidgets.QTableWidget()
        self.table_b_results.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_b_results.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        st_layout.addWidget(self.table_b_results)

        # Table Action Bar
        h_tab_act = QtWidgets.QHBoxLayout()
        btn_del_b_row = QtWidgets.QPushButton("🗑️ Delete Selected Row(s)")
        btn_del_b_row.clicked.connect(self.delete_selected_batch_rows)
        h_tab_act.addWidget(btn_del_b_row)

        btn_b_col_filter = QtWidgets.QPushButton("☑️ Choose Columns to Export...")
        btn_b_col_filter.clicked.connect(self.open_batch_column_selector)
        h_tab_act.addWidget(btn_b_col_filter)

        btn_b_export_csv = QtWidgets.QPushButton("💾 Export Batch CSV...")
        btn_b_export_csv.clicked.connect(self.export_batch_csv)
        h_tab_act.addWidget(btn_b_export_csv)

        btn_b_export_excel = QtWidgets.QPushButton("💾 Export Batch Excel (.xlsx)...")
        btn_b_export_excel.clicked.connect(self.export_batch_excel)
        h_tab_act.addWidget(btn_b_export_excel)

        st_layout.addLayout(h_tab_act)
        self.b_sub_tabs.addTab(sub_tab_table, "📋 Batch Results Table")

        # =====================================================================
        # SUB-TAB 2: 📈 TEMPERATURE DEPENDENCE PLOTS
        # =====================================================================
        sub_tab_plots = QtWidgets.QWidget()
        sp_layout = QtWidgets.QVBoxLayout(sub_tab_plots)

        # Plot Controls Header
        h_plot_ctrl = QtWidgets.QHBoxLayout()
        h_plot_ctrl.addWidget(QtWidgets.QLabel("<b>Select Parameter vs Temperature (T):</b>"))
        self.combo_t_param = QtWidgets.QComboBox()
        self.combo_t_param.addItems([
            "Hall Mobility (μ) vs Temperature (T)",
            "Carrier Concentration (n) vs Temperature (T)",
            "Sheet Density (ns) vs Temperature (T)",
            "Bulk Resistivity (ρ) vs Temperature (T)",
            "Hall Voltage (V_H) vs Temperature (T)"
        ])
        self.combo_t_param.currentIndexChanged.connect(self.update_batch_plot)
        h_plot_ctrl.addWidget(self.combo_t_param)

        self.chk_log_y = QtWidgets.QCheckBox("Log Scale (Y-axis)")
        self.chk_log_y.toggled.connect(self.update_batch_plot)
        h_plot_ctrl.addWidget(self.chk_log_y)

        btn_copy_t = QtWidgets.QPushButton("📷 Copy Figure")
        btn_copy_t.setToolTip("Copy temperature-dependence plot to clipboard")
        btn_copy_t.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: 600;
                padding: 3px 10px;
                border-radius: 4px;
                border: 1px solid #cbd5e1;
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        btn_copy_t.clicked.connect(lambda: self.copy_plot_to_clipboard(self.plot_batch, btn_copy_t))
        h_plot_ctrl.addWidget(btn_copy_t)

        h_plot_ctrl.addStretch()
        sp_layout.addLayout(h_plot_ctrl)

        # Batch Plot Widget
        self.plot_batch = pg.PlotWidget()
        self.plot_batch.setLabel('bottom', "Temperature", units='K')
        self.plot_batch.setLabel('left', "Hall Mobility", units='cm²/V·s')
        self.plot_batch.showGrid(x=True, y=True, alpha=0.3)

        # 4-sided bounding box
        self.plot_batch.showAxis('top')
        self.plot_batch.showAxis('right')
        self.plot_batch.getAxis('top').setStyle(showValues=False)
        self.plot_batch.getAxis('right').setStyle(showValues=False)
        self.plot_batch.getAxis('top').setPen(pg.mkPen('k', width=1.5))
        self.plot_batch.getAxis('right').setPen(pg.mkPen('k', width=1.5))
        self.plot_batch.getAxis('bottom').setPen(pg.mkPen('k', width=1.5))
        self.plot_batch.getAxis('left').setPen(pg.mkPen('k', width=1.5))
        self.plot_batch.addLegend(offset=(10, 10))

        sp_layout.addWidget(self.plot_batch)
        self.b_sub_tabs.addTab(sub_tab_plots, "📈 Temperature Dependence Plots")

        b_right_layout.addWidget(self.b_sub_tabs)
        self.batch_splitter.addWidget(b_right_widget)
        self.batch_splitter.setStretchFactor(0, 0)
        self.batch_splitter.setStretchFactor(1, 1)
        self.batch_splitter.setCollapsible(0, False)
        self.batch_splitter.setCollapsible(1, False)
        self.batch_splitter.setSizes([430, 950])
        batch_layout.addWidget(self.batch_splitter)

    # =========================================================================
    # SINGLE STUDIO METHODS
    # =========================================================================
    def create_metric_card(self, title, val_main, val_sub):
        box = QtWidgets.QFrame()
        box.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-left: 4px solid #0d6efd; border-radius: 6px; padding: 6px;")
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(2)

        lbl_t = QtWidgets.QLabel(title)
        lbl_t.setStyleSheet("font-size: 11px; color: #6c757d; font-weight: 600;")
        lbl_m = QtWidgets.QLabel(val_main)
        lbl_m.setStyleSheet("font-family: 'Consolas', 'Segoe UI Mono', monospace; font-size: 16px; color: #212529; font-weight: bold;")
        lbl_s = QtWidgets.QLabel(val_sub)
        lbl_s.setStyleSheet("font-size: 11px; color: #495057;")

        layout.addWidget(lbl_t)
        layout.addWidget(lbl_m)
        layout.addWidget(lbl_s)
        card = {"widget": box, "title": lbl_t, "main": lbl_m, "sub": lbl_s}
        self.all_metric_cards.append(card)
        return card

    def create_legend_bar(self, plot_widget, is_batch=False):
        legend_bar = QtWidgets.QFrame()
        legend_bar.setObjectName("legend_bar")
        leg_layout = QtWidgets.QHBoxLayout(legend_bar)
        leg_layout.setContentsMargins(10, 4, 10, 4)
        leg_layout.setSpacing(12)

        def make_legend_item(color_code, label_text, is_dash=False, is_symbol=False, is_box=False):
            item = QtWidgets.QWidget()
            i_lay = QtWidgets.QHBoxLayout(item)
            i_lay.setContentsMargins(0, 0, 0, 0)
            i_lay.setSpacing(5)

            icon = QtWidgets.QLabel()
            if is_box:
                icon.setFixedSize(14, 10)
                icon.setStyleSheet(f"background-color: {color_code}; border: 1px solid rgba(0,0,0,0.3); border-radius: 2px;")
            elif is_dash:
                icon.setFixedSize(20, 10)
                icon.setText("╌╌")
                icon.setStyleSheet(f"color: {color_code}; font-weight: bold; font-size: 13px; line-height: 10px;")
            elif is_symbol:
                icon.setFixedSize(20, 10)
                icon.setText("━●━")
                icon.setStyleSheet(f"color: {color_code}; font-weight: bold; font-size: 10px;")
            else:
                icon.setFixedSize(18, 3)
                icon.setStyleSheet(f"background-color: {color_code};")

            lbl = QtWidgets.QLabel(label_text)
            lbl.setStyleSheet("font-size: 11px; font-weight: 600;")
            i_lay.addWidget(icon)
            i_lay.addWidget(lbl)
            return item

        leg_layout.addWidget(make_legend_item("#1f77b4", "Measured V"))
        leg_layout.addWidget(make_legend_item("#e377c2", "Fitted Drift Line", is_dash=True))
        leg_layout.addWidget(make_legend_item("#d62728", "ΔV Step (V_Hall)", is_symbol=True))
        leg_layout.addWidget(make_legend_item("rgba(44, 160, 44, 140)", "Base 1 & 2 (Drag to fit)", is_box=True))
        leg_layout.addWidget(make_legend_item("rgba(255, 127, 14, 170)", "Pulse Plateau (B ON)", is_box=True))
        leg_layout.addStretch()

        # Real-time coordinate tracker readout
        lbl_coord = QtWidgets.QLabel("📍 t = -- s | V = -- mV")
        lbl_coord.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; background: rgba(100, 116, 139, 0.12);")
        if is_batch:
            self.lbl_coord_batch = lbl_coord
        else:
            self.lbl_coord_single = lbl_coord
        leg_layout.addWidget(lbl_coord)

        # 1-Click Publication Figure Copy button
        btn_copy = QtWidgets.QPushButton("📷 Copy Figure")
        btn_copy.setToolTip("Copy publication-grade plot snapshot to clipboard for PowerPoint, Word, or LaTeX")
        btn_copy.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: 600;
                padding: 3px 10px;
                border-radius: 4px;
                border: 1px solid #cbd5e1;
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        btn_copy.clicked.connect(lambda: self.copy_plot_to_clipboard(plot_widget, btn_copy))
        leg_layout.addWidget(btn_copy)

        return legend_bar

    def copy_plot_to_clipboard(self, plot_widget, btn=None):
        try:
            pixmap = plot_widget.grab()
            QtWidgets.QApplication.clipboard().setPixmap(pixmap)
            if btn is not None:
                orig_text = btn.text()
                btn.setText("✅ Copied!")
                QtCore.QTimer.singleShot(1800, lambda: btn.setText(orig_text))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Clipboard Copy", f"Could not copy figure to clipboard:\n{e}")

    def on_single_plot_mouse_moved(self, pos):
        if hasattr(self, 'plot_widget') and hasattr(self, 'lbl_coord_single'):
            vb = self.plot_widget.plotItem.vb
            if vb.sceneBoundingRect().contains(pos):
                pt = vb.mapSceneToView(pos)
                self.lbl_coord_single.setText(f"📍 t = {pt.x():.2f} s | V = {pt.y():.4f} mV")

    def on_batch_plot_mouse_moved(self, pos):
        if hasattr(self, 'plot_b_manual') and hasattr(self, 'lbl_coord_batch'):
            vb = self.plot_b_manual.plotItem.vb
            if vb.sceneBoundingRect().contains(pos):
                pt = vb.mapSceneToView(pos)
                self.lbl_coord_batch.setText(f"📍 t = {pt.x():.2f} s | V = {pt.y():.4f} mV")

    def toggle_theme(self):
        self.apply_theme(not self.is_dark_theme)

    def apply_theme(self, is_dark):
        self.is_dark_theme = is_dark
        if is_dark:
            self.setStyleSheet(DARK_STYLE)
            self.btn_theme_toggle.setText("☀️ Light Lab Mode")
            self.btn_theme_toggle.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    font-weight: 600;
                    padding: 5px 14px;
                    border-radius: 5px;
                    border: 1px solid #334155;
                    background: #1e293b;
                    color: #f1f5f9;
                }
                QPushButton:hover {
                    background: #334155;
                }
            """)
            bg_color = '#0b0f19'
            axis_pen = pg.mkPen('#94a3b8', width=1.5)
            text_pen = pg.mkPen('#94a3b8')
            curve_raw_pen = pg.mkPen(color=(100, 116, 139, 140), width=1)
            curve_active_pen = pg.mkPen(color='#38bdf8', width=2)
            curve_baseline_pen = pg.mkPen(color='#f472b6', width=2.5, style=QtCore.Qt.PenStyle.DashLine)
            curve_delta_pen = pg.mkPen(color='#f87171', width=3)
            delta_brush = pg.mkBrush('#f87171')
            reg_b_brush = pg.mkBrush(52, 211, 153, 50)
            reg_b_pen = pg.mkPen(52, 211, 153, 190, width=1.5)
            reg_p_brush = pg.mkBrush(251, 146, 60, 65)
            reg_p_pen = pg.mkPen(251, 146, 60, 220, width=2)
        else:
            self.setStyleSheet(LIGHT_STYLE)
            self.btn_theme_toggle.setText("🌙 Dark Cryo Mode")
            self.btn_theme_toggle.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    font-weight: 600;
                    padding: 5px 14px;
                    border-radius: 5px;
                    border: 1px solid #cbd5e1;
                    background: #f1f5f9;
                    color: #1e293b;
                }
                QPushButton:hover {
                    background: #e2e8f0;
                }
            """)
            bg_color = '#ffffff'
            axis_pen = pg.mkPen('#1e293b', width=1.5)
            text_pen = pg.mkPen('#1e293b')
            curve_raw_pen = pg.mkPen(color=(190, 190, 190, 140), width=1)
            curve_active_pen = pg.mkPen(color='#1f77b4', width=2)
            curve_baseline_pen = pg.mkPen(color='#e377c2', width=2.5, style=QtCore.Qt.PenStyle.DashLine)
            curve_delta_pen = pg.mkPen(color='#d62728', width=3)
            delta_brush = pg.mkBrush('#d62728')
            reg_b_brush = pg.mkBrush(44, 160, 44, 45)
            reg_b_pen = pg.mkPen(44, 160, 44, 180, width=1.5)
            reg_p_brush = pg.mkBrush(255, 127, 14, 60)
            reg_p_pen = pg.mkPen(255, 127, 14, 220, width=2)

        # Style all plot canvases and bounding boxes
        for p_attr in ['plot_widget', 'plot_b_manual', 'plot_batch']:
            if hasattr(self, p_attr):
                p = getattr(self, p_attr)
                p.setBackground(bg_color)
                for ax_name in ['left', 'bottom', 'top', 'right']:
                    ax = p.getAxis(ax_name)
                    ax.setPen(axis_pen)
                    ax.setTextPen(text_pen)

        # Update curves & regions on Single Studio
        if hasattr(self, 'curve_raw'):
            self.curve_raw.setPen(curve_raw_pen)
            self.curve_active.setPen(curve_active_pen)
            self.curve_baseline.setPen(curve_baseline_pen)
            self.curve_delta.setPen(curve_delta_pen)
            self.curve_delta.setSymbolBrush(delta_brush)
            self.curve_delta.setSymbolPen(axis_pen)
        def style_region(reg, brush, pen):
            reg.setBrush(brush)
            for line in reg.lines:
                line.setPen(pen)

        if hasattr(self, 'region_b1'):
            style_region(self.region_b1, reg_b_brush, reg_b_pen)
            style_region(self.region_pulse, reg_p_brush, reg_p_pen)
            style_region(self.region_b2, reg_b_brush, reg_b_pen)

        # Update curves & regions on Batch Manual Studio
        if hasattr(self, 'b_curve_raw'):
            self.b_curve_raw.setPen(curve_raw_pen)
            self.b_curve_active.setPen(curve_active_pen)
            self.b_curve_baseline.setPen(curve_baseline_pen)
            self.b_curve_delta.setPen(curve_delta_pen)
            self.b_curve_delta.setSymbolBrush(delta_brush)
            self.b_curve_delta.setSymbolPen(axis_pen)
        if hasattr(self, 'b_region_b1'):
            style_region(self.b_region_b1, reg_b_brush, reg_b_pen)
            style_region(self.b_region_pulse, reg_p_brush, reg_p_pen)
            style_region(self.b_region_b2, reg_b_brush, reg_b_pen)

        # Update metric cards
        for card in self.all_metric_cards:
            if is_dark:
                card["widget"].setStyleSheet(
                    "background-color: #131b2e; border: 1px solid #334155; border-left: 4px solid #0284c7; border-radius: 6px; padding: 6px;"
                )
                card["title"].setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 600;")
                card["main"].setStyleSheet("font-family: 'Consolas', 'Segoe UI Mono', monospace; font-size: 16px; color: #f8fafc; font-weight: bold;")
                card["sub"].setStyleSheet("font-size: 11px; color: #64748b;")
            else:
                card["widget"].setStyleSheet(
                    "background-color: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #2563eb; border-radius: 6px; padding: 6px;"
                )
                card["title"].setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600;")
                card["main"].setStyleSheet("font-family: 'Consolas', 'Segoe UI Mono', monospace; font-size: 16px; color: #0f172a; font-weight: bold;")
                card["sub"].setStyleSheet("font-size: 11px; color: #475569;")

        # Refresh temperature plot if batch results exist
        if hasattr(self, 'plot_batch') and hasattr(self, 'update_batch_plot'):
            self.update_batch_plot()

        # Re-trigger current calculation to apply specific colors like n-type/p-type pills
        if hasattr(self, 'recalculate_all') and self.t_sec is not None:
            self.recalculate_all()
        if hasattr(self, 'recalculate_batch_manual') and self.b_t_sec is not None:
            self.recalculate_batch_manual()
        if hasattr(self, 'refresh_batch_files_table'):
            self.refresh_batch_files_table()

    def browse_file(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Hall Measurement CSV", os.getcwd(), "CSV Files (*.csv *.txt)")
        if fname:
            idx = self.combo_files.findData(fname)
            if idx == -1:
                self.combo_files.addItem(os.path.basename(fname), fname)
                self.combo_files.setCurrentIndex(self.combo_files.count() - 1)
            else:
                self.combo_files.setCurrentIndex(idx)

    def on_combo_file_changed(self, idx):
        path = self.combo_files.itemData(idx)
        if path and os.path.exists(path):
            self.load_file(path)

    def load_file(self, filepath):
        try:
            self.raw_t_full, self.raw_v_full = hall_core.parse_hall_csv(filepath)
            self.active_filename = os.path.basename(filepath)

            # Parse metadata (Sample, current, temp)
            meta = hall_core.parse_filename_metadata(self.active_filename)
            if meta['current_uA'] is not None:
                self.spin_curr.setValue(meta['current_uA'])
                self.combo_curr_unit.setCurrentText("µA")

            self.update_data_pipeline()
            self.plot_widget.autoRange()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "File Error", f"Could not load file:\n{e}")

    def update_data_pipeline(self):
        if self.raw_t_full is None:
            return

        n_skip = self.spin_spike.value()
        if n_skip >= len(self.raw_t_full):
            n_skip = 0

        t_sliced = self.raw_t_full[n_skip:]
        v_sliced = self.raw_v_full[n_skip:]

        self.t_sec = t_sliced / 1000.0
        self.raw_t = t_sliced
        self.raw_v = v_sliced

        if self.chk_denoise.isChecked():
            win = self.spin_denoise_win.value()
            self.v_active = hall_core.apply_denoising(self.raw_v, window_length=win)
        else:
            self.v_active = self.raw_v.copy()

        self.recalculate_all()

    def apply_preset(self, b1_0, b1_1, p_0, p_1, b2_0, b2_1):
        self.region_b1.setRegion([b1_0, b1_1])
        self.region_pulse.setRegion([p_0, p_1])
        self.region_b2.setRegion([b2_0, b2_1])
        self.recalculate_all()

    def on_region_dragged(self):
        self.recalculate_all()

    def recalculate_all(self):
        if self.t_sec is None or len(self.t_sec) < 5:
            return

        b1_range = self.region_b1.getRegion()
        p_range = self.region_pulse.getRegion()
        b2_range = self.region_b2.getRegion()

        b1_ms = (b1_range[0] * 1000.0, b1_range[1] * 1000.0)
        p_ms = (p_range[0] * 1000.0, p_range[1] * 1000.0)
        b2_ms = (b2_range[0] * 1000.0, b2_range[1] * 1000.0)

        res = hall_core.calc_option_a_3zone(self.raw_t, self.v_active, b1_ms, p_ms, b2_ms)

        rh = self.spin_rh.value()
        rv = self.spin_rv.value()
        rs_ohm, ratio = hall_core.solve_van_der_pauw(rh, rv)
        self.lbl_solved_rs.setText(f"Rs: {rs_ohm:.2f} Ω/□")
        self.lbl_vdp_ratio.setText(f"Rh / Rv Ratio: {ratio:.2f}")

        curr_mult = {"µA": 1e-6, "mA": 1e-3, "A": 1.0}[self.combo_curr_unit.currentText()]
        current_a = self.spin_curr.value() * curr_mult

        thick_mult = {"nm": 1e-9, "µm": 1e-6, "mm": 1e-3, "cm": 1e-2}[self.combo_thick_unit.currentText()]
        thickness_m = self.spin_thick.value() * thick_mult
        field_t = self.spin_b.value()

        if res is not None:
            v_hall_v = res["v_hall"]
            phys = hall_core.calc_hall_physics(v_hall_v, current_a, field_t, thickness_m, rs_ohm)

            self.card_vh["main"].setText(f"{res['v_hall']*1e3:.4f} mV")
            self.card_vh["sub"].setText(f"{res['v_hall']*1e6:.1f} µV (± {res['v_hall_std']*1e6:.1f} µV)")

            if phys["is_n_type"]:
                self.card_type["main"].setText("● n-type (electrons)")
                if self.is_dark_theme:
                    self.card_type["main"].setStyleSheet("font-size: 13px; color: #38bdf8; font-weight: bold; padding: 2px 6px; background-color: #0c4a6e; border-radius: 4px;")
                else:
                    self.card_type["main"].setStyleSheet("font-size: 13px; color: #0369a1; font-weight: bold; padding: 2px 6px; background-color: #e0f2fe; border-radius: 4px;")
            else:
                self.card_type["main"].setText("● p-type (holes)")
                if self.is_dark_theme:
                    self.card_type["main"].setStyleSheet("font-size: 13px; color: #34d399; font-weight: bold; padding: 2px 6px; background-color: #064e3b; border-radius: 4px;")
                else:
                    self.card_type["main"].setStyleSheet("font-size: 13px; color: #047857; font-weight: bold; padding: 2px 6px; background-color: #d1fae5; border-radius: 4px;")
            self.card_type["sub"].setText(f"Drift: {res['slope_v_per_s']*1e6:.2f} µV/s")

            self.card_ns["main"].setText(f"{phys['ns_cm2']:.3e} cm⁻²")
            self.card_ns["sub"].setText(f"R_Hs: {phys['r_hs_si']:.2f} Ω/T")

            if phys["n_bulk_cm3"] is not None:
                self.card_n["main"].setText(f"{phys['n_bulk_cm3']:.3e} cm⁻³")
                self.card_n["sub"].setText(f"RH: {phys['r_h_cm3_c']:.3e} cm³/C")

            if phys["mobility_cm2_vs"] is not None:
                self.card_mu["main"].setText(f"{phys['mobility_cm2_vs']:.1f} cm²/V·s")
                self.card_mu["sub"].setText(f"Using Rs = {rs_ohm:.1f} Ω/□")

            if phys["resistivity_ohm_cm"] is not None:
                self.card_rho["main"].setText(f"{phys['resistivity_ohm_cm']:.3e} Ω·cm")
                self.card_rho["sub"].setText(f"d = {self.spin_thick.value()} {self.combo_thick_unit.currentText()}")

            if self.chk_flatten.isChecked():
                v_flat_mv = hall_core.compute_flattened_curve(self.raw_t, self.v_active, res["slope"], res["intercept"]) * 1e3
                self.curve_active.setData(self.t_sec, v_flat_mv)
                self.curve_raw.setData([], [])
                self.curve_baseline.setData([self.t_sec[0], self.t_sec[-1]], [0.0, 0.0])
                self.curve_delta.setData([res["t_mid"] / 1000.0, res["t_mid"] / 1000.0], [0.0, res["v_hall"] * 1e3])
                self.plot_widget.setLabel('left', "Flattened Voltage ΔV", units='mV')
            else:
                v_active_mv = self.v_active * 1e3
                v_raw_mv = self.raw_v * 1e3
                self.curve_active.setData(self.t_sec, v_active_mv)
                if self.chk_denoise.isChecked():
                    self.curve_raw.setData(self.t_sec, v_raw_mv)
                else:
                    self.curve_raw.setData([], [])

                t_span_s = res["t_span"] / 1000.0
                v_span_mv = res["v_span"] * 1e3
                self.curve_baseline.setData(t_span_s, v_span_mv)

                self.curve_delta.setData(
                    [res["t_mid"] / 1000.0, res["t_mid"] / 1000.0],
                    [res["v_base_mid"] * 1e3, res["v_pulse_mid"] * 1e3]
                )
                self.plot_widget.setLabel('left', "Measured Voltage", units='mV')

            self.latest_res = res
            self.latest_phys = phys

    def log_current_run(self):
        if not hasattr(self, 'latest_res') or not hasattr(self, 'latest_phys'):
            QtWidgets.QMessageBox.warning(self, "No Result", "Please drag regions over a pulse first.")
            return

        meta = hall_core.parse_filename_metadata(self.active_filename)
        p_range = self.region_pulse.getRegion()
        row = {
            "File": self.active_filename,
            "Sample": meta.get('sample', 'Sample'),
            "Temp (K)": meta.get('temp_K', 'N/A'),
            "Pulse Time (s)": f"{p_range[0]:.1f} - {p_range[1]:.1f}",
            "V_Hall (mV)": round(self.latest_res["v_hall"] * 1e3, 4),
            "V_Hall (µV)": round(self.latest_res["v_hall"] * 1e6, 2),
            "Carrier Type": self.latest_phys["carrier_type"],
            "ns (cm^-2)": f"{self.latest_phys['ns_cm2']:.3e}",
            "n_bulk (cm^-3)": f"{self.latest_phys['n_bulk_cm3']:.3e}" if self.latest_phys['n_bulk_cm3'] else "N/A",
            "Mobility (cm^2/Vs)": f"{self.latest_phys['mobility_cm2_vs']:.1f}" if self.latest_phys['mobility_cm2_vs'] else "N/A",
            "Rs (Ohm/sq)": f"{self.latest_phys['resistivity_ohm_cm']:.2e}" if self.latest_phys['resistivity_ohm_cm'] else "N/A",
            "Current": f"{self.spin_curr.value()} {self.combo_curr_unit.currentText()}",
            "Field (T)": self.spin_b.value(),
            "Thickness": f"{self.spin_thick.value()} {self.combo_thick_unit.currentText()}"
        }
        self.measurement_log.append(row)
        QtWidgets.QMessageBox.information(self, "Logged", f"Measurement saved to Session Log!\nTotal logged runs: {len(self.measurement_log)}")

    def open_log_dialog(self):
        if not self.measurement_log:
            QtWidgets.QMessageBox.information(self, "Empty Log", "No runs logged yet. Click 'Log This Measurement' to add runs.")
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Session Measurement Summary & Export")
        dialog.resize(1050, 500)
        d_layout = QtWidgets.QVBoxLayout(dialog)

        # Instructions
        d_layout.addWidget(QtWidgets.QLabel("💡 <i>Tip: Select row(s) and click 'Delete Selected' to remove any misclicks. Use 'Choose Columns' to customize your export.</i>"))

        # Table with multi-row selection
        table = QtWidgets.QTableWidget()
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

        df = pd.DataFrame(self.measurement_log)
        all_cols = list(df.columns)
        if self.selected_export_cols is None:
            self.selected_export_cols = list(all_cols)

        self.populate_qt_table(table, df)
        d_layout.addWidget(table)

        # Action Buttons
        h_btn = QtWidgets.QHBoxLayout()

        btn_del = QtWidgets.QPushButton("🗑️ Delete Selected Row(s)")
        btn_del.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        btn_del.clicked.connect(lambda: self.delete_log_rows(table))
        h_btn.addWidget(btn_del)

        btn_col_filter = QtWidgets.QPushButton("☑️ Choose Columns to Export...")
        btn_col_filter.clicked.connect(lambda: self.open_column_selector(all_cols))
        h_btn.addWidget(btn_col_filter)

        btn_csv = QtWidgets.QPushButton("💾 Export CSV...")
        btn_csv.clicked.connect(lambda: self.export_table_data(self.measurement_log, is_excel=False))
        h_btn.addWidget(btn_csv)

        btn_excel = QtWidgets.QPushButton("💾 Export Excel (.xlsx)...")
        btn_excel.clicked.connect(lambda: self.export_table_data(self.measurement_log, is_excel=True))
        h_btn.addWidget(btn_excel)

        btn_clear = QtWidgets.QPushButton("Clear All")
        btn_clear.clicked.connect(lambda: self.clear_log(table, dialog))
        h_btn.addWidget(btn_clear)

        d_layout.addLayout(h_btn)
        dialog.exec()

    def populate_qt_table(self, table, df):
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(list(df.columns))
        for r_idx, row in df.iterrows():
            for c_idx, val in enumerate(row):
                table.setItem(r_idx, c_idx, QtWidgets.QTableWidgetItem(str(val)))
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def delete_log_rows(self, table):
        selected_indexes = table.selectionModel().selectedRows()
        if not selected_indexes:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please click on a row to select it first.")
            return

        rows = sorted([idx.row() for idx in selected_indexes], reverse=True)
        for r in rows:
            if 0 <= r < len(self.measurement_log):
                del self.measurement_log[r]
            table.removeRow(r)

    def open_column_selector(self, all_cols):
        dlg = ColumnSelectorDialog(all_cols, self.selected_export_cols, self)
        if dlg.exec():
            chosen = dlg.get_selected()
            if chosen:
                self.selected_export_cols = chosen
                QtWidgets.QMessageBox.information(self, "Columns Set", f"Selected {len(chosen)} parameters for export.")

    def export_table_data(self, data_list, is_excel=False):
        if not data_list:
            return
        df = pd.DataFrame(data_list)
        if self.selected_export_cols:
            cols = [c for c in self.selected_export_cols if c in df.columns]
            if cols:
                df = df[cols]

        if is_excel:
            p, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Excel", "Hall_Summary.xlsx", "Excel Files (*.xlsx)")
            if p:
                df.to_excel(p, index=False)
                QtWidgets.QMessageBox.information(self, "Saved", f"Exported {len(df)} rows to:\n{p}")
        else:
            p, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export CSV", "Hall_Summary.csv", "CSV Files (*.csv)")
            if p:
                df.to_csv(p, index=False)
                QtWidgets.QMessageBox.information(self, "Saved", f"Exported {len(df)} rows to:\n{p}")

    def clear_log(self, table, dialog):
        self.measurement_log = []
        table.setRowCount(0)
        QtWidgets.QMessageBox.information(self, "Cleared", "Session log cleared.")
        dialog.close()

    # =========================================================================
    # BATCH STUDIO METHODS (Interactive Step-Through & Bulk Processing)
    # =========================================================================
    def batch_add_files(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Select Hall Data Files", os.getcwd(), "Data Files (*.csv *.txt)"
        )
        if files:
            for f in files:
                if not any(d['path'] == f for d in self.batch_files_data):
                    meta = hall_core.parse_filename_metadata(f)
                    self.batch_files_data.append({
                        'path': f,
                        'filename': os.path.basename(f),
                        'meta': meta,
                        'status': 'Pending',
                        'regions': None,
                        'result': None
                    })
            # Sort staged files by (Sample, Temp_K) for clean chronological workflow
            self.batch_files_data.sort(key=lambda x: (
                str(x['meta'].get('sample', '')),
                x['meta'].get('temp_K') if x['meta'].get('temp_K') is not None else 999999
            ))
            self.refresh_batch_files_table()

            # Automatically load the first file if none is loaded yet
            if self.batch_current_idx == -1 and len(self.batch_files_data) > 0:
                self.load_batch_file_for_manual_extraction(0)

    def batch_add_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder Containing Hall Files", os.getcwd())
        if folder:
            for f in glob.glob(os.path.join(folder, "*.*")):
                if f.lower().endswith(('.csv', '.txt')):
                    if not any(d['path'] == f for d in self.batch_files_data):
                        meta = hall_core.parse_filename_metadata(f)
                        self.batch_files_data.append({
                            'path': f,
                            'filename': os.path.basename(f),
                            'meta': meta,
                            'status': 'Pending',
                            'regions': None,
                            'result': None
                        })
            self.batch_files_data.sort(key=lambda x: (
                str(x['meta'].get('sample', '')),
                x['meta'].get('temp_K') if x['meta'].get('temp_K') is not None else 999999
            ))
            self.refresh_batch_files_table()

            if self.batch_current_idx == -1 and len(self.batch_files_data) > 0:
                self.load_batch_file_for_manual_extraction(0)

    def batch_clear_files(self):
        self.batch_files_data = []
        self.batch_results = []
        self.batch_current_idx = -1
        self.b_raw_t = None
        self.b_raw_v = None
        self.b_t_sec = None
        self.b_v_active = None
        self.refresh_batch_files_table()
        self.refresh_batch_results_table()
        self.update_batch_plot()
        self.lbl_b_file_badge.setText("No file loaded. Please add files on the left.")
        self.lbl_b_meta_info.setText("vdP: -- | Current: -- | Field: --")
        self.btn_b_prev.setEnabled(False)
        self.btn_b_next.setEnabled(False)
        self.b_curve_raw.setData([], [])
        self.b_curve_active.setData([], [])
        self.b_curve_baseline.setData([], [])
        self.b_curve_delta.setData([], [])

    def refresh_batch_files_table(self):
        self.table_b_files.setRowCount(len(self.batch_files_data))
        for r, item in enumerate(self.batch_files_data):
            m = item['meta']
            status = item.get('status', 'Pending')

            # Col 0: Index
            idx_item = QtWidgets.QTableWidgetItem(str(r + 1))
            idx_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table_b_files.setItem(r, 0, idx_item)

            # Col 1: Status Pill Badge
            if status == 'Done':
                res = item.get('result', {})
                vh_str = ""
                if res and 'V_Hall (mV)' in res:
                    try:
                        vh_val = float(res['V_Hall (mV)'])
                        vh_str = f" · {vh_val:+.3f} mV"
                    except Exception:
                        vh_str = f" · {res['V_Hall (mV)']} mV"
                stat_item = QtWidgets.QTableWidgetItem(f"🟢 Done{vh_str}")
                color = QtGui.QColor("#34d399") if self.is_dark_theme else QtGui.QColor("#059669")
                stat_item.setForeground(QtGui.QBrush(color))
            elif status.startswith('Error'):
                stat_item = QtWidgets.QTableWidgetItem("🔴 Error")
                stat_item.setForeground(QtGui.QBrush(QtGui.QColor("#ef4444")))
            else:
                stat_item = QtWidgets.QTableWidgetItem("⚪ Pending")
                color = QtGui.QColor("#94a3b8") if self.is_dark_theme else QtGui.QColor("#64748b")
                stat_item.setForeground(QtGui.QBrush(color))
            stat_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table_b_files.setItem(r, 1, stat_item)

            # Col 2: Sample
            self.table_b_files.setItem(r, 2, QtWidgets.QTableWidgetItem(str(m.get('sample', ''))))

            # Col 3: Temp (K)
            temp_val = m.get('temp_K')
            t_item = QtWidgets.QTableWidgetItem(f"{temp_val} K" if temp_val is not None else "N/A")
            t_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table_b_files.setItem(r, 3, t_item)

            # Col 4: Current
            self.table_b_files.setItem(r, 4, QtWidgets.QTableWidgetItem(f"{m.get('current_uA', 100.0)} µA"))

            # Col 5: File Name
            self.table_b_files.setItem(r, 5, QtWidgets.QTableWidgetItem(item['filename']))

        if 0 <= self.batch_current_idx < len(self.batch_files_data):
            self.table_b_files.selectRow(self.batch_current_idx)

        total_files = len(self.batch_files_data)
        done_count = sum(1 for item in self.batch_files_data if item.get('status') == 'Done')
        self.lbl_b_file_count.setText(f"{total_files} staged ({done_count} extracted)")

        if hasattr(self, 'b_progress_bar'):
            self.b_progress_bar.setRange(0, max(1, total_files))
            self.b_progress_bar.setValue(done_count)
            pct = int(100 * done_count / total_files) if total_files > 0 else 0
            self.b_progress_bar.setFormat(f"Batch Progress: {done_count} of {total_files} files completed ({pct}%)")

    def batch_load_vdp_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open van der Pauw Reference Sheet", os.getcwd(), "vdP Files (*.csv *.xlsx *.txt *.xls)"
        )
        if path:
            try:
                self.vdp_df = hall_core.load_vdp_reference_table(path)
                self.vdp_filepath = path
                self.lbl_vdp_status.setText(f"✅ Loaded: {os.path.basename(path)} ({len(self.vdp_df)} entries)")
                self.lbl_vdp_status.setStyleSheet("color: #198754; font-size: 11px; font-weight: bold;")

                # Populate preview
                self.table_vdp_preview.setRowCount(len(self.vdp_df))
                for r, row in self.vdp_df.iterrows():
                    self.table_vdp_preview.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row.get('Sample', ''))))
                    self.table_vdp_preview.setItem(r, 1, QtWidgets.QTableWidgetItem(str(row.get('Rh', ''))))
                    self.table_vdp_preview.setItem(r, 2, QtWidgets.QTableWidgetItem(str(row.get('Rv', ''))))

                # Update current active batch file if loaded
                if 0 <= self.batch_current_idx < len(self.batch_files_data):
                    self.load_batch_file_for_manual_extraction(self.batch_current_idx)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "vdP File Error", f"Could not parse van der Pauw file:\n{e}")

    def on_batch_file_cell_clicked(self, row, col):
        if 0 <= row < len(self.batch_files_data):
            self.load_batch_file_for_manual_extraction(row)
            self.b_sub_tabs.setCurrentIndex(0)

    def start_batch_manual_queue(self):
        if not self.batch_files_data:
            QtWidgets.QMessageBox.warning(self, "No Files", "Please add Hall measurement files first.")
            return
        self.load_batch_file_for_manual_extraction(0)
        self.b_sub_tabs.setCurrentIndex(0)

    def batch_manual_prev_file(self):
        if self.batch_current_idx > 0:
            self.load_batch_file_for_manual_extraction(self.batch_current_idx - 1)

    def batch_manual_next_file(self):
        if self.batch_current_idx < len(self.batch_files_data) - 1:
            self.load_batch_file_for_manual_extraction(self.batch_current_idx + 1)

    def batch_apply_preset(self, b1_0, b1_1, p_0, p_1, b2_0, b2_1):
        self.b_region_b1.setRegion([b1_0, b1_1])
        self.b_region_pulse.setRegion([p_0, p_1])
        self.b_region_b2.setRegion([b2_0, b2_1])
        self.recalculate_batch_manual()

    def on_batch_param_changed(self):
        if hasattr(self, 'b_raw_t') and self.b_raw_t is not None:
            self.recalculate_batch_manual()

    def on_batch_prep_changed(self):
        if 0 <= self.batch_current_idx < len(self.batch_files_data):
            self.load_batch_file_for_manual_extraction(self.batch_current_idx)

    def load_batch_file_for_manual_extraction(self, idx):
        if not self.batch_files_data or idx < 0 or idx >= len(self.batch_files_data):
            return

        self.batch_current_idx = idx
        item = self.batch_files_data[idx]
        fpath = item['path']
        meta = item['meta']

        # Update navigation controls
        self.lbl_b_file_badge.setText(
            f"File {idx + 1} of {len(self.batch_files_data)}: {item['filename']}"
        )
        self.btn_b_prev.setEnabled(idx > 0)
        self.btn_b_next.setEnabled(idx < len(self.batch_files_data) - 1)
        self.table_b_files.selectRow(idx)

        # Match van der Pauw
        sample_name = meta.get('sample', 'Sample')
        temp_k = meta.get('temp_K', None)
        curr_uA = meta.get('current_uA', 100.0)

        rh, rv, matched_label, is_matched = hall_core.match_sample_vdp(sample_name, temp_k, self.vdp_df)
        if not is_matched:
            rh = self.spin_b_fallback_rh.value()
            rv = self.spin_b_fallback_rv.value()
            matched_label = "Fallback"

        rs_ohm, vdp_ratio = hall_core.solve_van_der_pauw(rh, rv)

        self.b_active_meta = meta
        self.b_active_rh = rh
        self.b_active_rv = rv
        self.b_active_rs = rs_ohm
        self.b_active_vdp_match = matched_label

        t_str = f"{temp_k} K" if temp_k is not None else "N/A"
        self.lbl_b_meta_info.setText(
            f"<b>Sample:</b> {sample_name} | <b>T:</b> {t_str} | <b>I:</b> {curr_uA} µA | "
            f"<b>vdP ({matched_label}):</b> Rh = {rh:.1f} Ω, Rv = {rv:.1f} Ω → <b>Rs = {rs_ohm:.1f} Ω/□</b> (Ratio: {vdp_ratio:.2f})"
        )

        try:
            t_raw, v_raw = hall_core.parse_hall_csv(fpath)
            skip_pts = self.spin_b_spike.value()
            if skip_pts > 0 and len(t_raw) > skip_pts:
                t_raw = t_raw[skip_pts:]
                v_raw = v_raw[skip_pts:]

            self.b_raw_t = t_raw
            self.b_raw_v = v_raw
            self.b_t_sec = t_raw / 1000.0

            if self.chk_b_denoise.isChecked():
                self.b_v_active = hall_core.apply_denoising(self.b_raw_v, 15)
            else:
                self.b_v_active = self.b_raw_v.copy()

            # Restore regions if previously saved for this file, else set intelligent defaults
            if item.get('regions'):
                b1, p, b2 = item['regions']
                self.b_region_b1.setRegion(b1)
                self.b_region_pulse.setRegion(p)
                self.b_region_b2.setRegion(b2)
            else:
                total_duration_s = self.b_t_sec[-1] - self.b_t_sec[0]
                if total_duration_s >= 150:
                    self.b_region_b1.setRegion([10.0, 20.0])
                    self.b_region_pulse.setRegion([35.0, 50.0])
                    self.b_region_b2.setRegion([65.0, 75.0])
                else:
                    t0 = self.b_t_sec[0]
                    t_end = self.b_t_sec[-1]
                    dt = t_end - t0
                    self.b_region_b1.setRegion([t0 + 0.05 * dt, t0 + 0.15 * dt])
                    self.b_region_pulse.setRegion([t0 + 0.35 * dt, t0 + 0.55 * dt])
                    self.b_region_b2.setRegion([t0 + 0.70 * dt, t0 + 0.85 * dt])

            self.recalculate_batch_manual()
            self.plot_b_manual.autoRange()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Read Error", f"Error loading {item['filename']}:\n{e}")

    def on_batch_manual_region_dragged(self):
        self.recalculate_batch_manual()

    def recalculate_batch_manual(self):
        if not hasattr(self, 'b_t_sec') or self.b_t_sec is None or len(self.b_t_sec) < 5:
            return

        b1_range = self.b_region_b1.getRegion()
        p_range = self.b_region_pulse.getRegion()
        b2_range = self.b_region_b2.getRegion()

        b1_ms = (b1_range[0] * 1000.0, b1_range[1] * 1000.0)
        p_ms = (p_range[0] * 1000.0, p_range[1] * 1000.0)
        b2_ms = (b2_range[0] * 1000.0, b2_range[1] * 1000.0)

        res = hall_core.calc_option_a_3zone(self.b_raw_t, self.b_v_active, b1_ms, p_ms, b2_ms)

        field_t = self.spin_b_field.value()
        thick_m = self.spin_b_thick.value() * 1e-9
        curr_a = self.b_active_meta.get('current_uA', 100.0) * 1e-6
        rs_ohm = self.b_active_rs

        mode = self.combo_b_calc_mode.currentText()

        if mode == "Full 3-Pulse Sequence (+B / -B / +B)":
            w_b1 = (10000, 20000)
            w_p1 = (35000, 50000)
            w_b2 = (65000, 75000)
            w_p2 = (90000, 110000)
            w_b3 = (125000, 135000)
            w_p3 = (150000, 170000)
            w_b4 = (185000, 195000)
            p1 = hall_core.calc_option_a_3zone(self.b_raw_t, self.b_v_active, w_b1, w_p1, w_b2)
            p2 = hall_core.calc_option_a_3zone(self.b_raw_t, self.b_v_active, w_b2, w_p2, w_b3)
            p3 = hall_core.calc_option_a_3zone(self.b_raw_t, self.b_v_active, w_b3, w_p3, w_b4)
            if p1 and p2 and p3:
                v_hall_v = 0.5 * (((p1['v_hall'] + p3['v_hall']) / 2.0) - p2['v_hall'])
            elif res:
                v_hall_v = res['v_hall']
            else:
                v_hall_v = 0.0
        else:
            v_hall_v = res['v_hall'] if res else 0.0

        if res is not None:
            phys = hall_core.calc_hall_physics(v_hall_v, curr_a, field_t, thick_m, rs_ohm)

            self.b_card_vh["main"].setText(f"{v_hall_v * 1e3:.4f} mV")
            self.b_card_vh["sub"].setText(f"{v_hall_v * 1e6:.1f} µV")

            if phys["is_n_type"]:
                self.b_card_type["main"].setText("● n-type (electrons)")
                if self.is_dark_theme:
                    self.b_card_type["main"].setStyleSheet("font-size: 13px; color: #38bdf8; font-weight: bold; padding: 2px 6px; background-color: #0c4a6e; border-radius: 4px;")
                else:
                    self.b_card_type["main"].setStyleSheet("font-size: 13px; color: #0369a1; font-weight: bold; padding: 2px 6px; background-color: #e0f2fe; border-radius: 4px;")
            else:
                self.b_card_type["main"].setText("● p-type (holes)")
                if self.is_dark_theme:
                    self.b_card_type["main"].setStyleSheet("font-size: 13px; color: #34d399; font-weight: bold; padding: 2px 6px; background-color: #064e3b; border-radius: 4px;")
                else:
                    self.b_card_type["main"].setStyleSheet("font-size: 13px; color: #047857; font-weight: bold; padding: 2px 6px; background-color: #d1fae5; border-radius: 4px;")
            self.b_card_type["sub"].setText(f"Drift: {res['slope_v_per_s']*1e6:.2f} µV/s")

            self.b_card_ns["main"].setText(f"{phys['ns_cm2']:.3e} cm⁻²")
            self.b_card_ns["sub"].setText(f"R_Hs: {phys['r_hs_si']:.2f} Ω/T")

            if phys["n_bulk_cm3"] is not None:
                self.b_card_n["main"].setText(f"{phys['n_bulk_cm3']:.3e} cm⁻³")
                self.b_card_n["sub"].setText(f"RH: {phys['r_h_cm3_c']:.3e} cm³/C")

            if phys["mobility_cm2_vs"] is not None:
                self.b_card_mu["main"].setText(f"{phys['mobility_cm2_vs']:.1f} cm²/V·s")
                self.b_card_mu["sub"].setText(f"Using Rs = {rs_ohm:.1f} Ω/□")

            if phys["resistivity_ohm_cm"] is not None:
                self.b_card_rho["main"].setText(f"{phys['resistivity_ohm_cm']:.3e} Ω·cm")
                self.b_card_rho["sub"].setText(f"d = {self.spin_b_thick.value()} nm")

            # Update curves
            if self.chk_b_flatten.isChecked():
                v_flat_mv = hall_core.compute_flattened_curve(self.b_raw_t, self.b_v_active, res["slope"], res["intercept"]) * 1e3
                self.b_curve_active.setData(self.b_t_sec, v_flat_mv)
                self.b_curve_raw.setData([], [])
                self.b_curve_baseline.setData([self.b_t_sec[0], self.b_t_sec[-1]], [0.0, 0.0])
                self.b_curve_delta.setData([res["t_mid"] / 1000.0, res["t_mid"] / 1000.0], [0.0, v_hall_v * 1e3])
                self.plot_b_manual.setLabel('left', "Flattened Voltage ΔV", units='mV')
            else:
                v_active_mv = self.b_v_active * 1e3
                v_raw_mv = self.b_raw_v * 1e3
                self.b_curve_active.setData(self.b_t_sec, v_active_mv)
                if self.chk_b_denoise.isChecked():
                    self.b_curve_raw.setData(self.b_t_sec, v_raw_mv)
                else:
                    self.b_curve_raw.setData([], [])

                t_span_s = res["t_span"] / 1000.0
                v_span_mv = res["v_span"] * 1e3
                self.b_curve_baseline.setData(t_span_s, v_span_mv)

                self.b_curve_delta.setData(
                    [res["t_mid"] / 1000.0, res["t_mid"] / 1000.0],
                    [res["v_base_mid"] * 1e3, res["v_pulse_mid"] * 1e3]
                )
                self.plot_b_manual.setLabel('left', "Measured Voltage", units='mV')

            self.b_latest_res = res
            self.b_latest_v_hall = v_hall_v
            self.b_latest_phys = phys

    def batch_manual_save_and_next(self):
        if not self.batch_files_data or self.batch_current_idx < 0:
            return

        idx = self.batch_current_idx
        item = self.batch_files_data[idx]

        if not hasattr(self, 'b_latest_res') or self.b_latest_res is None or not hasattr(self, 'b_latest_phys') or self.b_latest_phys is None:
            QtWidgets.QMessageBox.warning(self, "No Result", "Please drag regions over a pulse first.")
            return

        # Save active regions for this file
        b1_range = list(self.b_region_b1.getRegion())
        p_range = list(self.b_region_pulse.getRegion())
        b2_range = list(self.b_region_b2.getRegion())
        item['regions'] = (b1_range, p_range, b2_range)

        meta = item['meta']
        sample_name = meta.get('sample', 'Sample')
        temp_k = meta.get('temp_K', None)
        curr_uA = meta.get('current_uA', 100.0)
        field_t = self.spin_b_field.value()
        rs_ohm = self.b_active_rs
        rh = self.b_active_rh
        rv = self.b_active_rv
        matched_label = self.b_active_vdp_match
        phys = self.b_latest_phys
        v_h = self.b_latest_v_hall

        res_row = {
            "Sample": sample_name,
            "Temp (K)": temp_k if temp_k is not None else "N/A",
            "Temp_Num": temp_k if temp_k is not None else -1.0,
            "Current": f"{curr_uA} µA",
            "B (T)": field_t,
            "V_Hall (mV)": round(v_h * 1e3, 4),
            "V_Hall (µV)": round(v_h * 1e6, 2),
            "Carrier Type": phys["carrier_type"] if phys else "N/A",
            "ns (cm^-2)": f"{phys['ns_cm2']:.3e}" if phys else "N/A",
            "n_bulk (cm^-3)": f"{phys['n_bulk_cm3']:.3e}" if phys and phys['n_bulk_cm3'] else "N/A",
            "Mobility (cm^2/Vs)": round(phys['mobility_cm2_vs'], 1) if phys and phys['mobility_cm2_vs'] else "N/A",
            "Rh (Ω)": round(rh, 2),
            "Rv (Ω)": round(rv, 2),
            "Rs (Ohm/sq)": round(rs_ohm, 2),
            "Resistivity (Ohm*cm)": f"{phys['resistivity_ohm_cm']:.3e}" if phys and phys['resistivity_ohm_cm'] else "N/A",
            "vdP Match": matched_label,
            "File": item['filename'],
            "_ns_val": phys['ns_cm2'] if phys else None,
            "_n_val": phys['n_bulk_cm3'] if phys else None,
            "_mu_val": phys['mobility_cm2_vs'] if phys else None,
            "_rho_val": phys['resistivity_ohm_cm'] if phys else None,
            "_vh_mv": v_h * 1e3
        }

        # Upsert into batch_results
        existing_idx = next((i for i, r in enumerate(self.batch_results) if r['File'] == item['filename']), None)
        if existing_idx is not None:
            self.batch_results[existing_idx] = res_row
        else:
            self.batch_results.append(res_row)

        self.batch_results.sort(key=lambda r: (r['Sample'], r['Temp_Num']))

        item['status'] = 'Done'
        item['result'] = res_row

        # Refresh table of files and batch summary table and plot
        self.refresh_batch_files_table()
        self.refresh_batch_results_table()
        self.update_batch_plot()

        # Advance to next file in queue
        if idx + 1 < len(self.batch_files_data):
            self.load_batch_file_for_manual_extraction(idx + 1)
        else:
            reply = QtWidgets.QMessageBox.information(
                self, "Batch Complete",
                f"🎉 All {len(self.batch_files_data)} files in the batch have been extracted and verified!\n\n"
                "Would you like to switch to the Temperature Dependence Plots now?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.b_sub_tabs.setCurrentIndex(2)

    def auto_process_remaining_files(self):
        if not self.batch_files_data:
            QtWidgets.QMessageBox.warning(self, "No Files", "Please add Hall measurement files first.")
            return

        field_t = self.spin_b_field.value()
        thick_m = self.spin_b_thick.value() * 1e-9
        skip_pts = self.spin_b_spike.value()
        denoise = self.chk_b_denoise.isChecked()

        w_b1 = (10000, 20000)
        w_p1 = (35000, 50000)
        w_b2 = (65000, 75000)
        w_p2 = (90000, 110000)
        w_b3 = (125000, 135000)
        w_p3 = (150000, 170000)
        w_b4 = (185000, 195000)

        count_processed = 0
        for item in self.batch_files_data:
            if item.get('status') == 'Done':
                continue

            fpath = item['path']
            meta = item['meta']
            sample_name = meta.get('sample', 'Sample')
            temp_k = meta.get('temp_K', None)
            curr_a = meta.get('current_uA', 100.0) * 1e-6

            try:
                t, v = hall_core.parse_hall_csv(fpath)
                if skip_pts > 0 and len(t) > skip_pts:
                    t = t[skip_pts:]
                    v = v[skip_pts:]

                v_sig = hall_core.apply_denoising(v, 15) if denoise else v

                rh, rv, matched_label, is_matched = hall_core.match_sample_vdp(sample_name, temp_k, self.vdp_df)
                if not is_matched:
                    rh = self.spin_b_fallback_rh.value()
                    rv = self.spin_b_fallback_rv.value()
                    matched_label = "Fallback"

                rs_ohm, vdp_ratio = hall_core.solve_van_der_pauw(rh, rv)

                p1 = hall_core.calc_option_a_3zone(t, v_sig, w_b1, w_p1, w_b2)
                p2 = hall_core.calc_option_a_3zone(t, v_sig, w_b2, w_p2, w_b3)
                p3 = hall_core.calc_option_a_3zone(t, v_sig, w_b3, w_p3, w_b4)

                if p1 and p2 and p3:
                    v_h_comb = 0.5 * (((p1['v_hall'] + p3['v_hall']) / 2.0) - p2['v_hall'])
                elif p1:
                    v_h_comb = p1['v_hall']
                else:
                    v_h_comb = 0.0

                phys = hall_core.calc_hall_physics(v_h_comb, curr_a, field_t, thick_m, rs_ohm)

                res_row = {
                    "Sample": sample_name,
                    "Temp (K)": temp_k if temp_k is not None else "N/A",
                    "Temp_Num": temp_k if temp_k is not None else -1.0,
                    "Current": f"{meta.get('current_uA', 100.0)} µA",
                    "B (T)": field_t,
                    "V_Hall (mV)": round(v_h_comb * 1e3, 4),
                    "V_Hall (µV)": round(v_h_comb * 1e6, 2),
                    "Carrier Type": phys["carrier_type"] if phys else "N/A",
                    "ns (cm^-2)": f"{phys['ns_cm2']:.3e}" if phys else "N/A",
                    "n_bulk (cm^-3)": f"{phys['n_bulk_cm3']:.3e}" if phys and phys['n_bulk_cm3'] else "N/A",
                    "Mobility (cm^2/Vs)": round(phys['mobility_cm2_vs'], 1) if phys and phys['mobility_cm2_vs'] else "N/A",
                    "Rh (Ω)": round(rh, 2),
                    "Rv (Ω)": round(rv, 2),
                    "Rs (Ohm/sq)": round(rs_ohm, 2),
                    "Resistivity (Ohm*cm)": f"{phys['resistivity_ohm_cm']:.3e}" if phys and phys['resistivity_ohm_cm'] else "N/A",
                    "vdP Match": matched_label,
                    "File": item['filename'],
                    "_ns_val": phys['ns_cm2'] if phys else None,
                    "_n_val": phys['n_bulk_cm3'] if phys else None,
                    "_mu_val": phys['mobility_cm2_vs'] if phys else None,
                    "_rho_val": phys['resistivity_ohm_cm'] if phys else None,
                    "_vh_mv": v_h_comb * 1e3
                }

                existing_idx = next((i for i, r in enumerate(self.batch_results) if r['File'] == item['filename']), None)
                if existing_idx is not None:
                    self.batch_results[existing_idx] = res_row
                else:
                    self.batch_results.append(res_row)

                item['status'] = 'Done'
                item['result'] = res_row
                count_processed += 1
            except Exception as e:
                item['status'] = f"Error: {e}"

        self.batch_results.sort(key=lambda r: (r['Sample'], r['Temp_Num']))
        self.refresh_batch_files_table()
        self.refresh_batch_results_table()
        self.update_batch_plot()

        QtWidgets.QMessageBox.information(
            self, "Auto-Process Complete",
            f"Successfully auto-processed {count_processed} pending files."
        )

    def run_batch_processing(self):
        if not self.batch_files_data:
            QtWidgets.QMessageBox.warning(self, "No Files", "Please add Hall measurement files first.")
            return

        field_t = self.spin_b_field.value()
        thick_m = self.spin_b_thick.value() * 1e-9  # nm to m
        skip_pts = self.spin_b_spike.value()
        denoise = self.chk_b_denoise.isChecked()

        self.batch_results = []
        errors = []

        # Standard timing windows for 200s sequence
        w_b1 = (10000, 20000)
        w_p1 = (35000, 50000)
        w_b2 = (65000, 75000)
        w_p2 = (90000, 110000)
        w_b3 = (125000, 135000)
        w_p3 = (150000, 170000)
        w_b4 = (185000, 195000)

        for item in self.batch_files_data:
            fpath = item['path']
            meta = item['meta']
            sample_name = meta.get('sample', 'Sample')
            temp_k = meta.get('temp_K', None)
            curr_a = meta.get('current_uA', 100.0) * 1e-6

            try:
                t, v = hall_core.parse_hall_csv(fpath)
                if skip_pts > 0 and len(t) > skip_pts:
                    t = t[skip_pts:]
                    v = v[skip_pts:]

                v_sig = hall_core.apply_denoising(v, 15) if denoise else v

                # Match vdP Rh and Rv
                rh, rv, matched_label, is_matched = hall_core.match_sample_vdp(sample_name, temp_k, self.vdp_df)
                if not is_matched:
                    rh = self.spin_b_fallback_rh.value()
                    rv = self.spin_b_fallback_rv.value()
                    matched_label = "Fallback"

                rs_ohm, vdp_ratio = hall_core.solve_van_der_pauw(rh, rv)

                # 3-pulse stepped calculation
                p1 = hall_core.calc_option_a_3zone(t, v_sig, w_b1, w_p1, w_b2)
                p2 = hall_core.calc_option_a_3zone(t, v_sig, w_b2, w_p2, w_b3)
                p3 = hall_core.calc_option_a_3zone(t, v_sig, w_b3, w_p3, w_b4)

                if p1 and p2 and p3:
                    v_h_comb = 0.5 * (((p1['v_hall'] + p3['v_hall']) / 2.0) - p2['v_hall'])
                elif p1:
                    v_h_comb = p1['v_hall']
                else:
                    v_h_comb = 0.0

                phys = hall_core.calc_hall_physics(v_h_comb, curr_a, field_t, thick_m, rs_ohm)

                res_row = {
                    "Sample": sample_name,
                    "Temp (K)": temp_k if temp_k is not None else "N/A",
                    "Temp_Num": temp_k if temp_k is not None else -1.0,
                    "Current": f"{meta.get('current_uA', 100.0)} µA",
                    "B (T)": field_t,
                    "V_Hall (mV)": round(v_h_comb * 1e3, 4),
                    "V_Hall (µV)": round(v_h_comb * 1e6, 2),
                    "Carrier Type": phys["carrier_type"] if phys else "N/A",
                    "ns (cm^-2)": f"{phys['ns_cm2']:.3e}" if phys else "N/A",
                    "n_bulk (cm^-3)": f"{phys['n_bulk_cm3']:.3e}" if phys and phys['n_bulk_cm3'] else "N/A",
                    "Mobility (cm^2/Vs)": round(phys['mobility_cm2_vs'], 1) if phys and phys['mobility_cm2_vs'] else "N/A",
                    "Rh (Ω)": round(rh, 2),
                    "Rv (Ω)": round(rv, 2),
                    "Rs (Ohm/sq)": round(rs_ohm, 2),
                    "Resistivity (Ohm*cm)": f"{phys['resistivity_ohm_cm']:.3e}" if phys and phys['resistivity_ohm_cm'] else "N/A",
                    "vdP Match": matched_label,
                    "File": item['filename'],
                    # Raw numeric values for temperature plotting
                    "_ns_val": phys['ns_cm2'] if phys else None,
                    "_n_val": phys['n_bulk_cm3'] if phys else None,
                    "_mu_val": phys['mobility_cm2_vs'] if phys else None,
                    "_rho_val": phys['resistivity_ohm_cm'] if phys else None,
                    "_vh_mv": v_h_comb * 1e3
                }
                self.batch_results.append(res_row)
                item['status'] = 'Done'
                item['result'] = res_row
            except Exception as e:
                item['status'] = f"Error: {e}"
                errors.append(f"{item['filename']}: {e}")

        # Sort batch results by temperature if present
        self.batch_results.sort(key=lambda r: (r['Sample'], r['Temp_Num']))

        # Populate tables & plot
        self.refresh_batch_files_table()
        self.refresh_batch_results_table()
        self.update_batch_plot()
        self.b_sub_tabs.setCurrentIndex(1)  # switch to results table

        msg = f"Auto-Batch processing finished!\nProcessed: {len(self.batch_results)} files successfully."
        if errors:
            msg += f"\nErrors in {len(errors)} files."
        QtWidgets.QMessageBox.information(self, "Batch Complete", msg)

    def refresh_batch_results_table(self):
        if not self.batch_results:
            self.table_b_results.setRowCount(0)
            return

        display_cols = [k for k in self.batch_results[0].keys() if not k.startswith('_') and k != 'Temp_Num']
        df = pd.DataFrame(self.batch_results)[display_cols]
        self.populate_qt_table(self.table_b_results, df)

    def delete_selected_batch_rows(self):
        selected_indexes = self.table_b_results.selectionModel().selectedRows()
        if not selected_indexes:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please click on a row to select it first.")
            return

        rows = sorted([idx.row() for idx in selected_indexes], reverse=True)
        for r in rows:
            if 0 <= r < len(self.batch_results):
                deleted_file = self.batch_results[r].get('File')
                del self.batch_results[r]
                # Reset status in staged files
                for item in self.batch_files_data:
                    if item['filename'] == deleted_file:
                        item['status'] = 'Pending'
                        item['result'] = None
                        break
        self.refresh_batch_results_table()
        self.refresh_batch_files_table()
        self.update_batch_plot()

    def open_batch_column_selector(self):
        if not self.batch_results:
            return
        all_cols = [k for k in self.batch_results[0].keys() if not k.startswith('_') and k != 'Temp_Num']
        dlg = ColumnSelectorDialog(all_cols, self.selected_export_cols, self)
        if dlg.exec():
            chosen = dlg.get_selected()
            if chosen:
                self.selected_export_cols = chosen
                QtWidgets.QMessageBox.information(self, "Columns Set", f"Selected {len(chosen)} parameters for batch export.")

    def export_batch_csv(self):
        if not self.batch_results:
            QtWidgets.QMessageBox.warning(self, "No Data", "No batch results to export.")
            return
        display_cols = [k for k in self.batch_results[0].keys() if not k.startswith('_') and k != 'Temp_Num']
        df = pd.DataFrame(self.batch_results)[display_cols]
        if self.selected_export_cols:
            cols = [c for c in self.selected_export_cols if c in df.columns]
            if cols:
                df = df[cols]
        p, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Batch CSV", "Hall_Batch_Results.csv", "CSV Files (*.csv)")
        if p:
            df.to_csv(p, index=False)
            QtWidgets.QMessageBox.information(self, "Saved", f"Exported {len(df)} rows to:\n{p}")

    def export_batch_excel(self):
        if not self.batch_results:
            QtWidgets.QMessageBox.warning(self, "No Data", "No batch results to export.")
            return
        display_cols = [k for k in self.batch_results[0].keys() if not k.startswith('_') and k != 'Temp_Num']
        df = pd.DataFrame(self.batch_results)[display_cols]
        if self.selected_export_cols:
            cols = [c for c in self.selected_export_cols if c in df.columns]
            if cols:
                df = df[cols]
        p, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Batch Excel", "Hall_Batch_Results.xlsx", "Excel Files (*.xlsx)")
        if p:
            df.to_excel(p, index=False)
            QtWidgets.QMessageBox.information(self, "Saved", f"Exported {len(df)} rows to:\n{p}")

    def update_batch_plot(self):
        self.plot_batch.clear()
        if not self.batch_results:
            return

        param_choice = self.combo_t_param.currentText()
        log_y = self.chk_log_y.isChecked()
        self.plot_batch.setLogMode(x=False, y=log_y)

        # Determine y-variable and labels
        if "Mobility" in param_choice:
            key = "_mu_val"
            self.plot_batch.setLabel('left', "Hall Mobility (μ)", units='cm²/V·s')
        elif "Carrier Concentration" in param_choice:
            key = "_n_val"
            self.plot_batch.setLabel('left', "Bulk Carrier Density (n)", units='cm⁻³')
        elif "Sheet Density" in param_choice:
            key = "_ns_val"
            self.plot_batch.setLabel('left', "Sheet Carrier Density (ns)", units='cm⁻²')
        elif "Resistivity" in param_choice:
            key = "_rho_val"
            self.plot_batch.setLabel('left', "Resistivity (ρ)", units='Ω·cm')
        else:
            key = "_vh_mv"
            self.plot_batch.setLabel('left', "Hall Voltage (V_H)", units='mV')

        # Group data points by Sample name
        samples = {}
        for r in self.batch_results:
            if r['Temp_Num'] > 0 and r.get(key) is not None:
                s_name = r['Sample']
                if s_name not in samples:
                    samples[s_name] = []
                samples[s_name].append((r['Temp_Num'], r[key]))

        colors = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b']

        for idx, (s_name, pts) in enumerate(samples.items()):
            pts.sort(key=lambda x: x[0])
            xs = np.array([p[0] for p in pts])
            ys = np.array([p[1] for p in pts])

            c = colors[idx % len(colors)]
            self.plot_batch.plot(
                xs, ys, name=s_name,
                pen=pg.mkPen(c, width=2.5),
                symbol='o', symbolSize=8, symbolBrush=c, symbolPen='k'
            )

    # =========================================================================
    # INFO & THEORY DIALOG
    # =========================================================================
    def open_info_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Information & Physical Theory Reference")
        dialog.resize(920, 620)
        d_layout = QtWidgets.QVBoxLayout(dialog)

        tabs = QtWidgets.QTabWidget()

        # Tab 1: Credits
        tab_credit = QtWidgets.QWidget()
        c_layout = QtWidgets.QVBoxLayout(tab_credit)
        credit_browser = QtWidgets.QTextBrowser()
        credit_browser.setOpenExternalLinks(True)
        credit_html = """
        <div style='font-family: Segoe UI, Arial, sans-serif; padding: 12px; color: #212529;'>
            <h2 style='color: #0d6efd; margin-bottom: 4px;'>🔬 Hall Effect Measurement Studio</h2>
            <p style='font-size: 13px; color: #6c757d; margin-top: 0;'>Version 2.0 — Dual Single & Batch Production Edition</p>
            <hr style='border: none; border-top: 1px solid #dee2e6; margin: 15px 0;'/>
            
            <h3 style='color: #343a40;'>About This Application</h3>
            <p style='font-size: 14px; line-height: 1.6;'>
                <b>Hall Effect Measurement Studio</b> is a specialized, hardware-accelerated scientific analysis application 
                developed for experimental condensed matter physics, semiconductor characterization, and thin-film electronic transport research.
            </p>
            <p style='font-size: 14px; line-height: 1.6;'>
                It was designed to completely eliminate the tedious and error-prone manual process of drawing lines across drifting baselines 
                in Excel or Origin, copying numbers between sheets, and manually re-calculating carrier concentrations and mobility.
            </p>
            
            <h3 style='color: #343a40; margin-top: 20px;'>Core Engineering Highlights</h3>
            <ul style='font-size: 14px; line-height: 1.8;'>
                <li><b>Single Studio (60+ FPS):</b> Hardware-accelerated Qt/OpenGL canvas with real-time recalculation as you drag shaded regions.</li>
                <li><b>Batch Calculation Studio:</b> Multi-file bulk processing of temperature-dependent Hall runs, matching van der Pauw sheets, and rendering temperature curves.</li>
                <li><b>Dynamic Baseline Drift Interpolation:</b> Ordinary least squares extrapolation connecting pre- and post-pulse intervals across the pulse window.</li>
                <li><b>Field Reversal Symmetry Subtraction:</b> Cancels geometric contact misalignment voltages (<i>V<sub>offset</sub></i>) and thermal EMF.</li>
                <li><b>Integrated van der Pauw Solver:</b> Numerically solves the transcendental van der Pauw equation to compute sheet resistance <i>R<sub>s</sub></i>, symmetry ratio <i>R<sub>h</sub>/R<sub>v</sub></i>, and bulk resistivity <i>ρ</i>.</li>
                <li><b>Export Checkboard & Row Deletion:</b> Choose exactly which parameters to export and clean up accidental log entries.</li>
            </ul>

            <h3 style='color: #343a40; margin-top: 20px;'>Credits & Collaboration</h3>
            <p style='font-size: 14px; line-height: 1.6;'>
                • <b>Development & Architecture:</b> Pair-programmed with <b>Antigravity</b> (Google DeepMind Advanced Agentic Coding team).<br>
                • <b>Experimental Protocol:</b> Designed for stepped pulse magnetic field sequences (<i>0 → +B → 0 → -B → 0 → +B → 0</i>) with van der Pauw 4-contact geometry.
            </p>
        </div>
        """
        credit_browser.setHtml(credit_html)
        c_layout.addWidget(credit_browser)
        tabs.addTab(tab_credit, "📜 Credits")

        # Tab 2: Physical Check
        tab_physics = QtWidgets.QWidget()
        p_layout = QtWidgets.QVBoxLayout(tab_physics)
        physics_browser = QtWidgets.QTextBrowser()
        physics_browser.setOpenExternalLinks(True)
        physics_html = """
        <div style='font-family: Segoe UI, Arial, sans-serif; padding: 12px; color: #212529;'>
            <h2 style='color: #0d6efd; margin-bottom: 4px;'>📐 Physical Parameter Extraction Reference</h2>
            <p style='font-size: 13px; color: #6c757d; margin-top: 0;'>Theory & Mathematical Formulas used in calculations</p>
            <hr style='border: none; border-top: 1px solid #dee2e6; margin: 15px 0;'/>

            <h3 style='color: #343a40;'>1. Physical Parameters Extraction Table</h3>
            <table style='width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px;'>
                <thead>
                    <tr style='background-color: #e9ecef; border-top: 1px solid #ced4da; border-bottom: 2px solid #adb5bd;'>
                        <th style='padding: 10px; text-align: left;'>Physical Quantity</th>
                        <th style='padding: 10px; text-align: left;'>Mathematical Formula</th>
                        <th style='padding: 10px; text-align: left;'>SI & Common Units</th>
                        <th style='padding: 10px; text-align: left;'>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style='border-bottom: 1px solid #dee2e6;'>
                        <td style='padding: 10px; font-weight: bold;'>Sheet Hall Coefficient (R<sub>Hs</sub>)</td>
                        <td style='padding: 10px;'><code>R<sub>Hs</sub> = V<sub>H</sub> / (I · B)</code></td>
                        <td style='padding: 10px;'>Ω / T &nbsp;(or m² / C)</td>
                        <td style='padding: 10px;'>Signed value</td>
                    </tr>
                    <tr style='border-bottom: 1px solid #dee2e6; background-color: #f8f9fa;'>
                        <td style='padding: 10px; font-weight: bold;'>Carrier Type</td>
                        <td style='padding: 10px;'><code>R<sub>Hs</sub> &lt; 0 ⇒ n-type<br>R<sub>Hs</sub> &gt; 0 ⇒ p-type</code></td>
                        <td style='padding: 10px;'>Electrons / Holes</td>
                        <td style='padding: 10px;'>Sign determined by Lorentz force</td>
                    </tr>
                    <tr style='border-bottom: 1px solid #dee2e6;'>
                        <td style='padding: 10px; font-weight: bold;'>Sheet Carrier Density (n<sub>s</sub>)</td>
                        <td style='padding: 10px;'><code>n<sub>s</sub> = 1 / (q · |R<sub>Hs</sub>|) = |I · B| / (q · |V<sub>H</sub>|)</code></td>
                        <td style='padding: 10px;'>cm⁻²</td>
                        <td style='padding: 10px;'>2D carrier density (q = 1.602×10⁻¹⁹ C)</td>
                    </tr>
                    <tr style='border-bottom: 1px solid #dee2e6; background-color: #f8f9fa;'>
                        <td style='padding: 10px; font-weight: bold;'>Bulk 3D Carrier Density (n)</td>
                        <td style='padding: 10px;'><code>n = n<sub>s</sub> / d = |I · B| / (q · |V<sub>H</sub>| · d)</code></td>
                        <td style='padding: 10px;'>cm⁻³</td>
                        <td style='padding: 10px;'>d = sample thickness in cm</td>
                    </tr>
                    <tr style='border-bottom: 1px solid #dee2e6;'>
                        <td style='padding: 10px; font-weight: bold;'>Bulk Hall Coefficient (R<sub>H</sub>)</td>
                        <td style='padding: 10px;'><code>R<sub>H</sub> = R<sub>Hs</sub> · d = (V<sub>H</sub> · d) / (I · B)</code></td>
                        <td style='padding: 10px;'>cm³ / C &nbsp;(or m³ / C)</td>
                        <td style='padding: 10px;'>1 m³/C = 10⁶ cm³/C</td>
                    </tr>
                    <tr style='border-bottom: 1px solid #dee2e6; background-color: #f8f9fa;'>
                        <td style='padding: 10px; font-weight: bold;'>Hall Mobility (μ)</td>
                        <td style='padding: 10px;'><code>μ = (|R<sub>Hs</sub>| / R<sub>s</sub>) × 10⁴ = 1 / (q · n<sub>s</sub> · R<sub>s</sub>)</code></td>
                        <td style='padding: 10px;'>cm² / (V · s)</td>
                        <td style='padding: 10px;'>R<sub>s</sub> from van der Pauw (Ω/□)</td>
                    </tr>
                    <tr style='border-bottom: 1px solid #dee2e6;'>
                        <td style='padding: 10px; font-weight: bold;'>Bulk Resistivity (ρ)</td>
                        <td style='padding: 10px;'><code>ρ = R<sub>s</sub> · d</code></td>
                        <td style='padding: 10px;'>Ω · cm</td>
                        <td style='padding: 10px;'>R<sub>s</sub> in Ω/□, d in cm</td>
                    </tr>
                </tbody>
            </table>

            <h3 style='color: #343a40;'>2. van der Pauw Method for Sheet Resistance</h3>
            <p style='font-size: 14px; line-height: 1.6;'>
                For an arbitrary flat sample with 4 peripheral contacts, the sheet resistance <code>R<sub>s</sub></code> satisfies:
            </p>
            <div style='background-color: #f1f3f5; padding: 10px 16px; border-radius: 5px; font-size: 15px; font-family: monospace;'>
                exp(-π · R<sub>h</sub> / R<sub>s</sub>) + exp(-π · R<sub>v</sub> / R<sub>s</sub>) = 1
            </div>
            <p style='font-size: 14px; line-height: 1.6; margin-top: 8px;'>
                The application uses Brent's root-finding algorithm to solve this transcendental equation to high precision.
            </p>

            <h3 style='color: #343a40; margin-top: 20px;'>3. Misalignment Voltage & Drift Cancellation</h3>
            <p style='font-size: 14px; line-height: 1.6;'>
                Due to unavoidable geometric contact asymmetry, the transverse voltage contains an Ohmic misalignment voltage 
                <code>V<sub>offset</sub> = I · R<sub>misalign</sub></code>. Because Hall voltage is odd in B (<code>V<sub>H</sub>(-B) = -V<sub>H</sub>(+B)</code>) 
                while offset voltage is even in B, reversing the magnetic field cleanly eliminates the offset:
            </p>
            <div style='background-color: #f1f3f5; padding: 10px 16px; border-radius: 5px; font-size: 15px; font-family: monospace;'>
                V<sub>H</sub> = [ ΔV(+B) - ΔV(-B) ] / 2
            </div>
        </div>
        """
        physics_browser.setHtml(physics_html)
        p_layout.addWidget(physics_browser)
        tabs.addTab(tab_physics, "📐 Physical Check & Theory")

        d_layout.addWidget(tabs)
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        btn_close.setFixedWidth(100)
        btn_close.setStyleSheet("padding: 6px 16px; font-size: 13px;")
        d_layout.addWidget(btn_close, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        dialog.exec()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    window = HallDesktopApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
