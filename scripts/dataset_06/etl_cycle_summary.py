import pandas as pd
import numpy as np
import glob
import os

# === SNL 基础路径配置 ===
RAW_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_06_SNL"
OUT_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_06"
DATASET_NAME = "dataset_06"
# ========================

KEEP_ZERO_N = 3 

STANDARD_COLUMNS = [
    'cell_id', 'cycle_id', 'step_type', 'capacity_Ah', 'SOH', 'RUL', 
    'charge_capacity_Ah', 'discharge_capacity_Ah', 'temperature_max_C', 
    'temperature_avg_C', 'charge_duration_s', 'discharge_duration_s', 
    'internal_resistance_Ohm', 'cycle_end_flag'
]

def find_col(columns, keywords):
    for key in keywords:
        for col in columns:
            if key.lower() in col.lower():
                if key.lower() == 'time' and 'date' in col.lower():
                    continue
                return col
    return None

def process_all_data():
    subfolders = [f.name for f in os.scandir(RAW_BASE_DIR) if f.is_dir()]
    print(f"检测到 {len(subfolders)} 个子文件夹，开始提取...")

    for subfolder in subfolders:
        raw_dir = os.path.join(RAW_BASE_DIR, subfolder)
        out_dir = os.path.join(OUT_BASE_DIR, subfolder)
        os.makedirs(out_dir, exist_ok=True)
        
        cycle_files = glob.glob(os.path.join(raw_dir, "*_cycle_data.csv"))
        print(f"\n📁 正在处理 [{subfolder}]，共 {len(cycle_files)} 组数据...")

        for cp in cycle_files:
            base_name = os.path.basename(cp).replace('_cycle_data.csv', '')
            tp = cp.replace('_cycle_data.csv', '_timeseries.csv') 
            
            # 生成带子文件夹标识的全局唯一 cell_id
            cell_id = f"{DATASET_NAME}_{subfolder}_{base_name}"
            
            if not os.path.exists(tp): continue

            try:
                df_c_raw = pd.read_csv(cp)
                df_t_raw = pd.read_csv(tp, low_memory=False)

                time_col = find_col(df_t_raw.columns, ['Test_Time', 'Time (s)', 'Time'])
                cycle_col = find_col(df_t_raw.columns, ['Cycle_Index', 'Cycle_Inde', 'Cycle'])
                curr_col = find_col(df_t_raw.columns, ['Current'])
                temp_col = find_col(df_t_raw.columns, ['Cell_Temperature', 'Temperature', 'Cell_Temp', 'Environ', 'Temp'])

                for c in [time_col, curr_col, temp_col, cycle_col]:
                    if c: df_t_raw[c] = pd.to_numeric(df_t_raw[c], errors='coerce')

                ts_features = []
                if time_col and cycle_col:
                    df_t_valid = df_t_raw.dropna(subset=[cycle_col, time_col])
                    for cycle, group in df_t_valid.groupby(cycle_col):
                        t_max, t_avg = np.nan, np.nan
                        if temp_col and group[temp_col].notna().any():
                            t_max = group[temp_col].max()
                            t_avg = group[temp_col].mean()
                        
                        c_dur, d_dur = 0.0, 0.0
                        if curr_col:
                            c_data = group[group[curr_col] > 0.01]
                            d_data = group[group[curr_col] < -0.01]
                            if not c_data.empty: c_dur = float(c_data[time_col].max() - c_data[time_col].min())
                            if not d_data.empty: d_dur = float(d_data[time_col].max() - d_data[time_col].min())

                        ts_features.append({
                            'c_id_map': int(cycle),
                            'temperature_max_C': t_max,
                            'temperature_avg_C': t_avg,
                            'charge_duration_s': c_dur,
                            'discharge_duration_s': d_dur
                        })

                df_final = pd.DataFrame()
                df_final['cycle_id'] = pd.to_numeric(df_c_raw['Cycle_Index'], errors='coerce')
                df_final['cell_id'] = cell_id
                
                cap_col = find_col(df_c_raw.columns, ['Discharge_Capacity'])
                char_col = find_col(df_c_raw.columns, ['Charge_Capacity'])
                if cap_col: 
                    df_final['capacity_Ah'] = pd.to_numeric(df_c_raw[cap_col], errors='coerce')
                    df_final['discharge_capacity_Ah'] = df_final['capacity_Ah']
                if char_col: 
                    df_final['charge_capacity_Ah'] = pd.to_numeric(df_c_raw[char_col], errors='coerce')

                if ts_features:
                    df_ts_agg = pd.DataFrame(ts_features)
                    df_final = pd.merge(df_final, df_ts_agg, left_on='cycle_id', right_on='c_id_map', how='left').drop(columns=['c_id_map'])

                is_zero = df_final['capacity_Ah'].fillna(0) <= 0
                df_final = df_final[(~is_zero) | (df_final.groupby((is_zero != is_zero.shift()).cumsum()).cumcount() + 1 <= KEEP_ZERO_N)].copy()

                for col in STANDARD_COLUMNS:
                    if col not in df_final.columns: df_final[col] = np.nan
                
                df_final[STANDARD_COLUMNS].to_csv(os.path.join(out_dir, f"{cell_id}_cycle_summary.csv"), index=False, float_format='%g')
                print(f"  ✅ 处理完成: {cell_id}")

            except Exception as e:
                print(f"  ❌ 失败 {base_name}: {e}")

if __name__ == "__main__":
    process_all_data()