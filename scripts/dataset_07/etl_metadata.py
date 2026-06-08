import pandas as pd
import os
import glob
import re

PROCESSED_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_07"
DATASET_ID = "dataset_07" 
# ============================================================

META_COLS = [
    'dataset_id', 'cell_id', 'source_type', 'split_tag', 'chemistry', 
    'cathode_material', 'anode_material', 'brand_or_manufacturer', 
    'model_or_size', 'form_factor', 'nominal_capacity_Ah', 
    'nominal_voltage_V', 'temperature_C', 'charge_protocol', 
    'discharge_protocol', 'C_rate', 'cutoff_voltage_upper', 'cutoff_voltage_lower'
]

def parse_general_filename(filename, dataset_id):
    info = {col: 'unknown' for col in META_COLS}
    info.update({
        'dataset_id': dataset_id,
        'source_type': 'public',
        'split_tag': 'unassigned',
        'anode_material': 'Graphite',
        'nominal_voltage_V': 3.6,
        'cutoff_voltage_upper': 4.2,
        'cutoff_voltage_lower': 2.5
    })
    
    fn_lower = filename.lower()
    
    # 1. 提取形状
    if '18650' in fn_lower:
        info.update({'model_or_size': '18650', 'form_factor': 'cylindrical'})
    elif 'pouch' in fn_lower:
        info.update({'model_or_size': 'pouch', 'form_factor': 'pouch'})

    # 2. 提取化学体系与容量
    if 'nmc_lco' in fn_lower or ('nmc' in fn_lower and 'lco' in fn_lower):
        info.update({'chemistry': 'NMC_LCO', 'cathode_material': 'LiNiMnCoO2-LiCoO2', 'cutoff_voltage_lower': 2.7})
        if info['model_or_size'] == '18650': info['nominal_capacity_Ah'] = 2.8 # HNEI 专属
    elif 'nca' in fn_lower:
        info.update({'chemistry': 'NCA', 'cathode_material': 'LiNiCoAlO2'})
        if info['model_or_size'] == '18650': info['nominal_capacity_Ah'] = 3.4 # UL 专属

    # 3. 提取温度
    temp_match = re.search(r'_(\d+)c_', fn_lower)
    if temp_match: info['temperature_C'] = float(temp_match.group(1))

    # 4. 提取倍率并生成协议
    crate_match = re.search(r'_(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)c_', fn_lower)
    charge_c, discharge_c = "unknown", "unknown"
    if crate_match: 
        charge_c = f"{crate_match.group(1)}C"
        discharge_c = f"{crate_match.group(2)}C"
        info['C_rate'] = f"{charge_c}/{discharge_c}"

    up_v = info['cutoff_voltage_upper']
    low_v = info['cutoff_voltage_lower']
    info['charge_protocol'] = f"CC-CV {charge_c} to {up_v}V" if charge_c != "unknown" else "CC-CV"
    info['discharge_protocol'] = f"CC {discharge_c} to {low_v}V" if discharge_c != "unknown" else "CC"

    return info

def generate_general_metadata():
    search_pattern = os.path.join(PROCESSED_BASE_DIR, "**", "*_cycle_summary.csv")
    files = glob.glob(search_pattern, recursive=True)
    print(f"正在扫描 {DATASET_ID} 已处理文件...")

    records = []
    for f in files:
        cell_id = os.path.basename(f).replace('_cycle_summary.csv', '')
        info = parse_general_filename(cell_id, DATASET_ID)
        info['cell_id'] = cell_id
        records.append(info)

    df_meta = pd.DataFrame(records, columns=META_COLS)
    out_path = os.path.join(PROCESSED_BASE_DIR, f"{DATASET_ID}_metadata.csv")
    df_meta.to_csv(out_path, index=False)
    print(f"✅ {DATASET_ID} 标准元数据表已导出至: {out_path}")

if __name__ == "__main__":
    generate_general_metadata()