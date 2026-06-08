#!/usr/bin/env python3
"""
NASA PCoE 数据质检与可视化
===========================
生成:
  - 容量衰减曲线 (5 cells)
  - SOH曲线
  - 电压Profile (3 cells)
  - 温度分布
  - 质检报告

用法:
  python quality_check_nasa.py --input /path/to/processed_output
"""

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True,
                        help="包含 NASA_PCoE_*.csv/parquet 的目录")
    args = parser.parse_args()

    ds = "NASA_PCoE"
    d = args.input

    # ---- 加载数据 ----
    cs_path = os.path.join(d, f"{ds}_cycle_summary.csv")
    meta_path = os.path.join(d, f"{ds}_metadata.csv")

    ts_pq = os.path.join(d, f"{ds}_timeseries.parquet")
    ts_csv = os.path.join(d, f"{ds}_timeseries.csv")

    cs = pd.read_csv(cs_path)
    meta = pd.read_csv(meta_path)

    ts = None
    if os.path.exists(ts_pq):
        ts = pd.read_parquet(ts_pq)
    elif os.path.exists(ts_csv):
        ts = pd.read_csv(ts_csv)

    print(f"📋 metadata: {len(meta)} cells")
    print(f"📋 cycle_summary: {len(cs):,} rows, {cs['cell_id'].nunique()} cells")
    if ts is not None:
        print(f"📋 timeseries: {len(ts):,} rows")

    # ---- 质检 ----
    print(f"\n{'='*50}")
    print("数据质检")
    print(f"{'='*50}")

    # metadata完整性
    for col in meta.columns:
        n_null = meta[col].isna().sum()
        if n_null > 0:
            print(f"  ⚠️ metadata.{col}: {n_null} null")

    # 放电容量检查
    dc = cs["discharge_capacity_Ah"].dropna()
    print(f"\n  放电容量: {len(dc)} 条有效记录")
    print(f"  范围: [{dc.min():.4f}, {dc.max():.4f}] Ah")
    if dc.min() < 0 or dc.max() > 3.0:
        print(f"  ❌ 容量范围异常!")

    # 标记
    flags = cs["cycle_end_flag"].value_counts()
    print(f"\n  cycle_end_flag:")
    for f, c in flags.items():
        print(f"    {f}: {c}")

    # timeseries检查
    if ts is not None:
        print(f"\n  电压: [{ts['voltage_V'].min():.3f}, {ts['voltage_V'].max():.3f}] V")
        print(f"  电流: [{ts['current_A'].min():.3f}, {ts['current_A'].max():.3f}] A")
        if ts["temperature_C"].notna().any():
            print(f"  温度: [{ts['temperature_C'].min():.1f}, {ts['temperature_C'].max():.1f}] °C")

    # ---- 可视化 ----
    print(f"\n📊 生成可视化...")

    # 选出 discharge 数据最多的 5 个 cell
    dc_df = cs[cs["discharge_capacity_Ah"].notna()]
    top5 = dc_df.groupby("cell_id").size().nlargest(5).index.tolist()

    # 图1: 容量衰减 + SOH
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for cid in top5:
        sub = dc_df[dc_df["cell_id"] == cid].sort_values("cycle_id")
        ax1.plot(sub["cycle_id"], sub["discharge_capacity_Ah"],
                 label=cid, linewidth=1.2, alpha=0.8)
        init = sub["discharge_capacity_Ah"].iloc[0]
        if init > 0:
            ax2.plot(sub["cycle_id"], sub["discharge_capacity_Ah"] / init * 100,
                     label=cid, linewidth=1.2, alpha=0.8)

    ax1.set_xlabel("Cycle")
    ax1.set_ylabel("Discharge Capacity (Ah)")
    ax1.set_title("NASA PCoE — Capacity Degradation")
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    ax2.axhline(70, color="red", ls="--", alpha=0.5, label="70% EOL")
    ax2.set_xlabel("Cycle")
    ax2.set_ylabel("SOH (%)")
    ax2.set_title("NASA PCoE — SOH")
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    fig1_path = os.path.join(d, f"{ds}_capacity_degradation.png")
    plt.savefig(fig1_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ {fig1_path}")

    # 图2: 电压曲线 (如果有timeseries)
    if ts is not None:
        sel_cells = top5[:3]
        fig2, axes = plt.subplots(len(sel_cells), 2, figsize=(14, 4 * len(sel_cells)))
        if len(sel_cells) == 1:
            axes = axes.reshape(1, -1)

        for i, cid in enumerate(sel_cells):
            ct = ts[ts["cell_id"] == cid]
            avail = sorted(ct["cycle_id"].unique())
            early = avail[min(1, len(avail) - 1)]
            mid = avail[len(avail) // 2]

            for j, (cyc, lab) in enumerate([(early, f"Cycle {early}"), (mid, f"Cycle {mid}")]):
                sub = ct[ct["cycle_id"] == cyc]
                axes[i][j].plot(sub["time_s"], sub["voltage_V"], color="steelblue", lw=0.8)
                axes[i][j].set_xlabel("Time (s)")
                axes[i][j].set_ylabel("Voltage (V)")
                axes[i][j].set_title(f"{cid} — {lab}")
                axes[i][j].grid(True, alpha=0.3)

        plt.suptitle("NASA PCoE — Voltage Profiles", fontsize=13, y=1.01)
        plt.tight_layout()
        fig2_path = os.path.join(d, f"{ds}_voltage_profiles.png")
        plt.savefig(fig2_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  ✅ {fig2_path}")

    print(f"\n🎉 质检完成!")


if __name__ == "__main__":
    main()
