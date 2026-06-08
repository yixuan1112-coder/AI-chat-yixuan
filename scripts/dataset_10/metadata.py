import pandas as pd
import numpy as np
from pathlib import Path

def generate_metadata(input_file, output_file):
    df = pd.read_csv(input_file)
    
    # 构建全局唯一的 cell_id
    df['cell_id'] = 'ev_charging_' + df['EV Model'].str.replace(' ', '') + '_' + df['Battery Type'].str.replace('-', '')
    
    # 提取该类别下固有的物理信息和平均环境温度
    meta_df = df.groupby('cell_id').agg({
        'EV Model': 'first',
        'Battery Type': 'first',
        'Ambient Temp (°C)': 'mean',
        'Charging Mode': 'first'
    }).reset_index()
    
    # 严格按照 Schema 定义列顺序
    columns = [
        'dataset_id', 'cell_id', 'source_type', 'split_tag', 'chemistry',
        'cathode_material', 'anode_material', 'brand_or_manufacturer', 
        'model_or_size', 'form_factor', 'nominal_capacity_Ah', 
        'nominal_voltage_V', 'temperature_C', 'charge_protocol', 
        'discharge_protocol', 'C_rate', 'cutoff_voltage_upper', 'cutoff_voltage_lower'
    ]
    
    out_df = pd.DataFrame(columns=columns)
    
    out_df['dataset_id'] = 'dataset_ev_charging'
    out_df['cell_id'] = meta_df['cell_id']
    out_df['source_type'] = 'public'
    out_df['split_tag'] = np.nan
    
    # 映射化学体系，将 LiFePO4 转为标准的 LFP
    chem_map = {'LiFePO4': 'LFP', 'Li-ion': 'unknown'}
    out_df['chemistry'] = meta_df['Battery Type'].map(chem_map).fillna('unknown')
    out_df['cathode_material'] = meta_df['Battery Type']
    out_df['anode_material'] = 'unknown'
    
    out_df['brand_or_manufacturer'] = meta_df['EV Model']
    out_df['model_or_size'] = 'unknown'
    out_df['form_factor'] = 'unknown'
    out_df['nominal_capacity_Ah'] = np.nan  # 原始数据无明确的额定容量
    out_df['nominal_voltage_V'] = np.nan
    out_df['temperature_C'] = meta_df['Ambient Temp (°C)'].round(1).astype(str)
    out_df['charge_protocol'] = meta_df['Charging Mode']
    out_df['discharge_protocol'] = 'unknown'
    out_df['C_rate'] = np.nan
    out_df['cutoff_voltage_upper'] = np.nan
    out_df['cutoff_voltage_lower'] = np.nan
    
    out_df.to_csv(output_file, index=False)
    print(f"Metadata 已成功保存至: {output_file}")

if __name__ == "__main__":
    # 1. 定义本地绝对路径
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_10_EV\archive")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_10")
    
    # 2. 确保输出目录存在
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. 拼接文件路径
    input_file = raw_dir / "ev_battery_charging_data.csv"
    output_file = processed_dir / "dataset_10_EV_metadata.csv"
    
    # 4. 执行
    generate_metadata(input_file, output_file)