#!/usr/bin/env python3
"""
BatteryTwin ETL — NASA PCoE Battery Aging Dataset
==================================================
一键生成:
  - NASA_PCoE_timeseries.parquet + .csv
  - NASA_PCoE_cycle_summary.csv

使用方法:
  1. 下载: https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip
  2. 解压 .mat 文件到某个目录
  3. 运行:
     python etl_nasa.py --input /path/to/mat_files --output /path/to/output

作者: Liu Kefan
日期: 2026-03-12
"""

import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
from scipy.io import loadmat
from pathlib import Path

# ================================================================
# 已知电池-温度映射 (来自NASA文档)
# ================================================================
CELL_TEMP = {
    "B0005": 24, "B0006": 24, "B0007": 24, "B0018": 24,
    "B0025": 24, "B0026": 24, "B0027": 24, "B0028": 24,
    "B0029": 43, "B0030": 43, "B0031": 43, "B0032": 43,
    "B0033": 4,  "B0034": 4,  "B0036": 4,
    "B0038": 24, "B0039": 24, "B0040": 24,
    "B0041": 24, "B0042": 24, "B0043": 24, "B0044": 24,
    "B0045": 43, "B0046": 43, "B0047": 43, "B0048": 43,
    "B0049": 4,  "B0050": 4,  "B0051": 4,  "B0052": 4,
    "B0053": 24, "B0054": 24, "B0055": 24, "B0056": 24,
}


def parse_one_mat(mat_path: str):
    """解析单个 .mat 文件，返回 (timeseries_rows, cycle_summary_rows)"""
    cell_id = Path(mat_path).stem
    mat = loadmat(mat_path, squeeze_me=True, struct_as_record=False)

    # 找到数据对象
    data_keys = [k for k in mat if not k.startswith("__")]
    if cell_id in mat:
        obj = mat[cell_id]
    elif data_keys:
        obj = mat[data_keys[0]]
    else:
        print(f"  ⚠️ {cell_id}: 无数据键, 跳过")
        return [], []

    cycles = obj.cycle
    if not hasattr(cycles, "__len__"):
        cycles = [cycles]

    ts_rows = []
    cs_rows = []

    for idx, cyc in enumerate(cycles):
        cycle_id = idx + 1
        step_type = str(getattr(cyc, "type", "unknown")).strip().lower()

        # 跳过 impedance
        if step_type == "impedance":
            continue

        data = getattr(cyc, "data", None)
        if data is None:
            continue

        # 提取数组
        try:
            V = np.asarray(data.Voltage_measured, dtype=float).ravel()
            I = np.asarray(data.Current_measured, dtype=float).ravel()
            T = np.asarray(data.Temperature_measured, dtype=float).ravel()
            t = np.asarray(data.Time, dtype=float).ravel()
        except Exception:
            continue

        n = min(len(V), len(I), len(T), len(t))
        if n == 0:
            continue
        V, I, T, t = V[:n], I[:n], T[:n], t[:n]

        # --- 容量 ---
        dchg_cap = np.full(n, np.nan)
        chg_cap = np.full(n, np.nan)

        if step_type == "discharge":
            try:
                raw_cap = np.asarray(data.Capacity, dtype=float).ravel()
                dchg_cap[:min(n, len(raw_cap))] = raw_cap[:n]
            except Exception:
                pass

        if step_type == "charge":
            dt = np.diff(t, prepend=t[0])
            chg_cap = np.cumsum(np.abs(I) * dt / 3600.0)

        # --- timeseries rows ---
        for j in range(n):
            ts_rows.append((
                cell_id, cycle_id, step_type, t[j],
                V[j], I[j], T[j],
                chg_cap[j] if step_type == "charge" else np.nan,
                dchg_cap[j] if step_type == "discharge" else np.nan,
            ))

        # --- cycle summary row ---
        dc_ah = np.nanmax(dchg_cap) if step_type == "discharge" and np.any(~np.isnan(dchg_cap)) else np.nan
        cc_ah = chg_cap[-1] if step_type == "charge" else np.nan

        cs_rows.append({
            "cell_id": cell_id,
            "cycle_id": cycle_id,
            "cycle_type": "aging",
            "charge_protocol_note": "CC-CV 1.5A/4.2V/20mA" if step_type == "charge" else "",
            "discharge_capacity_Ah": dc_ah,
            "charge_capacity_Ah": cc_ah,
            "discharge_energy_Wh": np.nan,
            "charge_energy_Wh": np.nan,
            "coulombic_efficiency": np.nan,
            "temperature_max_C": float(np.nanmax(T)),
            "temperature_avg_C": float(np.nanmean(T)),
            "temperature_min_C": float(np.nanmin(T)),
            "charge_duration_s": float(t[-1] - t[0]) if step_type == "charge" else np.nan,
            "discharge_duration_s": float(t[-1] - t[0]) if step_type == "discharge" else np.nan,
            "internal_resistance_Ohm": np.nan,
            "cycle_end_flag": "normal",
        })

    return ts_rows, cs_rows


def detect_capacity_jumps(cs_df: pd.DataFrame) -> pd.DataFrame:
    """标记容量异常跳变"""
    for cid in cs_df["cell_id"].unique():
        mask = (cs_df["cell_id"] == cid) & cs_df["discharge_capacity_Ah"].notna()
        caps = cs_df.loc[mask, "discharge_capacity_Ah"].values
        if len(caps) < 2:
            continue
        diffs = np.abs(np.diff(caps))
        med = np.median(diffs[diffs > 0]) if np.any(diffs > 0) else 0
        threshold = max(med * 5, 0.05)
        jump_pos = np.where(diffs > threshold)[0] + 1
        idx_list = cs_df.loc[mask].index.tolist()
        for p in jump_pos:
            if p < len(idx_list):
                cs_df.loc[idx_list[p], "cycle_end_flag"] = "capacity_jump"
    return cs_df


def main():
    parser = argparse.ArgumentParser(description="NASA PCoE Battery ETL")
    parser.add_argument("--input", "-i", required=True,
                        help="包含 .mat 文件的目录路径")
    parser.add_argument("--output", "-o", default=".",
                        help="输出目录 (默认当前目录)")
    args = parser.parse_args()

    # 查找 .mat 文件
    mat_files = sorted(glob.glob(os.path.join(args.input, "*.mat")))
    if not mat_files:
        mat_files = sorted(glob.glob(os.path.join(args.input, "**", "*.mat"), recursive=True))
    if not mat_files:
        print(f"❌ 在 {args.input} 中未找到 .mat 文件")
        print(f"   请先下载: https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip")
        sys.exit(1)

    print(f"📂 发现 {len(mat_files)} 个 .mat 文件")

    # 解析
    all_ts = []
    all_cs = []

    for mf in mat_files:
        cid = Path(mf).stem
        print(f"  处理 {cid}...", end=" ")
        ts, cs = parse_one_mat(mf)
        print(f"✓ ({len(ts):,} timeseries rows, {len(cs)} cycles)")
        all_ts.extend(ts)
        all_cs.extend(cs)

    # 构建 DataFrame
    ts_cols = ["cell_id", "cycle_id", "step_type", "time_s",
               "voltage_V", "current_A", "temperature_C",
               "charge_capacity_Ah", "discharge_capacity_Ah"]
    ts_df = pd.DataFrame(all_ts, columns=ts_cols)
    cs_df = pd.DataFrame(all_cs)

    # 后处理
    cs_df = detect_capacity_jumps(cs_df)

    # 保存
    os.makedirs(args.output, exist_ok=True)
    ds = "NASA_PCoE"

    # timeseries parquet
    ts_pq = os.path.join(args.output, f"{ds}_timeseries.parquet")
    ts_df.to_parquet(ts_pq, index=False, engine="pyarrow")
    sz = os.path.getsize(ts_pq) / 1024 / 1024
    print(f"\n✅ {ts_pq}  ({len(ts_df):,} rows, {sz:.1f} MB)")

    # timeseries csv
    ts_csv = os.path.join(args.output, f"{ds}_timeseries.csv")
    ts_df.to_csv(ts_csv, index=False)
    print(f"✅ {ts_csv}")

    # cycle summary
    cs_path = os.path.join(args.output, f"{ds}_cycle_summary.csv")
    cs_df.to_csv(cs_path, index=False)
    print(f"✅ {cs_path}  ({len(cs_df):,} rows)")

    # 统计摘要
    print(f"\n📊 统计摘要:")
    print(f"   电池数: {ts_df['cell_id'].nunique()}")
    print(f"   时序总行数: {len(ts_df):,}")
    print(f"   Cycle总数: {len(cs_df):,}")
    dc = cs_df["discharge_capacity_Ah"].dropna()
    if len(dc) > 0:
        print(f"   放电容量范围: [{dc.min():.4f}, {dc.max():.4f}] Ah")
    jumps = cs_df[cs_df["cycle_end_flag"] == "capacity_jump"]
    if len(jumps) > 0:
        print(f"   容量跳变标记: {len(jumps)} cycles")

    print(f"\n🎉 完成! 输出目录: {args.output}")


if __name__ == "__main__":
    main()
