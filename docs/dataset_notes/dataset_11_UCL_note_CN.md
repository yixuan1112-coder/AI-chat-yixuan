

---

# UCL/Beihang Battery Dataset (Dataset 11) - 数据整理说明 (README)

## 1. 数据集概况

* **Dataset ID**: `dataset_11`
* **数据集归属与溯源**:
* **原始实验数据来源**: 伦敦大学学院 (UCL) 电化学创新实验室 (Electrochemical Innovation Lab)。负责了真实物理电池的充放电循环测试。
* **仿真数据与发布方**: 北京航空航天大学 (Beihang University) 成章 李。负责基于物理数据生成理论衰减模型，并打包发布。


* **电池规格**: LG INR18650-MJ1，圆柱形 18650 电池，额定容量 3.5Ah，标称电压 3.63V，充放电电压区间 4.2V - 2.5V。
* **材料体系**: NMC (正极: 高镍 NMC, 负极: Si-Graphite 硅碳负极)。
* **包含文件**:
1. `dataset_11_metadata.csv` (元数据表)
2. `dataset_11_cycle_summary.csv` (周期汇总表)
3. `dataset_11_timeseries.csv` (时间序列表)



## 2. 字段映射与物理量标准化

根据 `BatteryTwin Schema v0.2` 规范，对原始实测数据进行了以下标准化处理：

* **核心参数显式注入 (Metadata)**: 原始数据表头缺失电池本体信息。基于文献调研与 `EIL-MJ1` 的型号标志，在脚本中硬编码注入了 LG MJ1 的标准台架参数（如 `nominal_capacity_Ah` = 3.5, `chemistry` = NMC 等）。
* **时间单位对齐 (Timeseries)**: 原始测试仪器输出的时序时间单位为小时 (`Test Time (Hrs)`)，已在代码中乘以 3600 转换为标准秒 (`time_s`)。
* **健康状态 (SOH) 换算**: 使用放电容量 (`Discharge Capacity`) 作为核心 `capacity_Ah`。基于额定容量 3.5Ah，通过公式 `SOH = capacity_Ah / 3.5` 进行无量纲化处理。

## 3. 核心工程挑战与清洗逻辑记录

*注：本数据集的原始文件结构极其特殊，同一张 CSV 表格内混合了宏观汇总数据与微观时序数据，且存在罕见的横向数据平铺现象。*

1. **同表异构数据的切割分离**
在处理 `EIL-MJ1-015.csv` 等实测文件时，左侧前 3 列为按循环统计的宏观 Summary 数据，而右侧则是微观的 Timeseries 数据。ETL 流水线被设计为两套独立的脚本，分别截取左侧和右侧进行单独的结构化转换。
2. **时序数据的横向解构 (Unstacking & Melt)**
原始时序数据并未采取传统的纵向堆叠，而是将不同时段的 `Test Time`, `Cycle Number`, `Temp`, `Capacity` 粗暴地向右横向拼接，导致存在大量冗余列名和空值填充。脚本通过动态特征列探测技术，将横向铺开的 Block 逐一切割，随后执行垂直拼接 (Concat) 和去空值 (Dropna) 操作，成功将其重塑为标准的具有单调递增时间戳的长表 (Long Format)。
3. **消除 Pandas 空表广播 Bug**
在生成 `Cycle Summary` 的过程中，遭遇了 Pandas 为带有固定 columns 预设的空表赋值标量（如 `cell_id`）失效的底层缺陷。通过调整代码架构，采用“先填充定长数组（`cycle_id`）撑开 DataFrame 行维度，再填充标量”的策略，确保了所有输出结果完整无缺。

## 4. 仿真文件的隔离与基准声明 (Baseline Policy)

压缩包内附带了数个名为 `Simulation results...` 的 `.xlsx` 文件。

* **隔离策略**：为保证 BatteryTwin Benchmark Ground Truth 训练数据的绝对物理纯洁性，清洗脚本已加入白名单过滤机制，主动拦截并剔除了所有带有 Simulation 标记的文件。
* **未来用途**：这些模型推演数据已被保存在未标准化的副产品目录下，将作为评估平台后续数字孪生算法与 AI 预测性能的**基准对比组 (Baseline)**。

## 5. 缺失字段说明

* **RUL**: 未定义明确的寿命终止 (EOL) 阈值，剩余可用寿命 (`RUL`) 字段留空。
* **内阻 (Internal Resistance)**: 各循环周期未提供 DCR 或 EIS 测试所得的内阻数据。
* **充放电协议细节**: 数据本身缺乏具体的倍率 (C-rate) 记录，已在 Metadata 中标记为 `unknown`。