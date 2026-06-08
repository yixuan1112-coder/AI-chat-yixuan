import pandas as pd
from pathlib import Path
import h5py
import numpy as np

def get_matlab_string(f, ref):
    try: return "".join(chr(c[0]) for c in f[ref][:])
    except: return ""

def process_cqu_timeseries():
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_39_CQU\Battery aging datasets for Increasing generalization capability of battery health estimation using continual learning approach")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_39")
    processed_dir.mkdir(parents=True, exist_ok=True)

    for raw_file in raw_dir.rglob("*.mat"):
        print(f"\n🚀 正在扫描: {raw_file.name}")
        with h5py.File(raw_file, 'r') as f:
            top_key = [k for k in f.keys() if k != '#refs#'][0]
            top_group = f[top_key]
            cell_refs, profile_refs = top_group['cell'], top_group['Workingprofile']

            for i in range(cell_refs.shape[0]):
                cell_id = f"CQU_{get_matlab_string(f, cell_refs[i,0]).strip()}"
                print(f"  -> 检查电池 {cell_id}...", end=" ")
                
                # 获取 profile 对象
                prof_obj = f[profile_refs[i, 0]]
                
                # 情况 A: 如果它是 uint16，说明它只是个工况名字字符串，没有原始数据
                if prof_obj.dtype == 'uint16':
                    print(f"ℹ️ 该文件仅含汇总数据，工况名为: {get_matlab_string(f, profile_refs[i,0])}")
                    continue
                
                # 情况 B: 如果它是 object，说明是片段指针列表
                all_v, all_i = [], []
                for seg_ref in prof_obj[:].flatten():
                    if not isinstance(seg_ref, h5py.Reference): continue
                    data_matrix = np.array(f[seg_ref])
                    if data_matrix.ndim == 2:
                        if data_matrix.shape[0] < data_matrix.shape[1]: data_matrix = data_matrix.T
                        # CQU 原始矩阵列顺序：0=Time, 1=Current, 2=Voltage
                        all_i.append(data_matrix[:, 1])
                        all_v.append(data_matrix[:, 2])
                
                if all_v:
                    df_ts = pd.DataFrame({
                        'cell_id': cell_id, 'cycle_id': 1, 'time_s': np.arange(len(np.concatenate(all_v))),
                        'voltage_V': np.concatenate(all_v), 'current_A': np.concatenate(all_i),
                        'temperature_C': 25.0, 'step_type': 'dynamic'
                    })
                    df_ts.to_csv(processed_dir / f"{cell_id}_timeseries.csv", index=False)
                    print(f"✅ 成功提取原始时序 ({len(df_ts)} 行)")
                else:
                    print("❌ 未发现时序矩阵")

if __name__ == "__main__":
    process_cqu_timeseries()