#!/usr/bin/env python3
"""
Quality Check script for Dataset_03: Stanford-MIT-TRI
Generates QC plots for capacity degradation, voltage profiles, etc.

Usage:
    python scripts/quality_check_stanford.py \
        --input data/processed/dataset_03_Stanford_MIT_TRI \
        --output docs/qc_reports/dataset_03
"""

import argparse
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def plot_capacity_degradation(cs_df, output_dir):
    """Plot discharge capacity vs cycle number for all cells."""
    fig, ax = plt.subplots(figsize=(12, 6))

    cells = cs_df["cell_id"].unique()
    cmap = plt.cm.viridis(np.linspace(0, 1, len(cells)))

    for i, cell_id in enumerate(cells):
        cell_data = cs_df[cs_df["cell_id"] == cell_id]
        ax.plot(
            cell_data["cycle_number"],
            cell_data["discharge_capacity_Ah"],
            alpha=0.4,
            linewidth=0.5,
            color=cmap[i],
        )

    ax.set_xlabel("Cycle Number")
    ax.set_ylabel("Discharge Capacity (Ah)")
    ax.set_title("Stanford-MIT-TRI: Capacity Degradation (All Cells)")
    ax.set_ylim(0.8, 1.15)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "capacity_degradation.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅ {path}")


def plot_cycle_life_distribution(meta_df, output_dir):
    """Plot histogram of cycle life across all cells."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Overall histogram
    axes[0].hist(meta_df["cycle_life"], bins=30, edgecolor="black", alpha=0.7, color="steelblue")
    axes[0].set_xlabel("Cycle Life")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Cycle Life Distribution (All Cells)")
    axes[0].axvline(meta_df["cycle_life"].median(), color="red", linestyle="--",
                    label=f'Median: {meta_df["cycle_life"].median():.0f}')
    axes[0].legend()

    # Per-batch boxplot
    batches = meta_df.groupby("batch")["cycle_life"].apply(list).to_dict()
    batch_labels = sorted(batches.keys())
    batch_data = [batches[b] for b in batch_labels]
    axes[1].boxplot(batch_data, labels=batch_labels)
    axes[1].set_xlabel("Batch")
    axes[1].set_ylabel("Cycle Life")
    axes[1].set_title("Cycle Life by Batch")
    axes[1].grid(True, alpha=0.3)

    path = os.path.join(output_dir, "cycle_life_distribution.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅ {path}")


def plot_ir_trends(cs_df, output_dir):
    """Plot internal resistance trend over cycles."""
    fig, ax = plt.subplots(figsize=(12, 6))

    cells = cs_df["cell_id"].unique()
    cmap = plt.cm.plasma(np.linspace(0, 1, len(cells)))

    for i, cell_id in enumerate(cells):
        cell_data = cs_df[cs_df["cell_id"] == cell_id]
        ir = cell_data["internal_resistance_ohm"]
        # Filter out zero/invalid IR
        valid = ir > 0
        if valid.sum() > 0:
            ax.plot(
                cell_data.loc[valid, "cycle_number"],
                ir[valid] * 1000,  # Convert to mΩ
                alpha=0.4,
                linewidth=0.5,
                color=cmap[i],
            )

    ax.set_xlabel("Cycle Number")
    ax.set_ylabel("Internal Resistance (mΩ)")
    ax.set_title("Stanford-MIT-TRI: Internal Resistance Trend")
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "ir_trends.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅ {path}")


def plot_charge_time_distribution(cs_df, output_dir):
    """Plot charge time trends."""
    fig, ax = plt.subplots(figsize=(12, 6))

    cells = cs_df["cell_id"].unique()
    sample_cells = cells[::max(1, len(cells) // 20)]  # Sample ~20 cells for clarity

    for cell_id in sample_cells:
        cell_data = cs_df[cs_df["cell_id"] == cell_id]
        valid = cell_data["charge_time_min"] > 0
        if valid.sum() > 0:
            ax.plot(
                cell_data.loc[valid, "cycle_number"],
                cell_data.loc[valid, "charge_time_min"],
                alpha=0.5,
                linewidth=0.8,
                label=cell_id,
            )

    ax.set_xlabel("Cycle Number")
    ax.set_ylabel("Charge Time (min)")
    ax.set_title("Stanford-MIT-TRI: Charge Time Trend (Sample Cells)")
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "charge_time_trends.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅ {path}")


def print_summary_stats(meta_df, cs_df):
    """Print summary statistics."""
    print("\n📊 Summary Statistics")
    print(f"  Total cells: {len(meta_df)}")
    print(f"  Batches: {meta_df['batch'].nunique()}")
    for b in sorted(meta_df["batch"].unique()):
        n = len(meta_df[meta_df["batch"] == b])
        print(f"    {b}: {n} cells")

    print(f"\n  Cycle life range: {meta_df['cycle_life'].min()} – {meta_df['cycle_life'].max()}")
    print(f"  Cycle life median: {meta_df['cycle_life'].median():.0f}")
    print(f"  Cycle life mean: {meta_df['cycle_life'].mean():.0f}")

    print(f"\n  Total cycle_summary rows: {len(cs_df):,}")
    print(f"  Discharge capacity range: {cs_df['discharge_capacity_Ah'].min():.4f} – "
          f"{cs_df['discharge_capacity_Ah'].max():.4f} Ah")

    ir_valid = cs_df[cs_df["internal_resistance_ohm"] > 0]["internal_resistance_ohm"]
    if len(ir_valid) > 0:
        print(f"  IR range: {ir_valid.min()*1000:.2f} – {ir_valid.max()*1000:.2f} mΩ")

    ct_valid = cs_df[cs_df["charge_time_min"] > 0]["charge_time_min"]
    if len(ct_valid) > 0:
        print(f"  Charge time range: {ct_valid.min():.1f} – {ct_valid.max():.1f} min")


def main():
    parser = argparse.ArgumentParser(description="Quality check for Stanford-MIT-TRI dataset")
    parser.add_argument("--input", required=True, help="Path to processed data directory")
    parser.add_argument("--output", required=True, help="Path to QC output directory")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # Load data
    meta_path = os.path.join(args.input, "Stanford_MIT_TRI_metadata.csv")
    cs_path = os.path.join(args.input, "Stanford_MIT_TRI_cycle_summary.csv")

    print("Loading data...")
    meta_df = pd.read_csv(meta_path)
    cs_df = pd.read_csv(cs_path)

    print_summary_stats(meta_df, cs_df)

    print("\nGenerating QC plots...")
    plot_capacity_degradation(cs_df, args.output)
    plot_cycle_life_distribution(meta_df, args.output)
    plot_ir_trends(cs_df, args.output)
    plot_charge_time_distribution(cs_df, args.output)

    print("\n✅ All QC plots generated!")


if __name__ == "__main__":
    main()
