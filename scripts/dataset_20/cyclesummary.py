import pandas as pd
from pathlib import Path
import re

RAW_DATA_ROOT = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_20_UM\Battery Test Data")
OUTPUT_ROOT = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_20")

CS_SCHEMA = [
    "cell_id", "cycle_id", "capacity_Ah", "SOH", "RUL",
    "charge_capacity_Ah", "discharge_capacity_Ah", "temperature_max_C",
    "temperature_avg_C", "charge_duration_s", "discharge_duration_s",
    "internal_resistance_Ohm", "cycle_end_flag"
]

def parse_cell_id_only(folder_path):
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
    if temp_c == "unknown": return None
    temp_str = str(temp_c).replace(".", "_")
    return f"UM_{chemistry}_{temp_str}C"

def get_col(df, keywords):
    for col in df.columns:
        c_lower = str(col).lower().strip()
        if any(k in c_lower for k in keywords):
            return df[col]
    return None

def process_cyclesummary():
    print("Step 3: 正在扫描全量文件提取循环统计 (无视任何文件名枷锁)...")
    if not RAW_DATA_ROOT.exists(): return
    all_files = list(RAW_DATA_ROOT.rglob("*.csv")) + list(RAW_DATA_ROOT.rglob("*.xls*"))
    
    folders_map = {}
    for f in all_files:
        if f.parent not in folders_map: folders_map[f.parent] = []
        folders_map[f.parent].append(f)
        
    for raw_folder, files in folders_map.items():
        try: rel_path = raw_folder.relative_to(RAW_DATA_ROOT)
        except: continue
            
        cell_id = parse_cell_id_only(raw_folder)
        if not cell_id: continue
            
        target_out_folder = OUTPUT_ROOT / rel_path
        all_dfs = []
        
        for file in files:
            try:
                if file.suffix.lower() == '.csv': sheets = {file.name: pd.read_csv(file)}
                else: sheets = pd.read_excel(file, sheet_name=None)
            except: continue
                
            for sheet_name, df_tmp in sheets.items():
                try:
                    df_tmp.columns = [str(c).strip() for c in df_tmp.columns]
                    col_cycle = get_col(df_tmp, ["total of cycle", "cycle_index", "cycle id"])
                    col_dis_cap = get_col(df_tmp, ["discharge(mah)", "discharge capacity", "capacity of discharge"])
                    col_chg_cap = get_col(df_tmp, ["charge(mah)", "charge capacity", "capacity of charge"])
                    col_soh = get_col(df_tmp, ["cycle life(%)", "soh"])
                    
                    # 只要列名符合特征，不管它是哪里的 Sheet，通通抠出作为汇总表
                    if col_cycle is not None and col_dis_cap is not None and len(df_tmp) < 5000:
                        
                        # 转换并清洗可能混入的脏字符串数据
                        c_id = pd.to_numeric(col_cycle, errors='coerce')
                        d_cap = pd.to_numeric(col_dis_cap, errors='coerce')
                        
                        df_clean = pd.DataFrame({
                            "cell_id": cell_id,
                            "cycle_id": c_id,
                            "capacity_Ah": d_cap / 1000.0 if d_cap.abs().max() > 50 else d_cap, 
                            "SOH": col_soh / 100.0 if col_soh is not None and col_soh.max() > 1.5 else col_soh, 
                            "charge_capacity_Ah": col_chg_cap / 1000.0 if col_chg_cap is not None else None,
                            "discharge_capacity_Ah": d_cap / 1000.0 if d_cap.abs().max() > 50 else d_cap,
                            "cycle_end_flag": "normal"
                        }).dropna(subset=["cycle_id", "capacity_Ah"])
                        
                        all_dfs.append(df_clean)
                except:
                    continue
                        
        if all_dfs:
            final_cycle = pd.concat(all_dfs, ignore_index=True).reindex(columns=CS_SCHEMA)
            final_cycle = final_cycle.drop_duplicates(subset=["cycle_id"])
            final_cycle['cycle_id'] = final_cycle['cycle_id'].astype(int)
            
            target_out_folder.mkdir(parents=True, exist_ok=True)
            out_file = target_out_folder / "cycle_summary.csv"
            final_cycle.to_csv(out_file, index=False)
            print(f"  🔋 汇总成功输出 -> {rel_path}\\cycle_summary.csv")

if __name__ == "__main__":
    process_cyclesummary()