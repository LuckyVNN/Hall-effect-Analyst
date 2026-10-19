"""
app.py - Streamlit application for Hall effect measurement data analysis.
Features:
  - Initial datapoint spike exclusion (clips initial switching transients)
  - Van der Pauw sheet resistance (Rh & Rv inputs with numerical solver)
  - Updated defaults: B = 0.4264 T, Thickness = 20 nm
  - Optimized region selection: Numeric step inputs + quick shift/nudge buttons + pulse presets
  - Local Pulse Zoom toggle for high-resolution inspection
  - Option A: 3-Zone Range Brushing (Pre-baseline, Pulse plateau, Post-baseline linear fit)
  - Option B: 2-Point Digital Ruler (Point A to Point B baseline extrapolation)
  - Denoise filter (Savitzky-Golay) & Baseline Drift Flattening (horizontal at 0V)
  - Auto-detection of horizontal & vertical CSV layouts
  - Real-time physical parameter extraction (RH, ns, n, mobility, resistivity, carrier type)
  - Session measurement log with one-click Excel and CSV export
"""

import os
import glob
import io
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

import hall_core

# Page configuration
st.set_page_config(
    page_title="Hall Effect Measurement Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for high readability and scientific polish
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 10px;
    }
    .badge-n {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 1.1em;
    }
    .badge-p {
        background-color: #cfe2ff;
        color: #084298;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 1.1em;
    }
    .stNumberInput div label {
        font-size: 0.85em;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for measurement log and region settings
if "measurement_log" not in st.session_state:
    st.session_state.measurement_log = []

# Region memory in session state
if "opt_a_b1_start" not in st.session_state:
    st.session_state.opt_a_b1_start = 10.0
    st.session_state.opt_a_b1_end = 20.0
    st.session_state.opt_a_p_start = 35.0
    st.session_state.opt_a_p_end = 50.0
    st.session_state.opt_a_b2_start = 65.0
    st.session_state.opt_a_b2_end = 75.0

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🔬 Hall Analyzer")

# 1. File Selection
st.sidebar.subheader("1. Data Source")
file_mode = st.sidebar.radio("Input method:", ["Local Workspace CSV", "Upload CSV File"])

raw_t = None
raw_v = None
active_filename = "No file loaded"

local_csvs = glob.glob(os.path.join(os.getcwd(), "*.csv"))

if file_mode == "Local Workspace CSV":
    if local_csvs:
        csv_basenames = [os.path.basename(f) for f in local_csvs]
        selected_file = st.sidebar.selectbox("Select CSV file:", csv_basenames)
        active_filename = selected_file
        full_path = os.path.join(os.getcwd(), selected_file)
        try:
            raw_t, raw_v = hall_core.parse_hall_csv(full_path)
        except Exception as e:
            st.sidebar.error(f"Error loading file: {e}")
    else:
        st.sidebar.info("No CSV files found in current directory.")
else:
    uploaded = st.sidebar.file_uploader("Upload CSV file:", type=["csv", "txt"])
    if uploaded is not None:
        active_filename = uploaded.name
        try:
            raw_t, raw_v = hall_core.parse_hall_csv(uploaded)
        except Exception as e:
            st.sidebar.error(f"Error parsing uploaded file: {e}")

if raw_t is None:
    st.info("👋 Welcome! Please select or upload a Hall measurement CSV file from the sidebar to begin.")
    st.stop()

# 2. Initial Spike Exclusion
st.sidebar.subheader("2. Spike Exclusion")
total_points_loaded = len(raw_t)
skip_points = st.sidebar.number_input(
    "Exclude initial datapoints:",
    min_value=0,
    max_value=min(200, total_points_loaded - 10),
    value=10,
    step=1,
    help="Removes initial instrument transient spikes (e.g. current turn-on voltage) so they do not distort the plot scale."
)

if skip_points > 0:
    time_skipped_s = (raw_t[skip_points] - raw_t[0]) / 1000.0 if skip_points < len(raw_t) else 0.0
    st.sidebar.caption(f"⚡ Skipping first **{skip_points} points** (0 to {time_skipped_s:.2f} s)")
    raw_t = raw_t[skip_points:]
    raw_v = raw_v[skip_points:]

t_sec = raw_t / 1000.0
t_min_s = float(t_sec[0])
t_max_s = float(t_sec[-1])

# 3. Experimental Parameters
st.sidebar.subheader("3. Sample & Field Parameters")

# Magnetic field (Default 0.4264 T as requested)
field_t = st.sidebar.number_input("Magnetic Field B (T):", value=0.4264, step=0.01, format="%.4f")

# Current input
col_curr, col_unit_curr = st.sidebar.columns([2, 1])
with col_curr:
    default_curr = 100.0
    if "200uA" in active_filename:
        default_curr = 200.0
    elif "100uA" in active_filename:
        default_curr = 100.0
    current_val = st.number_input("Current (I):", value=default_curr, format="%.2f")
with col_unit_curr:
    current_unit = st.selectbox("Unit:", ["µA", "mA", "A"])

curr_mult = {"µA": 1e-6, "mA": 1e-3, "A": 1.0}
current_a = current_val * curr_mult[current_unit]

# Thickness input (Default 20 nm as requested)
col_thick_val, col_thick_unit = st.sidebar.columns([2, 1])
with col_thick_val:
    thick_val = st.number_input("Thickness (d):", value=20.0, step=1.0, format="%.1f")
with col_thick_unit:
    thick_unit = st.selectbox("Unit:", ["nm", "µm", "mm", "cm"], index=0)

thick_mult = {"nm": 1e-9, "µm": 1e-6, "mm": 1e-3, "cm": 1e-2}
thickness_m = thick_val * thick_mult[thick_unit]

# 4. Van der Pauw Sheet Resistance Input
st.sidebar.subheader("4. Sheet Resistance (Rs)")
rs_mode = st.sidebar.radio("Resistance Input Mode:", ["van der Pauw (Rh & Rv)", "Direct Rs Input"])

sheet_res_ohm = None
vdp_ratio = None

if rs_mode == "van der Pauw (Rh & Rv)":
    col_rh, col_rv = st.sidebar.columns(2)
    with col_rh:
        rh_val = st.number_input("R horizontal (Ω):", value=250.0, step=10.0, format="%.2f")
    with col_rv:
        rv_val = st.number_input("R vertical (Ω):", value=250.0, step=10.0, format="%.2f")

    if rh_val > 0 and rv_val > 0:
        solved_rs, vdp_ratio = hall_core.solve_van_der_pauw(rh_val, rv_val)
        sheet_res_ohm = solved_rs
        st.sidebar.markdown(f"**Solved Rs:** `{sheet_res_ohm:.2f} Ω/□`")
        if vdp_ratio > 1.2:
            st.sidebar.caption(f"⚠️ Asymmetry ratio: {vdp_ratio:.2f}")
        else:
            st.sidebar.caption(f"✅ Symmetry ratio: {vdp_ratio:.2f}")
else:
    sheet_res_ohm = st.sidebar.number_input("Sheet Resistance Rs (Ω/□):", value=1133.0, step=50.0, format="%.1f")

# 5. Denoising & Baseline Flattening
st.sidebar.subheader("5. Signal Preprocessing")
apply_denoise = st.sidebar.checkbox("Enable Savitzky-Golay Filter", value=True, help="Removes instrument jitter while preserving sharp step edges")
denoise_window = 15
if apply_denoise:
    denoise_window = st.sidebar.slider("Denoise Window (points):", min_value=5, max_value=51, value=15, step=2)

v_active = hall_core.apply_denoising(raw_v, window_length=denoise_window) if apply_denoise else raw_v.copy()

flatten_baseline_view = st.sidebar.checkbox(
    "Flatten Baseline (Horizontal Line at 0V)",
    value=False,
    help="Subtracts linear baseline drift so the baseline lies horizontally at 0V, allowing direct visual readout of Hall step height."
)

# --- MAIN APP AREA ---
st.title("🔬 Hall Effect Measurement Analyzer")
st.caption(f"Loaded: **{active_filename}** ({len(raw_t):,} points, {t_max_s:.1f} s duration) | B = **{field_t:.4f} T** | d = **{thick_val} {thick_unit}**")

# Mode Selection Tabs
tab_a, tab_b, tab_summary, tab_log = st.tabs([
    "📐 Option A: 3-Zone Range Fit",
    "📏 Option B: 2-Point Digital Ruler",
    "📊 Multi-Pulse Full Run Summary",
    "📋 Session Log & Export"
])

# -------------------------------------------------------------
# TAB 1: OPTION A (3-Zone Interval Range Brushing)
# -------------------------------------------------------------
with tab_a:
    st.markdown("### Option A: 3-Zone Baseline Drift Compensation")

    # Quick preset selection buttons to make region setting effortless
    st.markdown("##### ⚡ Quick Pulse Presets:")
    cp1, cp2, cp3, cp_zoom = st.columns([1, 1, 1, 1.5])

    if cp1.button("📍 Set to Pulse 1 (+B) ~30–55s"):
        st.session_state.opt_a_b1_start = max(t_min_s, 10.0)
        st.session_state.opt_a_b1_end = 20.0
        st.session_state.opt_a_p_start = 35.0
        st.session_state.opt_a_p_end = 50.0
        st.session_state.opt_a_b2_start = 65.0
        st.session_state.opt_a_b2_end = 75.0
        st.rerun()

    if cp2.button("📍 Set to Pulse 2 (-B) ~85–115s"):
        st.session_state.opt_a_b1_start = 65.0
        st.session_state.opt_a_b1_end = 75.0
        st.session_state.opt_a_p_start = 90.0
        st.session_state.opt_a_p_end = 110.0
        st.session_state.opt_a_b2_start = 125.0
        st.session_state.opt_a_b2_end = 135.0
        st.rerun()

    if cp3.button("📍 Set to Pulse 3 (+B) ~145–175s"):
        st.session_state.opt_a_b1_start = 125.0
        st.session_state.opt_a_b1_end = 135.0
        st.session_state.opt_a_p_start = 150.0
        st.session_state.opt_a_p_end = 170.0
        st.session_state.opt_a_b2_start = 185.0
        st.session_state.opt_a_b2_end = min(t_max_s, 195.0)
        st.rerun()

    with cp_zoom:
        zoom_to_pulse = st.checkbox("🔍 Zoom View to Pulse Neighborhood", value=False, help="Zooms the chart x-axis directly around the active pulse and baselines")

    # Optimized Region Setting Controls (Numeric Inputs with +/- Step Buttons)
    st.markdown("##### 🎯 Region Time Boundaries (Seconds):")
    col_ctrl_b1, col_ctrl_p, col_ctrl_b2 = st.columns(3)

    with col_ctrl_b1:
        st.markdown("**🟢 Baseline 1 (Pre-Pulse)**")
        c_b1_s, c_b1_e = st.columns(2)
        with c_b1_s:
            b1_start = st.number_input("Start (s)", min_value=t_min_s, max_value=t_max_s, value=float(st.session_state.opt_a_b1_start), step=0.5, key="num_a_b1_s")
        with c_b1_e:
            b1_end = st.number_input("End (s)", min_value=t_min_s, max_value=t_max_s, value=float(st.session_state.opt_a_b1_end), step=0.5, key="num_a_b1_e")

    with col_ctrl_p:
        st.markdown("**🟠 Pulse Plateau (B ON)**")
        c_p_s, c_p_e = st.columns(2)
        with c_p_s:
            p_start = st.number_input("Start (s)", min_value=t_min_s, max_value=t_max_s, value=float(st.session_state.opt_a_p_start), step=0.5, key="num_a_p_s")
        with c_p_e:
            p_end = st.number_input("End (s)", min_value=t_min_s, max_value=t_max_s, value=float(st.session_state.opt_a_p_end), step=0.5, key="num_a_p_e")

    with col_ctrl_b2:
        st.markdown("**🟢 Baseline 2 (Post-Pulse)**")
        c_b2_s, c_b2_e = st.columns(2)
        with c_b2_s:
            b2_start = st.number_input("Start (s)", min_value=t_min_s, max_value=t_max_s, value=float(st.session_state.opt_a_b2_start), step=0.5, key="num_a_b2_s")
        with c_b2_e:
            b2_end = st.number_input("End (s)", min_value=t_min_s, max_value=t_max_s, value=float(st.session_state.opt_a_b2_end), step=0.5, key="num_a_b2_e")

    # Quick Nudge Bar for fine adjustment
    col_nudge1, col_nudge2, col_nudge3, col_nudge4 = st.columns(4)
    if col_nudge1.button("◀ Shift Pulse Left (1s)"):
        st.session_state.opt_a_p_start = max(t_min_s, p_start - 1.0)
        st.session_state.opt_a_p_end = max(t_min_s + 1.0, p_end - 1.0)
        st.rerun()
    if col_nudge2.button("▶ Shift Pulse Right (1s)"):
        st.session_state.opt_a_p_start = min(t_max_s - 1.0, p_start + 1.0)
        st.session_state.opt_a_p_end = min(t_max_s, p_end + 1.0)
        st.rerun()
    if col_nudge3.button("➕ Expand Pulse (±0.5s)"):
        st.session_state.opt_a_p_start = max(t_min_s, p_start - 0.5)
        st.session_state.opt_a_p_end = min(t_max_s, p_end + 0.5)
        st.rerun()
    if col_nudge4.button("➖ Narrow Pulse (±0.5s)"):
        if (p_end - p_start) > 2.0:
            st.session_state.opt_a_p_start = p_start + 0.5
            st.session_state.opt_a_p_end = p_end - 0.5
            st.rerun()

    # Convert to ms
    range_a_b1_ms = (b1_start * 1000.0, b1_end * 1000.0)
    range_a_p_ms = (p_start * 1000.0, p_end * 1000.0)
    range_a_b2_ms = (b2_start * 1000.0, b2_end * 1000.0)

    res_a = hall_core.calc_option_a_3zone(raw_t, v_active, range_a_b1_ms, range_a_p_ms, range_a_b2_ms)

    if res_a is not None:
        fig_a = go.Figure()

        if flatten_baseline_view:
            v_flat = hall_core.compute_flattened_curve(raw_t, v_active, res_a["slope"], res_a["intercept"]) * 1e3
            fig_a.add_trace(go.Scatter(
                x=t_sec, y=v_flat, mode="lines", name="Flattened Voltage (mV)",
                line=dict(color="#1f77b4", width=1.5)
            ))
            fig_a.add_hline(y=0.0, line_dash="dash", line_color="black", annotation_text="Baseline (0 mV)")
            fig_a.add_hrect(
                y0=res_a["v_hall"] * 1e3, y1=res_a["v_hall"] * 1e3,
                line=dict(color="red", width=2, dash="dot"),
                annotation_text=f"V_H = {res_a['v_hall']*1e3:.4f} mV"
            )
            y_title = "Flattened Voltage ΔV (mV)"
        else:
            v_display_mv = v_active * 1e3
            raw_display_mv = raw_v * 1e3
            if apply_denoise:
                fig_a.add_trace(go.Scatter(
                    x=t_sec, y=raw_display_mv, mode="lines", name="Raw Voltage",
                    line=dict(color="#cccccc", width=1), opacity=0.6
                ))
            fig_a.add_trace(go.Scatter(
                x=t_sec, y=v_display_mv, mode="lines", name="Measured Voltage (mV)",
                line=dict(color="#1f77b4", width=2)
            ))

            # Draw extrapolated linear baseline
            t_span_s = res_a["t_span"] / 1000.0
            v_span_mv = res_a["v_span"] * 1e3
            fig_a.add_trace(go.Scatter(
                x=t_span_s, y=v_span_mv, mode="lines", name="Fitted Baseline Drift",
                line=dict(color="#e377c2", width=2.5, dash="dash")
            ))

            # Vertical delta line at mid-pulse
            fig_a.add_trace(go.Scatter(
                x=[res_a["t_mid"] / 1000.0, res_a["t_mid"] / 1000.0],
                y=[res_a["v_base_mid"] * 1e3, res_a["v_pulse_mid"] * 1e3],
                mode="lines+markers",
                name="ΔV Step (V_Hall)",
                line=dict(color="red", width=3)
            ))
            y_title = "Voltage (mV)"

        # Highlight regions
        fig_a.add_vrect(x0=b1_start, x1=b1_end, fillcolor="#2ca02c", opacity=0.18, line_width=1, annotation_text="Base 1")
        fig_a.add_vrect(x0=p_start, x1=p_end, fillcolor="#ff7f0e", opacity=0.22, line_width=1, annotation_text="Pulse")
        fig_a.add_vrect(x0=b2_start, x1=b2_end, fillcolor="#2ca02c", opacity=0.18, line_width=1, annotation_text="Base 2")

        # Range zoom
        x_range = None
        if zoom_to_pulse:
            x_pad = 10.0
            x_range = [max(t_min_s, b1_start - x_pad), min(t_max_s, b2_end + x_pad)]

        fig_a.update_layout(
            title="Option A: 3-Zone Range Selection & Linear Baseline Fit",
            xaxis_title="Time (s)",
            yaxis_title=y_title,
            xaxis=dict(range=x_range) if x_range else dict(),
            hovermode="x unified",
            margin=dict(l=40, r=40, t=50, b=40),
            height=420
        )
        st.plotly_chart(fig_a, use_container_width=True)

        # Physics Calculations Card
        phys_a = hall_core.calc_hall_physics(res_a["v_hall"], current_a, field_t, thickness_m, sheet_res_ohm)

        st.markdown("#### 📐 Extracted Results & Physical Parameters")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("V_Hall", f"{res_a['v_hall']*1e3:.4f} mV", f"± {res_a['v_hall_std']*1e3:.4f} mV")
            st.caption(f"In µV: **{res_a['v_hall']*1e6:.1f} µV**")
        with c2:
            badge_class = "badge-n" if phys_a["is_n_type"] else "badge-p"
            st.markdown(f"**Carrier Type:**<br><span class='{badge_class}'>{phys_a['carrier_type']}</span>", unsafe_allow_html=True)
            st.caption(f"Drift: {res_a['slope_v_per_s']*1e6:.2f} µV/s")
        with c3:
            st.metric("Sheet Density (ns)", f"{phys_a['ns_cm2']:.3e} cm⁻²")
            st.caption(f"R_Hs: {phys_a['r_hs_si']:.2f} Ω/T")
        with c4:
            if phys_a["n_bulk_cm3"] is not None:
                st.metric("Bulk Density (n)", f"{phys_a['n_bulk_cm3']:.3e} cm⁻³")
                st.caption(f"RH: {phys_a['r_h_cm3_c']:.3e} cm³/C")
            else:
                st.info("Set thickness for 3D n")
        with c5:
            if phys_a["mobility_cm2_vs"] is not None:
                st.metric("Hall Mobility (μ)", f"{phys_a['mobility_cm2_vs']:.1f} cm²/V·s")
                if phys_a["resistivity_ohm_cm"]:
                    st.caption(f"ρ: {phys_a['resistivity_ohm_cm']:.3e} Ω·cm")
            else:
                st.info("Set Rs for Mobility")

        if st.button("💾 Save Option A Result to Session Log", key="save_a"):
            st.session_state.measurement_log.append({
                "File": active_filename,
                "Method": "Option A (3-Zone)",
                "Pulse Time (s)": f"{p_start:.1f}-{p_end:.1f}",
                "V_Hall (mV)": round(res_a["v_hall"] * 1e3, 4),
                "V_Hall (µV)": round(res_a["v_hall"] * 1e6, 2),
                "Carrier Type": phys_a["carrier_type"],
                "ns (cm^-2)": f"{phys_a['ns_cm2']:.3e}",
                "n_bulk (cm^-3)": f"{phys_a['n_bulk_cm3']:.3e}" if phys_a['n_bulk_cm3'] else "N/A",
                "Mobility (cm^2/Vs)": f"{phys_a['mobility_cm2_vs']:.1f}" if phys_a['mobility_cm2_vs'] else "N/A",
                "Rs (Ohm/sq)": f"{sheet_res_ohm:.1f}" if sheet_res_ohm else "N/A",
                "Current": f"{current_val} {current_unit}",
                "Field (T)": field_t,
                "Thickness": f"{thick_val} {thick_unit}"
            })
            st.success("✅ Measurement logged successfully! View in the 'Session Log & Export' tab.")
    else:
        st.warning("Please ensure each selected region contains at least 2 data points.")

# -------------------------------------------------------------
# TAB 2: OPTION B (2-Point Digital Ruler)
# -------------------------------------------------------------
with tab_b:
    st.markdown("### Option B: 2-Point Digital Ruler")
    st.write("Pick **Anchor Point A (pre-pulse)** and **Anchor Point B (post-pulse)** on the baseline. The app draws a straight line connecting them (like laying a physical ruler) and measures the vertical distance to the pulse plateau.")

    col_b_a, col_b_p, col_b_b = st.columns(3)
    with col_b_a:
        st.markdown("**📍 Anchor Point A (Pre-Pulse)**")
        t_a_s = st.number_input("Time A (s):", value=max(t_min_s, 15.0), min_value=t_min_s, max_value=t_max_s, step=0.5, key="num_b_a")
    with col_b_p:
        st.markdown("**🟠 Pulse Plateau Range**")
        cp_b_s, cp_b_e = st.columns(2)
        with cp_b_s:
            p_b_start = st.number_input("Start (s)", min_value=t_min_s, max_value=t_max_s, value=35.0, step=0.5, key="num_b_ps")
        with cp_b_e:
            p_b_end = st.number_input("End (s)", min_value=t_min_s, max_value=t_max_s, value=50.0, step=0.5, key="num_b_pe")
    with col_b_b:
        st.markdown("**📍 Anchor Point B (Post-Pulse)**")
        t_b_s = st.number_input("Time B (s):", value=min(t_max_s, 70.0), min_value=t_min_s, max_value=t_max_s, step=0.5, key="num_b_b")

    t_a_ms = t_a_s * 1000.0
    t_b_ms = t_b_s * 1000.0
    range_b_p_ms = (p_b_start * 1000.0, p_b_end * 1000.0)

    res_b = hall_core.calc_option_b_2point(raw_t, v_active, t_a_ms, t_b_ms, range_b_p_ms)

    if res_b is not None:
        fig_b = go.Figure()

        if flatten_baseline_view:
            v_flat = hall_core.compute_flattened_curve(raw_t, v_active, res_b["slope"], res_b["intercept"]) * 1e3
            fig_b.add_trace(go.Scatter(
                x=t_sec, y=v_flat, mode="lines", name="Flattened Voltage (mV)",
                line=dict(color="#1f77b4", width=1.5)
            ))
            fig_b.add_hline(y=0.0, line_dash="dash", line_color="black", annotation_text="Baseline (0 mV)")
            fig_b.add_hrect(
                y0=res_b["v_hall"] * 1e3, y1=res_b["v_hall"] * 1e3,
                line=dict(color="red", width=2, dash="dot"),
                annotation_text=f"V_H = {res_b['v_hall']*1e3:.4f} mV"
            )
            y_title = "Flattened Voltage ΔV (mV)"
        else:
            if apply_denoise:
                fig_b.add_trace(go.Scatter(
                    x=t_sec, y=raw_v * 1e3, mode="lines", name="Raw Voltage",
                    line=dict(color="#cccccc", width=1), opacity=0.6
                ))
            fig_b.add_trace(go.Scatter(
                x=t_sec, y=v_active * 1e3, mode="lines", name="Measured Voltage (mV)",
                line=dict(color="#1f77b4", width=2)
            ))

            # Ruler line
            t_span_s = res_b["t_span"] / 1000.0
            v_span_mv = res_b["v_span"] * 1e3
            fig_b.add_trace(go.Scatter(
                x=t_span_s, y=v_span_mv, mode="lines", name="Digital Ruler Line",
                line=dict(color="#d62728", width=2.5, dash="dash")
            ))

            # Anchor markers A and B
            fig_b.add_trace(go.Scatter(
                x=[res_b["t_a"] / 1000.0, res_b["t_b"] / 1000.0],
                y=[res_b["v_a"] * 1e3, res_b["v_b"] * 1e3],
                mode="markers+text",
                name="Anchor Points",
                text=["Anchor A", "Anchor B"],
                textposition="top center",
                marker=dict(size=10, color="#d62728", symbol="diamond")
            ))

            # Vertical delta line at mid-pulse
            fig_b.add_trace(go.Scatter(
                x=[res_b["t_mid"] / 1000.0, res_b["t_mid"] / 1000.0],
                y=[res_b["v_base_mid"] * 1e3, res_b["v_pulse_mid"] * 1e3],
                mode="lines+markers",
                name="ΔV Step",
                line=dict(color="red", width=3)
            ))
            y_title = "Voltage (mV)"

        fig_b.add_vrect(x0=p_b_start, x1=p_b_end, fillcolor="#ff7f0e", opacity=0.22, line_width=1, annotation_text="Pulse")

        fig_b.update_layout(
            title=f"Option B: 2-Point Ruler Connecting ({res_b['t_a']/1000:.1f} s, {res_b['v_a']*1e3:.3f} mV) and ({res_b['t_b']/1000:.1f} s, {res_b['v_b']*1e3:.3f} mV)",
            xaxis_title="Time (s)",
            yaxis_title=y_title,
            hovermode="x unified",
            margin=dict(l=40, r=40, t=50, b=40),
            height=420
        )
        st.plotly_chart(fig_b, use_container_width=True)

        phys_b = hall_core.calc_hall_physics(res_b["v_hall"], current_a, field_t, thickness_m, sheet_res_ohm)

        st.markdown("#### 📏 Extracted Results & Physical Parameters")
        cb1, cb2, cb3, cb4, cb5 = st.columns(5)
        with cb1:
            st.metric("V_Hall", f"{res_b['v_hall']*1e3:.4f} mV", f"± {res_b['v_hall_std']*1e3:.4f} mV")
            st.caption(f"In µV: **{res_b['v_hall']*1e6:.1f} µV**")
        with cb2:
            badge_class = "badge-n" if phys_b["is_n_type"] else "badge-p"
            st.markdown(f"**Carrier Type:**<br><span class='{badge_class}'>{phys_b['carrier_type']}</span>", unsafe_allow_html=True)
            st.caption(f"Drift: {res_b['slope_v_per_s']*1e6:.2f} µV/s")
        with cb3:
            st.metric("Sheet Density (ns)", f"{phys_b['ns_cm2']:.3e} cm⁻²")
            st.caption(f"R_Hs: {phys_b['r_hs_si']:.2f} Ω/T")
        with cb4:
            if phys_b["n_bulk_cm3"] is not None:
                st.metric("Bulk Density (n)", f"{phys_b['n_bulk_cm3']:.3e} cm⁻³")
                st.caption(f"RH: {phys_b['r_h_cm3_c']:.3e} cm³/C")
            else:
                st.info("Set thickness for 3D n")
        with cb5:
            if phys_b["mobility_cm2_vs"] is not None:
                st.metric("Hall Mobility (μ)", f"{phys_b['mobility_cm2_vs']:.1f} cm²/V·s")
                if phys_b["resistivity_ohm_cm"]:
                    st.caption(f"ρ: {phys_b['resistivity_ohm_cm']:.3e} Ω·cm")
            else:
                st.info("Set Rs for Mobility")

        if st.button("💾 Save Option B Result to Session Log", key="save_b"):
            st.session_state.measurement_log.append({
                "File": active_filename,
                "Method": "Option B (2-Point Ruler)",
                "Pulse Time (s)": f"{p_b_start:.1f}-{p_b_end:.1f}",
                "V_Hall (mV)": round(res_b["v_hall"] * 1e3, 4),
                "V_Hall (µV)": round(res_b["v_hall"] * 1e6, 2),
                "Carrier Type": phys_b["carrier_type"],
                "ns (cm^-2)": f"{phys_b['ns_cm2']:.3e}",
                "n_bulk (cm^-3)": f"{phys_b['n_bulk_cm3']:.3e}" if phys_b['n_bulk_cm3'] else "N/A",
                "Mobility (cm^2/Vs)": f"{phys_b['mobility_cm2_vs']:.1f}" if phys_b['mobility_cm2_vs'] else "N/A",
                "Rs (Ohm/sq)": f"{sheet_res_ohm:.1f}" if sheet_res_ohm else "N/A",
                "Current": f"{current_val} {current_unit}",
                "Field (T)": field_t,
                "Thickness": f"{thick_val} {thick_unit}"
            })
            st.success("✅ Measurement logged successfully! View in the 'Session Log & Export' tab.")

# -------------------------------------------------------------
# TAB 3: FULL RUN SUMMARY (7-STAGE 0 -> +B -> 0 -> -B -> 0 -> +B -> 0)
# -------------------------------------------------------------
with tab_summary:
    st.markdown("### 📊 Multi-Pulse Analysis (0 → +B → 0 → -B → 0 → +B → 0)")
    st.write("Calculates all three pulses simultaneously to cancel out both misalignment offset and baseline drift.")

    # Calculate 3 pulses with 3-zone fit
    p1 = hall_core.calc_option_a_3zone(raw_t, v_active, (max(t_min_s*1000, 10000), 20000), (35000, 50000), (65000, 75000))
    p2 = hall_core.calc_option_a_3zone(raw_t, v_active, (65000, 75000), (90000, 110000), (125000, 135000))
    p3 = hall_core.calc_option_a_3zone(raw_t, v_active, (125000, 135000), (150000, 170000), (185000, min(t_max_s*1000, 195000)))

    if p1 and p2 and p3:
        v1 = p1["v_hall"]
        v2 = p2["v_hall"]
        v3 = p3["v_hall"]
        # Standard combined Hall formula: ( (V(+B)_1 + V(+B)_2)/2 - V(-B) ) / 2
        v_h_combined = 0.5 * (((v1 + v3) / 2.0) - v2)
        phys_comb = hall_core.calc_hall_physics(v_h_combined, current_a, field_t, thickness_m, sheet_res_ohm)

        col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
        with col_sum1:
            st.metric("Pulse 1 (+B)", f"{v1*1e3:.4f} mV", f"{v1*1e6:.1f} µV")
        with col_sum2:
            st.metric("Pulse 2 (-B)", f"{v2*1e3:.4f} mV", f"{v2*1e6:.1f} µV")
        with col_sum3:
            st.metric("Pulse 3 (+B)", f"{v3*1e3:.4f} mV", f"{v3*1e6:.1f} µV")
        with col_sum4:
            st.metric("Combined V_Hall", f"{v_h_combined*1e3:.4f} mV", f"{v_h_combined*1e6:.1f} µV")

        st.markdown(f"**Combined Carrier Type:** `{phys_comb['carrier_type']}` | **Sheet Density ns:** `{phys_comb['ns_cm2']:.3e} cm⁻²` | **Bulk Density n:** `{phys_comb['n_bulk_cm3']:.3e} cm⁻³` | **Mobility μ:** `{phys_comb['mobility_cm2_vs']:.1f} cm²/V·s`")

        if st.button("💾 Save Combined 3-Pulse Result to Session Log"):
            st.session_state.measurement_log.append({
                "File": active_filename,
                "Method": "Combined 3-Pulse Sequence",
                "Pulse Time (s)": "30-50, 90-110, 150-170",
                "V_Hall (mV)": round(v_h_combined * 1e3, 4),
                "V_Hall (µV)": round(v_h_combined * 1e6, 2),
                "Carrier Type": phys_comb["carrier_type"],
                "ns (cm^-2)": f"{phys_comb['ns_cm2']:.3e}",
                "n_bulk (cm^-3)": f"{phys_comb['n_bulk_cm3']:.3e}" if phys_comb['n_bulk_cm3'] else "N/A",
                "Mobility (cm^2/Vs)": f"{phys_comb['mobility_cm2_vs']:.1f}" if phys_comb['mobility_cm2_vs'] else "N/A",
                "Rs (Ohm/sq)": f"{sheet_res_ohm:.1f}" if sheet_res_ohm else "N/A",
                "Current": f"{current_val} {current_unit}",
                "Field (T)": field_t,
                "Thickness": f"{thick_val} {thick_unit}"
            })
            st.success("✅ Combined multi-pulse measurement logged successfully!")

# -------------------------------------------------------------
# TAB 4: SESSION LOG & EXPORT
# -------------------------------------------------------------
with tab_log:
    st.markdown("### 📋 Session Measurement Log & Export")
    if st.session_state.measurement_log:
        df_log = pd.DataFrame(st.session_state.measurement_log)
        st.dataframe(df_log, use_container_width=True)

        col_dl1, col_dl2, col_clear = st.columns([1, 1, 2])
        with col_dl1:
            csv_data = df_log.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV Summary", csv_data, "Hall_Effect_Summary.csv", "text/csv")
        with col_dl2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_log.to_excel(writer, index=False, sheet_name="Hall_Results")
            st.download_button("📥 Download Excel (.xlsx)", buffer.getvalue(), "Hall_Effect_Summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_clear:
            if st.button("🗑️ Clear Log"):
                st.session_state.measurement_log = []
                st.rerun()
    else:
        st.info("No measurements logged in this session yet. Calculate a pulse in Option A, Option B, or Multi-Pulse and click 'Save to Session Log'.")
