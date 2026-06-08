import pandas as pd
import numpy as np
from pathlib import Path
import re

def find_col(columns, keywords):
    """健壮的列名匹配：支持大小写不敏感、去除空格、部分匹配"""
    for key in keywords:
        for col in columns:
            clean_col = str(col).strip().lower()
            clean_key = str(key).strip().lower()
            if clean_key == clean_col or clean_key in clean_col:
                return col
    return None

def generate_cycle_summary(raw_dir, processed_dir):
    files = list(raw_dir.rglob("*.[cC][sS][vV]"))
    columns = ['cell_id', 'cycle_id', 'capacity_Ah', 'SOH', 'RUL', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'temperature_max_C', 'temperature_avg_C', 'charge_duration_s', 'discharge_duration_s', 'internal_resistance_Ohm', 'cycle_end_flag']
    
    success_count = 0
    for file in files:
        cell_id = file.stem.replace(' ', '_')
        temp_match = re.search(r'(25|45)C?', file.name, re.IGNORECASE)
        env_temp = float(temp_match.group(1)) if temp_match else np.nan
        
        try:
            # 使用 sep=None 和 engine='python' 自动检测逗号或分号
            df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
            # 移除可能因为原始数据格式问题产生的空列名
            df.columns = [c if c and not c.startswith('Unnamed') else f"col_{i}" for i, c in enumerate(df.columns)]
            
            # 寻找循环 ID：优先找 Cycle，找不到就找 Step
            cyc_col = find_col(df.columns, ['Cycle', 'Step'])
            # 寻找容量列
            cap_col = find_col(df.columns, ['Discharge_Capacity_Ah', 'Capacity (Ah)', 'Capacity'])
            
            if not cyc_col or not cap_col:
                print(f"⚠️ 跳过 {file.name}: 无法匹配关键列。检测到的列: {list(df.columns)}")
                continue
                
            agg_df = df.groupby(cyc_col)[cap_col].max().reset_index()
            
            out_df = pd.DataFrame()
            out_df['cycle_id'] = agg_df[cyc_col].fillna(0).astype(int)
            out_df['cell_id'] = cell_id
            out_df['capacity_Ah'] = agg_df[cap_col].round(4)
            out_df['discharge_capacity_Ah'] = out_df['capacity_Ah']
            out_df['temperature_max_C'] = env_temp
            out_df['temperature_avg_C'] = env_temp
            out_df['cycle_end_flag'] = 'normal'
            
            initial_cap = out_df['capacity_Ah'].iloc[0] if not out_df.empty else 1.0
            out_df['SOH'] = (out_df['capacity_Ah'] / initial_cap).round(4)
            
            for col in columns:
                if col not in out_df.columns: out_df[col] = np.nan
            
            output_path = processed_dir / f"dataset_22_{cell_id}_cycle_summary.csv"
            out_df[columns].to_csv(output_path, index=False)
            print(f"✅ 已生成: {output_path.name}")
            success_count += 1
        except Exception as e:
            print(f"❌ 处理 {file.name} 失败: {e}")
            
    print(f"\n🎉 处理完毕，共生成 {success_count} 个文件的汇总。")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_22_VITO\Calendar ageing test results on commercial 18650 Li ion cell @ 25°C and 45°C_1_all")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_22")
    processed_dir.mkdir(parents=True, exist_ok=True)
    generate_cycle_summary(raw_dir, processed_dir)