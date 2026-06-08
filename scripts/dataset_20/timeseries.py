import pandas as pd
from pathlib import Path
import re

RAW_DATA_ROOT = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_20_UM\Battery Test Data")
OUTPUT_ROOT = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_20")

TS_SCHEMA = [
    "cell_id", "cycle_id", "time_s", "voltage_V", "current_A",
    "temperature_C", "charge_capacity_Ah", "discharge_capacity_Ah", "step_type"
]

def parse_cell_id_and_temp(folder_path):
    path_str_lower = str(folder_path.absolute()).lower()
    path_parts = [p.lower() for p in folder_path.parts]
    chemistry = "unknown"
    if "lifepo4" in path_str_lower or "lfp" in path_str_lower: chemistry = "LFP"
    elif "nca" in path_str_lower: chemistry = "NCA"
    elif "nmc" in path_str_lower or "murata" in path_str_lower or "vtc6" in path_str_lower: chemistry = "NMC"
    temp_c = "unknown"
    for part in path_parts:
        if any(k in part for k in ["degree", "deg", "drgree", "dgree"]):
            part_mod = re.sub(r'(?i)(negative|minus|n)\s*(\d+)', r'-\2', part)
            match = re.search(r'(-?\d+)', part_mod)
            if match:
                temp_c = float(match.group())
                break
    if temp_c == "unknown": return None, None
    temp_str = str(temp_c).replace(".", "_")
    return f"UM_{chemistry}_{temp_str}C", temp_c

def get_col(df, keywords):
    for col in df.columns:
        c_lower = str(col).lower().strip()
        if any(k in c_lower for k in keywords):
            return df[col]
    return None

def process_timeseries():
    print("Step 2: 正在提取时序数据 (抗污染高鲁棒版)...")
    if not RAW_DATA_ROOT.exists(): return
    all_files = list(RAW_DATA_ROOT.rglob("*.csv")) + list(RAW_DATA_ROOT.rglob("*.xls*"))
    
    folders_map = {}
    for f in all_files:
        if f.parent not in folders_map: folders_map[f.parent] = []
        folders_map[f.parent].append(f)

    for raw_folder, files in folders_map.items():
        try: rel_path = raw_folder.relative_to(RAW_DATA_ROOT)
        except: continue
            
        target_out_folder = OUTPUT_ROOT / rel_path
        cell_id, temp_c = parse_cell_id_and_temp(raw_folder)
        all_dfs = []
        
        for file in files:
            fname = file.name
            try:
                if file.suffix.lower() == '.csv': sheets = {fname: pd.read_csv(file)}
                else: sheets = pd.read_excel(file, sheet_name=None)
            except: continue
                
            for sheet_name, df_tmp in sheets.items():
                name_to_check = f"{fname} - {sheet_name}".lower()
                
                # 过滤掉明显的统计汇总页，避免时序误抓
                if "total of cycle" in [str(c).lower().strip() for c in df_tmp.columns]:
                    continue
                    
                try:
                    df_tmp.columns = [str(c).strip() for c in df_tmp.columns]
                    col_time = get_col(df_tmp, ["time", "record", "index"])
                    col_volt = get_col(df_tmp, ["volt", "v"])
                    col_curr = get_col(df_tmp, ["curr", "cur", "amp", "a"])
                    col_cap = get_col(df_tmp, ["cap"])
                    
                    if col_time is None or col_volt is None or col_curr is None:
                        continue
                    
                    # 终极强固：强制将可能包含字符串的列转化为纯数值，阻断 abs() 报错崩溃
                    col_time = pd.to_numeric(col_time, errors='coerce')
                    col_volt = pd.to_numeric(col_volt, errors='coerce')
                    col_curr = pd.to_numeric(col_curr, errors='coerce')
                    if col_cap is not None:
                        col_cap = pd.to_numeric(col_cap, errors='coerce')
                    
                    curr_a = col_curr / 1000.0 if col_curr.abs().max() > 50 else col_curr
                    cap_ah = col_cap / 1000.0 if col_cap is not None and col_cap.abs().max() > 50 else col_cap
                    
                    if "detail" in name_to_check or "pcpd" in name_to_check:
                        col_cycle = get_col(df_tmp, ["cycle"])
                        col_status = get_col(df_tmp, ["status", "step"])
                        df_clean = pd.DataFrame({
                            "cell_id": cell_id,
                            "cycle_id": col_cycle.fillna(1).astype(int) if col_cycle is not None else 1,
                            "time_s": col_time - 1 if "index" in str(col_time.name).lower() else col_time,
                            "voltage_V": col_volt, "current_A": curr_a, "temperature_C": temp_c,
                            "charge_capacity_Ah": cap_ah, "discharge_capacity_Ah": None,
                            "step_type": col_status if col_status is not None else "Detail"
                        })
                    else:
                        test_type = str(sheet_name).strip() if file.suffix.lower() != '.csv' else fname.split("-")[-1].replace(".csv", "").strip()
                        if test_type.startswith("Sheet"): test_type = file.stem
                        df_clean = pd.DataFrame({
                            "cell_id": cell_id, "cycle_id": 1, "time_s": col_time,
                            "voltage_V": col_volt, "current_A": curr_a, "temperature_C": temp_c,
                            "charge_capacity_Ah": cap_ah, "discharge_capacity_Ah": None,
                            "step_type": test_type 
                        })
                        
                    if not df_clean.empty:
                        all_dfs.append(df_clean.dropna(subset=["time_s", "voltage_V"]))
                except:
                    continue

        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True).reindex(columns=TS_SCHEMA)
            target_out_folder.mkdir(parents=True, exist_ok=True)
            final_df.to_csv(target_out_folder / "timeseries.csv", index=False)
            print(f"  ✅ 时序成功深层克隆输出 -> {rel_path}\\timeseries.csv")

if __name__ == "__main__":
    process_timeseries()