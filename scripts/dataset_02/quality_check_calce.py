#!/usr/bin/env python3
"""
Quality Check script for Dataset 02: CALCE CS2
================================================
Reads processed data and generates QC report + visualizations.

Usage:
    python scripts/quality_check_calce.py \
        --input data/processed/dataset_02 \
        --output docs/qc_reports/dataset_02

Author: Liu Kefan (liukefan821)
"""

import argparse
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


def main():
    parser = argparse.ArgumentParser(description="QC for CALCE CS2 dataset")
    parser.add_argument("--input", required=True, help="Path to data/processed/dataset_02/")
    parser.add_argument("--output", required=True, help="Path to docs/qc_reports/dataset_02/")
    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    # ----------------------------------------------------------
    # Load data
    # ----------------------------------------------------------
    meta_path = os.path.join(input_dir, "CALCE_CS2_metadata.csv")
    cs_path = os.path.join(input_dir, "CALCE_CS2_cycle_summary.csv")
    ts_path = os.path.join(input_dir, "CALCE_CS2_timeseries.parquet")

    meta = pd.read_csv(meta_path) if os.path.exists(meta_path) else None
    cs = pd.read_csv(cs_path) if os.path.exists(cs_path) else None

    # Try parquet first, fallback to CSV
    if os.path.exists(ts_path):
        ts = pd.read_parquet(ts_path)
    else:
        ts_csv = ts_path.replace(".parquet", ".csv")
        ts = pd.read_csv(ts_csv) if os.path.exists(ts_csv) else None

    print("=== CALCE CS2 Quality Check Report ===\n")

    # ----------------------------------------------------------
    # 1. Metadata check
    # ----------------------------------------------------------
    if meta is not None:
        print(f"Metadata: {len(meta)} cells")
        print(f"  Columns: {list(meta.columns)}")
        missing = meta.isnull().sum()
        if missing.any():
            print(f"  Missing values:\n{missing[missing > 0].to_string()}")
        print()

    # ----------------------------------------------------------
    # 2. Timeseries check
    # ----------------------------------------------------------
    if ts is not None:
        print(f"Timeseries: {len(ts):,} rows, {ts['cell_id'].nunique()} cells")
        print(f"  Voltage range: {ts['voltage_V'].min():.4f} ~ {ts['voltage_V'].max():.4f} V")
        print(f"  Current range: {ts['current_A'].min():.4f} ~ {ts['current_A'].max():.4f} A")
        print(f"  Null counts:")
        for c in ts.columns:
            n_null = ts[c].isnull().sum()
            pct = n_null / len(ts) * 100
            if n_null > 0:
                print(f"    {c}: {n_null:,} ({pct:.1f}%)")

        # Check cell_ids in timeseries vs metadata
        if meta is not None:
            ts_cells = set(ts["cell_id"].unique())
            meta_cells = set(meta["cell_id"].unique())
            only_ts = ts_cells - meta_cells
            only_meta = meta_cells - ts_cells
            if only_ts:
                print(f"  ⚠️ Cells in timeseries but NOT in metadata: {only_ts}")
            if only_meta:
                print(f"  ⚠️ Cells in metadata but NOT in timeseries: {only_meta}")
        print()

    # ----------------------------------------------------------
    # 3. Cycle summary check
    # ----------------------------------------------------------
    if cs is not None:
        print(f"Cycle Summary: {len(cs):,} rows, {cs['cell_id'].nunique()} cells")
        dch = cs[cs["step_type"] == "discharge"]
        if not dch.empty:
            print(f"  Discharge capacity range: {dch['capacity_Ah'].min():.4f} ~ {dch['capacity_Ah'].max():.4f} Ah")
            print(f"  SOH range: {dch['SOH'].min():.1f}% ~ {dch['SOH'].max():.1f}%")
            print(f"  Null capacity rows: {dch['capacity_Ah'].isnull().sum()}")
        print()

    # ----------------------------------------------------------
    # 4. Visualizations
    # ----------------------------------------------------------
    print("Generating plots...")
    plt.style.use("seaborn-v0_8-whitegrid")

    # --- Plot 1: Capacity degradation curves ---
    if cs is not None:
        dch = cs[(cs["step_type"] == "discharge") & (cs["capacity_Ah"].notna()) & (cs["capacity_Ah"] > 0)]
        if not dch.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            for cell_id, grp in dch.groupby("cell_id"):
                ax.plot(grp["cycle_id"], grp["capacity_Ah"], label=cell_id, alpha=0.8, linewidth=1)
            ax.set_xlabel("Cycle ID")
            ax.set_ylabel("Discharge Capacity (Ah)")
            ax.set_title("CALCE CS2 — Capacity Degradation")
            ax.legend(fontsize=7, ncol=3, loc="upper right")
            ax.axhline(y=1.1 * 0.7, color="red", linestyle="--", alpha=0.5, label="70% EOL")
            fig.tight_layout()
            fig.savefig(os.path.join(output_dir, "capacity_degradation.png"), dpi=150)
            plt.close(fig)
            print("  ✅ capacity_degradation.png")

    # --- Plot 2: Voltage profiles (sample cycles) ---
    if ts is not None:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        sample_cells = ts["cell_id"].unique()[:4]
        for ax, cell_id in zip(axes.flat, sample_cells):
            cell_ts = ts[ts["cell_id"] == cell_id]
            sample_cycles = sorted(cell_ts["cycle_id"].unique())[:5]
            for cyc in sample_cycles:
                cyc_data = cell_ts[cell_ts["cycle_id"] == cyc]
                t = cyc_data["time_s"] - cyc_data["time_s"].min()
                ax.plot(t, cyc_data["voltage_V"], alpha=0.7, linewidth=0.8, label=f"Cycle {cyc}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Voltage (V)")
            ax.set_title(f"{cell_id}")
            ax.legend(fontsize=6)
        fig.suptitle("CALCE CS2 — Voltage Profiles (First Cycles)", fontsize=14)
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, "voltage_profiles.png"), dpi=150)
        plt.close(fig)
        print("  ✅ voltage_profiles.png")

    # --- Plot 3: SOH distribution across cells ---
    if cs is not None:
        dch = cs[(cs["step_type"] == "discharge") & (cs["SOH"].notna())]
        if not dch.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            # Get last SOH per cell
            last_soh = dch.groupby("cell_id")["SOH"].last().sort_values()
            ax.barh(last_soh.index, last_soh.values, color="steelblue")
            ax.axvline(x=70, color="red", linestyle="--", label="70% EOL threshold")
            ax.set_xlabel("Final SOH (%)")
            ax.set_title("CALCE CS2 — Final SOH per Cell")
            ax.legend()
            fig.tight_layout()
            fig.savefig(os.path.join(output_dir, "soh_distribution.png"), dpi=150)
            plt.close(fig)
            print("  ✅ soh_distribution.png")

    print("\n=== QC Complete ===")


if __name__ == "__main__":
    main()
