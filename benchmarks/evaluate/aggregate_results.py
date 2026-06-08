"""
aggregate_results.py — BatteryTwin Benchmark · 结果汇总脚本
============================================================
用法:
    python aggregate_results.py --results_dir benchmarks/results/ --output summary_table.csv

产出:
    summary_table.csv：行 = 数据集，列 = 模型 × {MAE, RMSE}
    summary_table_rul.csv：RUL 结果（含 N/A 标注）
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd


# 已知模型名（用于列排序）
KNOWN_MODELS = ["mlp", "cnn", "lstm", "transformer", "pinn"]
KNOWN_TASKS  = ["soh", "rul"]
MAIN_METRICS = ["mae", "rmse"]


def load_result_files(results_dir: Path) -> List[Dict]:
    """加载目录下所有结果 JSON"""
    results = []
    json_files = sorted(results_dir.glob("*.json"))

    if not json_files:
        print(f"[WARN] 在 {results_dir} 下未找到任何 JSON 结果文件")
        return results

    for f in json_files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            data["_source_file"] = f.name
            results.append(data)
        except Exception as e:
            print(f"  [WARN] 读取 {f.name} 失败: {e}")

    print(f"加载了 {len(results)} 个结果文件")
    return results


def extract_metric(result: Dict, metric_name: str) -> Any:
    """从结果字典中提取指标值（支持单次 / 多次运行格式）"""
    status = result.get("status", "")

    if status == "na":
        return "N/A"
    if status != "ok":
        return "ERR"

    # 优先用聚合值（多次运行）
    agg = result.get("metrics_aggregated", {})
    if agg and metric_name in agg:
        val = agg[metric_name]
        if isinstance(val, dict):
            mean = val.get("mean")
            std  = val.get("std")
            if mean == "N/A":
                return "N/A"
            return f"{mean:.4f}±{std:.4f}" if std else f"{mean:.4f}"

    # 单次运行
    metrics = result.get("metrics", {})
    val = metrics.get(metric_name)
    if val is None or val == "N/A":
        return "N/A"
    return f"{val:.4f}" if isinstance(val, float) else str(val)


def infer_model_name(result: Dict) -> str:
    """从 model_path 推断模型名称"""
    model_path = result.get("model_path", "")
    path_lower = Path(model_path).stem.lower()

    for m in KNOWN_MODELS:
        if m in path_lower:
            return m

    # fallback：取文件名第一段
    parts = path_lower.replace("-", "_").split("_")
    return parts[0] if parts else "unknown"


def build_summary_table(results: List[Dict], task: str) -> pd.DataFrame:
    """
    构建汇总表：
    行 = 数据集，列 = 模型 × {MAE, RMSE}
    """
    task_results = [r for r in results if r.get("task") == task]

    if not task_results:
        print(f"[WARN] 没有找到 task={task} 的结果")
        return pd.DataFrame()

    # 收集所有数据集和模型
    datasets = sorted(set(r.get("dataset", "unknown") for r in task_results))
    models   = []
    for r in task_results:
        m = infer_model_name(r)
        if m not in models:
            models.append(m)

    # 按 KNOWN_MODELS 顺序排列
    ordered_models = [m for m in KNOWN_MODELS if m in models]
    extra_models   = [m for m in models if m not in KNOWN_MODELS]
    models = ordered_models + extra_models

    # 构建多级列
    col_tuples = [(m, metric) for m in models for metric in MAIN_METRICS]
    cols = pd.MultiIndex.from_tuples(col_tuples, names=["Model", "Metric"])

    rows = {}
    for r in task_results:
        ds    = r.get("dataset", "unknown")
        model = infer_model_name(r)
        if ds not in rows:
            rows[ds] = {}
        for metric in MAIN_METRICS:
            rows[ds][(model, metric)] = extract_metric(r, metric)

    df = pd.DataFrame(rows).T.reindex(columns=cols)
    df.index.name = "Dataset"

    # 按数据集名称排序（按数字前缀）
    def ds_sort_key(name: str):
        import re
        m = re.search(r'(\d+)', name)
        return int(m.group(1)) if m else 999
    df = df.loc[sorted(df.index, key=ds_sort_key)]

    return df


def print_summary(df: pd.DataFrame, task: str):
    """终端打印汇总表"""
    if df.empty:
        return
    print(f"\n{'='*70}")
    print(f"  {task.upper()} 预测 Benchmark 汇总（MAE / RMSE）")
    print(f"{'='*70}")

    # 扁平化列名用于打印
    flat_df = df.copy()
    flat_df.columns = [f"{m}_{metric}" for m, metric in flat_df.columns]
    print(flat_df.to_string())
    print(f"{'='*70}")
    print(f"  N/A = 该数据集无 EOL 数据，RUL 标签不可靠")
    print(f"  ERR = 评估失败，检查对应 JSON 文件")


def main():
    parser = argparse.ArgumentParser(description="BatteryTwin 结果汇总")
    parser.add_argument("--results_dir", default="benchmarks/results",
                        help="结果 JSON 目录")
    parser.add_argument("--output", default="summary_table.csv",
                        help="输出汇总 CSV 路径（SOH）")
    parser.add_argument("--output_rul", default="summary_table_rul.csv",
                        help="RUL 汇总 CSV 路径")
    parser.add_argument("--tasks", nargs="+", default=["soh", "rul"],
                        choices=["soh", "rul"])
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"[ERROR] 结果目录不存在: {results_dir}")
        return

    results = load_result_files(results_dir)
    if not results:
        print("没有可汇总的结果，请先运行 evaluate.py")
        return

    output_map = {"soh": args.output, "rul": args.output_rul}

    for task in args.tasks:
        print(f"\n处理 {task.upper()} 结果...")
        df = build_summary_table(results, task)

        if df.empty:
            print(f"  跳过（无数据）")
            continue

        print_summary(df, task)

        out_path = Path(output_map[task])
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存（扁平化列名）
        flat_df = df.copy()
        flat_df.columns = [f"{m}_{metric}" for m, metric in flat_df.columns]
        flat_df.to_csv(out_path, encoding="utf-8-sig")
        print(f"\n✅ {task.upper()} 汇总表已保存: {out_path}")
        print(f"   数据集数: {len(df)}, 模型数: {len(df.columns.get_level_values(0).unique())}")

    print("\n全部完成！下一步可用此 CSV 生成论文/报告图表。")


if __name__ == "__main__":
    main()
