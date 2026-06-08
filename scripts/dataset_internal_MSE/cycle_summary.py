import pandas as pd
import numpy as np
import os
import glob


RAW_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_internal_MSE\MSE"
OUT_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_internal_MSE\MSE"
DATASET_ID = "dataset_internal"
# ========================

STANDARD_COLUMNS = [
    'cell_id', 'cycle_id', 'step_type', 'capacity_Ah', 'SOH', 'RUL', 
    'charge_capacity_Ah', 'discharge_capacity_Ah', 'temperature_max_C', 
    'temperature_avg_C', 'charge_duration_s', 'discharge_duration_s', 
    'internal_resistance_Ohm', 'cycle_end_flag'
]

def process_single_timeseries(input_csv, output_csv, cell_id):
    """将单个高频时序 CSV 降维提取为周期特征表"""
    
    # === 核心修复：智能多重编码兼容 ===
    try:
        df_raw = pd.read_csv(input_csv, low_memory=False, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            # 兼容国产测试仪（如新威尔）导出的含有中文或特殊符号(℃)的 CSV
            df_raw = pd.read_csv(input_csv, low_memory=False, encoding='gbk')
        except UnicodeDecodeError:
            try:
                df_raw = pd.read_csv(input_csv, low_memory=False, encoding='gb18030')
            except UnicodeDecodeError:
                # 终极兜底：强行读取，忽略无法解析的乱码符号（不影响数字特征提取）
                df_raw = pd.read_csv(input_csv, low_memory=False, encoding='latin1')
    # ==================================

    df_raw['Time(s)'] = pd.to_numeric(df_raw['Time(s)'], errors='coerce')
    
    # ... 下面全部保持不变 ...

    if 'DChg. Cap.(Ah)' in df_raw.columns:
        nominal_capacity = df_raw['DChg. Cap.(Ah)'].max()
    else:
        nominal_capacity = 0

    records = []
    
    for cycle_id, group in df_raw.groupby('Cycle Index'):
        dchg_cap = group['DChg. Cap.(Ah)'].max() if 'DChg. Cap.(Ah)' in group.columns else np.nan
        chg_cap = group['Chg. Cap.(Ah)'].max() if 'Chg. Cap.(Ah)' in group.columns else np.nan

        if pd.isna(dchg_cap) or dchg_cap <= 0:
            continue

        c_dur, d_dur = np.nan, np.nan
        if 'Current(A)' in group.columns:
            c_data = group[group['Current(A)'] > 0.01]
            if not c_data.empty: c_dur = float(c_data['Time(s)'].max() - c_data['Time(s)'].min())

            d_data = group[group['Current(A)'] < -0.01]
            if not d_data.empty: d_dur = float(d_data['Time(s)'].max() - d_data['Time(s)'].min())

        record = {
            'cell_id': cell_id,
            'cycle_id': int(cycle_id),
            'step_type': 'discharge', 
            'capacity_Ah': dchg_cap,
            'SOH': (dchg_cap / nominal_capacity) if nominal_capacity > 0 else np.nan,
            'RUL': np.nan,             
            'charge_capacity_Ah': chg_cap,
            'discharge_capacity_Ah': dchg_cap,
            'temperature_max_C': np.nan,  
            'temperature_avg_C': np.nan,  
            'charge_duration_s': c_dur,
            'discharge_duration_s': d_dur,
            'internal_resistance_Ohm': np.nan, 
            'cycle_end_flag': 'normal'
        }
        records.append(record)

    df_summary = pd.DataFrame(records, columns=STANDARD_COLUMNS)
    df_summary.to_csv(output_csv, index=False, float_format='%g')

def run_batch_pipeline():
    os.makedirs(OUT_BASE_DIR, exist_ok=True)
    
    subfolders = [f.name for f in os.scandir(RAW_BASE_DIR) if f.is_dir()]
    total_folders = len(subfolders)
    print(f"🚀 侦测到 {total_folders} 个电池数据文件夹，启动批量提取流水线...\n")
    
    success_count = 0
    
    for idx, folder_name in enumerate(subfolders, 1):
        raw_folder_path = os.path.join(RAW_BASE_DIR, folder_name)
        
        # === 核心修改点：在输出端动态创建一模一样的同名文件夹 ===
        out_folder_path = os.path.join(OUT_BASE_DIR, folder_name)
        os.makedirs(out_folder_path, exist_ok=True)
        # ==========================================================
        
        csv_files = glob.glob(os.path.join(raw_folder_path, "*.csv"))
        
        if not csv_files:
            print(f"[{idx}/{total_folders}] ⚠️ 警告: 文件夹 '{folder_name}' 中未找到 CSV 文件，已跳过。")
            continue
            
        input_csv = csv_files[0]
        
        cell_id = f"{folder_name}"
        out_filename = f"{folder_name}_cycle_summary.csv"
        
        # === 核心修改点：将输出 CSV 存入刚刚建好的同名文件夹中 ===
        output_csv = os.path.join(out_folder_path, out_filename)
        # ==========================================================
        
        print(f"[{idx}/{total_folders}] 正在提取: {folder_name} ...", end="")
        
        try:
            process_single_timeseries(input_csv, output_csv, cell_id)
            print(" ✅ 成功")
            success_count += 1
        except Exception as e:
            print(f" ❌ 失败 ({e})")
            
    print(f"\n🎉 批量流水线执行完毕！共成功提取 {success_count} / {total_folders} 个电池特征表。")
    print(f"📁 1:1 映射的文件夹结构已生成在: {OUT_BASE_DIR}")

if __name__ == "__main__":
    run_batch_pipeline()