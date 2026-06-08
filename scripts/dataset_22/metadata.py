import pandas as pd
import numpy as np
from pathlib import Path
import re

def generate_metadata(raw_dir, output_file):
    files = list(raw_dir.rglob("*.csv"))
    
    columns = [
        'dataset_id', 'cell_id', 'source_type', 'split_tag', 'chemistry',
        'cathode_material', 'anode_material', 'brand_or_manufacturer', 
        'model_or_size', 'form_factor', 'nominal_capacity_Ah', 
        'nominal_voltage_V', 'temperature_C', 'charge_protocol', 
        'discharge_protocol', 'C_rate', 'cutoff_voltage_upper', 'cutoff_voltage_lower'
    ]
    
    records = []
    for file in files:
        cell_id = file.stem.replace(' ', '_')
        
        # 提取温度和 SOC 参数
        temp_match = re.search(r'(25|45)C?', file.name, re.IGNORECASE)
        temp = temp_match.group(1) if temp_match else 'unknown'
        
        soc_match = re.search(r'(10|70|90)\s*SOC', file.name, re.IGNORECASE)
        if not soc_match:
            soc_match = re.search(r'\b(10|70|90)\b', file.name)
        soc_status = f"Calendar Ageing Storage at {soc_match.group(1)}% SOC" if soc_match else "Calendar Ageing"

        record = {
            'dataset_id': 'dataset_22',
            'cell_id': cell_id,
            'source_type': 'public',
            'split_tag': np.nan,
            'chemistry': 'unknown',
            'cathode_material': 'Ni-rich',
            'anode_material': 'Si/Gr',
            'brand_or_manufacturer': 'unknown',
            'model_or_size': '18650',
            'form_factor': 'cylindrical',
            'nominal_capacity_Ah': np.nan,
            'nominal_voltage_V': np.nan,
            'temperature_C': temp,
            'charge_protocol': soc_status,
            'discharge_protocol': 'unknown',
            'C_rate': 'unknown',
            'cutoff_voltage_upper': np.nan,
            'cutoff_voltage_lower': np.nan
        }
        records.append(record)
        
    out_df = pd.DataFrame(records, columns=columns)
    out_df.to_csv(output_file, index=False)
    print(f"✅ Metadata 已保存至: {output_file}")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_22_VITO\Calendar ageing test results on commercial 18650 Li ion cell @ 25°C and 45°C_1_all")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_22")
    processed_dir.mkdir(parents=True, exist_ok=True)
    generate_metadata(raw_dir, processed_dir / "dataset_22_metadata.csv")