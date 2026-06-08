import pandas as pd
from pathlib import Path
import numpy as np

def process_jrc_timeseries():
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_40_JRC")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_40")
    processed_dir.mkdir(parents=True, exist_ok=True)

    test_conditions = ["3300", "2700", "1650", "1000", "660", "330"]

    for raw_file in raw_dir.rglob("*.csv"):
        print(f"🚀 正在解析 JRC 宽表: {raw_file.name}")
        
        # 🌟 关键修复 1: 直接指定分号分隔符和小数点为逗号
        # 这能从源头解决 15,5 变成 1550 的问题
        df_raw = pd.read_csv(raw_file, sep=';', decimal=',', low_memory=False)

        for condition in test_conditions:
            cell_id = f"JRC_{condition}"
            
            # 列名定位
            v_c, v_d = f'V_C_{condition}', f'V_D_{condition}'
            c_c, c_d = f'C_C_{condition}', f'C_D_{condition}'
            ta_c, ta_d = f'Ta_C_{condition}', f'Ta_D_{condition}'

            # 检查列是否存在
            if v_c not in df_raw.columns and v_d not in df_raw.columns:
                continue

            # 合并充放电序列
            v_series = df_raw[v_c].combine_first(df_raw[v_d]) if v_c in df_raw.columns else df_raw[v_d]
            c_series = df_raw[c_c].combine_first(df_raw[c_d]) if c_c in df_raw.columns else df_raw[c_d]
            ta_series = df_raw[ta_c].combine_first(df_raw[ta_d]) if ta_c in df_raw.columns else df_raw[ta_d]

            # 提取有效数据
            valid_mask = v_series.notna()
            if not valid_mask.any():
                continue

            df_ts = pd.DataFrame({
                'cell_id': cell_id,
                'cycle_id': 1,
                'time_s': np.arange(valid_mask.sum()),
                'voltage_V': v_series[valid_mask].values,
                'current_A': c_series[valid_mask].values,
                'temperature_C': ta_series[valid_mask].values,
                'step_type': 'dynamic'
            })

            # 🌟 关键修复 2: 修复文件名覆盖 Bug，每个工况独立存为一个文件
            out_file = processed_dir / f"{cell_id}_timeseries.csv"
            df_ts.to_csv(out_file, index=False)
            print(f"  ✅ {cell_id} 导出完成: {len(df_ts)} 行")

if __name__ == "__main__":
    process_jrc_timeseries()