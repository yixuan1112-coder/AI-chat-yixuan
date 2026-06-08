import pandas as pd
from pathlib import Path

# 读取数据集，可更改存放路径
RAW_DIR = Path(r"D:\phd\BatteryTwin-Benchmark-DataPrep\data\raw\XJTU_dataset\XJTU battery dataset")
PROCESSED_DIR = Path(r"D:\phd\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_XJTU")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# 按标准列处理
META_COLS = [
    'dataset_id', 'cell_id', 'source_type', 'split_tag', 'chemistry', 
    'cathode_material', 'anode_material', 'brand_or_manufacturer', 
    'model_or_size', 'form_factor', 'nominal_capacity_Ah', 
    'nominal_voltage_V', 'temperature_C', 'charge_protocol', 
    'discharge_protocol', 'C_rate', 'cutoff_voltage_upper', 'cutoff_voltage_lower'
]

# 
def generate_metadata():
    raw_files = [f for f in RAW_DIR.rglob("*.mat") if "Compensation" not in f.name]
    print(f" 找到 {len(raw_files)} 个电池文件，正在生成 Metadata...")

    meta_list = []
    for f in raw_files:
        cell_id = f"{f.parent.name}_{f.stem}"
        record = {col: 'unknown' for col in META_COLS}

        #注意！有些参数诸如标签、形状等，在数据集的mat文件里并不体现，而是在data-introduction里面，所以必须人为规定
        record.update({
            "dataset_id": "dataset_XJTU", "cell_id": cell_id, "source_type": "public",
            "chemistry": "NCM", "cathode_material": "LiNi0.5Co0.2Mn0.3O2", "anode_material": "Graphite",
            "brand_or_manufacturer": "Lishen", "model_or_size": "18650", "form_factor": "cylindrical", 
            "nominal_capacity_Ah": 2.0, "nominal_voltage_V": 3.6, "temperature_C": 25.0, 
            "charge_protocol": "CC-CV 4A to 4.2V, 100mA cutoff", "discharge_protocol": "CC 2A to 2.5V",
            "C_rate": "2C/1C", "cutoff_voltage_upper": 4.2, "cutoff_voltage_lower": 2.5                       
        })
        meta_list.append(record)

    df = pd.DataFrame(meta_list).reindex(columns=META_COLS)
    df.to_csv(PROCESSED_DIR / "dataset_XJTU_metadata.csv", index=False, encoding='utf-8-sig')
    print(" Metadata 生成完毕！。")

if __name__ == "__main__":
    generate_metadata()