import pandas as pd
import numpy as np
from pathlib import Path

def generate_metadata(raw_dir, output_file):
    # 查找所有的实测文件（排除 Simulation 文件）
    files = [f for f in raw_dir.glob("*.csv") if "Simulation" not in f.name]
    
    columns = [
        'dataset_id', 'cell_id', 'source_type', 'split_tag', 'chemistry',
        'cathode_material', 'anode_material', 'brand_or_manufacturer', 
        'model_or_size', 'form_factor', 'nominal_capacity_Ah', 
        'nominal_voltage_V', 'temperature_C', 'charge_protocol', 
        'discharge_protocol', 'C_rate', 'cutoff_voltage_upper', 'cutoff_voltage_lower'
    ]
    
    out_df = pd.DataFrame(columns=columns)
    
    records = []
    for file in files:
        cell_id = file.stem  # 例如 'EIL-MJ1-015'
        
        # 读取时跳过单位行(第1行)以获取温度均值
        try:
            df = pd.read_csv(file, header=0, skiprows=[1], usecols=['Temp'])
            avg_temp = round(df['Temp'].mean(), 1) if not df.empty else 'unknown'
        except Exception:
            avg_temp = 'unknown'

        record = {
            'dataset_id': 'dataset_11',
            'cell_id': cell_id,
            'source_type': 'public',
            'split_tag': np.nan,
            'chemistry': 'NMC',  # LG MJ1 是高镍 NMC
            'cathode_material': 'NMC',
            'anode_material': 'Si-Graphite',
            'brand_or_manufacturer': 'LG',
            'model_or_size': 'INR18650-MJ1',
            'form_factor': 'cylindrical',
            'nominal_capacity_Ah': 3.5,
            'nominal_voltage_V': 3.63,
            'temperature_C': str(avg_temp),
            'charge_protocol': 'unknown',
            'discharge_protocol': 'unknown',
            'C_rate': 'unknown',
            'cutoff_voltage_upper': 4.2,
            'cutoff_voltage_lower': 2.5
        }
        records.append(record)
        print(f"提取元数据: {cell_id}")
        
    out_df = pd.concat([out_df, pd.DataFrame(records)], ignore_index=True)
    out_df.to_csv(output_file, index=False)
    print(f"\nMetadata 汇总已成功保存至: {output_file}")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_11_UCL\Lithium-ion battery cycle data\Lithium-ion battery cycle data")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_11")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / "dataset_11_metadata.csv"
    generate_metadata(raw_dir, output_file)