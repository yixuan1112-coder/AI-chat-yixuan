# BatteryTwin Benchmark 数据准备仓库

## 项目简介

本仓库用于 BatteryTwin benchmark 的数据准备阶段。目标是将多个公开电池数据集和一个内部实验数据集整理为统一的轻量级 schema，以支持后续的 benchmark 实验。

当前仓库的重点是 **数据集整理与标准化**，而不是模型训练。

---

## 仓库结构

```text
BatteryTwin-Benchmark-DataPrep/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── configs/
├── docs/
├── scripts/
├── notebooks/
├── reports/
└── tests/
```

原始数据存储在 `data/raw` 目录中。  
统一格式的数据存储在 `data/processed` 目录中。

---

## 数据组织原则

1. **原始数据不可修改**  
   所有原始文件必须保存在 `data/raw/` 中，不允许直接修改。

2. **处理后的数据单独存储**  
   统一 schema 后的数据存储在 `data/processed/`。

3. **数据处理必须可复现**  
   所有数据转换必须通过脚本完成，而不是手动修改。

4. **每个数据集必须包含四类文件**

- `metadata`
- `timeseries`
- `cycle_summary`
- schema 说明文档

---

## BatteryTwin Schema v0.2 核心字段

### 数据身份

- `dataset_id`
- `cell_id`
- `source_type`
- `split_tag`

### 电池本体信息

- `chemistry`
- `cathode_material`
- `anode_material`
- `brand_or_manufacturer`
- `model_or_size`
- `form_factor`
- `nominal_capacity_Ah`
- `nominal_voltage_V`

### 实验协议信息

- `temperature_C`
- `charge_protocol`
- `discharge_protocol`
- `C_rate`
- `cutoff_voltage_upper`
- `cutoff_voltage_lower`

### 时间序列信号

- `time_s`
- `voltage_V`
- `current_A`
- `temperature_C`

### 周期级标签

- `cycle_id`
- `capacity_Ah`
- `SOH`
- `RUL`

完整 schema 文档见：

`docs/schema/schema_overview.md`

---

## 快速开始

### 环境

建议使用 Python 3.10 及以上版本。

安装依赖：

```bash
pip install -r requirements.txt
```

或使用 conda：

```bash
conda env create -f environment.yml
```

---

## 常用脚本

运行数据处理流程：

```bash
python scripts/run_pipeline.py --dataset dataset_01
```

运行数据质量检查：

```bash
python scripts/qc/check_required_fields.py
python scripts/qc/check_units.py
python scripts/qc/check_time_axis.py
```

生成示例可视化：

```bash
python scripts/qc/plot_sample_cells.py
```

---

## 项目交付标准

当满足以下条件时，一个数据集被视为完成接入：

1. 原始数据被完整保存且未修改  
2. 已生成 `metadata` 文件  
3. 已生成统一格式的 `timeseries` 文件  
4. 已生成 `cycle_summary` 文件  
5. 提供 schema 说明文件  
6. 完成基本数据质量检查  
7. 可以通过统一 loader 正确读取  

---

## 注意事项

- 不要修改 `data/raw` 中的文件  
- 所有数据处理必须脚本化  
- 缺失字段必须记录说明  
- 尽量补充完整的电池元信息  
- 优先保证数据一致性

---

## 维护者

Supervisor  
Zhu Tianwen / Wang Hao

Capstone Students  
Liu Kefan  
Cao Han

---

## 文档说明

详细文档位于：

- `docs/schema/`：schema 定义与字段说明  
- `docs/dataset_notes/`：各数据集整理说明  
- `docs/qc_reports/`：数据质量检查报告  
- `docs/project_plan/`：项目计划与交付说明

学生操作手册:

- `docs/project_plan/student_git_guide.md`
- `docs/project_plan/student_git_guide_CN.md`
