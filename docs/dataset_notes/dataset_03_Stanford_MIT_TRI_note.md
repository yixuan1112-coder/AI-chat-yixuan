# Dataset 03: Stanford-MIT-TRI 数据集说明

## 基本信息

| 项目 | 内容 |
|------|------|
| 数据集名称 | Stanford-MIT-TRI Battery Cycle Life Dataset |
| 发布机构 | Stanford University / MIT / Toyota Research Institute |
| 发表论文 | Severson et al. (2019) "Data-driven prediction of battery cycle life before capacity degradation", *Nature Energy* |
| DOI | https://doi.org/10.1038/s41560-019-0356-8 |
| 数据来源 | https://data.matr.io/1/ |
| 许可证 | CC BY 4.0 |

## 电池规格

| 项目 | 内容 |
|------|------|
| 电池化学 | LFP/Graphite (磷酸铁锂/石墨) |
| 电池型号 | A123 Systems APR18650M1A |
| 形状 | 18650 圆柱 |
| 标称容量 | 1.1 Ah |
| 标称电压 | 3.3 V |
| 电压范围 | 2.0–3.6 V |
| 测试温度 | 30°C（恒温箱） |

## 实验设计

本数据集的核心目标是研究**快充协议对电池寿命的影响**。实验采用 72 种不同的快充（CC-CV）协议，对 124 颗商用 LFP 电池进行循环老化测试直至失效（容量衰减至 80% SOH）。

### 三个 Batch

| Batch | 文件名 | 日期 | 电池数 | 说明 |
|-------|--------|------|--------|------|
| Batch 1 | 2017-05-12_batchdata_updated_struct_errorcorrect.mat | 2017-05-12 | 46 | 初始实验 |
| Batch 2 | 2017-06-30_batchdata_updated_struct_errorcorrect.mat | 2017-06-30 | 48 | 扩展实验 |
| Batch 3 | 2018-04-12_batchdata_updated_struct_errorcorrect.mat | 2018-04-12 | 40 | 闭环优化实验 (Attia et al. 2020) |

### 充电协议格式

充电协议以 `X1C(Y%)-X2C` 格式表示：
- `X1C`：第一阶段恒流充电倍率
- `Y%`：切换到第二阶段的 SOC 阈值
- `X2C`：第二阶段恒流充电倍率
- 所有电池以 4C 放电

示例：`3.6C(80%)-3.6C` 表示以 3.6C 充电至 80% SOC，然后以 3.6C 继续充电。

## 数据结构

### Summary（每 cycle 一行）

| 字段 | 说明 | 单位 |
|------|------|------|
| cycle | 循环编号 | - |
| QCharge | 充电容量 | Ah |
| QDischarge | 放电容量 | Ah |
| IR | 内阻 | Ω |
| Tavg | 平均温度 | °C |
| Tmax | 最高温度 | °C |
| Tmin | 最低温度 | °C |
| chargetime | 充电时间 | min |

### Cycles（每 cycle 内的时序数据）

| 字段 | 说明 | 单位 |
|------|------|------|
| t | 时间 | s |
| V | 电压 | V |
| I | 电流 | A |
| T | 温度 | °C |
| Qc | 充电容量 | Ah |
| Qd | 放电容量 | Ah |
| Qdlin | 线性插值放电容量 | Ah |
| Tdlin | 线性插值温度 | °C |
| discharge_dQdV | 放电 dQ/dV | Ah/V |

## ETL 处理说明

### 原始格式
MATLAB v7.3 格式（底层 HDF5），需要使用 `h5py` 库读取，`scipy.io.loadmat` 无法直接处理。

### 处理逻辑
1. 依次读取 3 个 batch 文件
2. 提取每颗电池的 metadata（cycle_life、charging_policy、barcode、channel_id）
3. 提取 summary 层数据 → cycle_summary.csv
4. 提取 cycles 层时序数据 → 每颗电池单独保存为 parquet
5. 合并所有电池时序数据 → 统一 parquet 文件
6. Cycle 0 为占位符（全零），ETL 中已跳过

### Cell ID 命名规则
`{batch_label}_cell{index:02d}`，例如 `batch1_cell00`, `batch2_cell15`, `batch3_cell39`

## 已知问题

1. **Cycle 0 占位符**：原始数据中每颗电池的 cycle 0 为全零占位符，ETL 已自动跳过
2. **文件体积大**：3 个 batch 文件合计约 7.7 GB，处理需要充足内存
3. **Batch 3 来源**：Batch 3 数据来自 Attia et al. (2020) 的闭环优化实验，充电协议由贝叶斯优化算法动态选择

## 引用

Severson, K.A., Attia, P.M., Jin, N., Perkins, N., Jiang, B., Yang, Z., Chen, M.H., Aykol, M., Herring, P.K., Fraggedakis, D., Bazant, M.Z., Harris, S.J., Chueh, W.C., & Braatz, R.D. (2019). Data-driven prediction of battery cycle life before capacity degradation. *Nature Energy*, 4, 383–391.

Attia, P.M., Grover, A., Jin, N., Severson, K.A., Marber, T.M., Liao, M.H., Chen, M.H., Cheung, B., Chu, N., Dasgupta, S., Manthiram, R., Müller, A., Schäfer, F., Shinde, D., Srivatsan, H., Viswanathan, V., Braatz, R.D., & Chueh, W.C. (2020). Closed-loop optimization of fast-charging protocols for batteries with machine learning. *Nature*, 578, 397–402.
