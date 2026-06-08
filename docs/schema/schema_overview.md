# BatteryTwin Schema v0.2 — 完整字段定义

> 本文档是 BatteryTwin Benchmark 数据准备阶段的 **权威字段定义**。所有数据集整理产出必须遵循此 schema。

---

## 1. 四类产出文件

| 序号 | 文件 | 命名规则 | 格式 | 说明 |
|------|------|----------|------|------|
| 1 | Metadata | `{DatasetName}_metadata.csv` | CSV | 每个 cell 一行，电池本体信息 + 实验协议 |
| 2 | Timeseries | `{DatasetName}_timeseries.parquet` (主) + `.csv` (备) | Parquet + CSV | 按秒记录的原始时序信号 |
| 3 | Cycle Summary | `{DatasetName}_cycle_summary.csv` | CSV | 每个 cycle 一行的汇总统计 |
| 4 | Dataset Note | `dataset_{XX}_note.md` | Markdown | 字段映射、缺失说明、处理备注 |

---

## 2. Metadata 字段定义

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `dataset_id` | str | ✅ | 数据集编号 | `dataset_01` |
| `cell_id` | str | ✅ | 电池编号，全局唯一 | `NASA_B0005` |
| `source_type` | str | ✅ | 数据来源类型 | `public` / `internal` |
| `split_tag` | str | ❌ | 训练/测试分组标签，可先留空 | `train` / `test` / `` |
| `chemistry` | str | ✅ | 化学体系 | `LCO` / `NMC` / `LFP` / `NCA` |
| `cathode_material` | str | ✅ | 正极材料 | `LiCoO2` / `LiNiMnCoO2` / `LiFePO4` |
| `anode_material` | str | ✅ | 负极材料 | `Graphite` / `Li metal` / `Si-C` |
| `brand_or_manufacturer` | str | ❌ | 品牌或制造商 | `Samsung` / `LG` / `unknown` |
| `model_or_size` | str | ❌ | 型号或尺寸规格 | `18650` / `INR21700-50E` |
| `form_factor` | str | ✅ | 外形 | `cylindrical` / `pouch` / `prismatic` / `coin` |
| `nominal_capacity_Ah` | float | ✅ | 额定容量 (Ah) | `2.0` |
| `nominal_voltage_V` | float | ❌ | 额定电压 (V) | `3.7` |
| `temperature_C` | float/str | ✅ | 测试温度 (°C) | `24` / `25` / `room_temp` |
| `charge_protocol` | str | ✅ | 充电协议描述 | `CC-CV 1.5A to 4.2V, 20mA cutoff` |
| `discharge_protocol` | str | ✅ | 放电协议描述 | `CC 2A to 2.7V` |
| `C_rate` | str | ❌ | 放电倍率 | `1C` / `2C` / `0.5C` |
| `cutoff_voltage_upper` | float | ❌ | 充电截止电压 (V) | `4.2` |
| `cutoff_voltage_lower` | float | ❌ | 放电截止电压 (V) | `2.7` |

**规则：**
- `cell_id` 建议使用 `{数据集缩写}_{原始编号}` 格式，确保全局唯一
- 若某字段在原始数据中不可获取，填写 `unknown` 或留空，并在 Dataset Note 中说明
- `temperature_C`：若原始数据是范围，取代表性值或填范围字符串如 `"24-43"`

---

## 3. Timeseries 字段定义

| 字段名 | 类型 | 必填 | 单位 | 说明 |
|--------|------|------|------|------|
| `cell_id` | str | ✅ | — | 对应 metadata 中的 cell_id |
| `cycle_id` | int | ✅ | — | 循环编号，从 1 开始 |
| `time_s` | float | ✅ | 秒 (s) | 时间戳，每个 cycle 内从 0 开始或全局累积 |
| `voltage_V` | float | ✅ | 伏特 (V) | 电压 |
| `current_A` | float | ✅ | 安培 (A) | 电流（充电为正，放电为负；或按原始数据约定，在 note 中说明） |
| `temperature_C` | float | ✅ | 摄氏度 (°C) | 温度（若无传感器数据，可用 metadata 中的环境温度填充） |
| `charge_capacity_Ah` | float | ❌ | Ah | 累积充电容量 |
| `discharge_capacity_Ah` | float | ❌ | Ah | 累积放电容量 |
| `step_type` | str | ❌ | — | 步骤类型：`charge` / `discharge` / `rest` |

**规则：**
- 主格式为 **Parquet**（节省空间），同时输出一份 CSV 供检查
- 时间分辨率保持原始采样率，不做重采样（除非特殊说明）
- 电流符号约定：在 note 中说明正值代表充电还是放电
- 若原始数据中无 `temperature_C` 列，用 metadata 中的 `temperature_C` 常数填充

---

## 4. Cycle Summary 字段定义

| 字段名 | 类型 | 必填 | 单位 | 说明 |
|--------|------|------|------|------|
| `cell_id` | str | ✅ | — | 对应 metadata 中的 cell_id |
| `cycle_id` | int | ✅ | — | 循环编号 |
| `capacity_Ah` | float | ✅ | Ah | 当前 cycle 的放电容量（主要退化指标） |
| `SOH` | float | ❌ | — | State of Health = capacity / nominal_capacity |
| `RUL` | int | ❌ | cycles | Remaining Useful Life（若已知 EOL） |
| `charge_capacity_Ah` | float | ❌ | Ah | 充电容量 |
| `discharge_capacity_Ah` | float | ❌ | Ah | 放电容量 |
| `temperature_max_C` | float | ❌ | °C | cycle 内最高温度 |
| `temperature_avg_C` | float | ❌ | °C | cycle 内平均温度 |
| `charge_duration_s` | float | ❌ | s | 充电持续时间 |
| `discharge_duration_s` | float | ❌ | s | 放电持续时间 |
| `internal_resistance_Ohm` | float | ❌ | Ω | 内阻（若可获取） |
| `cycle_end_flag` | str | ❌ | — | `normal` / `EOL` / `anomaly` |

**规则：**
- `capacity_Ah` 是核心字段，优先使用放电容量
- `SOH` = discharge_capacity_Ah / nominal_capacity_Ah × 100%（百分比或小数，在 note 中说明）
- `RUL` 需要知道 EOL 定义才能计算，若不确定则留空
- `cycle_end_flag`：`EOL` 表示该 cycle 后电池达到寿命终止标准

---

## 5. Dataset Note 要求

每个数据集的 note 文档需包含：

1. **Basic Information**：数据集 ID、名称、负责人、状态
2. **Source Information**：数据来源、下载链接、许可证
3. **Dataset Summary**：电池数量、化学体系、数据范围
4. **Raw File Inventory**：原始文件清单
5. **Field Mapping**：原始字段 → schema 字段的映射表
6. **Available Core Fields**：哪些字段可用的 checklist
7. **Unit Normalization**：单位转换规则
8. **Missing Fields and Gaps**：缺失字段及影响
9. **Quality Control Notes**：QC 检查结果
10. **Known Issues**：已知问题
11. **Processing Notes**：处理方法说明
12. **Handover Checklist**：交付检查清单

模板文件：`docs/dataset_notes/dataset_note_template.md`

---

## 6. 命名约定

| 项目 | 规则 | 示例 |
|------|------|------|
| 数据集目录 | `data/processed/dataset_{XX}/` | `data/processed/dataset_01/` |
| Metadata 文件 | `{DatasetName}_metadata.csv` | `NASA_PCoE_metadata.csv` |
| Timeseries 文件 | `{DatasetName}_timeseries.parquet` | `NASA_PCoE_timeseries.parquet` |
| Cycle Summary | `{DatasetName}_cycle_summary.csv` | `NASA_PCoE_cycle_summary.csv` |
| Dataset Note | `dataset_{XX}_{DatasetName}_note.md` | `dataset_01_NASA_PCoE_note.md` |
| ETL 脚本 | `scripts/etl_{dataset_name}.py` | `scripts/etl_nasa.py` |

---

## 7. 数据质量标准

### 必检项
- [ ] 所有必填字段存在且非空
- [ ] 单位正确（V, A, °C, s, Ah）
- [ ] `cell_id` 在 metadata 和 timeseries/cycle_summary 之间一致
- [ ] `cycle_id` 连续且无重复
- [ ] 时间轴单调递增
- [ ] 容量值在合理范围内（0 < capacity < 2 × nominal_capacity）

### 推荐检查
- [ ] 抽样 3-5 个 cell 画容量衰减曲线
- [ ] 抽样画电压 profile
- [ ] 检查温度分布是否合理
- [ ] 检查是否有异常 cycle（容量突变、时间异常等）

---

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v0.1 | 2026-02 | 初始 schema 定义 |
| v0.2 | 2026-03 | 增加电池本体信息字段、明确命名规则 |
