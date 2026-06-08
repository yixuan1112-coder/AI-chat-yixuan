import pandas as pd
import numpy as np
from pathlib import Path

def process_jrc_cyclesummary():
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_40")
    
    schema_cols = [
        'cell_id', 'cycle_id', 'capacity_Ah', 'SOH', 'RUL', 'charge_capacity_Ah', 
        'discharge_capacity_Ah', 'temperature_max_C', 'temperature_avg_C', 
        'charge_duration_s', 'discharge_duration_s', 'internal_resistance_Ohm', 'cycle_end_flag'
    ]

    for ts_file in processed_dir.glob("JRC_*_timeseries.csv"):
        print(f"📊 汇总特征: {ts_file.name}")
        df_ts = pd.read_csv(ts_file)
        
        # 1. 计算安时积分 (Ah)
        # JRC 采样频率为 1Hz (dt=1s)，容量 = sum(I * dt) / 3600
        # 只计算放电阶段 (current_A < 0)
        discharge_mask = df_ts['current_A'] < 0
        charge_mask = df_ts['current_A'] > 0
        
        d_cap = np.abs(df_ts.loc[discharge_mask, 'current_A']).sum() / 3600.0
        c_cap = df_ts.loc[charge_mask, 'current_A'].sum() / 3600.0

        # 2. 提取温度统计量 (此时已经是修复后的摄氏度)
        temp_max = df_ts['temperature_C'].max()
        temp_avg = df_ts['temperature_C'].mean()

        summary_record = {
            'cell_id': df_ts['cell_id'].iloc[0],
            'cycle_id': 1,
            'capacity_Ah': d_cap,
            'SOH': d_cap / 25.0, # 假设 JRC 软包电池标称为 25Ah
            'RUL': None,
            'charge_capacity_Ah': c_cap,
            'discharge_capacity_Ah': d_cap,
            'temperature_max_C': temp_max,
            'temperature_avg_C': temp_avg,
            'charge_duration_s': discharge_mask.sum(),
            'discharge_duration_s': charge_mask.sum(),
            'internal_resistance_Ohm': None,
            'cycle_end_flag': 1
        }

        df_sum = pd.DataFrame([summary_record], columns=schema_cols)
        out_file = processed_dir / f"{summary_record['cell_id']}_cycle_summary.csv"
        df_sum.to_csv(out_file, index=False)

if __name__ == "__main__":
    process_jrc_cyclesummary()