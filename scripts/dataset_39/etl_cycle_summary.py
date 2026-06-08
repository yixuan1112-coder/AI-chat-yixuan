import pandas as pd
import numpy as np
from pathlib import Path
import h5py

def get_matlab_string(f, ref):
    try: return "".join(chr(c[0]) for c in f[ref][:])
    except: return ""

def process_cqu_cyclesummary():
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_39_CQU\Battery aging datasets for Increasing generalization capability of battery health estimation using continual learning approach")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_39")
    processed_dir.mkdir(parents=True, exist_ok=True)

    for raw_file in raw_dir.rglob("*.mat"):
        print(f"正在处理汇总数据: {raw_file.name}")
        with h5py.File(raw_file, 'r') as f:
            top_key = [k for k in f.keys() if k != '#refs#'][0]
            top_group = f[top_key]
            
            # CQU 的汇总数据直接在 Capacity 和 cycles 里
            if 'Capacity' not in top_group: continue
            
            cell_refs = top_group['cell']
            cap_refs = top_group['Capacity']
            
            for i in range(cell_refs.shape[0]):
                cell_id = f"CQU_{get_matlab_string(f, cell_refs[i,0]).strip()}"
                print(f"  -> 生成 {cell_id} 的 {cap_refs[i,0].shape if hasattr(cap_refs[i,0], 'shape') else ''} 循环汇总...", end=" ")
                
                # 提取容量矩阵 (1 x N)
                cap_values = np.array(f[cap_refs[i, 0]]).flatten()
                
                recs = []
                for idx, val in enumerate(cap_values):
                    # 将百分比转换为 Ah (额定 2.0Ah)
                    actual_cap = (val / 100.0) * 2.0
                    
                    recs.append({
                        'cell_id': cell_id,
                        'cycle_id': idx + 1,
                        'capacity_Ah': actual_cap,
                        'SOH': val / 100.0, # SOH 即当前容量/额定容量
                        'RUL': None,
                        'charge_capacity_Ah': None,
                        'discharge_capacity_Ah': actual_cap,
                        'temperature_max_C': None, 'temperature_avg_C': None,
                        'charge_duration_s': None, 'discharge_duration_s': None,
                        'internal_resistance_Ohm': None, 'cycle_end_flag': 1
                    })
                
                df_sum = pd.DataFrame(recs)
                # 强制 Schema 13 列顺序
                schema_cols = ['cell_id', 'cycle_id', 'capacity_Ah', 'SOH', 'RUL', 'charge_capacity_Ah', 
                               'discharge_capacity_Ah', 'temperature_max_C', 'temperature_avg_C', 
                               'charge_duration_s', 'discharge_duration_s', 'internal_resistance_Ohm', 'cycle_end_flag']
                df_sum = df_sum[schema_cols]
                df_sum.to_csv(processed_dir / f"{cell_id}_cycle_summary.csv", index=False)
                print(f"✅ 完成 ({len(df_sum)} 行)")

if __name__ == "__main__":
    process_cqu_cyclesummary()