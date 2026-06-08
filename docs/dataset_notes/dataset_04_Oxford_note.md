# Dataset 04: Oxford Battery Degradation 数据集说明

## 概述

Oxford Battery Degradation 数据集来自牛津大学 Battery Intelligence Lab，包含两个子数据集：

1. **Kokam LCO 软包电池** (Dataset 1)：8 颗 Kokam SLPB533459H4 (740 mAh) LCO 软包电池的长期老化数据
2. **NCA 18650 路径依赖数据集** (Path Dependent Part 1)：12 颗 Panasonic NCR18650BD (3 Ah) NCA 圆柱电池的路径依赖老化数据

## 子数据集 A：Kokam LCO 软包电池

| 项目 | 说明 |
|------|------|
| 电池数量 | 8 |
| 型号 | Kokam SLPB533459H4 |
| 化学体系 | LCO（LiCoO₂）正极 / 石墨负极 |
| 封装形式 | 软包 (pouch) |
| 标称容量 | 740 mAh (0.740 Ah) |
| 测试温度 | 40°C |
| 循环方式 | Artemis Urban 驾驶循环放电 + 2C 恒流充电 |
| 表征方式 | 每 100 个驾驶循环做一次 1C 充放电 + pseudo-OCV |
| 测试设备 | Bio-Logic MPG-205, 8 通道 |
| 数据格式 | .mat（MATLAB 二进制，四层嵌套结构） |
| 许可证 | ODbL 1.0 |

### 数据结构

```
Layer 1: Cell (1-8)
  └─ Layer 2: 表征循环编号 (cyc0100, cyc0200, ...)
       └─ Layer 3: C1ch (1C 充电), C1dc (1C 放电), OCVch, OCVdc
            └─ Layer 4: t (秒), v (伏特), q (毫安时), T (°C)
```

### 注意事项

- **数据仅包含表征循环**：实际驾驶循环（Artemis Urban）的数据不在数据集中
- **单位转换**：原始数据中 charge (q) 单位为 mAh，需转换为 Ah
- cycle_summary 中的 cycle_number 对应驾驶循环数（如 100, 200, ...），非表征循环序号

## 子数据集 B：NCA 18650 路径依赖

| 项目 | 说明 |
|------|------|
| 电池数量 | 12 (4 组 × 3 颗) |
| 型号 | Panasonic NCR18650BD |
| 化学体系 | NCA（LiNiCoAlO₂）正极 / 石墨负极 |
| 封装形式 | 18650 圆柱 |
| 标称容量 | 3 Ah |
| 测试温度 | 24°C |
| 数据格式 | .mat |
| 许可证 | ODbL 1.0 |

### 实验分组

| 组别 | 循环方式 | 日历老化 |
|------|---------|---------|
| Group 1 | 1 天 CC 循环 (C/2) | 5 天 90% SoC |
| Group 2 | 1 天 CC 循环 (C/4) | 5 天 90% SoC |
| Group 3 | 2 天 CC 循环 (C/2) | 10 天 90% SoC |
| Group 4 | 2 天 CC 循环 (C/4) | 10 天 90% SoC |

每 48 个循环进行一次参考性能测试 (RPT)。

## 引用

1. Birkl, C.R., et al. "Degradation diagnostics for lithium ion cells." *Journal of Power Sources*, 341, 2017, pp. 373-386. DOI: 10.1016/j.jpowsour.2016.12.011
2. Raj, T., et al. "Investigation of path-dependent degradation in lithium-ion batteries." *Batteries & Supercaps*, 3(12), 2020, pp. 1377-1385. DOI: 10.1002/batt.202000160
