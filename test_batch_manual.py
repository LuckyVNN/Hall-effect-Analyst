import sys
import os
import glob
import pandas as pd
from PyQt6 import QtWidgets, QtCore

# Run headless with offscreen platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from desktop_app import HallDesktopApp

# Mock modal popups to run headlessly without waiting for user button clicks
QtWidgets.QMessageBox.information = lambda *args, **kwargs: QtWidgets.QMessageBox.StandardButton.Ok
QtWidgets.QMessageBox.question = lambda *args, **kwargs: QtWidgets.QMessageBox.StandardButton.Yes
QtWidgets.QMessageBox.warning = lambda *args, **kwargs: QtWidgets.QMessageBox.StandardButton.Ok

def test_batch_manual_studio():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    window = HallDesktopApp()
    
    print("[1] Window initialized successfully.")
    
    # 1. Switch to Batch tab
    window.main_tabs.setCurrentIndex(1)
    
    # 2. Add test files
    test_files = glob.glob("f:/Sn/Master-App/test-files/*.csv")
    hall_files = [f for f in test_files if "vdp" not in os.path.basename(f).lower()]
    vdp_file = "f:/Sn/Master-App/test-files/vdp_reference.csv"
    
    assert len(hall_files) == 14, f"Expected 14 test Hall files, found {len(hall_files)}"
    
    # Simulate loading vdP file
    window.vdp_df = pd.read_csv(vdp_file, sep=";")
    window.vdp_filepath = vdp_file
    window.lbl_vdp_status.setText(f"Loaded: {len(window.vdp_df)} entries")
    
    # Populate vdP preview table
    window.table_vdp_preview.setRowCount(len(window.vdp_df))
    for r, row in window.vdp_df.iterrows():
        window.table_vdp_preview.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row.get('Sample', ''))))
        window.table_vdp_preview.setItem(r, 1, QtWidgets.QTableWidgetItem(str(row.get('Rh', ''))))
        window.table_vdp_preview.setItem(r, 2, QtWidgets.QTableWidgetItem(str(row.get('Rv', ''))))
        
    print(f"[2] vdP reference file loaded ({len(window.vdp_df)} entries).")
    
    # Add hall files to batch_files_data
    for f in hall_files:
        meta = window.combo_files.itemData(0) # test parse
        import hall_core
        meta = hall_core.parse_filename_metadata(f)
        window.batch_files_data.append({
            'path': f,
            'filename': os.path.basename(f),
            'meta': meta,
            'status': 'Pending',
            'regions': None,
            'result': None
        })
        
    window.batch_files_data.sort(key=lambda x: (
        str(x['meta'].get('sample', '')),
        x['meta'].get('temp_K') if x['meta'].get('temp_K') is not None else 999999
    ))
    window.refresh_batch_files_table()
    
    # Verify files are sorted chronologically: 10K, 20K, ..., 280K
    temps = [item['meta']['temp_K'] for item in window.batch_files_data]
    print(f"[3] Staged files sorted temperatures: {temps}")
    expected_temps = [10.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 250.0, 280.0]
    assert temps == expected_temps, f"Expected {expected_temps}, got {temps}"
    
    # Load first file into manual extraction
    window.load_batch_file_for_manual_extraction(0)
    assert window.batch_current_idx == 0
    assert "10K" in window.batch_files_data[0]['filename']
    print(f"[4] File 1 loaded: {window.lbl_b_file_badge.text()}")
    print(f"    vdP info: {window.lbl_b_meta_info.text()}")
    print(f"    Live V_Hall card: {window.b_card_vh['main'].text()}")
    print(f"    Live Mobility card: {window.b_card_mu['main'].text()}")
    
    # Test manual draggable region adjustment on File 1
    window.b_region_b1.setRegion([12.0, 22.0])
    window.b_region_pulse.setRegion([36.0, 52.0])
    window.b_region_b2.setRegion([66.0, 76.0])
    window.on_batch_manual_region_dragged()
    
    vh_val = window.b_latest_v_hall
    assert abs(vh_val) > 0.0001, f"Expected non-zero V_Hall, got {vh_val}"
    print(f"[5] Region dragged. Recalculated V_Hall: {vh_val*1e3:.4f} mV")
    
    # Save & advance to next
    window.batch_manual_save_and_next()
    assert window.batch_files_data[0]['status'] == 'Done'
    assert len(window.batch_results) == 1
    assert window.batch_current_idx == 1
    print(f"[6] Saved File 1! Current queue index now: {window.batch_current_idx} ({window.batch_files_data[1]['filename']})")
    
    # Save File 2
    window.batch_manual_save_and_next()
    assert window.batch_files_data[1]['status'] == 'Done'
    assert len(window.batch_results) == 2
    assert window.batch_current_idx == 2
    print(f"[7] Saved File 2! Current queue index now: {window.batch_current_idx} ({window.batch_files_data[2]['filename']})")
    
    # Test jumping directly by clicking on table row 5 (Temp 100K)
    window.on_batch_file_cell_clicked(5, 0)
    assert window.batch_current_idx == 5
    assert window.batch_files_data[5]['meta']['temp_K'] == 100
    print(f"[8] Jumped to row 5: {window.batch_files_data[5]['filename']} (T=100K)")
    
    # Test auto-process remaining files
    window.auto_process_remaining_files()
    assert len(window.batch_results) == 14
    for item in window.batch_files_data:
        assert item['status'] == 'Done'
    print(f"[9] Auto-processed remaining files: All 14 files now marked Done!")
    
    # Verify results table has 14 rows
    assert window.table_b_results.rowCount() == 14
    print(f"[10] Batch results table has {window.table_b_results.rowCount()} rows.")
    
    # Verify temperature plot has plotted items
    window.update_batch_plot()
    plot_items = window.plot_batch.listDataItems()
    assert len(plot_items) > 0
    print(f"[11] Temperature plot has {len(plot_items)} curve(s) with {len(plot_items[0].xData)} data points.")
    
    # Test switching parameter in temperature plot
    for param_text in [
        "Hall Mobility (μ) vs Temperature (T)",
        "Carrier Concentration (n) vs Temperature (T)",
        "Sheet Density (ns) vs Temperature (T)",
        "Bulk Resistivity (ρ) vs Temperature (T)",
        "Hall Voltage (V_H) vs Temperature (T)"
    ]:
        idx = window.combo_t_param.findText(param_text)
        window.combo_t_param.setCurrentIndex(idx)
        window.update_batch_plot()
        curve = window.plot_batch.listDataItems()[0]
        assert len(curve.yData) == 14
        print(f"    Curve '{param_text}': {len(curve.yData)} points plotted.")
        
    print("\n==========================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==========================================")

if __name__ == "__main__":
    test_batch_manual_studio()
