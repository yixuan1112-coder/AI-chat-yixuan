import pandas as pd
import numpy as np
import glob
import os

# === SNL 基础路径配置 ===
RAW_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_06_SNL" 
OUT_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_06"
DATASET_NAME = "dataset_06"
# ========================

STANDARD_TS_COLUMNS = [
    'cell_id', 'cycle_id', 'time_s', 'voltage_V', 'current_A', 
    'temperature_C', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'step_type'
]

def find_col(columns, keywords):
    for key in keywords:
        for col in columns:
            if key.lower() in col.lower():
                if key.lower() == 'time' and 'date' in col.lower():
                    continue
                return col
    return None

def process_all_timeseries():
    # 自动获取基础路径下的所有子文件夹名称
    subfolders = [f.name for f in os.scandir(RAW_BASE_DIR) if f.is_dir()]
    print(f"检测到 {len(subfolders)} 个子文件夹: {subfolders}，开始遍历处理...")
    
    for subfolder in subfolders:
        raw_dir = os.path.join(RAW_BASE_DIR, subfolder)
        out_dir = os.path.join(OUT_BASE_DIR, subfolder)
        os.makedirs(out_dir, exist_ok=True) # 自动创建对应的输出子文件夹
        
        search_pattern = os.path.join(raw_dir, "*_timeseries.csv")
        file_list = glob.glob(search_pattern)
        print(f"\n📁 进入 [{subfolder}]，找到 {len(file_list)} 个 Timeseries 文件...")
        
        for file_path in file_list:
            file_name = os.path.basename(file_path)
            raw_cell_id = file_name.replace('_timeseries.csv', '')
            
            # 核心防御：将子文件夹名称加入 cell_id，防止不同文件夹的同名文件冲突
            cell_id = f"{DATASET_NAME}_{subfolder}_{raw_cell_id}"
            
            try:
                df_raw = pd.read_csv(file_path, low_memory=False)
                
                time_col = find_col(df_raw.columns, ['Test_Time', 'Time (s)', 'Time'])
                cycle_col = find_col(df_raw.columns, ['Cycle_Index', 'Cycle_Inde', 'Cycle'])
                volt_col = find_col(df_raw.columns, ['Voltage'])
                curr_col = find_col(df_raw.columns, ['Current'])
                temp_col = find_col(df_raw.columns, ['Cell_Temperature', 'Temperature', 'Cell_Temp', 'Environ', 'Temp'])
                char_cap = find_col(df_raw.columns, ['Charge_Capacity'])
                disc_cap = find_col(df_raw.columns, ['Discharge_Capacity'])
                step_col = find_col(df_raw.columns, ['step_type', 'Step'])

                df_ts = pd.DataFrame()
                if cycle_col: df_ts['cycle_id'] = pd.to_numeric(df_raw[cycle_col], errors='coerce')
                df_ts['cell_id'] = cell_id
                
                if time_col: df_ts['time_s'] = pd.to_numeric(df_raw[time_col], errors='coerce')
                if volt_col: df_ts['voltage_V'] = pd.to_numeric(df_raw[volt_col], errors='coerce')
                if curr_col: df_ts['current_A'] = pd.to_numeric(df_raw[curr_col], errors='coerce')
                if temp_col: df_ts['temperature_C'] = pd.to_numeric(df_raw[temp_col], errors='coerce')
                if char_cap: df_ts['charge_capacity_Ah'] = pd.to_numeric(df_raw[char_cap], errors='coerce')
                if disc_cap: df_ts['discharge_capacity_Ah'] = pd.to_numeric(df_raw[disc_cap], errors='coerce')
                df_ts['step_type'] = df_raw[step_col] if step_col else np.nan

                for col in STANDARD_TS_COLUMNS:
                    if col not in df_ts.columns: df_ts[col] = np.nan
                
                df_ts = df_ts[STANDARD_TS_COLUMNS]
                
                # 输出到对应的子文件夹 out_dir
                csv_path = os.path.join(out_dir, f"{cell_id}_timeseries.csv")
                df_ts.to_csv(csv_path, index=False, float_format='%g')
                print(f"  ✅ 成功: {os.path.basename(csv_path)}")
                
            except Exception as e:
                print(f"  ❌ 失败 {file_name}: {e}")

if __name__ == "__main__":
    process_all_timeseries()