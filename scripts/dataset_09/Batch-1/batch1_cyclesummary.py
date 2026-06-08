import pandas as pd
import numpy as np
from pathlib import Path
import scipy.io as sio
from concurrent.futures import ProcessPoolExecutor

# 路径，可改(注意大小写！)
RAW_DIR = Path(r"D:\phd\BatteryTwin-Benchmark-DataPrep\data\raw\XJTU_dataset\XJTU battery dataset\Batch-1")
PROCESSED_DIR = Path(r"D:\phd\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_09\Batch-1")

# 按标准列处理
SUMMARY_COLS = [
    'cell_id', 'cycle_id', 'step_type', 'capacity_Ah', 'SOH', 'RUL', 
    'charge_capacity_Ah', 'discharge_capacity_Ah', 'temperature_max_C', 
    'temperature_avg_C', 'charge_duration_s', 'discharge_duration_s', 
    'internal_resistance_Ohm', 'cycle_end_flag'
]

def process_single_summary(f):
    cell_id = f"{f.parent.name}_{f.stem}"
    local_sum_list = []
    try:
        mat_data = sio.loadmat(f)
        if 'data' not in mat_data: return None
        
        cycles = mat_data['data']
        for c_idx in range(cycles.shape[1]):
            raw_cycle = cycles[0, c_idx]
            if len(raw_cycle['capacity_Ah'].flatten()) == 0: continue
            
            cap = raw_cycle['capacity_Ah'].flatten().max()
            temps = raw_cycle['temperature_C'].flatten()
            
            record = {col: np.nan for col in SUMMARY_COLS}
            record.update({
                "cell_id": cell_id, "cycle_id": c_idx + 1, "step_type": "discharge",
                "capacity_Ah": cap, "SOH": cap / 2.0, "discharge_capacity_Ah": cap,
                "temperature_max_C": temps.max() if len(temps) > 0 else np.nan,
                "temperature_avg_C": temps.mean() if len(temps) > 0 else np.nan,
                "cycle_end_flag": "normal"
            })
            local_sum_list.append(record)
        return local_sum_list
    except Exception as e:
        print(f"⚠️ 跳过 {cell_id}: {e}")
        return None

def generate_summary():
    raw_files = [f for f in RAW_DIR.rglob("*.mat") if "Compensation" not in f.name]
    print(f" 开始提取 {len(raw_files)} 个电池的 Cycle Summary (多进程加速中)...")

    sum_list = []
    
    # 并行加速，根据电脑改max_workers的值
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = executor.map(process_single_summary, raw_files)
        
    for res in results:
        if res is not None:
            sum_list.extend(res)

    df = pd.DataFrame(sum_list).reindex(columns=SUMMARY_COLS)
    df.to_csv(PROCESSED_DIR / "dataset_XJTU_Batch-1_cycle_summary.csv", index=False, encoding='utf-8-sig')
    
    # 实际数据应该在3000-4000行左右，时间在30seconds左右
    print(f" Cycle Summary 生成完毕！总共提取了 {len(df)} 行衰减数据。")

if __name__ == "__main__":
    generate_summary()