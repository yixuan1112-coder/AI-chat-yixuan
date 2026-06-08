# BatteryTwin Benchmark — Part 1 分工说明

> v1.0 · 2026-04 · Kefan + Cao Han

---

## 分工总览

| 模块 | 负责人 | 文件 |
|------|--------|------|
| 数据划分 | **Kefan** | `benchmarks/data/data_split.py` |
| 泄漏检测 | **Kefan** | `benchmarks/data/check_leakage.py` |
| 数据接口契约 | **Kefan** | `benchmarks/data/dataset_interface.py` |
| 评估流水线 | **Kefan** | `benchmarks/evaluate/evaluate.py` |
| 结果汇总 | **Kefan** | `benchmarks/evaluate/aggregate_results.py` |
| 5类模型实现 | **Cao Han** | `benchmarks/models/*.py` |
| 统一训练入口 | **Cao Han** | `benchmarks/train.py` |
| 超参配置文件 | **Cao Han** | `benchmarks/configs/*.yaml` |

---

## 快速开始

### Step 1 — 数据划分（Kefan 完成后提交，Cao Han 直接用）

```bash
cd benchmarks/data

# 普通划分
python data_split.py --data_root ../../data --output split_config.json

# 对多温度数据集启用分层划分（XJTU / NTU EEE）
python data_split.py --data_root ../../data --output split_config.json --stratify_by_temp

# 验证无时序泄漏
python check_leakage.py --config split_config.json --data_root ../../data
```

### Step 2 — 模型训练（Cao Han 负责）

```bash
# 示例：训练 LSTM 做 SOH 预测
python benchmarks/train.py --model lstm --task soh --config benchmarks/configs/lstm_soh.yaml

# 模型需继承 dataset_interface.py 中的 BaseModel
# 使用 BatteryDataset / make_dataloader 加载数据（by split_config.json）
```

### Step 3 — 评估（任一人均可运行）

```bash
# 单次评估
python benchmarks/evaluate/evaluate.py \
    --model benchmarks/results/lstm_soh_best.pt \
    --dataset ../../data/dataset_02_CALCE \
    --task soh \
    --split_config benchmarks/data/split_config.json

# 多次运行取均值（推荐）
python benchmarks/evaluate/evaluate.py ... --n_runs 3

# 多温度分组（A2 实验）
python benchmarks/evaluate/evaluate.py ... --group_by_temp
```

### Step 4 — 汇总所有结果（集成阶段）

```bash
python benchmarks/evaluate/aggregate_results.py \
    --results_dir benchmarks/results/ \
    --output summary_table.csv \
    --output_rul summary_table_rul.csv
```

---

## 目录结构

```
benchmarks/
├── data/
│   ├── data_split.py          # Kefan
│   ├── check_leakage.py       # Kefan
│   ├── dataset_interface.py   # Kefan（接口契约）
│   └── split_config.json      # 自动生成，提交到 git
├── models/
│   ├── mlp.py                 # Cao Han
│   ├── cnn.py                 # Cao Han
│   ├── lstm.py                # Cao Han
│   ├── transformer.py         # Cao Han
│   └── pinn.py                # Cao Han
├── configs/
│   ├── cnn_soh.yaml           # Cao Han
│   ├── lstm_rul.yaml          # Cao Han
│   └── ...
├── evaluate/
│   ├── evaluate.py            # Kefan
│   └── aggregate_results.py   # Kefan
├── results/                   # 自动生成，存放 JSON 结果
│   └── *.json
└── train.py                   # Cao Han
```

---

## 接口约定（关键！）

Cao Han 的所有模型必须：

1. **继承 `BaseModel`**（来自 `benchmarks/data/dataset_interface.py`）
2. **实现 `predict(x: np.ndarray) -> np.ndarray`**，x shape = `[N, T, F]`
3. **保存为 `.pt` 或 `.pkl`**，路径放在 `benchmarks/results/`
4. 模型文件名包含模型类型，如 `lstm_soh_best.pt`、`cnn_rul_best.pt`

Kefan 的 `evaluate.py` 和 `aggregate_results.py` 会自动根据文件名识别模型类型。

---

## 环境依赖

```bash
conda activate batterytwin
pip install pandas numpy scikit-learn pyarrow
# 模型侧还需要: pip install torch
```
