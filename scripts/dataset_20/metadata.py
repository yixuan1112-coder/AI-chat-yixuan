import pandas as pd
from pathlib import Path
import re

RAW_DATA_ROOT = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_20_UM\Battery Test Data")
OUTPUT_ROOT = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_20")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

META_SCHEMA = [
    "dataset_id", "cell_id", "source_type", "split_tag", "chemistry",
    "cathode_material", "anode_material", "brand_or_manufacturer", "model_or_size",
    "form_factor", "nominal_capacity_Ah", "nominal_voltage_V", "temperature_C",
    "charge_protocol", "discharge_protocol", "C_rate", "cutoff_voltage_upper",
    "cutoff_voltage_lower"
]

def parse_cell_info_from_path(file_path):
    path_str_lower = str(file_path.absolute()).lower()
    path_parts = [p.lower() for p in file_path.parts]
    
    chemistry, cathode, brand, cap_ah, volt_v = "unknown", "unknown", "unknown", None, None
    charge_proto, discharge_proto, upper_v, lower_v = "unknown", "unknown", None, None
    
    if "lifepo4" in path_str_lower or "lfp" in path_str_lower:
        chemistry, cathode, brand, cap_ah, volt_v = "LFP", "LiFePO4", "A123 Systems", 1.1, 3.3
        upper_v, lower_v = 3.6, 2.0
        charge_proto, discharge_proto = "CC-CV 1.1A to 3.6V, 20mA cutoff", "CC to 2.0V"
    elif "nca" in path_str_lower:
        chemistry, cathode, brand, cap_ah, volt_v = "NCA", "LiNiCoAlO2", "Panasonic", 3.4, 3.6
        upper_v, lower_v = 4.2, 2.5
        charge_proto, discharge_proto = "CC-CV 1.625A to 4.2V, 50mA cutoff", "CC to 2.5V"
    elif "nmc" in path_str_lower or "murata" in path_str_lower or "vtc6" in path_str_lower:
        chemistry, cathode, brand, cap_ah, volt_v = "NMC", "LiNiMnCoO2", "Murata", 3.0, 3.6
        upper_v, lower_v = 4.2, 2.5
        charge_proto, discharge_proto = "CC-CV 3.0A to 4.2V, 50mA cutoff", "CC to 2.5V"
        
    if chemistry == "unknown": return None
        
    temp_c = "unknown"
    for part in path_parts:
        # 终极修复：加入 dgree 和所有已知错别字
        if any(k in part for k in ["degree", "deg", "drgree", "dgree"]):
            part_mod = re.sub(r'(?i)(negative|minus|n)\s*(\d+)', r'-\2', part)
            match = re.search(r'(-?\d+)', part_mod)
            if match:
                temp_c = float(match.group())
                break
                
    if temp_c == "unknown": return None
        
    temp_str = str(temp_c).replace(".", "_")
    cell_id = f"UM_{chemistry}_{temp_str}C"
    
    return {
        "dataset_id": "dataset_20", "cell_id": cell_id, "source_type": "public",
        "split_tag": "", "chemistry": chemistry, "cathode_material": cathode,
        "anode_material": "Graphite", "brand_or_manufacturer": brand,
        "model_or_size": "18650", "form_factor": "cylindrical",
        "nominal_capacity_Ah": cap_ah, "nominal_voltage_V": volt_v,
        "temperature_C": temp_c, "charge_protocol": charge_proto,
        "discharge_protocol": discharge_proto, "C_rate": "unknown",
        "cutoff_voltage_upper": upper_v, "cutoff_voltage_lower": lower_v
    }

def generate_metadata():
    print("Step 1: 生成 Metadata (终极容错版)...")
    if not RAW_DATA_ROOT.exists(): return
    all_files = list(RAW_DATA_ROOT.rglob("*.csv")) + list(RAW_DATA_ROOT.rglob("*.xls*"))
    metadata_dict = {}
    for file in all_files:
        info = parse_cell_info_from_path(file)
        if info: metadata_dict[info["cell_id"]] = info
    df_meta = pd.DataFrame(list(metadata_dict.values())).reindex(columns=META_SCHEMA)
    df_meta.to_csv(OUTPUT_ROOT / "dataset_20_metadata.csv", index=False)
    print(f"🎉 Metadata 生成完毕！写入了 {len(df_meta)} 个电芯。")

if __name__ == "__main__":
    generate_metadata()