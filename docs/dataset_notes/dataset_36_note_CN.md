# 数据集 36：帝国理工学院 21700 循环老化数据集（Kirkaldy 2024）

## 概述
来自帝国理工学院的锂离子电池循环老化数据集。
使用商用 21700 圆柱电池（LG M50T / LG GBM50T2170）在受控条件下进行老化实验。
本次 ETL 处理 Experiment 2,2（碳基负极退化实验 2）作为代表性子集。

## 电池信息
- **化学体系**：NMC/石墨-SiO，21700 圆柱
- **标称容量**：5.0 Ah
- **电池数量**：6 个（A–F）
- **温度条件**：10°C（A、B）/ 25°C（C、D）/ 40°C（E、F）
- **SoC 范围**：0–100%
- **充放电倍率**：0.3C 充电 / 1C 放电

## 数据文件说明
| 文件 | 说明 |
|------|------|
| Imperial_21700_timeseries.parquet | 2,548,630 行；每次 RPT 的时间/电压/电流/电荷/温度 |
| Imperial_21700_cycle_summary.csv | 78 行；SoH、LAM、LLI、容量等退化指标 |
| Imperial_21700_metadata.csv | 6 个电池的温度和化学信息 |
| Imperial_21700_timeseries_SAMPLE.csv | 前 100 行，用于 GitHub 预览 |

## 主要列说明（时序数据）
- `cell_id`：电池编号，如 Imperial_Expt2_2_cell_A
- `cycle_id`：RPT 编号（0–12）
- `time_s`：时间（秒）
- `voltage_V`：电池电压（V）
- `current_mA`：电流（mA）
- `charge_mAh`：累计电荷量（mAh）
- `temperature_C`：实测温度（°C）
- `temperature_nominal_C`：标称测试温度（10/25/40）
- `step_type`：放电类型（discharge_0.1C）

## 参考文献
Kirkaldy, N., Samieian, M. A., Offer, G. J., Marinescu, M. & Patel, Y. (2024).
Lithium-ion battery degradation: Comprehensive cycle ageing data and analysis
for commercial 21700 cells. *Journal of Power Sources*, 603, 234185.
https://doi.org/10.1016/j.jpowsour.2024.234185
