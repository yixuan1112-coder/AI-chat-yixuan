import pandas as pd
import json
from pathlib import Path

def generate_jrc_metadata():
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_40_JRC")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_40")
    processed_dir.mkdir(parents=True, exist_ok=True)

    org_name = "unknown"
    # 极速解析 JSON-LD 提取机构信息
    try:
        for json_file in raw_dir.rglob("*.jsonld"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("@graph", []):
                    if item.get("@type") == "foaf:Organization" and "foaf:name" in item:
                        org_name = item["foaf:name"]
                        break
    except Exception as e:
        print(f"JSON-LD 读取提示: {e}")

    metadata_records = []
    # 原始 CSV 中包含的 6 种不同测试功率级 (根据你上传的表头提取)
    test_conditions = ["3300", "2700", "1650", "1000", "660", "330"]

    for condition in test_conditions:
        cell_id = f"JRC_{condition}"
        record = {
            "dataset_id": "dataset_40",
            "cell_id": cell_id,
            "source_type": "public",
            "split_tag": "",
            "chemistry": "Li-ion", # 数据集名称写了 Lithium Ion
            "cathode_material": "unknown",
            "anode_material": "unknown",
            "brand_or_manufacturer": org_name, # 使用从 JSON-LD 提取的机构
            "model_or_size": "unknown",
            "form_factor": "unknown",
            "nominal_capacity_Ah": 0.0, 
            "nominal_voltage_V": 0.0,
            "temperature_C": "ambient",
            "charge_protocol": f"Charge_Power_{condition}",
            "discharge_protocol": f"Discharge_Power_{condition}",
            "C_rate": "unknown",
            "cutoff_voltage_upper": None,
            "cutoff_voltage_lower": None
        }
        metadata_records.append(record)

    df_meta = pd.DataFrame(metadata_records)
    out_path = processed_dir / "dataset_40_JRC_metadata.csv"
    df_meta.to_csv(out_path, index=False)
    print(f"✅ Metadata 生成完毕: {out_path.name}")

if __name__ == "__main__":
    generate_jrc_metadata()