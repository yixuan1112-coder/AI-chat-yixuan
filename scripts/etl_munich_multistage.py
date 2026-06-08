#!/usr/bin/env python3
"""
ETL: Dataset 37 - Munich Multistage Aging Samsung 21700 (Stroebl 2024)
Representative subset: 3x TP_k (calendar) + 3x TP_z (cycle aging)

Usage:
    conda activate batterytwin
    cd ~/Projects/BatteryTwin-Benchmark-DataPrep
    python scripts/etl_munich_multistage.py
"""

import os
import glob
import re
import pandas as pd
from tqdm import tqdm

# ── 路径配置 ──────────────────────────────────────────────
REPO_ROOT = os.path.expanduser("~/Projects/BatteryTwin-Benchmark-DataPrep")
RAW_DIR   = os.path.join(REPO_ROOT, "data/raw/dataset_37_Munich_Multistage/raw_unzipped")
META_CSV  = os.path.join(REPO_ROOT, "data/raw/dataset_37_Munich_Multistage/experiments_meta.csv")
PROC_DIR  = os.path.join(REPO_ROOT, "data/processed/dataset_37")
os.makedirs(PROC_DIR, exist_ok=True)

def parse_cell_info(folder_name):
    """从文件夹名提取 tp_id 和 cell_num，如 TP_k01_05 -> tp=k01, cell=05"""
    m = re.match(r'TP_([a-z]\d+)_(\d+)', folder_name)
    if m:
        return m.group(1), int(m.group(2))
    return folder_name, -1

def process_timeseries():
    """读取所有子文件夹的 CSV，合并成统一格式"""
    all_dfs = []
    folders = sorted(os.listdir(RAW_DIR))

    for folder in tqdm(folders, desc="Processing folders"):
        folder_path = os.path.join(RAW_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        tp_id, cell_num = parse_cell_info(folder)
        aging_type = 'calendar' if folder[3] == 'k' else 'cycle'

        csv_files = sorted(glob.glob(os.path.join(folder_path, "*.csv")))
        for csv_path in csv_files:
            fname = os.path.basename(csv_path)
            # 从文件名提取测试类型和温度，如 TP_k01_05_01_ET_T10 -> ET, 10
            m = re.search(r'_(\d+)_([A-Z]+)_T(\d+)\.csv$', fname)
            test_seq  = int(m.group(1)) if m else -1
            test_type = m.group(2) if m else 'UNK'   # ET=entry, AT=aging, ZYK=cycling
            test_temp = int(m.group(3)) if m else -1

            try:
                df = pd.read_csv(csv_path)
                df.columns = ['run_time', 'voltage_V', 'current_A',
                               'surf_temp_C', 'amb_temp_C', 'step_type']
                df['cell_id']     = f"Munich_{folder}"
                df['tp_id']       = tp_id
                df['cell_num']    = cell_num
                df['aging_type']  = aging_type
                df['test_type']   = test_type
                df['test_temp_C'] = test_temp
                df['test_seq']    = test_seq
                all_dfs.append(df)
            except Exception as e:
                print(f"  [WARN] 跳过 {fname}: {e}")

    if not all_dfs:
        print("[ERROR] 没有读取到任何数据！")
        return None

    ts = pd.concat(all_dfs, ignore_index=True)
    ts = ts[['cell_id', 'tp_id', 'cell_num', 'aging_type', 'test_type',
             'test_seq', 'test_temp_C', 'run_time', 'voltage_V',
             'current_A', 'surf_temp_C', 'amb_temp_C', 'step_type']]
    return ts

def process_metadata():
    """从 experiments_meta.csv 提取本次子集涉及的电池信息"""
    meta = pd.read_csv(META_CSV)
    # 只保留我们下载的 tp 对应的行
    downloaded = ['TP_k01_05', 'TP_k01_06', 'TP_k02_06',
                  'TP_z20_02', 'TP_z23_01', 'TP_z23_02']
    subset = meta[meta['serial'].isin(downloaded)].copy()

    # 补充 Tianwen 要求的三个字段
    subset['cell_form_factor']   = 'cylindrical'
    subset['cell_dimensions_mm'] = '21x70'
    subset['nominal_capacity_Ah'] = 4.9

    return subset

def main():
    print("=" * 60)
    print("ETL: Dataset 37 - Munich Multistage Aging")
    print("=" * 60)

    # 1. Timeseries
    print("\n[1/3] 处理 timeseries...")
    ts = process_timeseries()
    if ts is not None:
        out_ts = os.path.join(PROC_DIR, "Munich_multistage_timeseries.parquet")
        ts.to_parquet(out_ts, index=False)
        print(f"  ✅ Timeseries: {len(ts):,} 行 → {out_ts}")

        sample_path = os.path.join(PROC_DIR, "Munich_multistage_timeseries_SAMPLE.csv")
        ts.head(100).to_csv(sample_path, index=False)
        print(f"  ✅ Sample CSV: {sample_path}")

    # 2. Metadata
    print("\n[2/3] 处理 metadata...")
    meta = process_metadata()
    if meta is not None and len(meta) > 0:
        out_meta = os.path.join(PROC_DIR, "Munich_multistage_metadata.csv")
        meta.to_csv(out_meta, index=False)
        print(f"  ✅ Metadata: {len(meta)} 行 → {out_meta}")
        print(f"  列名: {list(meta.columns)}")
    else:
        # 如果 meta 匹配不到，生成基础版
        print("  [WARN] experiments_meta.csv 匹配不到，生成基础 metadata")
        rows = []
        for folder in sorted(os.listdir(RAW_DIR)):
            if not os.path.isdir(os.path.join(RAW_DIR, folder)):
                continue
            aging_type = 'calendar' if folder[3] == 'k' else 'cycle'
            rows.append({
                'cell_id': f"Munich_{folder}",
                'aging_type': aging_type,
                'chemistry': 'NMC/Graphite Samsung INR21700-50E',
                'cell_form_factor': 'cylindrical',
                'cell_dimensions_mm': '21x70',
                'nominal_capacity_Ah': 4.9,
                'dataset': 'dataset_37',
                'source': 'figshare 25975315',
            })
        meta_df = pd.DataFrame(rows)
        out_meta = os.path.join(PROC_DIR, "Munich_multistage_metadata.csv")
        meta_df.to_csv(out_meta, index=False)
        print(f"  ✅ Metadata (基础版): {len(meta_df)} 行")

    # 3. Cycle summary（从 meta 中提取关键老化参数）
    print("\n[3/3] 生成 cycle summary...")
    try:
        meta_all = pd.read_csv(META_CSV)
        downloaded = ['TP_k01_05', 'TP_k01_06', 'TP_k02_06',
                      'TP_z20_02', 'TP_z23_01', 'TP_z23_02']
        cs = meta_all[meta_all['serial'].isin(downloaded)][
            ['serial', 'lab', 'type', 'amb_temp_tp', 'soc_max_tp',
             'dod_tp', 'c_ch_tp', 'c_dch_tp', 'stage']
        ].copy()
        cs.columns = ['cell_id', 'lab', 'aging_type', 'amb_temp_C',
                      'soc_max', 'dod', 'c_rate_charge', 'c_rate_discharge', 'stage']
        out_cs = os.path.join(PROC_DIR, "Munich_multistage_cycle_summary.csv")
        cs.to_csv(out_cs, index=False)
        print(f"  ✅ Cycle summary: {len(cs)} 行 → {out_cs}")
    except Exception as e:
        print(f"  [WARN] Cycle summary 生成失败: {e}")

    print("\n" + "=" * 60)
    print("ETL COMPLETE ✅")
    print("=" * 60)

if __name__ == "__main__":
    main()
