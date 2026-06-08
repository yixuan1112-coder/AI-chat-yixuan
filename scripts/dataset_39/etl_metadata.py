import pandas as pd
from pathlib import Path
import h5py

def get_matlab_string(f, ref):
    try: return "".join(chr(c[0]) for c in f[ref][:])
    except: return ""

def generate_cqu_metadata():
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_39_CQU\Battery aging datasets for Increasing generalization capability of battery health estimation using continual learning approach")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_39")
    processed_dir.mkdir(parents=True, exist_ok=True)

    metadata_records = []
    for raw_file in raw_dir.rglob("*.mat"):
        print(f"正在读取元数据: {raw_file.name}")
        try:
            with h5py.File(raw_file, 'r') as f:
                top_key = [k for k in f.keys() if k != '#refs#'][0]
                cell_refs = f[top_key]['cell']
                for i in range(cell_refs.shape[0]):
                    cell_id = f"CQU_{get_matlab_string(f, cell_refs[i, 0]).strip()}"
                    metadata_records.append({
                        "dataset_id": "dataset_39", "cell_id": cell_id, "source_type": "public",
                        "split_tag": "", "chemistry": "NMC", "cathode_material": "LiNiMnCoO2",
                        "anode_material": "Graphite", "brand_or_manufacturer": "Samsung SDI",
                        "model_or_size": "INR18650-20R", "form_factor": "cylindrical",
                        "nominal_capacity_Ah": 2.0, "nominal_voltage_V": 3.6, "temperature_C": "ambient",
                        "charge_protocol": "CC-CV", "discharge_protocol": "Dynamic",
                        "C_rate": "unknown", "cutoff_voltage_upper": 4.2, "cutoff_voltage_lower": 2.5
                    })
        except Exception as e: print(f"跳过文件 {raw_file.name}: {e}")

    pd.DataFrame(metadata_records).to_csv(processed_dir / "dataset_39_CQU_metadata.csv", index=False)
    print(f"✅ Metadata 已生成")

if __name__ == "__main__":
    generate_cqu_metadata()