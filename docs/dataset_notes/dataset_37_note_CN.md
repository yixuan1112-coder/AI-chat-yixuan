# 数据集 37：慕尼黑应用科技大学多阶段老化数据集（Stroebl 2024）

## 概述
来自慕尼黑应用科技大学的多阶段锂离子电池老化数据集。
279 个 Samsung INR21700-50E 电池在 71 种老化条件下进行实验。
本次 ETL 处理代表性子集：3 个日历老化（TP_k）+ 3 个循环老化（TP_z）文件。

## 电池信息
- **化学体系**：NMC/石墨，Samsung INR21700-50E
- **电池形状**：圆柱形
- **电芯尺寸**：21x70 mm
- **标称容量**：4.9 Ah
- **最大充电电流**：1C（4.9A）
- **最大放电电流**：2C（9.8A）

## 实验设计
- **第一阶段**：非模型驱动实验设计（全因子 + 拉丁超立方）
- **第二阶段**：基于模型的最优实验设计（pi-OED）
- **老化类型**：日历老化（TP_k）+ 循环老化（TP_z）
- **实验室**：Siemens、Intilion、慕尼黑应用科技大学

## 数据文件说明
| 文件 | 说明 |
|------|------|
| Munich_multistage_timeseries.parquet | 16,039,771 行；每步的电压/电流/温度 |
| Munich_multistage_cycle_summary.csv | 12 行；每个电池的老化条件 |
| Munich_multistage_metadata.csv | 12 个电池的完整实验元数据 |
| Munich_multistage_timeseries_SAMPLE.csv | 前 100 行，用于 GitHub 预览 |

## 参考文献
Stroebl, F., Petersohn, R., Schricker, B., et al. (2024).
A multi-stage lithium-ion battery aging dataset using various experimental
design methodologies. *Scientific Data*, 11, 1020.
https://doi.org/10.1038/s41597-024-03859-z
