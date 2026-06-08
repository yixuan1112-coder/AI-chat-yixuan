import pandas as pd
import numpy as np
from pathlib import Path

def generate_cycle_summary(raw_dir, processed_dir):
    # 只取时序主文件
    files = [f for f in raw_dir.rglob("*.csv") if "impedance" not in f.name.lower()]
    columns = ['cell_id', 'cycle_id', 'capacity_Ah', 'SOH', 'RUL', 'charge_capacity_Ah', 'discharge_capacity_Ah', 'temperature_max_C', 'temperature_avg_C', 'charge_duration_s', 'discharge_duration_s', 'internal_resistance_Ohm', 'cycle_end_flag']
    
    success_count = 0
    for file in files:
        cell_id = file.stem
        imp_file = file.parent / f"{cell_id}_impedance.csv"
        
        try:
            df = pd.read_csv(file)
            
            # 按 cycleNumber 聚合时序数据
            agg_df = df.groupby('cycleNumber').agg({
                'QCharge_mA_h': 'max',
                'QDischarge_mA_h': 'max',
                'Temperature__C': ['max', 'mean']
            }).reset_index()
            
            # 扁平化多级表头
            agg_df.columns = ['cycle_id', 'max_q_charge', 'max_q_discharge', 'temp_max', 'temp_avg']
            
            out_df = pd.DataFrame()
            out_df['cycle_id'] = agg_df['cycle_id'].astype(int)
            out_df['cell_id'] = cell_id
            
            # 单位转换：mA_h -> Ah
            out_df['charge_capacity_Ah'] = (agg_df['max_q_charge'] / 1000.0).round(4)
            out_df['discharge_capacity_Ah'] = (agg_df['max_q_discharge'] / 1000.0).round(4)
            
            # 核心容量取放电容量，若缺失则用充电容量
            out_df['capacity_Ah'] = out_df['discharge_capacity_Ah'].where(out_df['discharge_capacity_Ah'] > 0, out_df['charge_capacity_Ah'])
            
            out_df['temperature_max_C'] = agg_df['temp_max'].round(2)
            out_df['temperature_avg_C'] = agg_df['temp_avg'].round(2)
            out_df['cycle_end_flag'] = 'normal'
            
            # 计算 SOH (基于标称容量 3.0Ah)
            out_df['SOH'] = (out_df['capacity_Ah'] / 3.0).round(4)
            out_df['internal_resistance_Ohm'] = np.nan
            
            # === 合并 Impedance 数据 ===
            if imp_file.exists():
                imp_df = pd.read_csv(imp_file)
                # 选择一个统一的标准内阻 (如 60% SOC 下 1秒测量的内阻)
                imp_col = '60%_1_second' if '60%_1_second' in imp_df.columns else imp_df.columns[0]
                
                # 重命名合并键以对齐
                imp_df = imp_df.rename(columns={'cycle numbers': 'cycle_id'})
                
                # 合并
                out_df = out_df.merge(imp_df[['cycle_id', imp_col]], on='cycle_id', how='left')
                out_df['internal_resistance_Ohm'] = out_df[imp_col].round(5)
                out_df = out_df.drop(columns=[imp_col])
                print(f"🔗 {cell_id} 成功融合内阻数据")
            
            # 补齐和排序列
            for col in columns:
                if col not in out_df.columns: out_df[col] = np.nan
            
            output_path = processed_dir / f"dataset_21_{cell_id}_cycle_summary.csv"
            out_df[columns].to_csv(output_path, index=False)
            success_count += 1
            
        except Exception as e:
            print(f"❌ 处理 {file.name} 失败: {e}")
            
    print(f"\n🎉 处理完毕，共生成 {success_count} 个汇总表。")

if __name__ == "__main__":
    raw_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\raw\dataset_21_CMU\14226830")
    processed_dir = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_21")
    processed_dir.mkdir(parents=True, exist_ok=True)
    generate_cycle_summary(raw_dir, processed_dir)