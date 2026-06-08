import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# 忽略 pandas 并置列名的警告
warnings.simplefilter(action='ignore', category=pd.errors.ParserWarning)

def process_file_timeseries(file_path):
    cell_id = file_path.stem
    # 读取所有列，剔除单位行
    df_raw = pd.read_csv(file_path, header=0)
    df_raw = df_raw.drop(0).reset_index(drop=True)
    
    # 动态匹配重复的列名（Pandas 自动重命名重复列如 Temp, Temp.1, Temp.2 等）
    time_cols = [c for c in df_raw.columns if c.startswith('Test Time')]
    cycle_cols = [c for c in df_raw.columns if c.startswith('Cycle Number')]
    temp_cols = [c for c in df_raw.columns if c.startswith('Temp')]
    cap_cols = [c for c in df_raw.columns if c.startswith('Capacity')]
    volt_cols = [c for c in df_raw.columns if c.startswith('Cell Potential')]
    
    # 取这几组特征中最小的数量，防止有列缺失
    num_blocks = min(len(time_cols), len(cycle_cols), len(temp_cols), len(cap_cols), len(volt_cols))
    
    blocks = []
    for i in range(num_blocks):
        block_df = pd.DataFrame({
            'cell_id': cell_id,
            'cycle_id': pd.to_numeric(df_raw[cycle_cols[i]], errors='coerce'),
            'time_hrs': pd.to_numeric(df_raw[time_cols[i]], errors='coerce'),
            'temperature_C': pd.to_numeric(df_raw[temp_cols[i]], errors='coerce'),
            'capacity_raw': pd.to_numeric(df_raw[cap_cols[i]], errors='coerce'),
            'voltage_V': pd.to_numeric(df_raw[volt_cols[i]], errors='coerce')
        })
        # 剔除空白数据 (横向拼接常常有大量为 NaN 的填充空位)
        block_df = block_df.dropna(subset=['time_hrs'])
        blocks.append(block_df)
        
    if not blocks:
        return pd.DataFrame()
        
    stacked_df = pd.concat(blocks, ignore_index=True)
    
    # 将时间转化为秒 (原始数据为 Hrs)
    stacked_df['time_s'] = (stacked_df['time_hrs'] * 3600).round(2)
    
    # 整理为标准列顺序
    columns = [
        'cell_id', 'cycle_id', 'time_s', 'voltage_V', 'current_A',
        'temperature_C', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'step_type'
    ]
    out_df = pd.DataFrame(columns=columns)
    
    out_df['cell_id'] = stacked_df['cell_id']
    out_df['cycle_id'] = stacked_df['cycle_id'].astype(int, errors='ignore')
    out_df['time_s'] = stacked_df['time_s']
    out_df['voltage_V'] = stacked_df['voltage_V']
    out_df['temperature_C'] = stacked_df['temperature_C']
    out_df['charge_capacity_Ah'] = stacked_df['capacity_raw'] # 原始数据统一放在一个容量列
    
    # 按时间戳全局排序，确保单调递增
    out_df = out_df.sort_values(by=['time_s'])
    
    return out_df

def generate_timeseries(raw_dir, output_file):
    files = [f for f in raw_dir.glob("*.csv") if "Simulation" not in f.name]
    
    all_ts = []
    for file in files:
        print(f"解析横向拼接的时序数据: {file.stem} ...", end=" ")
        df_ts = process_file_timeseries(file)
        all_ts.append(df_ts)
        print(f"[{len(df_ts)} 行]")
        
    final_df = pd.concat(all_ts, ignore_index=True)
    
    final_df.to_csv(output_file, index=False)
    print(f"\nTimeseries 汇总已成功保存至: {output_file}")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_11_UCL\Lithium-ion battery cycle data\Lithium-ion battery cycle data")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_11")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / "dataset_11_timeseries.csv"
    generate_timeseries(raw_dir, output_file)