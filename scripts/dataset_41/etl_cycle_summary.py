import pandas as pd
from pathlib import Path
import pickle
import numpy as np

def process_hust_cyclesummary():
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_41_HUST\nsc7hnsg4s-2\our_data\our_data")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_41")
    
    schema_cols = [
        'cell_id', 'cycle_id', 'capacity_Ah', 'SOH', 'RUL', 'charge_capacity_Ah', 
        'discharge_capacity_Ah', 'temperature_max_C', 'temperature_avg_C', 
        'charge_duration_s', 'discharge_duration_s', 'internal_resistance_Ohm', 'cycle_end_flag'
    ]

    for pkl_file in raw_dir.glob("*.pkl"):
        cell_name = pkl_file.stem
        cell_id = f"HUST_{cell_name}"
        print(f"汇总循环数据: {cell_id}")
        
        with open(pkl_file, 'rb') as f:
            full_data = pickle.load(f)
        
        content = full_data[cell_name]
        dq_dict = content['dq']
        rul_dict = content['rul']
        data_dict = content['data']
        
        summary_records = []
        for cycle_id in dq_dict.keys():
            # 获取当前循环的容量 (单位 mAh -> Ah)
            cap_ah = dq_dict[cycle_id] / 1000.0
            rul_val = rul_dict[cycle_id]
            
            # 从 timeseries 数据中计算时长
            df_cycle = data_dict[cycle_id]
            charge_duration = len(df_cycle[df_cycle['Current (mA)'] > 0])
            discharge_duration = len(df_cycle[df_cycle['Current (mA)'] < 0])
            
            summary_records.append({
                'cell_id': cell_id,
                'cycle_id': cycle_id,
                'capacity_Ah': cap_ah,
                'SOH': cap_ah / 1.1, # 标称容量 1.1Ah
                'RUL': rul_val,
                'charge_capacity_Ah': None, # 原始数据未直接给出，设为 None
                'discharge_capacity_Ah': cap_ah,
                'temperature_max_C': None,
                'temperature_avg_C': None,
                'charge_duration_s': charge_duration,
                'discharge_duration_s': discharge_duration,
                'internal_resistance_Ohm': None,
                'cycle_end_flag': 1
            })
            
        df_sum = pd.DataFrame(summary_records, columns=schema_cols)
        df_sum.to_csv(processed_dir / f"{cell_id}_cycle_summary.csv", index=False)
        print(f"  ✅ {len(df_sum)} 个循环处理完毕")

if __name__ == "__main__":
    process_hust_cyclesummary()