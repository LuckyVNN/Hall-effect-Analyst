"""
hall_core.py - Core physical and numerical calculation engine for Hall effect analysis.
Supports automatic CSV parsing (both horizontal row-based and vertical column-based),
signal denoising (Savitzky-Golay), baseline drift subtraction (horizontal flattening),
and physical parameter calculations (RH, ns, n, mobility, carrier type).
"""

import io
import os
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.stats import linregress

# Physical constants
E_CHARGE = 1.602176634e-19  # Coulombs


def parse_hall_csv(file_source):
    """
    Parses a Hall effect CSV file from file path or file-like buffer.
    Automatically identifies whether data is formatted as:
      - Horizontal (Row 1: Time in ms, Row 2: Voltage in V)
      - Vertical (Col 1: Time in ms, Col 2: Voltage in V)
    Returns:
      t (np.ndarray in ms), v (np.ndarray in V), filename/label (str)
    """
    if isinstance(file_source, str):
        with open(file_source, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]
    elif hasattr(file_source, "read"):
        content = file_source.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")
        lines = [line.strip() for line in content.splitlines() if line.strip()]
    else:
        raise ValueError("Unsupported file source")

    if not lines:
        raise ValueError("The provided file is empty.")

    # Check if horizontal format (2 or 3 lines total with many comma-separated values)
    first_line_parts = lines[0].split(",")
    if len(lines) <= 4 and len(first_line_parts) > 10:
        t_vals = [float(x.strip()) for x in lines[0].split(",") if x.strip()]
        v_vals = [float(x.strip()) for x in lines[1].split(",") if x.strip()]
        t = np.array(t_vals, dtype=float)
        v = np.array(v_vals, dtype=float)
        # Match lengths if slight discrepancy
        min_len = min(len(t), len(v))
        return t[:min_len], v[:min_len]

    # Otherwise vertical format (Time, Voltage per row)
    t_vals = []
    v_vals = []
    for line in lines:
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) >= 2:
            try:
                val_t = float(parts[0])
                val_v = float(parts[1])
                t_vals.append(val_t)
                v_vals.append(val_v)
            except ValueError:
                # Header row or comment
                continue

    if not t_vals:
        raise ValueError("Could not extract Time and Voltage numeric columns from CSV.")

    return np.array(t_vals, dtype=float), np.array(v_vals, dtype=float)


def apply_denoising(v, window_length=15, polyorder=2):
    """
    Denoise voltage signal using Savitzky-Golay filter.
    Savitzky-Golay is ideal because it smooths noise while preserving step edges.
    """
    if len(v) < 7:
        return v.copy()
    # Window length must be odd and <= len(v)
    w = max(5, int(window_length))
    if w % 2 == 0:
        w += 1
    if w >= len(v):
        w = len(v) - 1 if (len(v) - 1) % 2 != 0 else len(v) - 2
    p = min(polyorder, w - 1)
    return savgol_filter(v, window_length=w, polyorder=p)


def calc_option_a_3zone(t, v, range_b1, range_pulse, range_b2):
    """
    Option A: 3-Zone Range Brushing
    Fits linear drift V_base(t) = m*t + c across Baseline 1 and Baseline 2,
    then evaluates Hall voltage step across the pulse range.

    range_b1: (t_start, t_end) in ms
    range_pulse: (t_start, t_end) in ms
    range_b2: (t_start, t_end) in ms

    Returns dict with extracted parameters, fit lines, and stats.
    """
    mask_b1 = (t >= range_b1[0]) & (t <= range_b1[1])
    mask_b2 = (t >= range_b2[0]) & (t <= range_b2[1])
    mask_pulse = (t >= range_pulse[0]) & (t <= range_pulse[1])

    if np.sum(mask_b1) < 2 or np.sum(mask_b2) < 2 or np.sum(mask_pulse) < 1:
        return None

    # Baseline points pooled from both regions
    t_base = np.concatenate([t[mask_b1], t[mask_b2]])
    v_base = np.concatenate([v[mask_b1], v[mask_b2]])

    # Linear regression on baseline drift
    res = linregress(t_base, v_base)
    slope = res.slope
    intercept = res.intercept

    # Calculated baseline across the entire pulse segment
    t_pulse = t[mask_pulse]
    v_pulse = v[mask_pulse]
    v_base_at_pulse = slope * t_pulse + intercept

    # Delta V for every point on the pulse
    delta_v_points = v_pulse - v_base_at_pulse
    v_hall = float(np.mean(delta_v_points))
    v_hall_std = float(np.std(delta_v_points))
    v_hall_sem = float(v_hall_std / np.sqrt(len(delta_v_points)))

    # Midpoint of pulse for annotation
    t_mid = float(np.mean(t_pulse))
    v_base_mid = float(slope * t_mid + intercept)
    v_pulse_mid = float(np.mean(v_pulse))

    # Baseline line for plotting across the whole span [range_b1[0], range_b2[1]]
    t_span = np.array([range_b1[0], range_b2[1]])
    v_span = slope * t_span + intercept

    return {
        "v_hall": v_hall,
        "v_hall_std": v_hall_std,
        "v_hall_sem": v_hall_sem,
        "slope_v_per_s": slope * 1000.0,
        "intercept": intercept,
        "t_mid": t_mid,
        "v_base_mid": v_base_mid,
        "v_pulse_mid": v_pulse_mid,
        "t_span": t_span,
        "v_span": v_span,
        "pulse_count": len(t_pulse),
        "mask_pulse": mask_pulse,
        "slope": slope
    }


def calc_option_b_2point(t, v, t1, t2, range_pulse):
    """
    Option B: Digital Ruler / 2-Point Baseline Line
    Passes a straight line directly through Anchor 1 (t1, V(t1)) and Anchor 2 (t2, V(t2)),
    and computes the vertical distance to the pulse plateau.

    t1: ms
    t2: ms
    range_pulse: (t_start, t_end) in ms
    """
    if abs(t2 - t1) < 1e-6:
        return None

    # Find closest points for t1 and t2
    idx1 = np.argmin(np.abs(t - t1))
    idx2 = np.argmin(np.abs(t - t2))

    t_a, v_a = t[idx1], v[idx1]
    t_b, v_b = t[idx2], v[idx2]

    slope = (v_b - v_a) / (t_b - t_a)
    intercept = v_a - slope * t_a

    mask_pulse = (t >= range_pulse[0]) & (t <= range_pulse[1])
    if np.sum(mask_pulse) < 1:
        return None

    t_pulse = t[mask_pulse]
    v_pulse = v[mask_pulse]
    v_base_at_pulse = slope * t_pulse + intercept

    delta_v_points = v_pulse - v_base_at_pulse
    v_hall = float(np.mean(delta_v_points))
    v_hall_std = float(np.std(delta_v_points))
    v_hall_sem = float(v_hall_std / np.sqrt(len(delta_v_points)))

    t_mid = float(np.mean(t_pulse))
    v_base_mid = float(slope * t_mid + intercept)
    v_pulse_mid = float(np.mean(v_pulse))

    t_span = np.array([min(t_a, range_pulse[0]), max(t_b, range_pulse[1])])
    v_span = slope * t_span + intercept

    return {
        "v_hall": v_hall,
        "v_hall_std": v_hall_std,
        "v_hall_sem": v_hall_sem,
        "slope_v_per_s": slope * 1000.0,
        "intercept": intercept,
        "t_a": t_a,
        "v_a": v_a,
        "t_b": t_b,
        "v_b": v_b,
        "t_mid": t_mid,
        "v_base_mid": v_base_mid,
        "v_pulse_mid": v_pulse_mid,
        "t_span": t_span,
        "v_span": v_span,
        "pulse_count": len(t_pulse),
        "mask_pulse": mask_pulse,
        "slope": slope
    }


def compute_flattened_curve(t, v, slope, intercept):
    """
    Subtracts the linear baseline drift V_drift(t) = slope * t + intercept
    to make the baseline completely horizontal at 0 V.
    """
    v_drift = slope * t + intercept
    return v - v_drift


from scipy.optimize import brentq


def solve_van_der_pauw(rh, rv):
    """
    Solves the van der Pauw equation for sheet resistance Rs:
        exp(-pi * Rh / Rs) + exp(-pi * Rv / Rs) = 1
    Args:
        rh (float): Horizontal resistance (Ohms)
        rv (float): Vertical resistance (Ohms)
    Returns:
        rs (float): Sheet resistance in Ohm/sq
        ratio (float): Rh / Rv symmetry ratio
    """
    if rh is None or rv is None or rh <= 0 or rv <= 0:
        return None, None

    r_avg = (rh + rv) / 2.0
    r_s_approx = (np.pi / np.log(2.0)) * r_avg

    def func(rs):
        return np.exp(-np.pi * rh / rs) + np.exp(-np.pi * rv / rs) - 1.0

    try:
        rs = brentq(func, 0.01 * r_s_approx, 50.0 * r_s_approx)
    except Exception:
        rs = r_s_approx

    ratio = max(rh, rv) / min(rh, rv)
    return float(rs), float(ratio)


def calc_hall_physics(v_hall_v, current_a, field_t, thickness_m, sheet_res_ohm=None):
    """
    Computes all Hall effect semiconductor physical parameters:
      - Sheet Hall coefficient: R_Hs = V_H / (I * B)  [Ohm/T = m^2/C]
      - Bulk Hall coefficient: R_H = R_Hs * thickness [m^3/C = 1e6 cm^3/C]
      - Carrier type: n-type (electrons, RH < 0) or p-type (holes, RH > 0)
      - Sheet carrier concentration: ns = 1 / (e * |R_Hs|) [cm^-2]
      - Bulk carrier concentration: n = ns / thickness_cm [cm^-3]
      - Hall mobility: mu = |R_Hs| / R_sheet [cm^2 / (V*s)]
      - Bulk resistivity: rho = R_sheet * thickness [Ohm*cm]
    """
    if abs(current_a) < 1e-15 or abs(field_t) < 1e-15:
        return None

    # Sheet Hall coefficient in SI units (m^2 / C)
    r_hs_si = v_hall_v / (current_a * field_t)

    # Carrier type: convention: if RH < 0 -> electrons (n-type), if RH > 0 -> holes (p-type)
    carrier_type = "n-type (electrons)" if r_hs_si < 0 else "p-type (holes)"

    # Sheet carrier density ns: 1 / (e * |R_Hs|) in m^-2, then convert to cm^-2 (divide by 1e4)
    ns_m2 = 1.0 / (E_CHARGE * abs(r_hs_si)) if abs(r_hs_si) > 0 else 0.0
    ns_cm2 = ns_m2 * 1e-4

    # 3D bulk parameters (if thickness is given)
    r_h_si = None
    r_h_cm3_c = None
    n_bulk_cm3 = None
    thickness_cm = None
    if thickness_m and thickness_m > 0:
        r_h_si = r_hs_si * thickness_m  # m^3 / C
        r_h_cm3_c = r_h_si * 1e6  # cm^3 / C
        thickness_cm = thickness_m * 100.0
        n_bulk_cm3 = ns_cm2 / thickness_cm

    # Hall mobility (cm^2 / (V*s)) and Bulk resistivity (Ohm*cm)
    mobility_cm2_vs = None
    resistivity_ohm_cm = None
    if sheet_res_ohm and sheet_res_ohm > 0:
        mu_si = abs(r_hs_si) / sheet_res_ohm
        mobility_cm2_vs = mu_si * 1e4
        if thickness_cm:
            resistivity_ohm_cm = sheet_res_ohm * thickness_cm

    return {
        "v_hall_v": v_hall_v,
        "v_hall_mv": v_hall_v * 1e3,
        "v_hall_uv": v_hall_v * 1e6,
        "carrier_type": carrier_type,
        "is_n_type": r_hs_si < 0,
        "r_hs_si": r_hs_si,
        "r_h_cm3_c": r_h_cm3_c,
        "ns_cm2": ns_cm2,
        "n_bulk_cm3": n_bulk_cm3,
        "mobility_cm2_vs": mobility_cm2_vs,
        "resistivity_ohm_cm": resistivity_ohm_cm
    }


import re


def parse_filename_metadata(filename):
    """
    Parses metadata from Hall measurement filenames using the standard convention:
    'Sample name-R14-Current (xxx uA or xxx u)-temperature(10K, 20K, ...)'
    Supports both hyphen (-) and underscore (_) delimiters.
    """
    base = os.path.basename(filename).rsplit('.', 1)[0]
    parts = re.split(r'[-_]', base)
    
    meta = {
        'sample': parts[0].strip() if parts else 'Sample',
        'current_uA': 100.0,
        'temp_K': None,
        'geometry': 'R14',
        'raw': base
    }

    for p in parts[1:]:
        p_clean = p.strip()
        # Check current (e.g. 100uA, 200u, 50uA, 1mA)
        m_curr = re.match(r'^(\d+(?:\.\d+)?)\s*(uA|u|mA|A)$', p_clean, re.IGNORECASE)
        if m_curr:
            val = float(m_curr.group(1))
            unit = m_curr.group(2).lower()
            if unit in ['u', 'ua']:
                meta['current_uA'] = val
            elif unit == 'ma':
                meta['current_uA'] = val * 1000.0
            elif unit == 'a':
                meta['current_uA'] = val * 1e6
            continue

        # Check temperature (e.g. 10K, 180K, 300K, 4.2K)
        m_temp = re.match(r'^(\d+(?:\.\d+)?)\s*K$', p_clean, re.IGNORECASE)
        if m_temp:
            meta['temp_K'] = float(m_temp.group(1))
            continue

        # Check geometry tag (e.g. R14, R12, etc.)
        if p_clean.upper().startswith('R') and len(p_clean) <= 4 and p_clean[1:].isdigit():
            meta['geometry'] = p_clean.upper()
            continue

    return meta


def load_vdp_reference_table(filepath):
    """
    Loads a van der Pauw reference file (.csv, .txt, or .xlsx) with 3 columns:
    Sample; Rh; Rv (or comma/tab separated).
    Returns a cleaned pandas DataFrame with columns ['Sample', 'Rh', 'Rv'].
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"vdP reference file not found: {filepath}")

    ext = filepath.lower().rsplit('.', 1)[-1]
    if ext in ['xlsx', 'xls']:
        df = pd.read_excel(filepath)
    else:
        # Try delimiter autodetection (semicolon, comma, tab)
        try:
            df = pd.read_csv(filepath, sep=None, engine='python')
        except Exception:
            df = pd.read_csv(filepath, sep=';')

    # Standardize column headers
    col_map = {}
    for col in df.columns:
        c_str = str(col).strip()
        c_low = c_str.lower()
        if 'sample' in c_low or 'name' in c_low or 'id' in c_low:
            col_map[col] = 'Sample'
        elif 'rh' in c_low or 'r_h' in c_low or 'horizontal' in c_low:
            col_map[col] = 'Rh'
        elif 'rv' in c_low or 'r_v' in c_low or 'vertical' in c_low:
            col_map[col] = 'Rv'
        elif 'temp' in c_low or c_low == 'k':
            col_map[col] = 'Temperature'

    df = df.rename(columns=col_map)
    # Strip whitespace from string columns
    if 'Sample' in df.columns:
        df['Sample'] = df['Sample'].astype(str).str.strip()

    # Ensure Rh and Rv are numeric
    if 'Rh' in df.columns:
        df['Rh'] = pd.to_numeric(df['Rh'], errors='coerce')
    if 'Rv' in df.columns:
        df['Rv'] = pd.to_numeric(df['Rv'], errors='coerce')

    return df


def match_sample_vdp(sample_name, temp_k, vdp_df):
    """
    Matches a Hall measurement sample name and optional temperature against
    a van der Pauw reference DataFrame.
    Returns:
        (rh, rv, matched_sample_label, is_matched)
    """
    if vdp_df is None or vdp_df.empty or 'Sample' not in vdp_df.columns:
        return None, None, None, False

    s_clean = str(sample_name).strip()

    # 1. High priority: Match combined Sample and Temperature in the vdP Sample string
    # (e.g. "SampleA-10K", "SampleA_10K", "SampleA 10K")
    if temp_k is not None:
        t_tag = f"{int(temp_k)}k"
        t_num = str(int(temp_k))
        for _, row in vdp_df.iterrows():
            entry = str(row['Sample']).strip().lower()
            if s_clean.lower() in entry and (t_tag in entry or t_num in entry):
                return float(row['Rh']), float(row['Rv']), str(row['Sample']), True

    # 2. Match on separate Temperature column if present
    if 'Temperature' in vdp_df.columns and temp_k is not None:
        sample_subset = vdp_df[vdp_df['Sample'].str.lower() == s_clean.lower()]
        if not sample_subset.empty:
            temp_num = pd.to_numeric(sample_subset['Temperature'], errors='coerce')
            idx_temp = (temp_num - temp_k).abs().idxmin()
            row = sample_subset.loc[idx_temp]
            return float(row['Rh']), float(row['Rv']), str(row['Sample']), True

    # 3. Exact match on Sample column (single entry per sample)
    exact_matches = vdp_df[vdp_df['Sample'].str.lower() == s_clean.lower()]
    if not exact_matches.empty:
        row = exact_matches.iloc[0]
        return float(row['Rh']), float(row['Rv']), str(row['Sample']), True

    # 4. General Substring match fallback
    for _, row in vdp_df.iterrows():
        entry = str(row['Sample']).strip().lower()
        if entry in s_clean.lower() or s_clean.lower() in entry:
            return float(row['Rh']), float(row['Rv']), str(row['Sample']), True

    return None, None, None, False

