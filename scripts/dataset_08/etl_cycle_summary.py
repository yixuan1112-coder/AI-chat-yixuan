import pandas as pd
import numpy as np
import glob
import os

# 路径配置
RAW_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_08_UL-Purdue\UL-Purdue"
OUT_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_08"
DATASET_NAME = "dataset_08"
KEEP_ZERO_N = 3 

# 严格 14 列标准顺序
STANDARD_COLUMNS = [
    'cell_id', 'cycle_id', 'step_type', 'capacity_Ah', 'SOH', 'RUL', 
    'charge_capacity_Ah', 'discharge_capacity_Ah', 'temperature_max_C', 
    'temperature_avg_C', 'charge_duration_s', 'discharge_duration_s', 
    'internal_resistance_Ohm', 'cycle_end_flag'
]

def find_col(columns, keywords):
    """按照关键词顺序匹配，且避开带 'date' 的文本列"""
    for key in keywords:
        for col in columns:
            if key.lower() in col.lower():
                # 如果找时间但碰到了 'date'，跳过它去寻找纯数字时间列
                if key.lower() == 'time' and 'date' in col.lower():
                    continue
                return col
    return None

def process_all_data():
    cycle_files = glob.glob(os.path.join(RAW_DIR, "*_cycle_data.csv"))
    os.makedirs(OUT_DIR, exist_ok=True)

    for cp in cycle_files:
        base_name = os.path.basename(cp).replace('_cycle_data.csv', '')
        tp = cp.replace('_cycle_data.csv', '_timeseries.csv') 
        cell_id = f"{base_name}"
        
        if not os.path.exists(tp): continue

        try:
            df_c_raw = pd.read_csv(cp)
            df_t_raw = pd.read_csv(tp, low_memory=False)

            # --- 1. 识别 Timeseries 列并强制转为数字 ---
            time_col = find_col(df_t_raw.columns, ['Test_Time', 'Time (s)', 'Time'])
            cycle_col = find_col(df_t_raw.columns, ['Cycle_Index', 'Cycle_Inde', 'Cycle'])
            curr_col = find_col(df_t_raw.columns, ['Current'])
            # 增加对多种温度命名的兼容
            temp_col = find_col(df_t_raw.columns, ['Cell_Temperature', 'Temperature', 'Temp'])

            # 修复 str 问题
            for c in [time_col, curr_col, temp_col, cycle_col]:
                if c: df_t_raw[c] = pd.to_numeric(df_t_raw[c], errors='coerce')

            # --- 2. 聚合特征 ---
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
                        # 充放电时长计算
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

            # --- 3. 组装汇总表 (关键修复) ---
            df_final = pd.DataFrame()
            
            # 第一步：先填充带行数的 cycle_id，确立 DataFrame 的 Index
            df_final['cycle_id'] = pd.to_numeric(df_c_raw['Cycle_Index'], errors='coerce')
            
            # 第二步：此时赋值 cell_id，Pandas 才会广播填充到每一行！
            df_final['cell_id'] = cell_id
            
            # 第三步：填充容量
            cap_col = find_col(df_c_raw.columns, ['Discharge_Capacity'])
            char_col = find_col(df_c_raw.columns, ['Charge_Capacity'])
            if cap_col: 
                df_final['capacity_Ah'] = pd.to_numeric(df_c_raw[cap_col], errors='coerce')
                df_final['discharge_capacity_Ah'] = df_final['capacity_Ah']
            if char_col: 
                df_final['charge_capacity_Ah'] = pd.to_numeric(df_c_raw[char_col], errors='coerce')

            # 第四步：合并时序特征
            if ts_features:
                df_ts_agg = pd.DataFrame(ts_features)
                df_final = pd.merge(df_final, df_ts_agg, left_on='cycle_id', right_on='c_id_map', how='left').drop(columns=['c_id_map'])

            # 第五步：执行连续 0 过滤
            is_zero = df_final['capacity_Ah'].fillna(0) <= 0
            df_final = df_final[(~is_zero) | (df_final.groupby((is_zero != is_zero.shift()).cumsum()).cumcount() + 1 <= KEEP_ZERO_N)].copy()

            # 第六步：补齐并重排 14 列
            for col in STANDARD_COLUMNS:
                if col not in df_final.columns:
                    df_final[col] = np.nan
            
            df_final[STANDARD_COLUMNS].to_csv(os.path.join(OUT_DIR, f"{cell_id}_cycle_summary.csv"), index=False, float_format='%g')
            print(f" 处理完成: {cell_id}")

        except Exception as e:
            print(f" 失败 {base_name}: {e}")

if __name__ == "__main__":
    process_all_data()