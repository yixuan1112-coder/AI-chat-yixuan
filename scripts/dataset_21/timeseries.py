import pandas as pd
import numpy as np
from pathlib import Path

def generate_timeseries(raw_dir, processed_dir):
    files = [f for f in raw_dir.rglob("*.csv") if "impedance" not in f.name.lower()]
    columns = ['cell_id', 'cycle_id', 'time_s', 'voltage_V', 'current_A', 'temperature_C', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'step_type']
    
    success_count = 0
    for file in files:
        cell_id = file.stem
        try:
            df_raw = pd.read_csv(file)
            out_df = pd.DataFrame()
            
            out_df['cell_id'] = cell_id
            out_df['cycle_id'] = df_raw['cycleNumber']
            out_df['time_s'] = df_raw['time_s']
            out_df['voltage_V'] = df_raw['Ecell_V']
            
            # 重要：物理单位换算 (mA -> A)
            out_df['current_A'] = df_raw['I_mA'] / 1000.0
            
            out_df['temperature_C'] = df_raw['Temperature__C']
            
            # 容量换算 (mA_h -> Ah)
            out_df['charge_capacity_Ah'] = df_raw['QCharge_mA_h'] / 1000.0
            out_df['discharge_capacity_Ah'] = df_raw['QDischarge_mA_h'] / 1000.0
            
            # 记录原始数据中的步序 (用于细粒度截取)
            out_df['step_type'] = df_raw['Ns']
            
            for col in columns:
                if col not in out_df.columns: out_df[col] = np.nan
            
            output_path = processed_dir / f"dataset_21_{cell_id}_timeseries.csv"
            out_df[columns].to_csv(output_path, index=False)
            print(f"✅ 生成时序: {output_path.name}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 处理 {file.name} 失败: {e}")
            
    print(f"\n🎉 处理完毕，共生成 {success_count} 个时序表。")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_21_CMU\14226830")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_21")
    processed_dir.mkdir(parents=True, exist_ok=True)
    generate_timeseries(raw_dir, processed_dir)