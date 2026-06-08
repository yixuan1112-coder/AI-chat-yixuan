import pandas as pd
import numpy as np
from pathlib import Path
import re

def parse_readme_protocols(readme_path):
    """解析 README.txt 获取每个电池的测试协议"""
    protocols = {}
    if readme_path.exists():
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 正则匹配 VAH01.csv: Baseline 这种格式
            matches = re.findall(r'(VAH\d+)\.csv:\s*(.*)', content)
            for cell, protocol in matches:
                protocols[cell] = protocol.strip()
    return protocols

def generate_metadata(raw_dir, processed_dir):
    readme_path = raw_dir / "README.txt"
    protocols_map = parse_readme_protocols(readme_path)
    
    # 获取所有的时序数据文件 (排除 _impedance 文件)
    files = [f for f in raw_dir.rglob("*.csv") if "impedance" not in f.name.lower()]
    
    columns = [
        'dataset_id', 'cell_id', 'source_type', 'split_tag', 'chemistry',
        'cathode_material', 'anode_material', 'brand_or_manufacturer', 
        'model_or_size', 'form_factor', 'nominal_capacity_Ah', 
        'nominal_voltage_V', 'temperature_C', 'charge_protocol', 
        'discharge_protocol', 'C_rate', 'cutoff_voltage_upper', 'cutoff_voltage_lower'
    ]
    
    records = []
    for file in files:
        cell_id = file.stem # 如 VAH15
        
        # 从 map 中获取实验协议，如果没有则标记为 unknown
        protocol = protocols_map.get(cell_id, "eVTOL Flight Profile")
        
        record = {
            'dataset_id': 'dataset_21',
            'cell_id': cell_id,
            'source_type': 'public',
            'split_tag': np.nan,
            'chemistry': 'NMC',  # Sony VTC-6 通常为 NMC 体系
            'cathode_material': 'NMC',
            'anode_material': 'Graphite',
            'brand_or_manufacturer': 'Sony-Murata',
            'model_or_size': '18650 VTC-6',
            'form_factor': 'cylindrical',
            'nominal_capacity_Ah': 3.0, # VTC-6 标称 3000mAh
            'nominal_voltage_V': 3.6,
            'temperature_C': 'unknown', # 随循环变化，写 unknown 或环境设定温度
            'charge_protocol': protocol,
            'discharge_protocol': protocol,
            'C_rate': 'dynamic', # eVTOL 是动态变倍率工况
            'cutoff_voltage_upper': 4.2,
            'cutoff_voltage_lower': 2.5
        }
        records.append(record)
        
    out_df = pd.DataFrame(records, columns=columns)
    output_path = processed_dir / "dataset_21_metadata.csv"
    out_df.to_csv(output_path, index=False)
    print(f"✅ Metadata 已成功保存至: {output_path.name}")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_21_CMU\14226830")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_21")
    processed_dir.mkdir(parents=True, exist_ok=True)
    generate_metadata(raw_dir, processed_dir)