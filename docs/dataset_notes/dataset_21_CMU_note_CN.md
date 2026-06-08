
---

# CMU eVTOL Battery Dataset (Dataset 21) - 数据整理说明 (README)

## 1. 数据集概况

* **Dataset ID**: `dataset_21`
* **数据集归属与溯源**: 由卡内基梅隆大学 (Carnegie Mellon University) 的 Alexander Bills 等人提供。该数据集专门针对电动垂直起降飞行器 (eVTOL) 的高倍率脉冲工况设计。
* **电池规格**: Sony-Murata 18650 VTC-6 电芯，额定容量 3.0Ah，标称电压 3.6V。
* **材料体系**: NMC (正极: NMC, 负极: Graphite)。
* **包含文件**:
1. `dataset_21_metadata.csv` (元数据表)
2. `dataset_21_VAHxx_cycle_summary.csv` (周期汇总表，按电芯独立输出)
3. `dataset_21_VAHxx_timeseries.csv` (时间序列表，按电芯独立输出)

## 2. 字段映射与物理量标准化

根据 `BatteryTwin Schema v0.2` 规范，对原始数据进行了以下标准化处理：

* **物理单位换算**: 原始 CSV 数据采用毫安级单位。脚本在处理时执行了自动换算：电流从 `I_mA` 转换为 `current_A` (除以 1000)，容量从 `Q_mA_h` 转换为 `capacity_Ah` (除以 1000)。
* **内阻数据融合 (Impedance Fusion)**: 原始数据中内阻是独立存储在 `_impedance.csv` 文件中的。脚本利用 `cycleNumber` 作为关联键，将“60% SOC 下 1 秒测得的内阻”自动提取并填充至汇总表的 `internal_resistance_Ohm` 字段中。
* **实验协议动态提取**: 脚本通过正则表达式扫描 `README.txt` 文本，自动识别如 "Extended cruise" 或 "Baseline" 等文字描述，并将其注入 `metadata.csv` 的实验协议字段中，确保了工况信息的可追溯性。

## 3. 核心工程挑战与清洗逻辑记录

1. **多源异构数据的“1对1”解构**
不同于以往的单表数据集，CMU 数据集每个电池由一个时序文件和一个内阻文件组成。ETL 脚本采用了“文件对”识别逻辑，确保每个物理电芯产出一套标准的汇总和时序表，避免了超大数据集的内存溢出风险。
2. **容量基准的选择**
由于 eVTOL 工况包含复杂的脉冲放电，原始数据中的放电容量记录在某些极端循环下可能存在波动。脚本采用了“放电容量优先，充电容量备份”的逻辑，并基于 3.0Ah 的标称值统一计算 SOH。

## 4. 缺失字段说明

* **RUL**: 原始数据未定义 EOL 阈值，`RUL` 字段留空。
* **温度 (Metadata)**: 由于环境温度可能随循环协议变动，元数据表中的 `temperature_C` 标记为 `unknown`，具体温度记录保留在时序和汇总表的各循环采样点中。