import pandas as pd
from pathlib import Path

# 替换为你 MSE 数据集的真实路径
# 注意路径前面的 'r' 保留，防止 Windows 路径转义报错
MSE_DIR = Path(r"D:\p\BatteryTwin-Benchmark-DataPrep\data\processed\dataset_internal_MSE")

def merge_metadata():
    if not MSE_DIR.exists():
        print(f"❌ 找不到目录: {MSE_DIR}")
        return

    print("开始扫描并合并 metadata...\n")
    df_list = []
    
    # 递归查找所有文件名包含 'metadata' 的 csv 文件
    for csv_path in MSE_DIR.rglob('*metadata*.csv'):
        try:
            df = pd.read_csv(csv_path)
            df_list.append(df)
            # 打印进度，如果觉得太长可以注释掉下面这行
            print(f"  读取成功: {csv_path.parent.name}/{csv_path.name}")
        except Exception as e:
            print(f"  ❌ 读取失败 {csv_path.name}: {e}")

    if not df_list:
        print("\n⚠️ 没有找到任何 metadata 文件！")
        return

    # 1. 纵向拼接所有表格
    merged_df = pd.concat(df_list, ignore_index=True)
    
    # 2. 以电池 ID 去重（防止有些文件重复记录，请确保这里的列名是你真实的 cell id 列名）
    COL_CELL_ID = 'cell_id' 
    if COL_CELL_ID in merged_df.columns:
        original_len = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=[COL_CELL_ID])
        dropped = original_len - len(merged_df)
        if dropped > 0:
            print(f"\n清洗提示: 发现了 {dropped} 条重复的 {COL_CELL_ID} 记录，已自动去重。")

    # 3. 保存到 MSE 数据集的根目录
    output_path = MSE_DIR / "metadata.csv"
    merged_df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"\n🎉 合并大功告成！")
    print(f"共合并了 {len(df_list)} 个子文件夹的数据。")
    print(f"统一文件已保存至: {output_path}")

if __name__ == "__main__":
    merge_metadata()