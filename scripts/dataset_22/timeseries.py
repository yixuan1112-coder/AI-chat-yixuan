import pandas as pd
import numpy as np
from pathlib import Path
import re

def find_col(columns, keywords):
    for key in keywords:
        for col in columns:
            clean_col = str(col).strip().lower()
            clean_key = str(key).strip().lower()
            if clean_key == clean_col or clean_key in clean_col:
                return col
    return None

def generate_timeseries(raw_dir, processed_dir):
    files = list(raw_dir.rglob("*.[cC][sS][vV]"))
    columns = ['cell_id', 'cycle_id', 'time_s', 'voltage_V', 'current_A', 'temperature_C', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'step_type']
    
    success_count = 0
    for file in files:
        cell_id = file.stem.replace(' ', '_')
        temp_match = re.search(r'(25|45)C?', file.name, re.IGNORECASE)
        env_temp = float(temp_match.group(1)) if temp_match else np.nan
        
        try:
            # 自动识别分隔符
            df_raw = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
            
            cyc_col = find_col(df_raw.columns, ['Cycle', 'Step'])
            time_col = find_col(df_raw.columns, ['Total_Time_Seconds', 'Time (s)'])
            volt_col = find_col(df_raw.columns, ['Voltage_V', 'Voltage (V)'])
            curr_col = find_col(df_raw.columns, ['Current_A', 'Current (A)'])
            cap_col = find_col(df_raw.columns, ['Discharge_Capacity_Ah', 'Capacity (Ah)'])
            temp_col = find_col(df_raw.columns, ['Temperature', 'Temp'])
            
            if not all([time_col, volt_col]):
                print(f"⚠️ 跳过 {file.name}: 关键列缺失。检测到的列: {list(df_raw.columns)}")
                continue

            out_df = pd.DataFrame()
            out_df['cell_id'] = cell_id
            out_df['cycle_id'] = df_raw[cyc_col] if cyc_col else 1
            out_df['time_s'] = df_raw[time_col]
            out_df['voltage_V'] = df_raw[volt_col]
            out_df['current_A'] = df_raw[curr_col] if curr_col else 0
            out_df['temperature_C'] = df_raw[temp_col] if temp_col else env_temp
            out_df['discharge_capacity_Ah'] = df_raw[cap_col] if cap_col else 0
            
            for col in columns:
                if col not in out_df.columns: out_df[col] = np.nan
            
            output_path = processed_dir / f"dataset_22_{cell_id}_timeseries.csv"
            out_df[columns].to_csv(output_path, index=False)
            print(f"✅ 已生成: {output_path.name}")
            success_count += 1
        except Exception as e:
            print(f"❌ 处理 {file.name} 失败: {e}")
            
    print(f"\n🎉 处理完毕，共生成 {success_count} 个文件的时序。")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_22_VITO\Calendar ageing test results on commercial 18650 Li ion cell @ 25°C and 45°C_1_all")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_22")
    processed_dir.mkdir(parents=True, exist_ok=True)
    generate_timeseries(raw_dir, processed_dir)