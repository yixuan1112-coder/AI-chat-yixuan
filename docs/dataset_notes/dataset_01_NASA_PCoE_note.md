# Dataset 01 — NASA PCoE Battery Aging Dataset

## 1. 基本信息

| 属性 | 值 |
|------|-----|
| **数据集名称** | NASA PCoE Li-ion Battery Aging Dataset |
| **数据集ID** | NASA_PCoE |
| **发布机构** | NASA Ames Research Center, Prognostics Center of Excellence (PCoE) |
| **发布年份** | 2007 |
| **作者** | B. Saha, K. Goebel |
| **许可证** | Public Domain (NASA Open Data) |
| **下载链接** | https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip |
| **官方页面** | https://data.nasa.gov/dataset/li-ion-battery-aging-datasets |
| **PCoE仓库** | https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/ |
| **引用格式** | B. Saha and K. Goebel (2007). "Battery Data Set", NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA |

## 2. 电池本体信息

| 属性 | 值 |
|------|-----|
| **化学体系 (chemistry)** | LCO (LiCoO₂/Graphite) |
| **正极材料 (cathode)** | LiCoO₂ |
| **负极材料 (anode)** | Graphite |
| **品牌/厂家** | 商用电池（具体品牌未公开） |
| **型号/尺寸** | 18650 |
| **封装形态 (form_factor)** | cylindrical |
| **额定容量** | 2.0 Ah |
| **额定电压** | 3.7 V |
| **电池数量** | ~34 cells (B0005–B0056，部分编号缺失) |

## 3. 实验协议

### 3.1 充电协议
- CC-CV: 恒流 1.5A 充至 4.2V，然后恒压充至电流降到 20mA cutoff

### 3.2 放电协议
- CC: 恒流 2A 放电至不同截止电压：
  - 标准组: 2.7V (OEM推荐)
  - 深放电组: 2.5V
  - 超深放电组: 2.2V / 2.0V (低于OEM推荐值，用于诱导深放电老化效应)

### 3.3 EIS (电化学阻抗谱)
- 每隔若干cycle进行一次EIS测量
- 频率范围: 0.1Hz–5kHz
- 测量参数: Sense_current, Battery_impedance, Rectified_impedance, Re (电解质电阻), Rct (电荷转移电阻)

### 3.4 温度条件
- **4°C**: 低温组 (B0033, B0034, B0036, B0049–B0052)
- **24°C**: 室温组 (B0005–B0007, B0018, B0025–B0028, B0038–B0044, B0053–B0056)
- **43°C**: 高温组 (B0029–B0032, B0045–B0048)

### 3.5 EOL (寿命终止) 标准
- 容量衰减 30%：从 2.0Ah 降至 1.4Ah

## 4. 原始数据结构

### 4.1 文件格式
- **格式**: MATLAB `.mat` 文件 (v5)
- **组织**: 每个cell一个文件 (e.g., `B0005.mat`)
- **大小**: 压缩后约56MB

### 4.2 .mat 内部结构
```
B0005.mat
└── B0005 (struct)
    └── cycle (1×N struct array)
        ├── type: 'charge' | 'discharge' | 'impedance'
        ├── ambient_temperature: float (°C)
        ├── time: datetime string
        └── data (struct)
            ├── Voltage_measured (V)      — 端电压
            ├── Current_measured (A)       — 电流
            ├── Temperature_measured (°C)  — 表面温度
            ├── Current_charge (A)         — 充电电流 (仅charge)
            ├── Voltage_charge (V)         — 充电电压 (仅charge)
            ├── Time (s)                   — 从step开始的时间
            └── Capacity (Ah)             — 放电容量 (仅discharge)
```

### 4.3 采样频率
- 约 10Hz (具体值因测试阶段略有不同)

## 5. 字段映射表 (原始 → BatteryTwin Schema v0.2)

### 5.1 Timeseries 映射

| 原始字段 | → 统一字段 | 类型 | 单位 | 必填 | 映射说明 |
|----------|-----------|------|------|------|---------|
| (文件名) | cell_id | str | - | ✓ | 文件名即cell_id (B0005, B0006, ...) |
| (cycle index) | cycle_id | int | - | ✓ | 从1开始的循环编号 |
| type | step_type | str | - | ✓ | charge/discharge (impedance跳过) |
| Time | time_s | float | s | ✓ | 从step开始的经过时间，无换算 |
| Voltage_measured | voltage_V | float | V | ✓ | 端电压，无换算 |
| Current_measured | current_A | float | A | ✓ | 电流，正=充电，无换算 |
| Temperature_measured | temperature_C | float | °C | ✓ | 表面温度，无换算 |
| (积分计算) | charge_capacity_Ah | float | Ah | ○ | 充电cycle通过 ∫\|I\|dt 估算 |
| Capacity | discharge_capacity_Ah | float | Ah | ○ | 仅discharge cycle有 |

### 5.2 Cycle Summary 映射

| 原始来源 | → 统一字段 | 说明 |
|----------|-----------|------|
| max(Capacity) per discharge cycle | discharge_capacity_Ah | 每cycle最大放电容量 |
| ∫\|I\|dt per charge cycle | charge_capacity_Ah | 充电容量通过电流积分估算 |
| max(Temperature_measured) | temperature_max_C | 每cycle最高温度 |
| mean(Temperature_measured) | temperature_avg_C | 每cycle平均温度 |
| min(Temperature_measured) | temperature_min_C | 每cycle最低温度 |
| time[-1] - time[0] | charge_duration_s / discharge_duration_s | step持续时间 |
| (无) | discharge_energy_Wh | 原始不提供，留空 |
| (无) | internal_resistance_Ohm | 需从EIS数据另行提取 |

## 6. 数据处理说明

### 6.1 处理步骤
1. 使用 `scipy.io.loadmat` 读取 .mat 文件
2. 遍历 cycle struct array，跳过 type='impedance' 的 cycles
3. 提取 charge/discharge 的时序数据，映射到统一字段名
4. 对 discharge cycle 取 max(Capacity) 作为 cycle-level 放电容量
5. 对 charge cycle 通过 ∫|I|dt 积分估算充电容量
6. 统一写入 timeseries (parquet + csv) 和 cycle_summary (csv)

### 6.2 单位换算
- **无单位换算**：所有原始字段单位与目标schema一致（V, A, °C, s, Ah）

### 6.3 缺失/空值说明
| 字段 | 缺失情况 | 处理方式 |
|------|---------|---------|
| charge_capacity_Ah | 原始数据无此字段 | 通过电流积分估算；精度取决于采样频率 |
| discharge_capacity_Ah | 仅 discharge cycle 有 | charge cycle 此字段留 NaN |
| discharge_energy_Wh | 原始不提供 | 全部留 NaN |
| charge_energy_Wh | 原始不提供 | 全部留 NaN |
| internal_resistance_Ohm | 需从EIS单独提取 | 当前留 NaN，后续可补充 |
| coulombic_efficiency | 需同一cycle charge+discharge配对 | 目前留 NaN |

### 6.4 数据质量标记 (cycle_end_flag)
- `normal`: 正常cycle
- `capacity_jump`: 容量与前一cycle相比变化超过5倍中位数变化量或 >0.05Ah
- `missing_data`: 时序数据缺失或截断

### 6.5 已知问题
1. **EIS数据未纳入**: impedance cycle结构不同于charge/discharge，当前ETL跳过，后续可单独处理
2. **部分cell编号缺失**: B0035 不存在于数据集中
3. **charge_capacity_Ah为估算值**: 精度低于原生discharge Capacity字段
4. **部分cell数据不完整**: 某些cell可能在达到EOL之前测试中断

## 7. 输出文件清单

| 文件名 | 格式 | 说明 | 行数规模 |
|--------|------|------|---------|
| `NASA_PCoE_metadata.csv` | CSV | 元数据，每cell一行 | ~34 rows |
| `NASA_PCoE_timeseries.parquet` | Parquet | 时间序列，按秒采样 | ~数百万 rows |
| `NASA_PCoE_timeseries.csv` | CSV | 时间序列CSV副本 | 同上 |
| `NASA_PCoE_cycle_summary.csv` | CSV | 周期级汇总 | ~数千 rows |

## 8. 引用与参考

- [1] B. Saha, K. Goebel. "Battery Data Set", NASA Prognostics Data Repository, 2007.
- [2] B. Saha, K. Goebel. "Modeling Li-ion Battery Capacity Depletion in a Particle Filtering Framework", Annual Conf. of the PHM Society, 2009.
- [3] NASA PCoE Data Repository: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/

## 9. 处理者信息

- **处理者**: Liu Kefan
- **处理日期**: 2026-03-12
- **ETL脚本**: `scripts/etl_nasa.py`
- **质检脚本**: `scripts/quality_check.py`
