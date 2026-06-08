import pandas as pd
import numpy as np
import os
import glob

# === 批量流水线路径配置 ===
RAW_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_internal_MSE\MSE"
OUT_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_internal_MSE\MSE"
DATASET_ID = "dataset_internal_MSE"
# ========================

# 严格对齐目标模板的 9 列标准
TIMESERIES_COLS = [
    'cell_id', 'cycle_id', 'time_s', 'voltage_V', 'current_A', 
    'temperature_C', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'step_type'
]

def map_step_type(raw_step):
    """将新威尔/Arbin的原始工况映射为标准英文标签"""
    s = str(raw_step).lower()
    if 'dchg' in s or 'dis' in s:
        return 'discharge'
    elif 'chg' in s or 'cha' in s:
        return 'charge'
    elif 'rest' in s:
        return 'rest'
    return ''

def process_single_timeseries(input_csv, output_csv, cell_id):
    """提取高频时序数据并转换为标准列"""
    
    # 1. 智能多重编码兼容 (防止出现 0xa6 报错)
    try:
        df_raw = pd.read_csv(input_csv, low_memory=False, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df_raw = pd.read_csv(input_csv, low_memory=False, encoding='gbk')
        except UnicodeDecodeError:
            try:
                df_raw = pd.read_csv(input_csv, low_memory=False, encoding='gb18030')
            except UnicodeDecodeError:
                df_raw = pd.read_csv(input_csv, low_memory=False, encoding='latin1')

    # 2. 映射标准特征列
    # 创建一个空的标准 DataFrame
    df_ts = pd.DataFrame(columns=TIMESERIES_COLS)
    
    # 填充全局 ID
    df_ts['cell_id'] = cell_id
    
    # 映射 Cycle ID 和时间
    if 'Cycle Index' in df_raw.columns:
        df_ts['cycle_id'] = pd.to_numeric(df_raw['Cycle Index'], errors='coerce').astype('Int64')
    if 'Time(s)' in df_raw.columns:
        df_ts['time_s'] = pd.to_numeric(df_raw['Time(s)'], errors='coerce')
        
    # 映射电压与电流
    if 'Voltage(V)' in df_raw.columns:
        df_ts['voltage_V'] = pd.to_numeric(df_raw['Voltage(V)'], errors='coerce')
    if 'Current(A)' in df_raw.columns:
        df_ts['current_A'] = pd.to_numeric(df_raw['Current(A)'], errors='coerce')
        
    # 映射充放电容量
    if 'Chg. Cap.(Ah)' in df_raw.columns:
        df_ts['charge_capacity_Ah'] = pd.to_numeric(df_raw['Chg. Cap.(Ah)'], errors='coerce')
    if 'DChg. Cap.(Ah)' in df_raw.columns:
        df_ts['discharge_capacity_Ah'] = pd.to_numeric(df_raw['DChg. Cap.(Ah)'], errors='coerce')
        
    # 映射工况类型 (将 "CC DChg" 自动转换为 "discharge")
    if 'Step Type' in df_raw.columns:
        df_ts['step_type'] = df_raw['Step Type'].apply(map_step_type)
        
    # 处理温度列 (原始数据若无温度，自动全填 NaN，保持结构对齐)
    if 'Temperature(C)' in df_raw.columns:
        df_ts['temperature_C'] = pd.to_numeric(df_raw['Temperature(C)'], errors='coerce')
    else:
        df_ts['temperature_C'] = np.nan

    # 3. 过滤并导出
    # 删掉完全没有时间戳的空行
    df_ts = df_ts.dropna(subset=['time_s'])
    
    # 导出文件，采用 %g 抹除浮点数误差长尾，大幅减小文件体积
    df_ts.to_csv(output_csv, index=False, float_format='%g')

def run_timeseries_pipeline():
    subfolders = [f.name for f in os.scandir(RAW_BASE_DIR) if f.is_dir()]
    total_folders = len(subfolders)
    print(f"🚀 侦测到 {total_folders} 个电池数据文件夹，启动 Timeseries 提取流水线...\n")
    
    success_count = 0
    
    for idx, folder_name in enumerate(subfolders, 1):
        raw_folder_path = os.path.join(RAW_BASE_DIR, folder_name)
        out_folder_path = os.path.join(OUT_BASE_DIR, folder_name)
        
        # 确保输出目录存在
        os.makedirs(out_folder_path, exist_ok=True)
        
        # 自动寻找该文件夹下的 CSV 文件
        csv_files = glob.glob(os.path.join(raw_folder_path, "*.csv"))
        
        if not csv_files:
            print(f"[{idx}/{total_folders}] ⚠️ 警告: '{folder_name}' 未找到 CSV 文件，已跳过。")
            continue
            
        input_csv = csv_files[0]
        
        # 组装内部 ID 和输出文件名
        cell_id = f"{folder_name}"
        out_filename = f"{folder_name}_timeseries.csv"  # 保持文件名简洁，无多余前缀
        output_csv = os.path.join(out_folder_path, out_filename)
        
        print(f"[{idx}/{total_folders}] 正在提取高频时序: {folder_name} ...", end="", flush=True)
        
        try:
            process_single_timeseries(input_csv, output_csv, cell_id)
            print(" ✅ 成功")
            success_count += 1
        except Exception as e:
            print(f" ❌ 失败 ({e})")
            
    print(f"\n🎉 Timeseries 流水线执行完毕！共成功提取 {success_count} 份标准时序表。")
    print(f"📁 结果已存入各自分配的同名文件夹内。")

if __name__ == "__main__":
    run_timeseries_pipeline()