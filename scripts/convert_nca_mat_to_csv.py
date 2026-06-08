#!/usr/bin/env python3
"""
convert_nca_mat_to_csv.py
Convert Oxford NCA 18650 .mat files (MATLAB table objects) to CSV
using pure Python binary extraction. No MATLAB needed!

Usage:
    conda activate batterytwin
    python convert_nca_mat_to_csv.py
"""

import scipy.io as sio
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# === Configuration ===
BASE_DIR = os.path.expanduser(
    "~/Projects/BatteryTwin-Benchmark-DataPrep/data/raw/dataset_04_Oxford/nca_18650"
)
OUT_DIR = os.path.join(BASE_DIR, "csv_converted")

GROUPS = ["Group 1", "Group 2", "Group 3", "Group 4"]
DATA_START = 6_400_000  # bytes offset where data begins
N_COLS = 24  # 9 named + 15 VARx

# Only keep the 9 useful columns
COL_NAMES = ["Cyc", "Step", "TestTime", "StepTime", "Amphr", "Watthr", "Amps", "Volts", "Temp1"]


def extract_mat_to_df(filepath):
    """Extract battery data from a .mat file containing MATLAB table objects."""
    data = sio.loadmat(filepath, squeeze_me=False)
    
    if "__function_workspace__" not in data:
        raise ValueError(f"No __function_workspace__ found in {filepath}")
    
    raw = data["__function_workspace__"].flatten().tobytes()
    total = len(raw)
    
    # Calculate number of rows
    data_bytes = total - DATA_START
    if data_bytes <= 0:
        raise ValueError(f"File too small: {total} bytes, expected > {DATA_START}")
    
    nrows = data_bytes // (8 * N_COLS)
    remainder = data_bytes - nrows * 8 * N_COLS
    
    if remainder != 0:
        # Try auto-detecting: maybe different data_start
        # Search for data_start that gives 0 remainder
        found = False
        for test_start in range(0, min(total, 20_000_000), 8):
            test_bytes = total - test_start
            if test_bytes > 0 and test_bytes % (8 * N_COLS) == 0:
                test_nrows = test_bytes // (8 * N_COLS)
                if test_nrows > 10000:  # reasonable minimum
                    # Verify: first column should have small integers
                    arr = np.frombuffer(raw[test_start:test_start + 80], dtype="<f8")
                    if all(0 <= v <= 1000 for v in arr[:10]):
                        nrows = test_nrows
                        actual_start = test_start
                        found = True
                        break
        if not found:
            raise ValueError(f"Cannot determine data layout for {filepath}")
    else:
        actual_start = DATA_START
    
    # Extract column-major data
    arr = np.frombuffer(raw[actual_start:actual_start + nrows * N_COLS * 8], dtype="<f8")
    matrix = arr.reshape(N_COLS, nrows).T
    
    # Take only the first 9 columns
    df = pd.DataFrame(matrix[:, :9], columns=COL_NAMES)
    
    return df


def validate_df(df, filename):
    """Basic sanity checks on extracted data."""
    issues = []
    
    if df["Volts"].max() > 5.0 or df["Volts"].max() < 2.0:
        issues.append(f"Suspicious voltage range: {df['Volts'].min():.2f}-{df['Volts'].max():.2f}")
    
    if df["Temp1"].max() > 80 or df["Temp1"].max() < 10:
        issues.append(f"Suspicious temp range: {df['Temp1'].min():.2f}-{df['Temp1'].max():.2f}")
    
    if len(df) < 1000:
        issues.append(f"Very few rows: {len(df)}")
    
    return issues


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    total_files = 0
    ok_count = 0
    fail_count = 0
    results = []
    
    for group in GROUPS:
        group_dir = os.path.join(BASE_DIR, group)
        group_out = os.path.join(OUT_DIR, group.replace(" ", "_"))
        os.makedirs(group_out, exist_ok=True)
        
        mat_files = sorted([f for f in os.listdir(group_dir) if f.endswith(".mat")])
        print(f"\n{'='*60}")
        print(f"{group}: {len(mat_files)} .mat files")
        print(f"{'='*60}")
        
        for mat_file in mat_files:
            total_files += 1
            mat_path = os.path.join(group_dir, mat_file)
            csv_name = mat_file.replace(".mat", ".csv")
            csv_path = os.path.join(group_out, csv_name)
            
            try:
                df = extract_mat_to_df(mat_path)
                issues = validate_df(df, mat_file)
                
                df.to_csv(csv_path, index=False)
                ok_count += 1
                
                status = "OK"
                if issues:
                    status = f"OK (warnings: {'; '.join(issues)})"
                
                print(f"  OK: {csv_name} ({len(df):,} rows, "
                      f"V={df['Volts'].min():.2f}-{df['Volts'].max():.2f}, "
                      f"T={df['Temp1'].min():.1f}-{df['Temp1'].max():.1f}°C)")
                
                results.append({
                    "group": group,
                    "file": mat_file,
                    "status": "OK",
                    "rows": len(df),
                    "volts_min": df["Volts"].min(),
                    "volts_max": df["Volts"].max(),
                    "temp_min": df["Temp1"].min(),
                    "temp_max": df["Temp1"].max(),
                    "cycles": df["Cyc"].max(),
                    "issues": "; ".join(issues) if issues else "",
                })
                
            except Exception as e:
                fail_count += 1
                print(f"  FAIL: {mat_file} - {str(e)[:100]}")
                results.append({
                    "group": group,
                    "file": mat_file,
                    "status": f"FAIL: {str(e)[:80]}",
                    "rows": 0,
                })
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {ok_count}/{total_files} OK, {fail_count} failed")
    print(f"CSVs saved to: {OUT_DIR}")
    print(f"{'='*60}")
    
    # Save conversion report
    report_df = pd.DataFrame(results)
    report_path = os.path.join(OUT_DIR, "conversion_report.csv")
    report_df.to_csv(report_path, index=False)
    print(f"Conversion report: {report_path}")


if __name__ == "__main__":
    main()
