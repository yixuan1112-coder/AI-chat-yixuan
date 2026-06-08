#!/usr/bin/env python3
"""
ETL Script for NTU EEE Internal Battery Dataset
================================================
Dataset: NTU EEE Internal Battery Cycling Data
Cell types:
  - Ampace 21700A (4000mAh, 3.7V, 21700 cylindrical)
  - Samsung INR18650-35E (3350mAh, 3.60V, 18650 cylindrical)

Raw data format: CSV with columns [Cycle, Time, Voltage, Current, Capacity, Temperature]
  - Current > 0 = charge, Current < 0 = discharge
  - Capacity resets per charge/discharge phase within each cycle

Naming convention: {Brand}_{ChargeRate}_{DischargeRate}_{TempC}_{SampleID}.csv
  e.g. Samsung_1C_2C_40T_001.csv = Samsung cell, 1C charge, 2C discharge, 40°C, sample #1

Outputs (per project standard):
  - metadata.csv          : one row per cell with specs and test conditions
  - cycle_summary/{cell}.csv : per-cycle aggregated metrics
  - timeseries_sample/{cell}.csv : first 5 cycles timeseries (for validation)

Author: Kefan Liu
Date: 2026-03-24
"""

import os
import csv
import glob
import time
import sys
from collections import defaultdict
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────
RAW_DIR = "data/raw/dataset_eee"
OUT_DIR = "data/processed/dataset_eee"

# Cell spec lookup
CELL_SPECS = {
    "Ampace": {
        "cell_model": "Ampace 21700A",
        "form_factor": "21700 cylindrical",
        "chemistry": "Li-ion",
        "nominal_capacity_Ah": 4.0,
        "nominal_voltage_V": 3.7,
        "charge_cutoff_V": 4.2,
        "discharge_cutoff_V": 2.5,
        "max_weight_g": 70.0,
    },
    "Samsung": {
        "cell_model": "Samsung INR18650-35E",
        "form_factor": "18650 cylindrical",
        "chemistry": "Li-ion (NCA/NCM)",
        "nominal_capacity_Ah": 3.35,
        "nominal_voltage_V": 3.60,
        "charge_cutoff_V": 4.2,
        "discharge_cutoff_V": 2.65,
        "max_weight_g": 50.0,
    },
}


def parse_filename(filename):
    """Parse cell info from filename like Samsung_1C_2C_40T_001.csv"""
    stem = Path(filename).stem  # e.g. Samsung_1C_2C_40T_001
    parts = stem.split("_")
    brand = parts[0]
    charge_rate = parts[1]       # e.g. "1C"
    discharge_rate = parts[2]    # e.g. "2C"
    temp_str = parts[3]          # e.g. "40T"
    sample_id = parts[4]         # e.g. "001"

    temp_C = int(temp_str.replace("T", ""))

    return {
        "brand": brand,
        "charge_rate": charge_rate,
        "discharge_rate": discharge_rate,
        "temperature_C": temp_C,
        "sample_id": sample_id,
        "cell_id": stem,
    }


def process_one_cell(csv_path, cell_info):
    """
    Read one CSV, produce:
      - cycle_summary rows (list of dicts)
      - timeseries_sample rows (first 5 cycles, list of dicts)
      - stats for metadata
    """
    cell_id = cell_info["cell_id"]
    print(f"  Processing {cell_id} ...", end="", flush=True)
    t0 = time.time()

    # ── Pass 1: read all data, grouped by cycle ──
    cycle_data = defaultdict(list)
    total_rows = 0

    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cyc = int(row["Cycle"])
            cycle_data[cyc].append({
                "time_s": float(row["Time"]),
                "voltage_V": float(row["Voltage"]),
                "current_A": float(row["Current"]),
                "capacity_Ah": float(row["Capacity"]),
                "temperature_C": float(row["Temperature"]),
            })
            total_rows += 1

    sorted_cycles = sorted(cycle_data.keys())
    n_cycles = len(sorted_cycles)

    # ── Pass 2: compute per-cycle summary ──
    cycle_summaries = []
    for cyc in sorted_cycles:
        rows = cycle_data[cyc]

        voltages = [r["voltage_V"] for r in rows]
        currents = [r["current_A"] for r in rows]
        caps = [r["capacity_Ah"] for r in rows]
        temps = [r["temperature_C"] for r in rows]

        # Charge capacity = max positive capacity in the cycle
        chg_cap = max(caps) if max(caps) > 0 else 0.0
        # Discharge capacity = abs of min negative capacity
        dch_cap = abs(min(caps)) if min(caps) < 0 else 0.0

        # Energy estimation via trapezoidal integration
        chg_energy = 0.0
        dch_energy = 0.0
        for i in range(1, len(rows)):
            dt_s = rows[i]["time_s"] - rows[i - 1]["time_s"]
            if dt_s <= 0 or dt_s > 120:
                # Time resets between phases; skip those transitions
                continue
            avg_V = (rows[i]["voltage_V"] + rows[i - 1]["voltage_V"]) / 2
            avg_I = (rows[i]["current_A"] + rows[i - 1]["current_A"]) / 2
            power_Wh = avg_V * avg_I * (dt_s / 3600.0)
            if avg_I > 0.05:
                chg_energy += power_Wh
            elif avg_I < -0.05:
                dch_energy += abs(power_Wh)

        cycle_summaries.append({
            "cycle_number": cyc,
            "charge_capacity_Ah": round(chg_cap, 6),
            "discharge_capacity_Ah": round(dch_cap, 6),
            "charge_energy_Wh": round(chg_energy, 6),
            "discharge_energy_Wh": round(dch_energy, 6),
            "coulombic_efficiency": round(dch_cap / chg_cap, 6) if chg_cap > 0 else None,
            "energy_efficiency": round(dch_energy / chg_energy, 6) if chg_energy > 0 else None,
            "max_temperature_C": round(max(temps), 2),
            "min_voltage_V": round(min(voltages), 4),
            "max_voltage_V": round(max(voltages), 4),
            "n_datapoints": len(rows),
        })

    # ── Pass 3: timeseries sample (first 5 cycles) ──
    sample_cycles = sorted_cycles[:5]
    ts_rows = []
    for cyc in sample_cycles:
        for r in cycle_data[cyc]:
            ts_rows.append({
                "cycle_number": cyc,
                "time_s": r["time_s"],
                "voltage_V": r["voltage_V"],
                "current_A": r["current_A"],
                "capacity_Ah": r["capacity_Ah"],
                "temperature_C": r["temperature_C"],
            })

    # ── Stats for metadata ──
    first_dch = cycle_summaries[0]["discharge_capacity_Ah"] if cycle_summaries else 0
    last_dch = cycle_summaries[-1]["discharge_capacity_Ah"] if cycle_summaries else 0

    elapsed = time.time() - t0
    print(f" {n_cycles} cycles, {total_rows:,} rows ({elapsed:.1f}s)")

    return {
        "cycle_summaries": cycle_summaries,
        "timeseries_sample": ts_rows,
        "n_cycles": n_cycles,
        "n_rows": total_rows,
        "first_discharge_Ah": first_dch,
        "last_discharge_Ah": last_dch,
    }


def write_cycle_summary(out_dir, cell_id, summaries):
    """Write cycle_summary CSV for one cell."""
    path = os.path.join(out_dir, "cycle_summary", f"{cell_id}.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fieldnames = [
        "cycle_number", "charge_capacity_Ah", "discharge_capacity_Ah",
        "charge_energy_Wh", "discharge_energy_Wh",
        "coulombic_efficiency", "energy_efficiency",
        "max_temperature_C", "min_voltage_V", "max_voltage_V", "n_datapoints",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    return path


def write_timeseries_sample(out_dir, cell_id, ts_rows):
    """Write timeseries_sample CSV for one cell."""
    path = os.path.join(out_dir, "timeseries_sample", f"{cell_id}.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fieldnames = [
        "cycle_number", "time_s", "voltage_V", "current_A",
        "capacity_Ah", "temperature_C",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ts_rows)
    return path


def write_metadata(out_dir, all_meta):
    """Write metadata.csv with one row per cell."""
    path = os.path.join(out_dir, "metadata.csv")
    fieldnames = [
        "cell_id", "brand", "cell_model", "form_factor", "chemistry",
        "nominal_capacity_Ah", "nominal_voltage_V",
        "charge_cutoff_V", "discharge_cutoff_V",
        "charge_rate", "discharge_rate", "temperature_C", "sample_id",
        "n_cycles", "n_datapoints",
        "first_discharge_capacity_Ah", "last_discharge_capacity_Ah",
        "capacity_retention_pct",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in sorted(all_meta, key=lambda x: x["cell_id"]):
            writer.writerow(m)
    return path


def main():
    print("=" * 60)
    print("ETL: NTU EEE Internal Battery Dataset")
    print("=" * 60)

    # Find all CSV files (exclude PDFs)
    csv_pattern = os.path.join(RAW_DIR, "*.csv")
    csv_files = sorted(glob.glob(csv_pattern))

    if not csv_files:
        print(f"\n[ERROR] No CSV files found in {RAW_DIR}/")
        print("Make sure you have copied the EEE folder contents to:")
        print(f"  {RAW_DIR}/")
        sys.exit(1)

    print(f"\nFound {len(csv_files)} CSV files in {RAW_DIR}/")
    os.makedirs(OUT_DIR, exist_ok=True)

    all_meta = []
    total_cycles = 0
    total_rows = 0

    for csv_path in csv_files:
        fname = os.path.basename(csv_path)
        cell_info = parse_filename(fname)
        brand = cell_info["brand"]
        specs = CELL_SPECS.get(brand, {})

        result = process_one_cell(csv_path, cell_info)

        # Write outputs
        write_cycle_summary(OUT_DIR, cell_info["cell_id"], result["cycle_summaries"])
        write_timeseries_sample(OUT_DIR, cell_info["cell_id"], result["timeseries_sample"])

        # Collect metadata
        retention = (
            round(result["last_discharge_Ah"] / result["first_discharge_Ah"] * 100, 2)
            if result["first_discharge_Ah"] > 0 else None
        )
        all_meta.append({
            "cell_id": cell_info["cell_id"],
            "brand": brand,
            "cell_model": specs.get("cell_model", ""),
            "form_factor": specs.get("form_factor", ""),
            "chemistry": specs.get("chemistry", ""),
            "nominal_capacity_Ah": specs.get("nominal_capacity_Ah", ""),
            "nominal_voltage_V": specs.get("nominal_voltage_V", ""),
            "charge_cutoff_V": specs.get("charge_cutoff_V", ""),
            "discharge_cutoff_V": specs.get("discharge_cutoff_V", ""),
            "charge_rate": cell_info["charge_rate"],
            "discharge_rate": cell_info["discharge_rate"],
            "temperature_C": cell_info["temperature_C"],
            "sample_id": cell_info["sample_id"],
            "n_cycles": result["n_cycles"],
            "n_datapoints": result["n_rows"],
            "first_discharge_capacity_Ah": round(result["first_discharge_Ah"], 6),
            "last_discharge_capacity_Ah": round(result["last_discharge_Ah"], 6),
            "capacity_retention_pct": retention,
        })

        total_cycles += result["n_cycles"]
        total_rows += result["n_rows"]

    # Write metadata
    meta_path = write_metadata(OUT_DIR, all_meta)

    # ── Summary ──
    print("\n" + "=" * 60)
    print("ETL COMPLETE")
    print("=" * 60)
    print(f"  Cells processed : {len(all_meta)}")
    print(f"  Total cycles    : {total_cycles:,}")
    print(f"  Total datapoints: {total_rows:,}")
    print(f"\nOutputs written to: {OUT_DIR}/")
    print(f"  {meta_path}")
    print(f"  {OUT_DIR}/cycle_summary/  ({len(all_meta)} files)")
    print(f"  {OUT_DIR}/timeseries_sample/  ({len(all_meta)} files)")


if __name__ == "__main__":
    main()
