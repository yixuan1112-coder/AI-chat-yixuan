#!/usr/bin/env python3
"""
ETL: Dataset 36 - Imperial College 21700 Cycle Aging (Kirkaldy 2024)
Experiment 2,2 - C-based Degradation 2

Usage:
    conda activate batterytwin
    cd ~/Projects/BatteryTwin-Benchmark-DataPrep
    python scripts/etl_imperial_21700.py
"""

import os
import glob
import re
import pandas as pd
from tqdm import tqdm

# ── 路径配置 ──────────────────────────────────────────────
REPO_ROOT   = os.path.expanduser("~/Projects/BatteryTwin-Benchmark-DataPrep")
RAW_DIR     = os.path.join(REPO_ROOT, "data/raw/dataset_36_Imperial_21700/raw_unzipped/Expt 2,2 - C-based Degradation 2")
PROC_DIR    = os.path.join(REPO_ROOT, "data/processed/dataset_36")
os.makedirs(PROC_DIR, exist_ok=True)

# cell 对应温度（从文件名 Summary Data 得知）
CELL_TEMP = {
    "A": 10, "B": 10,
    "C": 25, "D": 25,
    "E": 40, "F": 40,
}

def parse_rpt_number(filename):
    """从文件名提取 RPT 编号，如 RPT0 -> 0"""
    m = re.search(r'RPT(\d+)', filename)
    return int(m.group(1)) if m else -1

def process_timeseries():
    """处理 0.1C Voltage Curves，合并所有 cell 所有 RPT"""
    base = os.path.join(RAW_DIR, "Processed Timeseries Data", "0.1C Voltage Curves")
    all_dfs = []

    cells = sorted(os.listdir(base))
    for cell_name in tqdm(cells, desc="Processing cells"):
        cell_dir = os.path.join(base, cell_name)
        if not os.path.isdir(cell_dir):
            continue

        cell_id = cell_name.replace("cell ", "").strip()  # "A", "B", ...
        temp_c  = CELL_TEMP.get(cell_id, -1)

        csv_files = sorted(glob.glob(os.path.join(cell_dir, "*.csv")))
        for csv_path in csv_files:
            rpt_num = parse_rpt_number(os.path.basename(csv_path))
            try:
                df = pd.read_csv(csv_path)
                df.columns = ["time_s", "voltage_V", "current_mA", "charge_mAh", "temperature_C"]
                df["cell_id"]      = f"Imperial_Expt2_2_cell_{cell_id}"
                df["cycle_id"]     = rpt_num
                df["temperature_nominal_C"] = temp_c
                df["step_type"]    = "discharge_0.1C"
                all_dfs.append(df)
            except Exception as e:
                print(f"  [WARN] 跳过 {csv_path}: {e}")

    if not all_dfs:
        print("[ERROR] 没有读取到任何数据！")
        return None

    ts = pd.concat(all_dfs, ignore_index=True)
    # 统一列顺序
    ts = ts[["cell_id", "cycle_id", "time_s", "voltage_V",
             "current_mA", "charge_mAh", "temperature_C",
             "temperature_nominal_C", "step_type"]]
    return ts

def process_cycle_summary():
    """从 Summary Data 提取每个 cell 的容量衰减曲线"""
    summary_dir = os.path.join(RAW_DIR, "Summary Data", "Performance Summary")
    all_dfs = []

    for csv_path in sorted(glob.glob(os.path.join(summary_dir, "*.csv"))):
        m = re.search(r'cell ([A-F])', os.path.basename(csv_path))
        if not m:
            continue
        cell_id = m.group(1)
        temp_c  = CELL_TEMP.get(cell_id, -1)
        try:
            df = pd.read_csv(csv_path)
            df["cell_id"] = f"Imperial_Expt2_2_cell_{cell_id}"
            df["temperature_nominal_C"] = temp_c
            all_dfs.append(df)
        except Exception as e:
            print(f"  [WARN] 跳过 {csv_path}: {e}")

    if not all_dfs:
        print("[WARN] Summary Data 读取失败")
        return None
    return pd.concat(all_dfs, ignore_index=True)

def main():
    print("=" * 60)
    print("ETL: Dataset 36 - Imperial College 21700")
    print("=" * 60)

    # 1. Timeseries
    print("\n[1/3] 处理 timeseries...")
    ts = process_timeseries()
    if ts is not None:
        out_ts = os.path.join(PROC_DIR, "Imperial_21700_timeseries.parquet")
        ts.to_parquet(out_ts, index=False)
        print(f"  ✅ Timeseries: {len(ts):,} 行 → {out_ts}")

        # 保存前100行 sample 供 GitHub
        sample_path = os.path.join(PROC_DIR, "Imperial_21700_timeseries_SAMPLE.csv")
        ts.head(100).to_csv(sample_path, index=False)
        print(f"  ✅ Sample CSV: {sample_path}")

    # 2. Cycle summary
    print("\n[2/3] 处理 cycle summary...")
    cs = process_cycle_summary()
    if cs is not None:
        out_cs = os.path.join(PROC_DIR, "Imperial_21700_cycle_summary.csv")
        cs.to_csv(out_cs, index=False)
        print(f"  ✅ Cycle summary: {len(cs):,} 行 → {out_cs}")
        print(f"  列名: {list(cs.columns)}")

    # 3. Metadata
    print("\n[3/3] 生成 metadata...")
    meta_rows = []
    for cell_id, temp in CELL_TEMP.items():
        meta_rows.append({
            "cell_id": f"Imperial_Expt2_2_cell_{cell_id}",
            "experiment": "Expt 2,2 - C-based Degradation 2",
            "chemistry": "LG M50T/GBM50T NMC 21700",
            "nominal_capacity_Ah": 5.0,
            "temperature_nominal_C": temp,
            "dataset": "dataset_36",
            "source": "Zenodo 10637534",
        })
    meta_df = pd.DataFrame(meta_rows)
    out_meta = os.path.join(PROC_DIR, "Imperial_21700_metadata.csv")
    meta_df.to_csv(out_meta, index=False)
    print(f"  ✅ Metadata: {out_meta}")
    print(meta_df.to_string(index=False))

    print("\n" + "=" * 60)
    print("ETL COMPLETE ✅")
    print("=" * 60)

if __name__ == "__main__":
    main()
