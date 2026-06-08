"""
data_split.py — BatteryTwin Benchmark · 数据划分脚本
=======================================================
用法:
    python data_split.py --data_root ../../data/processed --output split_config.json
    python data_split.py --data_root ../../data/processed --output split_config.json --stratify_by_temp
"""

import os
import re
import json
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


SPLIT_RATIO = (0.70, 0.15, 0.15)
SEED = 42
VERSION = "1.0.0"

MULTI_TEMP_DATASETS = {"dataset_eee", "xjtu", "dataset_05", "dataset_39"}


def get_cells_from_dataset(dataset_dir: Path) -> List[Dict]:
    """
    扫描数据集目录，识别所有 cell。
    支持两种结构：
      1. dataset_dir/cycle_summary/*.csv  （每个 cell 一个文件，文件名=cell_id）
      2. dataset_dir/cycle_summary*.csv   （单个汇总文件，内含 cell_id 列）
    """
    cells = []

    # 结构1：cycle_summary 是子目录
    cycle_dir = dataset_dir / "cycle_summary"
    if cycle_dir.exists() and cycle_dir.is_dir():
        for f in sorted(cycle_dir.glob("*.csv")):
            cell_id = f.stem
            # 从文件名提取温度，如 Ampace_2C_2C_25T_001 -> 25
            m = re.search(r"_(\d+)T", cell_id)
            temp = m.group(1) if m else None
            cells.append({"cell_id": cell_id, "temp": temp, "file": str(f)})
        return cells

    # 结构2：cycle_summary 是单个文件
    summary_files = list(dataset_dir.glob("*cycle_summary*.csv"))
    if summary_files:
        for sf in summary_files:
            try:
                df = pd.read_csv(sf)
                cell_col = _find_cell_column(df)
                if cell_col is None:
                    continue
                temp_col = _find_temp_column(df)
                for cell_id in df[cell_col].unique():
                    temp = None
                    if temp_col:
                        temps = df.loc[df[cell_col] == cell_id, temp_col].unique()
                        temp = str(int(temps[0])) if len(temps) == 1 else "mixed"
                    cells.append({"cell_id": str(cell_id), "temp": temp, "file": str(sf)})
            except Exception as e:
                print(f"  [WARN] 读取 {sf} 失败: {e}")
        return cells

    # 结构3：fallback，扫描 timeseries parquet
    ts_dir = dataset_dir / "timeseries"
    if ts_dir.exists():
        for f in sorted(ts_dir.glob("*.parquet")):
            cell_id = f.stem
            m = re.search(r"_(\d+)T", cell_id)
            temp = m.group(1) if m else None
            cells.append({"cell_id": cell_id, "temp": temp, "file": str(f)})

    return cells


def _find_cell_column(df: pd.DataFrame) -> Optional[str]:
    candidates = ["cell_id", "cell", "battery_id", "battery", "cell_name"]
    for c in candidates:
        if c in df.columns:
            return c
    for col in df.columns:
        if "cell" in col.lower() or "battery" in col.lower():
            return col
    return None


def _find_temp_column(df: pd.DataFrame) -> Optional[str]:
    candidates = ["temperature", "temp", "temp_c", "env_temp", "ambient_temp"]
    for c in candidates:
        if c in df.columns:
            return c
    for col in df.columns:
        if "temp" in col.lower():
            return col
    return None


def _extract_temp_from_name(name: str) -> Optional[str]:
    m = re.search(r'(\d+)[cCTt]', name)
    return m.group(1) if m else None


def split_cells(
    cells: List[Dict],
    ratio: Tuple[float, float, float] = SPLIT_RATIO,
    seed: int = SEED,
    stratify_by_temp: bool = False
) -> Dict[str, List[str]]:
    rng = np.random.default_rng(seed)
    train_ratio, val_ratio, _ = ratio
    result = {"train": [], "val": [], "test": []}

    if stratify_by_temp:
        temp_groups: Dict[str, List[str]] = {}
        for c in cells:
            t = c.get("temp") or "unknown"
            temp_groups.setdefault(t, []).append(c["cell_id"])

        print(f"  温度分组: { {t: len(v) for t, v in temp_groups.items()} }")

        for temp, cids in temp_groups.items():
            cids = sorted(cids)
            rng_t = np.random.default_rng(seed + abs(hash(temp)) % (2**31))
            rng_t.shuffle(cids)
            n = len(cids)
            n_train = max(1, int(n * train_ratio))
            n_val   = max(1, int(n * val_ratio))
            result["train"].extend(cids[:n_train])
            result["val"].extend(cids[n_train:n_train + n_val])
            result["test"].extend(cids[n_train + n_val:])
    else:
        cids = sorted([c["cell_id"] for c in cells])
        rng.shuffle(cids)
        n = len(cids)
        n_train = max(1, int(n * train_ratio))
        n_val   = max(1, int(n * val_ratio))
        result["train"] = list(cids[:n_train])
        result["val"]   = list(cids[n_train:n_train + n_val])
        result["test"]  = list(cids[n_train + n_val:])

    return result


def _compute_dir_hash(path: Path) -> str:
    files = sorted([f.name for f in path.rglob("*") if f.suffix in (".csv", ".parquet")])
    return hashlib.md5("\n".join(files).encode()).hexdigest()[:8]


def main():
    parser = argparse.ArgumentParser(description="BatteryTwin 数据划分脚本")
    parser.add_argument("--data_root", type=str, default="../../data/processed")
    parser.add_argument("--output", type=str, default="split_config.json")
    parser.add_argument("--stratify_by_temp", action="store_true")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    data_root = Path(args.data_root)
    if not data_root.exists():
        print(f"[ERROR] data_root 不存在: {data_root}")
        return

    config = {
        "version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "split_ratio": {"train": SPLIT_RATIO[0], "val": SPLIT_RATIO[1], "test": SPLIT_RATIO[2]},
        "stratify_by_temp": args.stratify_by_temp,
        "datasets": {}
    }

    dataset_dirs = sorted([d for d in data_root.iterdir() if d.is_dir() and not d.name.startswith(".")])

    if not dataset_dirs:
        print(f"[WARN] 在 {data_root} 下未找到任何数据集目录")
        return

    print(f"发现 {len(dataset_dirs)} 个数据集目录")

    for ds_dir in dataset_dirs:
        ds_name = ds_dir.name
        print(f"\n处理: {ds_name}")

        cells = get_cells_from_dataset(ds_dir)
        if not cells:
            print(f"  [SKIP] 未找到 cell 数据")
            continue

        is_multi_temp = args.stratify_by_temp and ds_name.lower() in MULTI_TEMP_DATASETS

        splits = split_cells(cells, ratio=SPLIT_RATIO, seed=args.seed, stratify_by_temp=is_multi_temp)

        n_train = len(splits["train"])
        n_val   = len(splits["val"])
        n_test  = len(splits["test"])
        total   = n_train + n_val + n_test

        print(f"  cells: {total} | train={n_train} val={n_val} test={n_test}")
        if is_multi_temp:
            print(f"  [分层划分] 按温度条件分层")

        config["datasets"][ds_name] = {
            "n_cells": total,
            "stratified_by_temp": is_multi_temp,
            "dir_hash": _compute_dir_hash(ds_dir),
            "splits": splits
        }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ split_config.json 已保存至: {out_path}")
    print(f"   数据集数量: {len(config['datasets'])}")
    print(f"   时间戳: {config['created_at']}")
    print("\n下一步: 运行 check_leakage.py 验证无时序泄漏后冻结配置")


if __name__ == "__main__":
    main()
