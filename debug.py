import json
import glob
import pandas as pd

# 1. 读取 json 里记录的第一个 cell_id
with open("benchmarks/data/split_config.json", "r") as f:
    cell_ids = json.load(f)["datasets"]["dataset_08"]["splits"]["train"]

cell = cell_ids[0]
print(f"🔍 1. 正在尝试匹配 JSON 中的 Cell: {cell}")

# 2. 去文件夹里找对应的 CSV
files = glob.glob(f"D:/p/BatteryTwin-Benchmark-DataPrep/data/processed/dataset_08/timeseries/*{cell}*.csv")
print(f"📂 2. 实际找到的文件路径: {files}")

if files:
    df = pd.read_csv(files[0])
    print(f"📊 3. CSV 实际包含的列名: {df.columns.tolist()}")
    
    # 检查容量列的健康度
    if "discharge_capacity_Ah" in df.columns:
        nans = df["discharge_capacity_Ah"].isna().sum()
        print(f"⚠️ 4. discharge_capacity_Ah 列共有 {len(df)} 行，其中空值(NaN)有 {nans} 行")
    elif "charge_capacity_Ah" in df.columns:
        nans = df["charge_capacity_Ah"].isna().sum()
        print(f"⚠️ 4. charge_capacity_Ah 列共有 {len(df)} 行，其中空值(NaN)有 {nans} 行")
    else:
        print("❌ 4. 致命错误：找不到任何容量标签列！")