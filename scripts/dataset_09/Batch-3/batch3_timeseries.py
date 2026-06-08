import pandas as pd
import numpy as np
from pathlib import Path
import scipy.io as sio
from concurrent.futures import ProcessPoolExecutor

# 路径设置
RAW_DIR = Path(r"D:\phd\BatteryTwin-Benchmark-DataPrep\data\raw\XJTU_dataset\XJTU battery dataset\Batch-3")
PROCESSED_DIR = Path(r"D:\phd\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_09\Batch-3")

# 标准列名
TS_COLS = [
    'cell_id', 'cycle_id', 'time_s', 'voltage_V', 'current_A', 
    'temperature_C', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'step_type'
]

def process_ts(file_path):
    # 生成该文件对应的 cell_id (例如: Batch-1_1_1)
    cell_id = f"{file_path.parent.name}_{file_path.stem}"
    # 定义该文件对应的 CSV 输出路径
    output_path = PROCESSED_DIR / f"{cell_id}_timeseries.csv"
    
    try:
        mat_data = sio.loadmat(file_path)
        if 'data' not in mat_data: return f"跳过 {file_path.name}: 无 data 键"
            
        cycles = mat_data['data']
        file_ts_list = []
        
        for c_idx in range(cycles.shape[1]):
            raw_cycle = cycles[0, c_idx]
            temp_dict = {name: raw_cycle[name].flatten() for name in raw_cycle.dtype.names}
            lengths = [len(arr) for arr in temp_dict.values() if len(arr) > 0]
            if not lengths: continue
            
            main_len = max(set(lengths), key=lengths.count)
            clean_dict = {k: v for k, v in temp_dict.items() if len(v) == main_len}
            df_cycle = pd.DataFrame(clean_dict)
            
            ts_part = pd.DataFrame(index=range(len(df_cycle)))
            ts_part['cell_id'] = cell_id
            ts_part['cycle_id'] = c_idx + 1
            ts_part['time_s'] = df_cycle['relative_time_min'] * 60  
            ts_part['voltage_V'] = df_cycle['voltage_V']
            ts_part['current_A'] = df_cycle['current_A'] * -1       
            ts_part['temperature_C'] = df_cycle['temperature_C']
            ts_part['charge_capacity_Ah'] = np.nan
            ts_part['discharge_capacity_Ah'] = df_cycle['capacity_Ah']
            ts_part['step_type'] = 'discharge'
            file_ts_list.append(ts_part.reindex(columns=TS_COLS))
            
        if file_ts_list:
            # 合并当前文件的所有 cycle 并保存
            df_final = pd.concat(file_ts_list, ignore_index=True)
            df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
            return f"成功: {output_path.name}"
        return f"忽略: {file_path.name} (无有效数据)"
        
    except Exception as e:
        return f"错误 {file_path.name}: {str(e)}"

def generate_timeseries():
    # 确保输出目录存在
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    raw_files = [f for f in RAW_DIR.rglob("*.mat") if "Compensation" not in f.name]
    print(f" 开始并行提取数据，共 {len(raw_files)} 个文件...")

    # 使用并行处理
    with ProcessPoolExecutor(max_workers=4) as executor:
        # map 会依次调用 process_ts 并返回结果（这里返回的是状态字符串）
        for result in executor.map(process_ts, raw_files):
            print(result)
                
    print("\n 所有时序数据分文件保存完成！")

if __name__ == "__main__":
    generate_timeseries()