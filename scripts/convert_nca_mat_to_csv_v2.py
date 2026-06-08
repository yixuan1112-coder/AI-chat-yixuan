#!/usr/bin/env python3
"""
convert_nca_mat_to_csv_v2.py
Convert Oxford NCA 18650 .mat files to CSV - v2 with auto data_start detection.
Fixes column misalignment issue in v1.

Usage:
    conda activate batterytwin
    python convert_nca_mat_to_csv_v2.py
"""

import scipy.io as sio
import numpy as np
import pandas as pd
import os

# === Configuration ===
BASE_DIR = os.path.expanduser(
    "~/Projects/BatteryTwin-Benchmark-DataPrep/data/raw/dataset_04_Oxford/nca_18650"
)
OUT_DIR = os.path.join(BASE_DIR, "csv_converted")
GROUPS = ["Group 1", "Group 2", "Group 3", "Group 4"]
N_COLS = 24  # 9 named + 15 VARx
BYTES_PER_ROW = N_COLS * 8  # 192 bytes per row in column-major layout

COL_NAMES = ["Cyc", "Step", "TestTime", "StepTime", "Amphr", "Watthr", "Amps", "Volts", "Temp1"]
MIN_FILE_SIZE = 200_000  # skip files smaller than this


def find_data_start(raw, total):
    """
    Auto-detect where the column-major float64 data begins.
    Strategy: data_start must satisfy (total - data_start) % 192 == 0,
    AND the first column (Cyc) should contain small non-negative integers.
    """
    # All valid data_start values share the same remainder mod 192
    base_remainder = total % BYTES_PER_ROW

    # Scan candidates from small to ~15MB
    for candidate in range(base_remainder, 15_000_000, BYTES_PER_ROW):
        nrows = (total - candidate) // BYTES_PER_ROW
        if nrows < 100:
            continue

        # Check: first 20 values of column 0 should be small non-negative integers (cycle numbers)
        end = min(candidate + 160, total)  # 20 float64 values
        if end - candidate < 80:
            continue

        vals = np.frombuffer(raw[candidate:end], dtype="<f8")
        if len(vals) < 10:
            continue

        # Cycle numbers: non-negative integers, typically 0-500
        is_valid = all(
            0 <= v <= 1000 and (v == int(v) or abs(v - round(v)) < 0.001)
            for v in vals[:10]
        )
        if is_valid:
            return candidate, nrows

    return None, None


def extract_mat_to_df(filepath):
    """Extract battery data from a .mat file with auto data_start detection."""
    file_size = os.path.getsize(filepath)
    if file_size < MIN_FILE_SIZE:
        raise ValueError(f"File too small: {file_size} bytes")

    data = sio.loadmat(filepath, squeeze_me=False)

    if "__function_workspace__" not in data:
        raise ValueError("No __function_workspace__ found")

    raw = data["__function_workspace__"].flatten().tobytes()
    total = len(raw)

    data_start, nrows = find_data_start(raw, total)
    if data_start is None:
        raise ValueError(f"Could not auto-detect data start (total={total})")

    # Extract column-major: each column is nrows consecutive float64 values
    arr = np.frombuffer(raw[data_start:data_start + nrows * N_COLS * 8], dtype="<f8")
    matrix = arr.reshape(N_COLS, nrows).T

    # Take first 9 columns
    df = pd.DataFrame(matrix[:, :9], columns=COL_NAMES)

    # Validate
    volts_max = df["Volts"].max()
    temp_max = df["Temp1"].max()
    cyc_max = df["Cyc"].max()

    issues = []
    if volts_max > 5.0 or volts_max < 2.0:
        issues.append(f"V_max={volts_max:.2f}")
    if temp_max > 80 or temp_max < 5:
        issues.append(f"T_max={temp_max:.1f}")
    if cyc_max < 0 or cyc_max > 1000:
        issues.append(f"Cyc_max={cyc_max:.0f}")
    # Check first Cyc value is a small integer
    first_cyc = df["Cyc"].iloc[0]
    if first_cyc < 0 or first_cyc > 500 or abs(first_cyc - round(first_cyc)) > 0.01:
        issues.append(f"Cyc[0]={first_cyc}")

    return df, data_start, issues


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
        print(f"\n{'='*70}")
        print(f"{group}: {len(mat_files)} .mat files")
        print(f"{'='*70}")

        for mat_file in mat_files:
            total_files += 1
            mat_path = os.path.join(group_dir, mat_file)
            csv_name = mat_file.replace(".mat", ".csv")
            csv_path = os.path.join(group_out, csv_name)

            try:
                df, data_start, issues = extract_mat_to_df(mat_path)
                df.to_csv(csv_path, index=False)
                ok_count += 1

                warn = f" ⚠ {'; '.join(issues)}" if issues else ""
                print(
                    f"  OK: {csv_name:40s} {len(df):>10,} rows  "
                    f"Cyc=0-{df['Cyc'].max():.0f}  "
                    f"V={df['Volts'].min():.2f}-{df['Volts'].max():.2f}  "
                    f"T={df['Temp1'].min():.1f}-{df['Temp1'].max():.1f}°C  "
                    f"start={data_start}{warn}"
                )

                results.append({
                    "group": group, "file": mat_file, "status": "OK",
                    "rows": len(df), "data_start": data_start,
                    "cyc_max": df["Cyc"].max(),
                    "volts_min": df["Volts"].min(), "volts_max": df["Volts"].max(),
                    "amps_min": df["Amps"].min(), "amps_max": df["Amps"].max(),
                    "temp_min": df["Temp1"].min(), "temp_max": df["Temp1"].max(),
                    "issues": "; ".join(issues),
                })

            except Exception as e:
                fail_count += 1
                print(f"  FAIL: {mat_file:40s} {str(e)[:80]}")
                results.append({
                    "group": group, "file": mat_file,
                    "status": f"FAIL: {str(e)[:80]}",
                    "rows": 0, "data_start": -1,
                })

    print(f"\n{'='*70}")
    print(f"SUMMARY: {ok_count}/{total_files} OK, {fail_count} failed")
    print(f"CSVs saved to: {OUT_DIR}")
    print(f"{'='*70}")

    report_df = pd.DataFrame(results)
    report_path = os.path.join(OUT_DIR, "conversion_report_v2.csv")
    report_df.to_csv(report_path, index=False)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
