import pandas as pd
import numpy as np
from pathlib import Path

def generate_cycle_summary(input_file, output_file):
    df = pd.read_csv(input_file)
    df['cell_id'] = 'ev_charging_' + df['EV Model'].str.replace(' ', '') + '_' + df['Battery Type'].str.replace('-', '')
    
    # 预计算一些中间字段
    df['calc_capacity'] = df['Current (A)'] * (df['Charging Duration (min)'] / 60)
    df['duration_s'] = df['Charging Duration (min)'] * 60
    
    # 以防同一个循环有多次记录，聚合保证 cycle_id 唯一
    agg_df = df.groupby(['cell_id', 'Charging Cycles']).agg({
        'calc_capacity': 'sum',
        'Degradation Rate (%)': 'mean',
        'Battery Temp (°C)': ['max', 'mean'],
        'duration_s': 'sum'
    }).reset_index()
    
    # 平铺 MultiIndex 列
    agg_df.columns = ['cell_id', 'cycle_id', 'capacity_Ah', 'deg_rate', 'temp_max', 'temp_avg', 'duration_s']
    
    # 严格按照 Schema 定义列顺序
    columns = [
        'cell_id', 'cycle_id', 'capacity_Ah', 'SOH', 'RUL',
        'charge_capacity_Ah', 'discharge_capacity_Ah', 'temperature_max_C',
        'temperature_avg_C', 'charge_duration_s', 'discharge_duration_s',
        'internal_resistance_Ohm', 'cycle_end_flag'
    ]
    
    out_df = pd.DataFrame(columns=columns)
    
    out_df['cell_id'] = agg_df['cell_id']
    out_df['cycle_id'] = agg_df['cycle_id']
    
    # Cycle Summary 的 capacity 优先使用放电，这里用充电作为基准参考
    out_df['capacity_Ah'] = agg_df['capacity_Ah'].round(4)
    # SOH = 1 - Degradation Rate
    out_df['SOH'] = ((100 - agg_df['deg_rate']) / 100.0).round(4)
    out_df['RUL'] = np.nan
    out_df['charge_capacity_Ah'] = out_df['capacity_Ah']
    out_df['discharge_capacity_Ah'] = np.nan
    out_df['temperature_max_C'] = agg_df['temp_max'].round(2)
    out_df['temperature_avg_C'] = agg_df['temp_avg'].round(2)
    out_df['charge_duration_s'] = agg_df['duration_s'].round(2)
    out_df['discharge_duration_s'] = np.nan
    out_df['internal_resistance_Ohm'] = np.nan
    out_df['cycle_end_flag'] = 'normal'
    
    # 保证顺序正确
    out_df = out_df.sort_values(by=['cell_id', 'cycle_id'])
    
    out_df.to_csv(output_file, index=False)
    print(f"Cycle Summary 已成功保存至: {output_file}")

if __name__ == "__main__":
    # 1. 定义本地绝对路径
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_10_EV\archive")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_10")
    
    # 2. 确保输出目录存在
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. 拼接文件路径
    input_file = raw_dir / "ev_battery_charging_data.csv"
    output_file = processed_dir / "dataset_10_EV_cycle_summary.csv"
    
    # 4. 执行
    generate_cycle_summary(input_file, output_file)