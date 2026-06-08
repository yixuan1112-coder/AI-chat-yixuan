import pandas as pd
import os
import glob
import re

# === SNL 专属配置 ===
PROCESSED_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_06"
DATASET_ID = "dataset_06"
# ====================

# 18 列 XJTU 标准规范
META_COLS = [
    'dataset_id', 'cell_id', 'source_type', 'split_tag', 'chemistry', 
    'cathode_material', 'anode_material', 'brand_or_manufacturer', 
    'model_or_size', 'form_factor', 'nominal_capacity_Ah', 
    'nominal_voltage_V', 'temperature_C', 'charge_protocol', 
    'discharge_protocol', 'C_rate', 'cutoff_voltage_upper', 'cutoff_voltage_lower'
]

def parse_snl_filename(filename):
    info = {col: 'unknown' for col in META_COLS}
    info.update({
        'dataset_id': DATASET_ID,
        'source_type': 'public',
        'split_tag': 'unassigned', 
        'anode_material': 'Graphite',
        'model_or_size': '18650',
        'form_factor': 'cylindrical'
    })
    
    fn_lower = filename.lower()
    
    # 1. 提取化学体系和参数
    if 'lfp' in fn_lower:
        info.update({'chemistry': 'LFP', 'cathode_material': 'LiFePO4', 'brand_or_manufacturer': 'A123',
                     'nominal_capacity_Ah': 1.1, 'nominal_voltage_V': 3.3, 
                     'cutoff_voltage_upper': 3.6, 'cutoff_voltage_lower': 2.0})
    elif 'nmc' in fn_lower:
        info.update({'chemistry': 'NMC', 'cathode_material': 'LiNiMnCoO2', 'brand_or_manufacturer': 'LG Chem',
                     'nominal_capacity_Ah': 3.0, 'nominal_voltage_V': 3.6, 
                     'cutoff_voltage_upper': 4.2, 'cutoff_voltage_lower': 2.5})
    elif 'nca' in fn_lower:
        info.update({'chemistry': 'NCA', 'cathode_material': 'LiNiCoAlO2', 'brand_or_manufacturer': 'Panasonic',
                     'nominal_capacity_Ah': 3.2, 'nominal_voltage_V': 3.6, 
                     'cutoff_voltage_upper': 4.2, 'cutoff_voltage_lower': 2.5})

    # 2. 提取温度
    temp_match = re.search(r'_(\d+)c_', fn_lower)
    if temp_match: info['temperature_C'] = float(temp_match.group(1))

    # 3. 提取倍率并生成协议
    crate_match = re.search(r'_(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)c_', fn_lower)
    charge_c, discharge_c = "unknown", "unknown"
    if crate_match: 
        charge_c = f"{crate_match.group(1)}C"
        discharge_c = f"{crate_match.group(2)}C"
        info['C_rate'] = f"{charge_c}/{discharge_c}"

    up_v = info.get('cutoff_voltage_upper', '4.2')
    low_v = info.get('cutoff_voltage_lower', '2.5')
    info['charge_protocol'] = f"CC-CV {charge_c} to {up_v}V" if charge_c != "unknown" else "CC-CV"
    info['discharge_protocol'] = f"CC {discharge_c} to {low_v}V" if discharge_c != "unknown" else "CC"

    return info

def generate_snl_metadata():
    # 修正了这里的变量名拼写错误
    search_pattern = os.path.join(PROCESSED_BASE_DIR, "**", "*_cycle_summary.csv")
    files = glob.glob(search_pattern, recursive=True)
    print(f"正在扫描 SNL 已处理文件，找到 {len(files)} 个...")

    records = []
    for f in files:
        cell_id = os.path.basename(f).replace('_cycle_summary.csv', '')
        info = parse_snl_filename(cell_id)
        info['cell_id'] = cell_id
        records.append(info)

    df_meta = pd.DataFrame(records, columns=META_COLS)
    out_path = os.path.join(PROCESSED_BASE_DIR, f"{DATASET_ID}_metadata.csv")
    df_meta.to_csv(out_path, index=False)
    print(f"✅ SNL 标准元数据表已导出至: {out_path}")

if __name__ == "__main__":
    generate_snl_metadata()