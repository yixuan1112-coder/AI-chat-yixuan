
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple  # 显式导入，防止 NameError[cite: 3]

import numpy as np
import pandas as pd


class BatteryDataset:
    def __init__(
        self,
        dataset_dir: str,
        split_config_path: str,
        split: str,
        task: str,
        window_size: int = 50,
        eol_threshold: float = 0.8,
        feature_cols: Optional[List[str]] = None,
    ):
        import json
        self.dataset_dir    = Path(dataset_dir)
        self.split          = split
        self.task           = task
        self.window_size    = window_size
        self.eol_threshold  = eol_threshold
        self.feature_cols   = feature_cols or ["voltage", "current", "temperature", "time"]

        ds_name = self.dataset_dir.name

        with open(split_config_path, "r") as f:
            config = json.load(f)

        self.cell_ids: List[str] = (
            config.get("datasets", {})
                  .get(ds_name, {})
                  .get("splits", {})
                  .get(split, [])
        )

        if not self.cell_ids:
            raise ValueError(f"split_config 中找不到数据集 {ds_name} 的 {split} 划分")

        self._samples = self._load_samples()

    def _load_samples(self) -> List[Tuple[np.ndarray, float, Dict]]:
        """加载样本：执行模糊搜索、初始容量锚定与特征标准化"""
        samples = []
        # 1. 递归扫描目录下所有 csv 和 parquet 文件
        all_files = list(self.dataset_dir.rglob("*.csv")) + list(self.dataset_dir.rglob("*.parquet"))
        ts_files = [f for f in all_files if "timeseries" in f.name.lower()]
        
        print(f"\n--- [BatteryTwin 数据加载诊断] ---")
        print(f"1. 硬盘扫描: 发现 {len(ts_files)} 个时序数据文件")
        print(f"2. 计划加载: 正在匹配 JSON 配置中的 {len(self.cell_ids)} 颗电池")

        for cell_id in self.cell_ids:
            # 🚀 模糊匹配策略：忽略大小写，且支持后缀容错
            match = [f for f in ts_files if cell_id.lower() in f.name.lower()]
            if not match and "_" in cell_id:
                base_id = "_".join(cell_id.split("_")[:-1])
                match = [f for f in ts_files if base_id.lower() in f.name.lower()]

            if not match:
                continue

            file_path = match[0]
            try:
                df = pd.read_csv(file_path) if file_path.suffix == '.csv' else pd.read_parquet(file_path)
                df = self._align_feature_cols(df)
                label_col = self._find_label_col(df)
                
                if label_col is None:
                    continue

                # 🚀 物理严谨性：使用该电池生命周期内的最大容量作为 SOH 分母
                # 避开时序开头的 0.0，同时适应不同型号电池的容量差异
                initial_cap = df[label_col].max()
                if initial_cap <= 0 or np.isnan(initial_cap):
                    continue

                # --- 特征标准化映射 (Normalization) ---
                df_proc = df.copy()
                df_proc['voltage'] = (df_proc['voltage'] - 3.7) / 0.5      # 3.7V为中性参考
                df_proc['current'] = df_proc['current'] / 2.0             # 缩放电流
                df_proc['temperature'] = (df_proc['temperature'] - 25) / 15 # 25°C环境基准
                df_proc['time'] = df_proc['time'] / 3600.0                # 秒转小时

                # --- Numpy 矩阵化切片加速 ---
                feature_vals = df_proc[self.feature_cols].values.astype(float)
                label_vals = df_proc[label_col].values.astype(float)
                
                n = len(feature_vals)
                if n < self.window_size:
                    continue

                step = self.window_size // 2
                for i in range(0, n - self.window_size, step):
                    x = feature_vals[i:i + self.window_size]
                    
                    # 归一化 SOH 标签，并确保数值安全地落在 [0, 1] 区间
                    raw_soh = label_vals[i + self.window_size - 1] / initial_cap
                    y = float(np.clip(raw_soh, 0.0, 1.0))

                    if np.isfinite(x).all():
                        samples.append((x, y, {"cell_id": cell_id, "window_start": i}))

            except Exception as e:
                print(f"处理 {cell_id} 时发生异常: {e}")
                continue

        print(f"--- [诊断结束] 成功构建样本总数: {len(samples)} ---")
        return samples

    def _align_feature_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """统一不同数据集的列名映射"""
        rename_map = {
            "voltage_V": "voltage", "current_A": "current",
            "temperature_C": "temperature", "temp_C": "temperature", "time_s": "time"
        }
        return df.rename(columns=rename_map)

    def _find_label_col(self, df: pd.DataFrame) -> Optional[str]:
        """根据任务查找对应的标签列[cite: 3]"""
        if self.task == "soh":
            candidates = ["soh", "SOH", "capacity_ratio", "normalized_capacity", "discharge_capacity_Ah", "charge_capacity_Ah"]
        else:
            candidates = ["rul", "RUL", "remaining_cycles", "discharge_capacity_Ah"]
        for c in candidates:
            if c in df.columns: return c
        return None

    def _extract_temp(self, df: pd.DataFrame, idx: int) -> Optional[str]:
        for col in ["temperature", "env_temp", "temp_C", "temperature_C"]:
            if col in df.columns: return str(int(df[col].iloc[idx]))
        return None

    def __len__(self): return len(self._samples)
    def __getitem__(self, idx): return self._samples[idx]
    def __iter__(self): return iter(self._samples)

    def to_numpy(self) -> Tuple[np.ndarray, np.ndarray]:
        X = np.stack([s[0] for s in self._samples])
        y = np.array([s[1] for s in self._samples])
        return X, y


class BaseModel(ABC):
    @abstractmethod
    def fit(self, train_loader, val_loader, config: Dict) -> None: ...
    @abstractmethod
    def predict(self, x: np.ndarray) -> np.ndarray: ...
    @abstractmethod
    def save(self, path: str) -> None: ...
    @abstractmethod
    def load(self, path: str) -> None: ...


# DataLoader 工厂

def make_dataloader(dataset_dir, split_config_path, split, task, batch_size=64, window_size=50, shuffle=True):
    try:
        import torch
        from torch.utils.data import DataLoader, Dataset as TorchDataset

        class _TorchWrapper(TorchDataset):
            def __init__(self, battery_ds): self.ds = battery_ds
            def __len__(self): return len(self.ds)
            def __getitem__(self, idx):
                x, y, _ = self.ds[idx]
                return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

        ds = BatteryDataset(dataset_dir, split_config_path, split, task, window_size)
        return DataLoader(_TorchWrapper(ds), batch_size=batch_size, shuffle=shuffle)
    except ImportError:
        raise ImportError("PyTorch 环境缺失，请先安装。")

if __name__ == "__main__":
    print("dataset_interface.py - 终极严谨版已就绪。")