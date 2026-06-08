import pandas as pd
import numpy as np
import glob
import os

# 路径配置
RAW_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_08_UL-Purdue\UL-Purdue"
OUT_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_08"
DATASET_NAME = "dataset_08"

# 严格按照图片中的 9 列顺序
STANDARD_TS_COLUMNS = [
    'cell_id', 'cycle_id', 'time_s', 'voltage_V', 'current_A', 
    'temperature_C', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'step_type'
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
def process_all_timeseries():
    search_pattern = os.path.join(RAW_DIR, "*_timeseries.csv")
    file_list = glob.glob(search_pattern)
    os.makedirs(OUT_DIR, exist_ok=True)
    
    print(f"找到 {len(file_list)} 个文件，开始导出csv...")
    
    for file_path in file_list:
        file_name = os.path.basename(file_path)
        raw_cell_id = file_name.replace('_timeseries.csv', '')
        cell_id = f"{raw_cell_id}"
        
        try:
            # low_memory=False 解决 DtypeWarning，确保数据读取稳定
            df_raw = pd.read_csv(file_path, low_memory=False)
            
            # 1. 自动识别列名
            time_col = find_col(df_raw.columns, ['Test_Time', 'Time (s)', 'Time'])
            cycle_col = find_col(df_raw.columns, ['Cycle_Index', 'Cycle_Inde', 'Cycle'])
            volt_col = find_col(df_raw.columns, ['Voltage'])
            curr_col = find_col(df_raw.columns, ['Current'])
            # 增加 Temperature 关键词，确保能抓取到温度列
            temp_col = find_col(df_raw.columns, ['Cell_Temperature', 'Temperature', 'Cell_Temp', 'Environ', 'Temp'])
            char_cap = find_col(df_raw.columns, ['Charge_Capacity'])
            disc_cap = find_col(df_raw.columns, ['Discharge_Capacity'])
            step_col = find_col(df_raw.columns, ['step_type', 'Step'])

            # 2. 构建目标 DataFrame 并强制转换数值
            df_ts = pd.DataFrame()
            
            # 必须先确立 cycle_id 这一列，确立行数
            if cycle_col:
                df_ts['cycle_id'] = pd.to_numeric(df_raw[cycle_col], errors='coerce')
            
            # 此时填充 cell_id 才能广播到每一行
            df_ts['cell_id'] = cell_id
            
            # 填充其他数值列
            if time_col: df_ts['time_s'] = pd.to_numeric(df_raw[time_col], errors='coerce')
            if volt_col: df_ts['voltage_V'] = pd.to_numeric(df_raw[volt_col], errors='coerce')
            if curr_col: df_ts['current_A'] = pd.to_numeric(df_raw[curr_col], errors='coerce')
            if temp_col: df_ts['temperature_C'] = pd.to_numeric(df_raw[temp_col], errors='coerce')
            if char_cap: df_ts['charge_capacity_Ah'] = pd.to_numeric(df_raw[char_cap], errors='coerce')
            if disc_cap: df_ts['discharge_capacity_Ah'] = pd.to_numeric(df_raw[disc_cap], errors='coerce')
            
            # 填充 step_type
            df_ts['step_type'] = df_raw[step_col] if step_col else np.nan

            # 3. 补齐并强制 9 列顺序
            for col in STANDARD_TS_COLUMNS:
                if col not in df_ts.columns:
                    df_ts[col] = np.nan
            
            df_ts = df_ts[STANDARD_TS_COLUMNS]
            
            # 4. 导出 CSV (移除了 to_parquet 避免报错)
            csv_path = os.path.join(OUT_DIR, f"{raw_cell_id}_timeseries.csv")
            df_ts.to_csv(csv_path, index=False, float_format='%g')
            print(f" 处理成功: {os.path.basename(csv_path)}")
            
        except Exception as e:
            print(f" 失败 {file_name}: {e}")

if __name__ == "__main__":
    process_all_timeseries()