
---

# EV Charging Dataset (Dataset 10) - 数据整理说明 (README)

## 1. 数据集概况

* **Dataset ID**: `dataset_10_EV`
* **原始数据规模**: 所有数据集中存放于一个高度扁平化的全局文件 `ev_battery_charging_data.csv` 中，包含多台不同型号电动汽车的充电循环数据。
* **车辆与电池规格**: 涵盖不同的电动车模型（如 Model A, Model B 等），具体电芯型号（Form factor / Model size）在原始数据中未标明 (`unknown`)。
* **材料体系**: 混合体系。根据原始字段 `Battery Type`，包含 `LiFePO4` (已在脚本中映射为标准 Schema 的 `LFP`) 以及泛指的 `Li-ion` (统一映射为 `unknown` 锂离子电池)。
* **包含文件**:
1. `dataset_10_EV_metadata.csv` (元数据表)
2. `dataset_10_EV_cycle_summary.csv` (周期汇总表)
3. `dataset_10_EV_timeseries.csv` (时间序列表)



## 2. 字段映射与物理量标准化

根据 `BatteryTwin Schema v0.2` 规范，对原始 EV 充电数据进行了以下标准化与估算处理：

* **唯一化标识 (Cell ID) 构造**: 由于原始数据并未直接提供电芯或电池包的唯一 ID，且数据高度混合，脚本采用 `{EV_Model}` 与 `{Battery_Type}` 拼接的方式生成伪唯一主键。例如：`ev_charging_ModelA_Liion`。
* **时间单位对齐**: 原始记录中的充电时长为分钟 (`Charging Duration (min)`)，已在 Timeseries 表中乘以 60，转换为标准秒 (`time_s`)。
* **容量 (Capacity) 估算**: 原始数据缺乏直接的容量测量值。基于安时积分物理逻辑，在脚本中通过公式 `Current (A) * (Charging Duration (min) / 60)` 估算出近似的 `charge_capacity_Ah`。在 Cycle Summary 中，该值被用作当前循环的 `capacity_Ah`。
* **健康状态 (SOH) 换算**: 原始数据提供了退化率 (`Degradation Rate (%)`)。为了与 Benchmark 标准无量纲 SOH 对齐，脚本采用了 `SOH = (100 - Degradation Rate) / 100` 的公式进行转换，保留 4 位小数。
* **化学体系对齐**: 严格遵守规范，将原始数据的 `LiFePO4` 转化为 `LFP`，其余笼统的 `Li-ion` 填入 `unknown`，原名保留在 `cathode_material` 字段中以防信息丢失。

## 3. 核心工程挑战与清洗逻辑记录

*注：与处理包含复杂多层嵌套结构体的 XJTU `.mat` 文件 或需要通过正则表达式解析文件名的 SNL 数据集不同，本数据集的 ETL 核心挑战在于“扁平化数据的逆向关系解耦”。*

1. **扁平表特征的聚合与剥离 (Metadata Extraction)**
原始数据是所有时间序列和本体属性的混合大表。为了生成符合规范的 `metadata.csv`，脚本摒弃了传统的逐文件读取模式，转而利用 Pandas 的 `groupby('cell_id')` 并结合 `agg('first')` 方法，从数万行时序数据中逆向抽取出每个电池实体的固有物理信息（如环境温度均值、车辆模型等），实现了数据的降维归一化。
2. **防重复与主键冲突处理 (Cycle Summary Aggregation)**
在提取 `cycle_summary.csv` 时，考虑到同一个 `Charging Cycles` 可能因采样或异常原因存在多条记录，直接提取可能导致主键重复。脚本采取了先 `groupby(['cell_id', 'Charging Cycles'])` 再进行 `mean` 和 `sum` 聚合的安全策略，确保最终输出的每个 `cycle_id` 在全局都是唯一且单调递增的。

## 4. 缺失字段说明

受限于本批次 EV 充电场景原始数据的采集维度，部分 Schema 字段无法获取，已作留空 (`NaN`) 或填入 `unknown` 处理：

* **放电相关字段 (全表)**: 本数据集仅记录充电 (Charging) 阶段特征。因此，Timeseries 和 Cycle Summary 中的所有放电相关指标（如 `discharge_capacity_Ah`, `discharge_duration_s`, `discharge_protocol`）均为空。
* **本体物理参数 (Metadata)**: 诸如额定容量 (`nominal_capacity_Ah`)、额定电压 (`nominal_voltage_V`)、截止电压、外形 (`form_factor`) 等电池静态台架参数在原始数据中完全缺失。
* **高级健康指标 (Cycle Summary)**: 数据未提供每个循环的内阻 (`internal_resistance_Ohm`)；同时，由于未定义明确的寿命终止 (EOL) 阈值，剩余可用寿命 (`RUL`) 字段留空。