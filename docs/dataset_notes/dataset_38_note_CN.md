# 数据集 38：ISU-ILCC 电池老化数据集（Thelen 2023）

## 概述
来自爱荷华州立大学（ISU）和爱荷华湖社区学院（ILCC）的电池老化数据集。
251 个 NMC/石墨锂聚合物电池在 63 种条件下循环老化，分两个版本发布。
研究三个应力因子对容量衰减的影响：充电倍率、放电倍率和放电深度（DoD）。

## 电池信息
- **化学体系**：NMC/石墨
- **电池形状**：软包（Pouch）
- **电芯尺寸**：50x20x3 mm（502030 规格）
- **标称容量**：250 mAh（0.25 Ah）
- **工作电压**：3.0–4.2 V
- **制造商**：深圳鸿浩盛电子
- **测试温度**：30°C

## 实验设计
- **Release 1.0**：238 个电池，63 种条件
- **Release 2.0**：13 个新增电池
- **应力因子**：充电倍率 / 放电倍率 / 放电深度
- **测试设备**：Neware BTS4000（64通道）

## 数据文件说明
| 文件 | 说明 |
|------|------|
| ISU_ILCC_timeseries.parquet | 5,505,000 行；每个循环的插值放电曲线 |
| ISU_ILCC_cycle_summary.csv | 5,455 行；每个电池的容量随时间衰减 |
| ISU_ILCC_metadata.csv | 251 个电池的化学体系、形状、尺寸信息 |
| ISU_ILCC_timeseries_SAMPLE.csv | 前 100 行，用于 GitHub 预览 |

## 参考文献
Thelen, A., Li, T., Liu, J., Tischer, C. & Hu, C. (2023).
ISU-ILCC Battery Aging Dataset. Iowa State University DataShare.
https://doi.org/10.25380/iastate.22582234.v2
