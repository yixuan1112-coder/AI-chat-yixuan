import pandas as pd
import numpy as np
from pathlib import Path

def generate_timeseries(input_file, output_file):
    df = pd.read_csv(input_file)
    df['cell_id'] = 'ev_charging_' + df['EV Model'].str.replace(' ', '') + '_' + df['Battery Type'].str.replace('-', '')
    
    # 严格按照 Schema 定义列顺序
    columns = [
        'cell_id', 'cycle_id', 'time_s', 'voltage_V', 'current_A',
        'temperature_C', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'step_type'
    ]
    
    out_df = pd.DataFrame(columns=columns)
    
    out_df['cell_id'] = df['cell_id']
    out_df['cycle_id'] = df['Charging Cycles']
    out_df['time_s'] = (df['Charging Duration (min)'] * 60).round(2)
    out_df['voltage_V'] = df['Voltage (V)']
    out_df['current_A'] = df['Current (A)']
    out_df['temperature_C'] = df['Battery Temp (°C)']
    
    # 估算充电容量: I * t
    out_df['charge_capacity_Ah'] = (df['Current (A)'] * (df['Charging Duration (min)'] / 60)).round(4)
    out_df['discharge_capacity_Ah'] = np.nan
    out_df['step_type'] = 'charge'
    
    # 排序以满足 QC 标准的时间轴单调递增
    out_df = out_df.sort_values(by=['cell_id', 'cycle_id', 'time_s'])
    
    out_df.to_csv(output_file, index=False)
    print(f"Timeseries 已成功保存至: {output_file}")

if __name__ == "__main__":
    # 1. 定义本地绝对路径
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_10_EV\archive")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_10")
    
    # 2. 确保输出目录存在
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. 拼接文件路径
    input_file = raw_dir / "ev_battery_charging_data.csv"
    output_file = processed_dir / "dataset_10_EV_timeseries.csv"
    
    # 4. 执行
    generate_timeseries(input_file, output_file)