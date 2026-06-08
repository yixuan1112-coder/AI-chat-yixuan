#!/usr/bin/env python3
"""
ETL script for Dataset 02: CALCE CS2 Battery Aging Dataset
===========================================================
Reads raw CALCE CS2 data (Arbin Excel + CADEX txt) and produces
BatteryTwin Schema v0.2 outputs:
  - timeseries.parquet / timeseries.csv
  - cycle_summary.csv
  - metadata.csv

Usage:
    conda activate batterytwin
    cd ~/Desktop/BatteryTwin-Benchmark-DataPrep
    python scripts/etl_calce.py \
        --input data/raw/dataset_02_CALCE \
        --output data/processed/dataset_02

Author: Liu Kefan (liukefan821)
"""

import argparse
import os
import re
import glob
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# ============================================================
# CALCE CS2 cell registry — discharge conditions per cell
# ============================================================
CELL_REGISTRY = {
    # Type 1: CC discharge at 0.5C (~0.55A)
    "CS2_8":  {"type": 1, "discharge_protocol": "CC 0.5C",  "C_rate": 0.5, "tester": "CADEX", "format": "txt"},
    "CS2_21": {"type": 1, "discharge_protocol": "CC 0.5C",  "C_rate": 0.5, "tester": "CADEX", "format": "txt"},
    "CS2_33": {"type": 1, "discharge_protocol": "CC 0.5C",  "C_rate": 0.5, "tester": "Arbin", "format": "xlsx"},
    "CS2_34": {"type": 1, "discharge_protocol": "CC 0.5C",  "C_rate": 0.5, "tester": "Arbin", "format": "xlsx"},
    # Type 2: CC discharge at 1C (~1.1A)
    "CS2_35": {"type": 2, "discharge_protocol": "CC 1C",    "C_rate": 1.0, "tester": "Arbin", "format": "xlsx"},
    "CS2_36": {"type": 2, "discharge_protocol": "CC 1C",    "C_rate": 1.0, "tester": "Arbin", "format": "xlsx"},
    "CS2_37": {"type": 2, "discharge_protocol": "CC 1C",    "C_rate": 1.0, "tester": "Arbin", "format": "xlsx"},
    "CS2_38": {"type": 2, "discharge_protocol": "CC 1C",    "C_rate": 1.0, "tester": "Arbin", "format": "xlsx"},
    # Type 3: alternating discharge currents (0.11/0.22/0.55/1.1/1.65/2.2 A)
    "CS2_3":  {"type": 3, "discharge_protocol": "CC variable (0.1-2C)", "C_rate": None, "tester": "Arbin", "format": "xlsx"},
    "CS2_9":  {"type": 3, "discharge_protocol": "CC variable (0.1-2C)", "C_rate": None, "tester": "Arbin", "format": "xlsx"},
    # Type 4: CC 0.55A with random cutoff voltage
    "CS2_7":  {"type": 4, "discharge_protocol": "CC 0.5C random cutoff", "C_rate": 0.5, "tester": "Arbin", "format": "xlsx"},
    # Type 5: partial cycling, low voltage regime (3.77V-2.7V)
    "CS2_5":  {"type": 5, "discharge_protocol": "CC 0.5C partial (low)", "C_rate": 0.5, "tester": "Arbin", "format": "xlsx"},
    "CS2_6":  {"type": 5, "discharge_protocol": "CC 0.5C partial (low)", "C_rate": 0.5, "tester": "Arbin", "format": "xlsx"},
    # Type 6: partial cycling, high voltage regime (4.2V-3.77V)
    "CS2_24": {"type": 6, "discharge_protocol": "CC 0.5C partial (high)", "C_rate": 0.5, "tester": "Arbin", "format": "xlsx"},
    "CS2_25": {"type": 6, "discharge_protocol": "CC 0.5C partial (high)", "C_rate": 0.5, "tester": "Arbin", "format": "xlsx"},
}

# Common specs for ALL CS2 cells
COMMON_SPECS = {
    "dataset_id": "dataset_02",
    "source_type": "public",
    "split_tag": "",
    "chemistry": "LCO",
    "cathode_material": "LiCoO2",
    "anode_material": "Graphite",
    "brand_or_manufacturer": "Unknown (prismatic)",
    "model_or_size": "5.4x33.6x50.6mm prismatic",
    "form_factor": "prismatic",
    "nominal_capacity_Ah": 1.1,
    "nominal_voltage_V": 3.7,
    "temperature_C": 25.0,  # room temperature (not controlled)
    "charge_protocol": "CC-CV 0.5C to 4.2V (50mA cutoff)",
    "cutoff_voltage_upper": 4.2,
    "cutoff_voltage_lower": 2.7,
}


# ============================================================
# Arbin Excel reader
# ============================================================
def read_arbin_excel(filepath: str) -> pd.DataFrame:
    """Read a single Arbin Excel file, return the Channel data sheet."""
    try:
        xl = pd.ExcelFile(filepath, engine="openpyxl")
    except Exception as e:
        print(f"  [WARN] Cannot read {filepath}: {e}")
        return pd.DataFrame()

    # Find the Channel sheet (name like 'Channel_1-006')
    channel_sheets = [s for s in xl.sheet_names if s.startswith("Channel")]
    if not channel_sheets:
        print(f"  [WARN] No Channel sheet in {filepath}, sheets: {xl.sheet_names}")
        return pd.DataFrame()

    df = pd.read_excel(xl, sheet_name=channel_sheets[0], engine="openpyxl")
    xl.close()

    # Standardize column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]

    # Keep only needed columns
    keep_cols = {
        "Data_Point": "data_point",
        "Test_Time(s)": "time_s",
        "Date_Time": "datetime",
        "Step_Time(s)": "step_time_s",
        "Step_Index": "step_index",
        "Cycle_Index": "cycle_index",
        "Current(A)": "current_A",
        "Voltage(V)": "voltage_V",
        "Charge_Capacity(Ah)": "charge_capacity_Ah",
        "Discharge_Capacity(Ah)": "discharge_capacity_Ah",
    }
    rename_map = {}
    for orig, new in keep_cols.items():
        if orig in df.columns:
            rename_map[orig] = new
    df = df.rename(columns=rename_map)

    # Keep only renamed columns that exist
    valid_cols = [c for c in rename_map.values() if c in df.columns]
    df = df[valid_cols].copy()

    return df


# ============================================================
# CADEX txt reader (for CS2_8 and CS2_21)
# ============================================================
def read_cadex_txt(filepath: str) -> pd.DataFrame:
    """Read a single CADEX txt file.
    CADEX format is tab-separated with columns like:
    Cycle, Step, Current(A), Voltage(V), Capacity(Ah), Energy(Wh), Time
    The exact format may vary — we detect columns dynamically.
    """
    try:
        # Try reading with different possible separators
        df = pd.read_csv(filepath, sep="\t", encoding="latin-1", on_bad_lines="skip")
    except Exception:
        try:
            df = pd.read_csv(filepath, sep=",", encoding="latin-1", on_bad_lines="skip")
        except Exception as e:
            print(f"  [WARN] Cannot read CADEX file {filepath}: {e}")
            return pd.DataFrame()

    if df.empty:
        return df

    # Standardize column names
    df.columns = [c.strip() for c in df.columns]

    # Map CADEX columns to our standard names
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if "cycle" in col_lower and "index" not in col_lower:
            col_mapping[col] = "cycle_index"
        elif "step" in col_lower:
            col_mapping[col] = "step_index"
        elif "current" in col_lower:
            col_mapping[col] = "current_A"
        elif "voltage" in col_lower or "volt" in col_lower:
            col_mapping[col] = "voltage_V"
        elif "capacity" in col_lower and "charge" not in col_lower and "discharge" not in col_lower:
            col_mapping[col] = "capacity_Ah"
        elif "charge" in col_lower and "capacity" in col_lower:
            col_mapping[col] = "charge_capacity_Ah"
        elif "discharge" in col_lower and "capacity" in col_lower:
            col_mapping[col] = "discharge_capacity_Ah"
        elif "time" in col_lower and "date" not in col_lower:
            col_mapping[col] = "time_s"

    df = df.rename(columns=col_mapping)

    # Ensure numeric
    for c in ["current_A", "voltage_V", "time_s", "cycle_index"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


# ============================================================
# Extract date from filename for sorting files chronologically
# ============================================================
def extract_date_from_filename(filename: str):
    """Extract date components from CALCE filenames like CS2_33_8_18_10.xlsx
    Format: CS2_{cell}_{month}_{day}_{2-digit-year}.xlsx
    """
    stem = Path(filename).stem
    # Remove known prefixes
    stem = stem.lower().replace("cs2_", "").replace("cs_2_", "")

    # Try to extract M_D_YY pattern
    parts = stem.split("_")
    # Filter out non-numeric parts (like 'calibration', 'logicerror', etc.)
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            continue

    if len(nums) >= 3:
        # Last number is typically the 2-digit cell number, but filename structure is:
        # CS2_{cell}_{month}_{day}_{2-digit-year}.xlsx
        # After removing CS2_ prefix, we have: {cell}_{month}_{day}_{year}
        # But cell number is already removed by our split logic above
        # Actually the structure after prefix removal depends on cell name
        # Let's be more careful:
        pass

    # More robust: just use the datetime from the Info sheet or file modification time
    # For sorting, parse from the original filename pattern
    match = re.search(r"(\d{1,2})_(\d{1,2})_(\d{2,4})", stem)
    if match:
        month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if year < 100:
            year += 2000
        try:
            return pd.Timestamp(year=year, month=month, day=day)
        except ValueError:
            pass

    # Fallback: file modification time
    return pd.Timestamp("2099-01-01")


def sort_files_chronologically(file_list: list) -> list:
    """Sort data files by the date encoded in filename."""
    dated = [(f, extract_date_from_filename(f)) for f in file_list]
    dated.sort(key=lambda x: x[1])
    return [f for f, _ in dated]


# ============================================================
# Process one cell → timeseries DataFrame
# ============================================================
def process_cell(cell_name: str, cell_dir: str, cell_info: dict) -> pd.DataFrame:
    """Read all files for a cell, concatenate, assign global cycle IDs."""

    fmt = cell_info["format"]

    if fmt == "xlsx":
        # Collect all xlsx files (skip calibration and xls files if needed)
        files = glob.glob(os.path.join(cell_dir, "*.xlsx"))
        # Also check for .xls files
        xls_files = glob.glob(os.path.join(cell_dir, "*.xls"))
        # Filter out calibration files
        files = [f for f in files if "calibration" not in f.lower()]
        xls_files = [f for f in xls_files if "calibration" not in f.lower()
                     and not f.endswith(".xlsx")]  # avoid double-counting

        files = sort_files_chronologically(files)
        xls_sorted = sort_files_chronologically(xls_files)

        all_dfs = []
        for fpath in files:
            df = read_arbin_excel(fpath)
            if not df.empty:
                df["source_file"] = os.path.basename(fpath)
                all_dfs.append(df)

        # Try xls files with xlrd
        for fpath in xls_sorted:
            try:
                xl = pd.ExcelFile(fpath, engine="xlrd")
                channel_sheets = [s for s in xl.sheet_names if s.startswith("Channel")]
                if channel_sheets:
                    df = pd.read_excel(xl, sheet_name=channel_sheets[0])
                    df.columns = [c.strip() for c in df.columns]
                    rename_map = {
                        "Test_Time(s)": "time_s", "Date_Time": "datetime",
                        "Step_Index": "step_index", "Cycle_Index": "cycle_index",
                        "Current(A)": "current_A", "Voltage(V)": "voltage_V",
                        "Charge_Capacity(Ah)": "charge_capacity_Ah",
                        "Discharge_Capacity(Ah)": "discharge_capacity_Ah",
                    }
                    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
                    df["source_file"] = os.path.basename(fpath)
                    all_dfs.append(df)
                xl.close()
            except Exception as e:
                print(f"  [WARN] Cannot read xls {fpath}: {e}")

    elif fmt == "txt":
        files = glob.glob(os.path.join(cell_dir, "*.txt"))
        files = sort_files_chronologically(files)

        all_dfs = []
        for fpath in files:
            df = read_cadex_txt(fpath)
            if not df.empty:
                df["source_file"] = os.path.basename(fpath)
                all_dfs.append(df)
    else:
        print(f"  [WARN] Unknown format '{fmt}' for {cell_name}")
        return pd.DataFrame()

    if not all_dfs:
        print(f"  [WARN] No data loaded for {cell_name}")
        return pd.DataFrame()

    # ----------------------------------------------------------
    # Concatenate all files and assign global cycle IDs
    # ----------------------------------------------------------
    # Each file's cycle_index may restart from 1, so we need global renumbering
    global_cycle_offset = 0
    combined_dfs = []

    for df in all_dfs:
        if "cycle_index" in df.columns:
            df["cycle_index"] = pd.to_numeric(df["cycle_index"], errors="coerce")
            df = df.dropna(subset=["cycle_index"])
            if df.empty:
                continue
            df["cycle_index"] = df["cycle_index"].astype(int)
            df["cycle_id"] = df["cycle_index"] + global_cycle_offset
            max_cycle = df["cycle_index"].max()
            global_cycle_offset += max_cycle
        else:
            # No cycle info — treat entire file as one cycle
            global_cycle_offset += 1
            df["cycle_id"] = global_cycle_offset

        combined_dfs.append(df)

    if not combined_dfs:
        return pd.DataFrame()

    ts = pd.concat(combined_dfs, ignore_index=True)

    # ----------------------------------------------------------
    # Determine step_type from current sign
    # ----------------------------------------------------------
    if "current_A" in ts.columns:
        ts["current_A"] = pd.to_numeric(ts["current_A"], errors="coerce")
        conditions = [
            ts["current_A"] > 0.01,   # charging threshold
            ts["current_A"] < -0.01,  # discharging threshold
        ]
        choices = ["charge", "discharge"]
        ts["step_type"] = np.select(conditions, choices, default="rest")
    else:
        ts["step_type"] = "unknown"

    # ----------------------------------------------------------
    # Build timeseries in schema format
    # ----------------------------------------------------------
    ts["cell_id"] = cell_name

    # Handle time_s: if not present or contains datetime, compute from datetime
    if "time_s" in ts.columns:
        ts["time_s"] = pd.to_numeric(ts["time_s"], errors="coerce")
    elif "datetime" in ts.columns:
        ts["datetime"] = pd.to_datetime(ts["datetime"], errors="coerce")
        t0 = ts["datetime"].min()
        ts["time_s"] = (ts["datetime"] - t0).dt.total_seconds()

    # Ensure voltage and current are numeric
    for col in ["voltage_V", "current_A"]:
        if col in ts.columns:
            ts[col] = pd.to_numeric(ts[col], errors="coerce")

    # Temperature: CALCE CS2 has no temperature sensor column → NaN
    ts["temperature_C"] = np.nan

    # Select schema columns
    schema_cols = ["cell_id", "cycle_id", "time_s", "voltage_V", "current_A",
                   "temperature_C", "step_type"]
    for c in schema_cols:
        if c not in ts.columns:
            ts[c] = np.nan

    ts_out = ts[schema_cols].copy()

    # Drop rows where voltage or current is entirely null
    ts_out = ts_out.dropna(subset=["voltage_V", "current_A"], how="all")

    # Also carry forward charge/discharge capacity for cycle_summary
    for extra in ["charge_capacity_Ah", "discharge_capacity_Ah"]:
        if extra in ts.columns:
            ts_out[extra] = pd.to_numeric(ts[extra], errors="coerce").values

    return ts_out


# ============================================================
# Build cycle_summary from timeseries
# ============================================================
def build_cycle_summary(ts: pd.DataFrame, cell_name: str) -> pd.DataFrame:
    """Compute per-cycle summary statistics."""
    if ts.empty:
        return pd.DataFrame()

    nominal_cap = COMMON_SPECS["nominal_capacity_Ah"]
    rows = []

    for cycle_id, grp in ts.groupby("cycle_id"):
        # --- Charge phase ---
        chg = grp[grp["step_type"] == "charge"]
        if "charge_capacity_Ah" in grp.columns and not chg.empty:
            chg_cap = chg["charge_capacity_Ah"].max() - chg["charge_capacity_Ah"].min()
        else:
            chg_cap = np.nan
        chg_duration = (chg["time_s"].max() - chg["time_s"].min()) if not chg.empty and len(chg) > 1 else np.nan

        # --- Discharge phase ---
        dch = grp[grp["step_type"] == "discharge"]
        if "discharge_capacity_Ah" in grp.columns and not dch.empty:
            dch_cap = dch["discharge_capacity_Ah"].max() - dch["discharge_capacity_Ah"].min()
        else:
            dch_cap = np.nan
        dch_duration = (dch["time_s"].max() - dch["time_s"].min()) if not dch.empty and len(dch) > 1 else np.nan

        # SOH based on discharge capacity
        soh = (dch_cap / nominal_cap) * 100 if pd.notna(dch_cap) and dch_cap > 0 else np.nan

        # Charge row
        rows.append({
            "cell_id": cell_name,
            "cycle_id": cycle_id,
            "step_type": "charge",
            "capacity_Ah": chg_cap if pd.notna(chg_cap) else np.nan,
            "SOH": np.nan,
            "RUL": np.nan,
            "charge_capacity_Ah": chg_cap if pd.notna(chg_cap) else np.nan,
            "discharge_capacity_Ah": np.nan,
            "temperature_max_C": np.nan,
            "temperature_avg_C": np.nan,
            "charge_duration_s": chg_duration,
            "discharge_duration_s": np.nan,
            "internal_resistance_Ohm": np.nan,
            "cycle_end_flag": "",
        })

        # Discharge row
        rows.append({
            "cell_id": cell_name,
            "cycle_id": cycle_id,
            "step_type": "discharge",
            "capacity_Ah": dch_cap if pd.notna(dch_cap) else np.nan,
            "SOH": soh,
            "RUL": np.nan,
            "charge_capacity_Ah": np.nan,
            "discharge_capacity_Ah": dch_cap if pd.notna(dch_cap) else np.nan,
            "temperature_max_C": np.nan,
            "temperature_avg_C": np.nan,
            "charge_duration_s": np.nan,
            "discharge_duration_s": dch_duration,
            "internal_resistance_Ohm": np.nan,
            "cycle_end_flag": "",
        })

    summary = pd.DataFrame(rows)
    return summary


# ============================================================
# Build metadata CSV
# ============================================================
def build_metadata(cells_processed: dict) -> pd.DataFrame:
    """Build metadata.csv for all processed cells."""
    rows = []
    for cell_name in sorted(cells_processed.keys()):
        info = CELL_REGISTRY.get(cell_name, {})
        row = {**COMMON_SPECS}
        row["cell_id"] = cell_name
        row["discharge_protocol"] = info.get("discharge_protocol", "")
        row["C_rate"] = info.get("C_rate", "")

        # Override cutoff_voltage_lower for partial cycling cells
        if info.get("type") == 5:
            row["cutoff_voltage_lower"] = 2.7
            row["cutoff_voltage_upper"] = 3.77
        elif info.get("type") == 6:
            row["cutoff_voltage_lower"] = 3.77
            row["cutoff_voltage_upper"] = 4.2

        # Add stats from processed data
        stats = cells_processed[cell_name]
        row["total_cycles"] = stats.get("total_cycles", 0)
        row["total_rows"] = stats.get("total_rows", 0)
        row["tester"] = info.get("tester", "")
        row["experiment_type"] = info.get("type", "")

        rows.append(row)

    meta_cols = [
        "dataset_id", "cell_id", "source_type", "split_tag", "chemistry",
        "cathode_material", "anode_material", "brand_or_manufacturer",
        "model_or_size", "form_factor", "nominal_capacity_Ah", "nominal_voltage_V",
        "temperature_C", "charge_protocol", "discharge_protocol", "C_rate",
        "cutoff_voltage_upper", "cutoff_voltage_lower",
    ]
    df = pd.DataFrame(rows)
    # Ensure all schema columns present
    for c in meta_cols:
        if c not in df.columns:
            df[c] = ""
    return df[meta_cols]


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="ETL for CALCE CS2 Battery Dataset")
    parser.add_argument("--input", required=True, help="Path to data/raw/dataset_02_CALCE/")
    parser.add_argument("--output", required=True, help="Path to data/processed/dataset_02/")
    parser.add_argument("--cells", default=None, help="Comma-separated cell names to process (default: all)")
    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    # Determine which cells to process
    if args.cells:
        target_cells = [c.strip() for c in args.cells.split(",")]
    else:
        # Auto-detect from directory listing
        target_cells = []
        for entry in sorted(os.listdir(input_dir)):
            full_path = os.path.join(input_dir, entry)
            if os.path.isdir(full_path) and entry.startswith("CS2_"):
                target_cells.append(entry)

    print(f"CALCE CS2 ETL — processing {len(target_cells)} cells")
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Cells:  {target_cells}")
    print()

    all_timeseries = []
    all_cycle_summary = []
    cells_processed = {}

    for cell_name in tqdm(target_cells, desc="Processing cells"):
        cell_dir = os.path.join(input_dir, cell_name)
        if not os.path.isdir(cell_dir):
            print(f"  [SKIP] Directory not found: {cell_dir}")
            continue

        info = CELL_REGISTRY.get(cell_name, {"format": "xlsx", "tester": "Unknown"})
        print(f"\n--- {cell_name} (Type {info.get('type', '?')}, {info['format']}) ---")

        # Read and process timeseries
        ts = process_cell(cell_name, cell_dir, info)
        if ts.empty:
            print(f"  [WARN] No data produced for {cell_name}")
            continue

        n_cycles = ts["cycle_id"].nunique()
        print(f"  Rows: {len(ts):,}  |  Cycles: {n_cycles}")

        # Build cycle summary
        cs = build_cycle_summary(ts, cell_name)

        # Store stats
        cells_processed[cell_name] = {
            "total_cycles": n_cycles,
            "total_rows": len(ts),
        }

        # Drop extra columns before saving timeseries
        ts_save = ts[["cell_id", "cycle_id", "time_s", "voltage_V", "current_A",
                       "temperature_C", "step_type"]].copy()

        all_timeseries.append(ts_save)
        all_cycle_summary.append(cs)

    if not all_timeseries:
        print("\n[ERROR] No data processed. Check input directory.")
        return

    # ----------------------------------------------------------
    # Concatenate and save
    # ----------------------------------------------------------
    print("\n=== Saving outputs ===")

    # Timeseries
    ts_all = pd.concat(all_timeseries, ignore_index=True)
    ts_parquet = os.path.join(output_dir, "CALCE_CS2_timeseries.parquet")
    ts_csv = os.path.join(output_dir, "CALCE_CS2_timeseries.csv")
    ts_all.to_parquet(ts_parquet, index=False)
    print(f"  timeseries.parquet: {len(ts_all):,} rows → {ts_parquet}")
    # CSV only if small enough (< 200MB estimated)
    estimated_csv_mb = len(ts_all) * 80 / 1e6  # ~80 bytes per row
    if estimated_csv_mb < 200:
        ts_all.to_csv(ts_csv, index=False)
        print(f"  timeseries.csv:     {len(ts_all):,} rows → {ts_csv}")
    else:
        print(f"  timeseries.csv:     SKIPPED (estimated {estimated_csv_mb:.0f}MB > 200MB limit)")

    # Cycle summary
    cs_all = pd.concat(all_cycle_summary, ignore_index=True)
    cs_path = os.path.join(output_dir, "CALCE_CS2_cycle_summary.csv")
    cs_all.to_csv(cs_path, index=False)
    print(f"  cycle_summary.csv:  {len(cs_all):,} rows → {cs_path}")

    # Metadata
    meta = build_metadata(cells_processed)
    meta_path = os.path.join(output_dir, "CALCE_CS2_metadata.csv")
    meta.to_csv(meta_path, index=False)
    print(f"  metadata.csv:       {len(meta)} cells → {meta_path}")

    # ----------------------------------------------------------
    # Print summary
    # ----------------------------------------------------------
    print("\n=== Summary ===")
    print(f"Total cells processed: {len(cells_processed)}")
    print(f"Total timeseries rows: {len(ts_all):,}")
    print(f"Total cycle_summary rows: {len(cs_all):,}")
    print(f"Timeseries voltage range: {ts_all['voltage_V'].min():.3f} ~ {ts_all['voltage_V'].max():.3f} V")
    print(f"Timeseries current range: {ts_all['current_A'].min():.3f} ~ {ts_all['current_A'].max():.3f} A")


if __name__ == "__main__":
    main()
