import pandas as pd
import json
import os
import glob
import re

# === 批量流水线路径配置 ===
RAW_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_internal_MSE\MSE"
OUT_BASE_DIR = r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_internal_MSE\MSE"
DATASET_ID = "dataset_internal_MSE"
# ========================

# 严格对齐 XJTU 的 18 列标准规范
META_COLS = [
    'dataset_id', 'cell_id', 'source_type', 'split_tag', 'chemistry', 
    'cathode_material', 'anode_material', 'brand_or_manufacturer', 
    'model_or_size', 'form_factor', 'nominal_capacity_Ah', 
    'nominal_voltage_V', 'temperature_C', 'charge_protocol', 
    'discharge_protocol', 'C_rate', 'cutoff_voltage_upper', 'cutoff_voltage_lower'
]

def parse_json_to_xjtu_standard(json_path, folder_name):
    """读取 JSON 并映射到 18 列标准"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # 初始化标准字典
    info = {col: 'unknown' for col in META_COLS}
    
    # 1. 基础信息对齐
    info['dataset_id'] = DATASET_ID
    # 保持和上一轮 cycle_summary 相同的命名规则，防止冲突
    info['cell_id'] = f"{folder_name}" 
    info['source_type'] = 'internal'  # 内部数据集标记
    info['split_tag'] = 'unassigned'
    info['brand_or_manufacturer'] = data.get('data_source', 'unknown')

    # 2. 物理与化学体系对齐
    info['anode_material'] = data.get('anode_material', 'Graphite')
    info['nominal_capacity_Ah'] = data.get('nominal_capacity_in_Ah', pd.NA)
    
    # 自动解析化学全称与标称电压常识
    raw_cathode = data.get('cathode_material', '').upper()
    info['chemistry'] = raw_cathode
    if 'LFP' in raw_cathode:
        info['cathode_material'] = 'LiFePO4'
        info['nominal_voltage_V'] = 3.2
    elif 'NCM' in raw_cathode or 'NMC' in raw_cathode:
        info['cathode_material'] = 'LiNiMnCoO2'
        info['nominal_voltage_V'] = 3.6
    elif 'NCA' in raw_cathode:
        info['cathode_material'] = 'LiNiCoAlO2'
        info['nominal_voltage_V'] = 3.6
    else:
        info['cathode_material'] = raw_cathode

    # 自动拆分封装形状 (例如: "cylindrical_18650" -> "18650" 和 "cylindrical")
    raw_form = data.get('form_factor', '')
    if '_' in raw_form:
        parts = raw_form.split('_')
        info['form_factor'] = parts[0]
        info['model_or_size'] = parts[1]
    else:
        info['form_factor'] = raw_form

    # 3. 电压窗口与环境对齐
    info['cutoff_voltage_upper'] = data.get('max_voltage_limit_in_V', pd.NA)
    info['cutoff_voltage_lower'] = data.get('min_voltage_limit_in_V', pd.NA)
    
    env_profile = data.get('environment_profile', {})
    info['temperature_C'] = env_profile.get('ambient_temp_c', pd.NA)

    # 4. 充放电协议与倍率 (C_rate) 动态合成
    raw_chg = data.get('charge_protocol', 'unknown')
    raw_dchg = data.get('discharge_protocol', 'unknown')
    
    # 提取类似 "1C CC" 中的 "1C"
    c_match_chg = re.search(r'([\d\.]+C)', raw_chg)
    c_match_dchg = re.search(r'([\d\.]+C)', raw_dchg)
    chg_rate = c_match_chg.group(1) if c_match_chg else 'unknown'
    dchg_rate = c_match_dchg.group(1) if c_match_dchg else 'unknown'
    
    if chg_rate != 'unknown' and dchg_rate != 'unknown':
        info['C_rate'] = f"{chg_rate}/{dchg_rate}"
        
    # 合成 XJTU 风格的 protocol 文本
    up_v = info['cutoff_voltage_upper']
    low_v = info['cutoff_voltage_lower']
    info['charge_protocol'] = f"{raw_chg} to {up_v}V" if raw_chg != 'unknown' else 'unknown'
    info['discharge_protocol'] = f"{raw_dchg} to {low_v}V" if raw_dchg != 'unknown' else 'unknown'

    return info

def run_metadata_pipeline():
    subfolders = [f.name for f in os.scandir(RAW_BASE_DIR) if f.is_dir()]
    total_folders = len(subfolders)
    print(f"🚀 侦测到 {total_folders} 个电池数据文件夹，启动 Metadata 提取流水线...\n")
    
    success_count = 0
    
    for idx, folder_name in enumerate(subfolders, 1):
        raw_folder_path = os.path.join(RAW_BASE_DIR, folder_name)
        out_folder_path = os.path.join(OUT_BASE_DIR, folder_name)
        
        # 确保输出目录存在（之前跑 summary 时已创建）
        os.makedirs(out_folder_path, exist_ok=True)
        
        # 寻找 metadata.json
        json_files = glob.glob(os.path.join(raw_folder_path, "*.json"))
        
        if not json_files:
            print(f"[{idx}/{total_folders}] ⚠️ 警告: '{folder_name}' 未找到 JSON 文件，已跳过。")
            continue
            
        json_path = json_files[0]
        
        print(f"[{idx}/{total_folders}] 正在解析 JSON: {folder_name} ...", end="")
        
        try:
            # 解析并生成记录
            record = parse_json_to_xjtu_standard(json_path, folder_name)
            
            # 转为 DataFrame 并导出至同名子文件夹
            df_meta = pd.DataFrame([record], columns=META_COLS)
            out_filename = f"{record['cell_id']}_metadata.csv"
            output_csv = os.path.join(out_folder_path, out_filename)
            
            df_meta.to_csv(output_csv, index=False)
            print(" ✅ 成功")
            success_count += 1
            
        except Exception as e:
            print(f" ❌ 失败 ({e})")
            
    print(f"\n🎉 Metadata 提取完毕！共成功生成 {success_count} 份标准元数据表。")
    print(f"📁 结果已存入各自分配的同名文件夹内。")

if __name__ == "__main__":
    run_metadata_pipeline()