import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# 忽略不必要的警告
warnings.simplefilter(action='ignore', category=UserWarning)

def generate_cycle_summary(raw_dir, output_file):
    # 过滤掉仿真文件，只保留实测数据
    files = [f for f in raw_dir.glob("*.csv") if "Simulation" not in f.name]
    
    # 最终需要的 Schema 严格列名
    columns = [
        'cell_id', 'cycle_id', 'capacity_Ah', 'SOH', 'RUL',
        'charge_capacity_Ah', 'discharge_capacity_Ah', 'temperature_max_C',
        'temperature_avg_C', 'charge_duration_s', 'discharge_duration_s',
        'internal_resistance_Ohm', 'cycle_end_flag'
    ]
    
    all_summaries = []
    
    for file in files:
        cell_id = file.stem
        
        try:
            # 只读取左侧包含 Summary 信息的列 (前3列)
            df = pd.read_csv(file, header=0, usecols=[0, 1, 2])
            
            # 剔除第1行（单位行，如 -,Ah,Ah）
            df = df.drop(0).reset_index(drop=True)
            df.columns = ['cycle_id', 'charge_cap', 'discharge_cap']
            
            # 转为纯数值，剔除无效的空行
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=['cycle_id']).copy()

            # ================= 核心修复区 =================
            # 不要建预设 columns 的空表，直接新建一个完全不受限的 DataFrame
            out_df = pd.DataFrame() 
            
            # 1. 先把有长度的数据列塞进去，这会直接把表格的“行数”撑开
            out_df['cycle_id'] = df['cycle_id'].astype(int)
            
            # 2. 表格有了确定的行数后，再赋标量值（单一字符串），它就能完美填满每一行！
            out_df['cell_id'] = cell_id
            
            # 3. 继续计算其它关键指标
            out_df['capacity_Ah'] = df['discharge_cap'].round(4)
            out_df['charge_capacity_Ah'] = df['charge_cap'].round(4)
            out_df['discharge_capacity_Ah'] = df['discharge_cap'].round(4)
            out_df['SOH'] = (out_df['capacity_Ah'] / 3.5).round(4)
            out_df['cycle_end_flag'] = 'normal'
            # ============================================
            
            # 4. 把 Schema 里要求但当前数据没有的列，统一补齐为 NaN
            for col in columns:
                if col not in out_df.columns:
                    out_df[col] = np.nan
                    
            # 5. 严格按照 Schema 的顺序重排所有列
            out_df = out_df[columns]
            
            print(f"成功处理: {cell_id} | 提取了 {len(out_df)} 个循环的 Summary")
            all_summaries.append(out_df)
            
        except Exception as e:
            print(f"❌ 处理 {file.name} 时发生意外: {e}")
            
    # 强制合并并输出文件
    if all_summaries:
        final_df = pd.concat(all_summaries, ignore_index=True)
        final_df = final_df.sort_values(by=['cell_id', 'cycle_id'])
        final_df.to_csv(output_file, index=False)
        print(f"\n🎉 完美！Cycle Summary 已成功保存并包含 cell_id 至:\n{output_file}")
    else:
        print("\n⚠️ 未能提取到任何有效数据，未生成文件。")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_11_UCL\Lithium-ion battery cycle data\Lithium-ion battery cycle data")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_11")
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_file = processed_dir / "dataset_11_cycle_summary.csv"
    
    generate_cycle_summary(raw_dir, output_file)