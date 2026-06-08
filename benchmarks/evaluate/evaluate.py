"""
evaluate.py — BatteryTwin Benchmark · 统一评估脚本
====================================================
用法:
    # SOH 评估
    python evaluate.py --model results/best_model.pt \\
                       --dataset ../../data/dataset_02_CALCE \\
                       --task soh \\
                       --split_config benchmarks/data/split_config.json

    # RUL 评估（含 N/A 自动判断）
    python evaluate.py --model results/best_model.pt \\
                       --dataset ../../data/dataset_02_CALCE \\
                       --task rul \\
                       --split_config benchmarks/data/split_config.json

    # 多温度分组评估（A2 实验）
    python evaluate.py ... --task soh --group_by_temp

    # 多次运行（不同种子）
    python evaluate.py ... --n_runs 3

产出:
    results/{dataset}_{model}_{task}_{timestamp}.json
"""

import os
import json
import argparse
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────

EOL_THRESHOLD = 0.8          # SOH 降至此值视为寿命终止（可在 config 中覆盖）
MIN_EOL_CELLS_FOR_RUL = 1    # 至少需要 n 个 cell 达到 EOL 才能计算 RUL 指标


# ──────────────────────────────────────────────
# 评估指标计算
# ──────────────────────────────────────────────

def compute_metrics_soh(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """计算 SOH 预测指标"""
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true, y_pred = y_true[mask], y_pred[mask]

    if len(y_true) == 0:
        return {"mae": None, "rmse": None, "mape": None, "r2": None, "n_samples": 0}

    mae  = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    # MAPE（避免除零）
    nonzero = y_true != 0
    mape = float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100) \
           if nonzero.any() else None

    # R²
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else None

    return {
        "mae":      round(mae,  6),
        "rmse":     round(rmse, 6),
        "mape":     round(mape, 4) if mape is not None else None,
        "r2":       round(r2,   6) if r2   is not None else None,
        "n_samples": int(len(y_true))
    }


def compute_metrics_rul(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, Any]:
    """计算 RUL 预测指标（单位：cycles）"""
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true, y_pred = y_true[mask], y_pred[mask]

    if len(y_true) == 0:
        return {"mae": None, "rmse": None, "mape": None,
                "early_ratio": None, "late_ratio": None, "n_samples": 0}

    err  = y_pred - y_true
    mae  = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))

    nonzero = y_true != 0
    mape = float(np.mean(np.abs(err[nonzero] / y_true[nonzero])) * 100) \
           if nonzero.any() else None

    # Early/Late ratio（预测 < 真实 = early，预测 > 真实 = late）
    early_ratio = float(np.mean(y_pred < y_true))
    late_ratio  = float(np.mean(y_pred > y_true))

    return {
        "mae":         round(mae,  2),
        "rmse":        round(rmse, 2),
        "mape":        round(mape, 2) if mape is not None else None,
        "early_ratio": round(early_ratio, 4),
        "late_ratio":  round(late_ratio,  4),
        "n_samples":   int(len(y_true))
    }


# ──────────────────────────────────────────────
# N/A 判断逻辑
# ──────────────────────────────────────────────

def check_eol_reachable(
    cycle_summary: pd.DataFrame,
    test_cells: List[str],
    eol_threshold: float = EOL_THRESHOLD
) -> Tuple[bool, int]:
    """
    检测测试集中是否有 cell 达到 EOL。
    返回: (has_eol, n_eol_cells)
    """
    soh_col = _find_soh_column(cycle_summary)
    cell_col = _find_col(cycle_summary, ["cell_id", "cell", "battery_id"])

    if soh_col is None or cell_col is None:
        return False, 0

    test_df = cycle_summary[cycle_summary[cell_col].astype(str).isin(test_cells)]
    if test_df.empty:
        return False, 0

    n_eol = 0
    for _, cell_df in test_df.groupby(cell_col):
        if (cell_df[soh_col] <= eol_threshold).any():
            n_eol += 1

    return n_eol >= MIN_EOL_CELLS_FOR_RUL, n_eol


def _find_soh_column(df: pd.DataFrame) -> Optional[str]:
    candidates = ["soh", "SOH", "capacity_ratio", "normalized_capacity", "soh_normalized"]
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


# ──────────────────────────────────────────────
# 模型加载接口（供队友模型接入）
# ──────────────────────────────────────────────

def load_model(model_path: str):
    """
    加载模型，支持：
    - .pt 文件（PyTorch）
    - .pkl 文件（sklearn）
    - 目录（含 config.json + weights）
    队友需确保模型实现 predict(x: np.ndarray) -> np.ndarray 接口
    """
    import os
    path = Path(model_path)

    if not path.exists():
        raise FileNotFoundError(f"模型路径不存在: {model_path}")

    if path.suffix == ".pt":
        try:
            import torch
            model = torch.load(model_path, map_location="cpu")
            model.eval()
            return model
        except ImportError:
            raise ImportError("需要安装 PyTorch: pip install torch")

    elif path.suffix == ".pkl":
        import pickle
        with open(model_path, "rb") as f:
            return pickle.load(f)

    else:
        raise ValueError(f"不支持的模型格式: {path.suffix}（支持 .pt / .pkl）")


def run_inference(model, dataset_dir: Path, test_cells: List[str], task: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    对测试集 cell 进行推断。
    返回: (y_true, y_pred)
    队友模型需实现 predict(x) 接口。
    """
    # 尝试加载测试数据
    ts_dir = dataset_dir / "timeseries"
    if not ts_dir.exists():
        raise FileNotFoundError(f"timeseries 目录不存在: {ts_dir}")

    all_true, all_pred = [], []

    for cell_id in test_cells:
        parquet_files = list(ts_dir.glob(f"*{cell_id}*.parquet"))
        if not parquet_files:
            continue
        df = pd.read_parquet(parquet_files[0])

        # 提取特征和标签（根据任务）
        feature_cols = [c for c in df.columns if c in
                        ["voltage", "current", "temperature", "time",
                         "voltage_V", "current_A", "temp_C"]]
        if not feature_cols:
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        label_col = _find_soh_column(df) if task == "soh" else \
                    _find_col(df, ["rul", "RUL", "remaining_cycles"])

        if label_col is None or len(feature_cols) == 0:
            continue

        x = df[feature_cols].values.astype(float)
        y = df[label_col].values.astype(float)

        # 滑动窗口推断（对齐训练时的 BatteryDataset 切片逻辑）
        window_size = 50
        if len(x) < window_size:
            continue

        import torch
        preds = []
        for start in range(0, len(x) - window_size + 1):
            window = x[start: start + window_size]                          # [W, F]
            window_t = torch.tensor(window, dtype=torch.float32).unsqueeze(0)  # [1, W, F]
            with torch.no_grad():
                try:
                    pred = model(window_t).item()
                except Exception:
                    pred = float(model.predict(window[np.newaxis])[0])
            preds.append(pred)

        y_hat = np.array(preds)
        y = y[window_size - 1:]  # 截掉前 window_size-1 个标签，与预测对齐

        all_true.append(y)
        all_pred.append(y_hat)

    if not all_true:
        return np.array([]), np.array([])

    return np.concatenate(all_true), np.concatenate(all_pred)


# ──────────────────────────────────────────────
# 主评估流程
# ──────────────────────────────────────────────

def evaluate_single(
    model_path: str,
    dataset_dir: Path,
    task: str,
    split_config: Dict,
    ds_name: str,
    group_by_temp: bool = False,
    eol_threshold: float = EOL_THRESHOLD
) -> Dict:
    """核心评估函数，返回结果字典"""

    splits = split_config.get("datasets", {}).get(ds_name, {}).get("splits", {})
    test_cells = splits.get("test", [])

    if not test_cells:
        return {"status": "error", "message": f"split_config 中未找到 {ds_name} 的测试集"}

    result = {
        "dataset":    ds_name,
        "model_path": str(model_path),
        "task":       task,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "n_test_cells": len(test_cells),
        "eol_threshold": eol_threshold,
    }

    # RUL N/A 判断
    if task == "rul":
        summary_files = list(dataset_dir.glob("cycle_summary*.csv"))
        if summary_files:
            try:
                df_summary = pd.read_csv(summary_files[0])
                has_eol, n_eol = check_eol_reachable(df_summary, test_cells, eol_threshold)
                result["eol_cells_in_test"] = n_eol
                if not has_eol:
                    result["status"]  = "na"
                    result["message"] = f"测试集中无 cell 达到 EOL（阈值={eol_threshold}），RUL 标签不可靠，标注 N/A"
                    result["metrics"] = {"mae": "N/A", "rmse": "N/A", "mape": "N/A",
                                         "early_ratio": "N/A", "late_ratio": "N/A"}
                    return result
            except Exception as e:
                result["eol_check_warning"] = str(e)

    # 加载模型 & 推断
    try:
        model = load_model(model_path)
        y_true, y_pred = run_inference(model, dataset_dir, test_cells, task)
    except Exception as e:
        result["status"]  = "error"
        result["message"] = str(e)
        return result

    if len(y_true) == 0:
        result["status"]  = "error"
        result["message"] = "推断结果为空，检查数据路径和模型接口"
        return result

    # 计算指标
    if task == "soh":
        result["metrics"] = compute_metrics_soh(y_true, y_pred)
    else:
        result["metrics"] = compute_metrics_rul(y_true, y_pred)

    # 多温度分组评估
    if group_by_temp:
        result["metrics_by_temp"] = _evaluate_by_temp(
            model, dataset_dir, test_cells, task, split_config, ds_name
        )

    result["status"] = "ok"
    return result


def _evaluate_by_temp(model, dataset_dir, test_cells, task, split_config, ds_name):
    """按温度分组评估（用于 A2 实验）"""
    # 读取温度信息
    summary_files = list(dataset_dir.glob("cycle_summary*.csv"))
    if not summary_files:
        return {"warning": "未找到 cycle_summary，无法按温度分组"}

    df = pd.read_csv(summary_files[0])
    cell_col = _find_col(df, ["cell_id", "cell", "battery_id"])
    temp_col = _find_col(df, ["temperature", "temp", "temp_c", "env_temp"])

    if cell_col is None or temp_col is None:
        return {"warning": "未找到 cell 或温度列"}

    by_temp = {}
    for temp, group in df[df[cell_col].astype(str).isin(test_cells)].groupby(temp_col):
        cells = list(group[cell_col].astype(str).unique())
        try:
            yt, yp = run_inference(model, dataset_dir, cells, task)
            if task == "soh":
                by_temp[str(temp)] = compute_metrics_soh(yt, yp)
            else:
                by_temp[str(temp)] = compute_metrics_rul(yt, yp)
        except Exception as e:
            by_temp[str(temp)] = {"error": str(e)}

    return by_temp


# ──────────────────────────────────────────────
# 多次运行取均值
# ──────────────────────────────────────────────

def evaluate_with_multiple_runs(n_runs: int, seeds: List[int], **kwargs) -> Dict:
    """多次运行取均值 ± 标准差"""
    all_metrics = []

    for i, seed in enumerate(seeds[:n_runs]):
        np.random.seed(seed)
        result = evaluate_single(**kwargs)
        if result.get("status") == "ok":
            all_metrics.append(result["metrics"])

    if not all_metrics:
        return {"status": "error", "message": "所有运行均失败"}

    # 聚合
    aggregated = {}
    for key in all_metrics[0]:
        vals = [m[key] for m in all_metrics if m[key] is not None and m[key] != "N/A"]
        if vals:
            aggregated[key] = {
                "mean": round(float(np.mean(vals)), 6),
                "std":  round(float(np.std(vals)),  6)
            }
        else:
            aggregated[key] = {"mean": "N/A", "std": "N/A"}

    result = evaluate_single(**kwargs)
    result["metrics_aggregated"] = aggregated
    result["n_runs"] = n_runs
    return result


# ──────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BatteryTwin 统一评估脚本")
    parser.add_argument("--model",        required=True,  help="模型文件路径（.pt 或 .pkl）")
    parser.add_argument("--dataset",      required=True,  help="数据集目录路径")
    parser.add_argument("--task",         required=True,  choices=["soh", "rul"])
    parser.add_argument("--split_config", default="benchmarks/data/split_config.json")
    parser.add_argument("--output_dir",   default="benchmarks/results")
    parser.add_argument("--group_by_temp",action="store_true", help="按温度分组输出（A2 实验）")
    parser.add_argument("--n_runs",       type=int, default=1, help="重复运行次数（建议 3）")
    parser.add_argument("--eol_threshold",type=float, default=EOL_THRESHOLD)
    args = parser.parse_args()

    # 加载 split_config
    config_path = Path(args.split_config)
    if not config_path.exists():
        print(f"[ERROR] 找不到 split_config: {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        split_config = json.load(f)

    dataset_dir = Path(args.dataset)
    ds_name = dataset_dir.name

    print(f"评估: {ds_name} | task={args.task} | model={args.model}")

    seeds = [42, 123, 2025]
    if args.n_runs > 1:
        result = evaluate_with_multiple_runs(
            n_runs=args.n_runs,
            seeds=seeds,
            model_path=args.model,
            dataset_dir=dataset_dir,
            task=args.task,
            split_config=split_config,
            ds_name=ds_name,
            group_by_temp=args.group_by_temp,
            eol_threshold=args.eol_threshold
        )
    else:
        result = evaluate_single(
            model_path=args.model,
            dataset_dir=dataset_dir,
            task=args.task,
            split_config=split_config,
            ds_name=ds_name,
            group_by_temp=args.group_by_temp,
            eol_threshold=args.eol_threshold
        )

    # 保存结果
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_name = Path(args.model).stem
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"{ds_name}_{model_name}_{args.task}_{ts}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n结果已保存: {out_file}")

    # 打印摘要
    status = result.get("status", "unknown")
    if status == "na":
        print(f"⚪ RUL = N/A（{result.get('message', '')}）")
    elif status == "ok":
        metrics = result.get("metrics_aggregated", result.get("metrics", {}))
        print(f"✅ 评估完成:")
        for k, v in metrics.items():
            if k != "n_samples":
                print(f"   {k}: {v}")
    else:
        print(f"❌ 评估失败: {result.get('message', '')}")


if __name__ == "__main__":
    main()
