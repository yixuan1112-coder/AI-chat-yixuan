# UM Battery Dataset - 数据整理说明 (README)

## 1. 数据集概况

* **Dataset ID**: `dataset_20`
* **原始数据名称**: Battery Test Data (University of Malaya)
* **原始数据规模**: 包含 3 种主流商业 18650 电芯，经历 4 个温度层级的多种复杂工况及循环测试，物理文件夹由于命名拼写不一分布极为混乱。
* **电池规格与化学体系**:
  1. **LFP 体系**: A123 Systems (APR18650M1A), 额定容量 1.1Ah, 额定电压 3.3V。正极: LiFePO4, 负极: Graphite。
  2. **NCA 体系**: Panasonic (NCR18650B), 额定容量 3.4Ah, 额定电压 3.6V。正极: LiNiCoAlO2, 负极: Graphite。
  3. **NMC 体系**: Murata/Sony (US18650VTC6), 额定容量 3.0Ah, 额定电压 3.6V。正极: LiNiMnCoO2, 负极: Graphite。
* **包含文件**:
  1. `dataset_20_metadata.csv` (元数据汇总表)
  2. 各电芯镜像目录下的 `timeseries.csv` (时间序列表)
  3. 各电芯镜像目录下的 `cycle_summary.csv` (周期汇总表)

## 2. 字段映射与物理量标准化

根据 `BatteryTwin Schema v0.2` 规范，对原始数据进行了以下扁平化和标准化清洗：

* **自适应单位转换**: 原始数据存在严重的单位不一致情况（部分文件和 Sheet 采用 `A/Ah` 记录，部分 Neware 导出的 Detail 表采用 `mA/mAh` 记录）。清洗引擎引入了最大值边界嗅探机制（最大绝对值 > 50 自动判定为 mA 级别），自动在时序表和循环表里将其转换为标准安培 (`current_A`) 和安时 (`capacity_Ah`, `charge_capacity_Ah`, `discharge_capacity_Ah`)。
* **时间轴保底平移**: 针对 Neware 部分底层表格只有 `Record Index`（记录行号）而缺少绝对时间戳的问题，清洗逻辑自动执行了 `Record Index - 1` 的保底物理时间平移，将其对齐为从 0 开始的标准秒 (`time_s`)。
* **电芯唯一标识 (Cell ID)**: 为确保全局唯一性，`cell_id` 采用了标准化的统一格式：`UM_{Chemistry}_{Temperature_C}C`（例如：`UM_NMC_25C`, `UM_NMC_-5C`）。

## 3. 核心工程挑战与清洗逻辑记录 (辛酸史)

*注：本数据集的清洗工作极具挑战性。原始数据集在保存时极其随意，经历了多届测试人员的“手办式拼写”，具有严重的格式碎片化问题。清洗引擎通过数十次重构，沉淀出了以下高鲁棒性的工业级处理逻辑：*

1. **突破 Windows 260 字符路径限制 (MAX_PATH limit)**
   原始压缩包解压后，由于原作者采用了超长的电池型号拼接作为文件夹名，导致多层嵌套后的路径总长度突破了 300 个字符。这引发了 Windows 底层的截断，导致 Python 脚本和 PowerShell 疯狂报错 `DirectoryNotFoundException` 却找不到任何文件。最终通过手动降维，将原始目录精简为 `D:\p\...\Battery Test Data`，消除了无意义的重复嵌套，救活了底层读取。
2. **“薛定谔的错别字” —— 极度鲁棒的路径级温度识别**
   原作者在保存不同温度文件夹时，命名完全看心情，大小写和拼写极其混乱。其中包括：正 25 度写为 `25 Degree`，零下 5 度写为 `Negative 5 degree`、`N5 Degree`、甚至拼错成 `Negative 5 drgree`（把 e 拼成了 r），45 度甚至写成了 `45 dgree`（漏了e）。如果使用单纯的字符比对，会导致 -5℃ 和 45℃ 的数据大面积漏扫。清洗引擎采用了“不限层级绝对路径纵向扫描 + 错别字字典模糊正则”，将 `drgree`、`dgree`、`negative`、`minus`、`n` 统一归一化为标准的浮点数温度，实现了“对错别字免疫”的无损提取。
3. **打破“文件名枷锁” —— 全 Sheet 特征码模糊探测**
   原始 Excel 文件管理极度混乱，作者经常把循环寿命数据（Cycle Summary）和工况时序数据（Timeseries）混在一个文件里，或者直接在工况文件里起个叫 `Cycle_9_1_3` 或 `Sheet1` 的名字。传统的“根据文件名/Sheet名”提取的脚本在此全部失效。为此，清洗逻辑直接采用“开箱验货”的降维打击策略：代码彻底放开对文件名和 Sheet 名的物理限制，直接读取每个 Sheet 内部的“列名特征码”。只要检测到一堆列中同时满足 `total of cycle` 和 `discharge capacity` 的数学特征，就直接判定其为 Summary 页面进行抠取，从而在大批杂乱的 Excel 中捞回了漏掉的全部衰减摘要。
4. **脏数据类型污染的“自愈”补丁**
   Neware 测试仪在导出时序大表（Detail）时，经常会在原本是数字的电流、电压列中随机混入诸如 `"▼"`、`"▲"`、`"End"`、`"Rest"` 等带有单体方向的字符串信息。导致 Pandas 在执行最大值绝对值计算 `abs()` 准备做单位换算时，直接抛出 `bad operand type for abs(): 'str'` 导致脚本静默崩溃退出。清洗引擎在核心计算前强制注入了 `pd.to_numeric(..., errors='coerce')` 的自愈滤网，把所有的文本垃圾强制软化为 `NaN` 并自动剔除，保障了数千万行时序数据的顺畅流出。
5. **镜像树复刻输出结构**
   为了最大化保留原始数据的物理对照关系，并且避免将所有电芯数据压扁到一个平面导致难以辨认，`timeseries.py` 和 `cyclesummary.py` 采用了路径克隆技术。它能在 `data/processed/dataset_20/` 下 **100% 镜像复刻** 原始数据的嵌套文件夹层级（如原样保留 `NMC/25 Degree` 等对应层级），并在各自的最底层文件夹内精准投递对齐规范的 `timeseries.csv` 和 `cycle_summary.csv`。

## 4. 缺失字段与异常说明

受原始物理实验限制，部分无法获取的 Schema 字段进行了留空或保底处理：

* `cutoff_voltage_upper` & `cutoff_voltage_lower`: 均根据 Mendeley 论文和官方电芯 Datasheet 进行了精确常数注入对齐（LFP 注入 3.6V/2.0V；NCA 注入 4.2V/2.5V；NMC 注入 4.2V/2.5V）。
* **NMC 45°C 数据集缺失**: 经 Python 深度全盘扫描核对，原作者在 `NMC/45 degree` 下**确实没有进行循环寿命测试**，仅保留了动态工况测试。因此该目录下没有 `cycle_summary.csv` 属于原始实验本身的数据 Gap，代码对其进行了合理的跳过处理。
* `discharge_capacity_Ah` (时序表): 由于部分工况大表在充放电过程中没有对充放电容量做细分剥离，为避免误导算法，时序表的容量统一存放在 `charge_capacity_Ah` 中（作为原始累积容量），而放电容量直接留空。

---