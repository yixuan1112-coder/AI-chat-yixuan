import pandas as pd
from pathlib import Path
import pickle
import numpy as np

def process_hust_timeseries():
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_41_HUST\nsc7hnsg4s-2\our_data\our_data")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_41")
    processed_dir.mkdir(parents=True, exist_ok=True)

    for pkl_file in raw_dir.glob("*.pkl"):
        cell_name = pkl_file.stem
        cell_id = f"HUST_{cell_name}"
        print(f"🚀 正在解析电池: {cell_id}")
        
        with open(pkl_file, 'rb') as f:
            full_data = pickle.load(f)
        
        # 提取核心数据字典
        battery_data = full_data[cell_name]['data']
        
        all_cycles_ts = []
        # battery_data 是一个以 cycle_id 为键的字典
        for cycle_id, df_cycle in battery_data.items():
            # 转换单位并重命名
            df_ts = pd.DataFrame({
                'cell_id': cell_id,
                'cycle_id': cycle_id,
                'time_s': df_cycle['Time (s)'],
                'voltage_V': df_cycle['Voltage (V)'],
                'current_A': df_cycle['Current (mA)'] / 1000.0,
                'temperature_C': None, # 原始数据中未见温度列
                'step_type': df_cycle['Status']
            })
            all_cycles_ts.append(df_ts)
        
        if all_cycles_ts:
            df_final = pd.concat(all_cycles_ts, ignore_index=True)
            out_file = processed_dir / f"{cell_id}_timeseries.csv"
            df_final.to_csv(out_file, index=False)
            print(f"  ✅ 导出成功: {len(df_final)} 行")

if __name__ == "__main__":
    process_hust_timeseries()