#!/usr/bin/env python3
"""
ETL: Dataset 38 - ISU-ILCC Battery Aging Dataset (Thelen 2023)
251 NMC/Gr Li-polymer cells, 63 conditions, 3 stress factors

Usage:
    conda activate batterytwin
    cd ~/Projects/BatteryTwin-Benchmark-DataPrep
    python scripts/etl_isu_ilcc.py
"""

import os
import glob
import pandas as pd
import numpy as np
from tqdm import tqdm

# ── 路径配置 ──────────────────────────────────────────────
REPO_ROOT    = os.path.expanduser("~/Projects/BatteryTwin-Benchmark-DataPrep")
RAW_DIR      = os.path.join(REPO_ROOT, "data/raw/dataset_38_ISU_ILCC/raw_unzipped")
VALID_CSV    = os.path.join(REPO_ROOT, "data/raw/dataset_38_ISU_ILCC/Valid_cells.csv")
PROC_DIR     = os.path.join(REPO_ROOT, "data/processed/dataset_38")
os.makedirs(PROC_DIR, exist_ok=True)

# 电池参数（来自论文）
CELL_INFO = {
    "chemistry":          "NMC/Graphite",
    "form_factor":        "pouch",
    "dimensions_mm":      "50x20x3",   # 502030 规格
    "nominal_capacity_Ah": 0.25,       # 250 mAh
    "voltage_range_V":    "3.0-4.2",
    "manufacturer":       "Honghaosheng Electronics, Shenzhen",
}

def get_valid_cells():
    """读取有效电池列表"""
    df = pd.read_csv(VALID_CSV)
    return set(df['Cell'].str.strip().tolist())

def process_cycle_summary():
    """处理 capacity_fade 数据 → cycle summary"""
    all_dfs = []
    valid_cells = get_valid_cells()

    for release in ['Release 1.0', 'Release 2.0']:
        fade_dir = os.path.join(RAW_DIR, "capacity_fade", release)
        if not os.path.isdir(fade_dir):
            continue
        csv_files = sorted(glob.glob(os.path.join(fade_dir, "*.csv")))
        for csv_path in tqdm(csv_files, desc=f"Cycle summary {release}"):
            cell_id = os.path.basename(csv_path).replace('.csv', '')
            if cell_id not in valid_cells:
                continue
            try:
                df = pd.read_csv(csv_path)
                df.columns = ['time_days', 'capacity_Ah']
                df['cell_id']  = f"ISU_ILCC_{cell_id}"
                df['cycle_id'] = range(len(df))
                df['release']  = release.replace(' ', '_')
                all_dfs.append(df)
            except Exception as e:
                print(f"  [WARN] 跳过 {cell_id}: {e}")

    if not all_dfs:
        return None
    cs = pd.concat(all_dfs, ignore_index=True)
    cs = cs[['cell_id', 'cycle_id', 'time_days', 'capacity_Ah', 'release']]
    return cs

def process_timeseries():
    """处理 Q_interpolated → timeseries（宽表转长表）"""
    all_dfs = []
    valid_cells = get_valid_cells()

    for release in ['Release 1.0', 'Release 2.0']:
        q_dir = os.path.join(RAW_DIR, "Q_interpolated", release)
        if not os.path.isdir(q_dir):
            continue
        csv_files = sorted(glob.glob(os.path.join(q_dir, "*.csv")))
        for csv_path in tqdm(csv_files, desc=f"Timeseries {release}"):
            cell_id = os.path.basename(csv_path).replace('.csv', '')
            if cell_id not in valid_cells:
                continue
            try:
                # 每行是一个 cycle 的插值放电曲线
                df_wide = pd.read_csv(csv_path, header=None)
                n_cycles, n_points = df_wide.shape
                # 转成长表
                records = []
                for cycle_idx in range(n_cycles):
                    q_values = df_wide.iloc[cycle_idx].values
                    # 归一化 SOC 轴（0到1等分）
                    soc = np.linspace(0, 1, n_points)
                    for j in range(n_points):
                        records.append({
                            'cell_id':    f"ISU_ILCC_{cell_id}",
                            'cycle_id':   cycle_idx,
                            'soc':        round(soc[j], 4),
                            'capacity_Ah': q_values[j],
                            'release':    release.replace(' ', '_'),
                        })
                all_dfs.append(pd.DataFrame(records))
            except Exception as e:
                print(f"  [WARN] 跳过 {cell_id}: {e}")

    if not all_dfs:
        return None
    return pd.concat(all_dfs, ignore_index=True)

def process_metadata():
    """生成 metadata，每个有效电池一行"""
    valid_cells = get_valid_cells()
    rows = []
    for cell_id in sorted(valid_cells):
        rows.append({
            'cell_id':              f"ISU_ILCC_{cell_id}",
            'original_cell_id':     cell_id,
            'chemistry':            CELL_INFO['chemistry'],
            'cell_form_factor':     CELL_INFO['form_factor'],
            'cell_dimensions_mm':   CELL_INFO['dimensions_mm'],
            'nominal_capacity_Ah':  CELL_INFO['nominal_capacity_Ah'],
            'voltage_range_V':      CELL_INFO['voltage_range_V'],
            'manufacturer':         CELL_INFO['manufacturer'],
            'dataset':              'dataset_38',
            'source':               'Iowa State DataShare 22582234',
        })
    return pd.DataFrame(rows)

def main():
    print("=" * 60)
    print("ETL: Dataset 38 - ISU-ILCC Battery Aging")
    print("=" * 60)

    # 1. Cycle summary
    print("\n[1/3] 处理 cycle summary...")
    cs = process_cycle_summary()
    if cs is not None:
        out_cs = os.path.join(PROC_DIR, "ISU_ILCC_cycle_summary.csv")
        cs.to_csv(out_cs, index=False)
        print(f"  ✅ Cycle summary: {len(cs):,} 行 → {out_cs}")

    # 2. Timeseries
    print("\n[2/3] 处理 timeseries (Q_interpolated)...")
    ts = process_timeseries()
    if ts is not None:
        out_ts = os.path.join(PROC_DIR, "ISU_ILCC_timeseries.parquet")
        ts.to_parquet(out_ts, index=False)
        print(f"  ✅ Timeseries: {len(ts):,} 行 → {out_ts}")

        sample_path = os.path.join(PROC_DIR, "ISU_ILCC_timeseries_SAMPLE.csv")
        ts.head(100).to_csv(sample_path, index=False)
        print(f"  ✅ Sample CSV: {sample_path}")

    # 3. Metadata
    print("\n[3/3] 生成 metadata...")
    meta = process_metadata()
    out_meta = os.path.join(PROC_DIR, "ISU_ILCC_metadata.csv")
    meta.to_csv(out_meta, index=False)
    print(f"  ✅ Metadata: {len(meta)} 个电池 → {out_meta}")
    print(f"  电池形状: {CELL_INFO['form_factor']}")
    print(f"  尺寸: {CELL_INFO['dimensions_mm']} mm")
    print(f"  标称容量: {CELL_INFO['nominal_capacity_Ah']} Ah")

    print("\n" + "=" * 60)
    print("ETL COMPLETE ✅")
    print("=" * 60)

if __name__ == "__main__":
    main()
