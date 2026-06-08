#!/usr/bin/env python3
"""
Quality Check script for Dataset 04: Oxford Battery Degradation

Usage:
    conda activate batterytwin
    cd ~/Projects/BatteryTwin-Benchmark-DataPrep
    python scripts/quality_check_oxford.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

REPO_ROOT = os.path.expanduser("~/Projects/BatteryTwin-Benchmark-DataPrep")
PROC_DIR = os.path.join(REPO_ROOT, "data/processed/dataset_04")
QC_DIR = os.path.join(REPO_ROOT, "docs/qc_reports/dataset_04")
os.makedirs(QC_DIR, exist_ok=True)

def check_metadata():
    """Validate metadata.csv."""
    meta_path = os.path.join(PROC_DIR, "Oxford_metadata.csv")
    if not os.path.exists(meta_path):
        print("[SKIP] metadata.csv not found")
        return
    df = pd.read_csv(meta_path)
    print(f"\n=== Metadata Check ===")
    print(f"  Total cells: {len(df)}")
    print(f"  Sub-datasets: {df['sub_dataset'].value_counts().to_dict()}")
    print(f"  Chemistries: {df['chemistry'].unique()}")
    print(f"  Null counts:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
    return df

def check_cycle_summaries():
    """Validate cycle_summary files and plot degradation curves."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for idx, subdir in enumerate(['kokam_lco', 'nca_18650']):
        cs_path = os.path.join(PROC_DIR, subdir, f"Oxford_{subdir}_cycle_summary.csv")
        if not os.path.exists(cs_path):
            print(f"[SKIP] {cs_path} not found")
            continue

        df = pd.read_csv(cs_path)
        print(f"\n=== Cycle Summary: {subdir} ===")
        print(f"  Total rows: {len(df)}")
        print(f"  Cells: {df['cell_id'].nunique()}")
        print(f"  Cycle range: {df['cycle_number'].min()} - {df['cycle_number'].max()}")
        print(f"  Capacity range (Ah): {df['discharge_capacity_Ah'].min():.4f} - {df['discharge_capacity_Ah'].max():.4f}")

        # Check for anomalies
        if df['discharge_capacity_Ah'].isnull().any():
            print(f"  [WARN] {df['discharge_capacity_Ah'].isnull().sum()} null capacity values")

        # Plot degradation curves
        ax = axes[idx]
        for cell_id, group in df.groupby('cell_id'):
            ax.plot(group['cycle_number'], group['discharge_capacity_Ah'], '-o', markersize=3, label=cell_id)
        ax.set_xlabel('Cycle Number')
        ax.set_ylabel('Discharge Capacity (Ah)')
        ax.set_title(f'Degradation: {subdir}')
        ax.legend(fontsize=7, loc='best')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path = os.path.join(QC_DIR, "degradation_curves.png")
    plt.savefig(fig_path, dpi=150)
    print(f"\nDegradation plot saved: {fig_path}")
    plt.close()

def check_timeseries_samples():
    """Spot-check timeseries index files."""
    print(f"\n=== Timeseries Index Check ===")
    for subdir in ['kokam_lco', 'nca_18650']:
        ts_dir = os.path.join(PROC_DIR, subdir)
        if not os.path.isdir(ts_dir):
            continue
        txt_files = [f for f in os.listdir(ts_dir) if f.endswith('.csv.txt')]
        print(f"\n  {subdir}: {len(txt_files)} index files")
        if txt_files:
            sample = pd.read_csv(os.path.join(ts_dir, txt_files[0]))
            print(f"  Sample file: {txt_files[0]}")
            print(f"  Columns: {list(sample.columns)}")
            print(f"  Rows: {len(sample)}")
            print(f"  Head:\n{sample.head(3).to_string()}")

def check_unit_conversion():
    """Verify mAh → Ah conversion for Kokam."""
    print(f"\n=== Unit Conversion Check (Kokam) ===")
    cs_path = os.path.join(PROC_DIR, "kokam_lco/Oxford_kokam_lco_cycle_summary.csv")
    if not os.path.exists(cs_path):
        print("  [SKIP] Cycle summary not found")
        return
    df = pd.read_csv(cs_path)
    # Kokam nominal = 0.740 Ah. If values are >> 1 Ah, conversion likely failed
    max_cap = df['discharge_capacity_Ah'].max()
    if max_cap > 2.0:
        print(f"  [ERROR] Max capacity = {max_cap:.3f} Ah. Still in mAh? Expected ~0.74 Ah")
    elif max_cap < 0.1:
        print(f"  [ERROR] Max capacity = {max_cap:.6f} Ah. Double-converted?")
    else:
        print(f"  [OK] Max capacity = {max_cap:.4f} Ah (expected ~0.740 Ah)")

def main():
    print("=" * 60)
    print("Quality Check: Dataset 04 - Oxford Battery Degradation")
    print("=" * 60)

    check_metadata()
    check_cycle_summaries()
    check_timeseries_samples()
    check_unit_conversion()

    print(f"\n{'=' * 60}")
    print(f"QC plots saved to: {QC_DIR}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
