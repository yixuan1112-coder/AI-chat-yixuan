# VITO Calendar Ageing Dataset (Dataset 22) - 数据整理说明 (README)

## 1. 数据集概况

* **Dataset ID**: `dataset_22`
* **数据集归属与溯源**: 由比利时 VITO/EnergyVille 实验室提供，属于 H2020 欧洲项目 Everlasting 的一部分。测试设备采用 PEC battery tester。
* **电池规格**: 商业 18650 圆柱形电池。
* **材料体系**: 正极为富镍材料 (Ni-rich)，负极为硅碳材料 (Si/Gr)。
* **实验协议**: 本数据集为日历老化 (Calendar Ageing) 实验。电池被储存在不同的恒温环境 (25°C 和 45°C) 和固定的 SOC 状态下 (10%, 70%, 90%) 进行老化。老化过程会定期中断，以运行参考性能测试 (Reference Performance Test) 来记录容量衰减。

## 2. 字段映射与工程逻辑

根据 `BatteryTwin Schema v0.2` 规范，进行了以下处理：
* **动态属性探测**: 由于原始 CSV 表头存在命名波动，ETL 脚本内部集成了 `find_col` 模糊匹配函数，自动捕获具有 `cycle`, `time`, `voltage`, `capacity` 等特征的列。
* **SOH 估算算法**: 在 Cycle Summary 的计算中，由于 ReadMe 文本未显式提供该商业电芯的准确额定容量 (Nominal Capacity)，脚本采用 **“基于首圈可用容量为基准”** 的算法动态估算后续循环的 SOH (即 `SOH_i = Capacity_i / Capacity_initial`)。

## 3. 缺失字段说明
* `nominal_capacity_Ah` (Metadata): 原文未提供具体标称安时数，暂且留空。
* `chemistry` (Metadata): 尽管指明了 Ni-rich，但未具体界定是 NMC 还是 NCA，故标记为 `unknown`（将具体材料保留在正负极字段中）。