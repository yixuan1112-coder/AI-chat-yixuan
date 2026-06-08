import pandas as pd
from pathlib import Path
import pickle

def generate_hust_metadata():
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_41_HUST\nsc7hnsg4s-2\our_data\our_data")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_41")
    processed_dir.mkdir(parents=True, exist_ok=True)

    metadata_records = []
    for pkl_file in raw_dir.glob("*.pkl"):
        cell_id = f"HUST_{pkl_file.stem}"
        
        # 基础元数据 (基于 HUST LFP 数据集标准参数)
        record = {
            "dataset_id": "dataset_41",
            "cell_id": cell_id,
            "source_type": "public",
            "split_tag": "",
            "chemistry": "LFP",
            "cathode_material": "LiFePO4",
            "anode_material": "Graphite",
            "brand_or_manufacturer": "A123 Systems",
            "model_or_size": "APR18650M1A",
            "form_factor": "cylindrical",
            "nominal_capacity_Ah": 1.1,
            "nominal_voltage_V": 3.3,
            "temperature_C": "ambient",
            "charge_protocol": "CC-CV",
            "discharge_protocol": "Fast Charge / Dynamic",
            "C_rate": "unknown",
            "cutoff_voltage_upper": 3.6,
            "cutoff_voltage_lower": 2.0
        }
        metadata_records.append(record)

    df_meta = pd.DataFrame(metadata_records)
    df_meta.to_csv(processed_dir / "dataset_41_HUST_metadata.csv", index=False)
    print(f"✅ Metadata 已生成: {len(df_meta)} 条记录")

if __name__ == "__main__":
    generate_hust_metadata()