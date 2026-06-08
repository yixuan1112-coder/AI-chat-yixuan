
---

# HNEI Battery Dataset - 数据整理说明 (README)

## 1. 数据集概况

* **Dataset ID**: `dataset_07`
* **原始数据规模**: 包含 15 个以上的原始测试文件（如 HNEI_18650_NMC_LCO_25C_a...t）。
* **电池规格**: 18650 圆柱形电池。
* **材料体系**: NMC/LCO 混合正极。
* **包含文件**:
    1. `dataset_07_{cell_id}_metadata.csv`
    2. `dataset_07_{cell_id}_cycle_summary.csv` (14 列标准格式)
    3. `dataset_07_{cell_id}_timeseries.csv` (9 列标准格式)

## 2. 字段映射与物理量标准化

本数据集严格遵循 `BatteryTwin Schema v0.2` 进行标准化映射：

### 周期汇总表 (Cycle Summary)
| Schema 字段 | 原始字段映射 | 处理说明 |
| :--- | :--- | :--- |
| `cell_id` | 文件名剔除后缀 | `{dataset_id}_{Original_Filename}` |
| `cycle_id` | `Cycle_Index` | 转换为 `int32` |
| `capacity_Ah` | `Discharge_Capacity (Ah)` | 核心退化指标，单位 Ah |
| `temperature_max_C` | `Cell_Temperature (C)` | 从时序数据聚合计算的最大值 |
| `charge_duration_s` | `Test_Time` | 基于电流正负判定计算的累计充电秒数 |

### 时间序列表 (Timeseries)
* **单位一致性**: 原始数据已是标准单位（V, A, s, Ah, °C），未进行额外数学转换。
* **数值强制转换**: 针对原始 CSV 中可能存在的非数字字符，在读取时统一通过 `pd.to_numeric` 强制转换为浮点数，解决了 `str` 减法报错问题。

## 3. 核心工程挑战与清洗逻辑记录

### 1. 跨表特征融合提取
不同于仅读取汇总表，本处理流程实现了 **Timeseries 驱动填充** 逻辑。通过对数百万行时序数据进行 `groupby` 聚合，计算出每个循环的真实温升（`temperature_max_C`）和精准的充放电持续时间（`duration_s`），解决了汇总表原始数据缺失关键特征的问题。

### 2. 冗余异常值过滤规则
针对电池失效后（EOL）产生的大量连续 0 容量记录，脚本引入了 `KEEP_ZERO_N = 3` 规则：
* 保留孤立的 0 容量循环（识别状态跳变信号）。
* 对于连续出现的 0 容量循环，仅保留前 3 条以锚定失效边界，剔除后续成百上千条冗余死数据，从而提升下游 LightGBM 模型的训练效率。

### 3. 严格的 Schema 占位对齐
为确保全数据集（HNEI, UL, SNL）合并时的兼容性，脚本强制输出了 Schema 定义的所有字段（周期表 14 列，时序表 9 列）。对于 HNEI 原始数据中未包含的 `SOH`、`RUL`、`internal_resistance_Ohm` 等字段，统一进行 NaN 补全处理。

### 4. 异常原始数据处理
原始数据的timeseries.csv中的HNEI_18650_NMC_LCO_25C_0-100_0.5-1.5C_m_timeseries.csv只有1kb大小（cycle_data有数据），文件里除原始数据的标准列不含任何数据，但依然按正常处理并生成对应时序表，保证时序文件所对应的处理的时序表与循环表的完整性。
