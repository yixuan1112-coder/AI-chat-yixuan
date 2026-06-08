# BatteryLife vs BatteryTwin 对比分析表格

> 文件路径: `docs/project_plan/weekly_comparison_batterylife_vs_batterytwin_tables.md`
> 对应任务书: 任务二 — 相关工作对比分析
> 参考论文: Tan et al., "BatteryLife: A Comprehensive Dataset and Benchmark for Battery Life Prediction", KDD 2025

---

## 表 1: BatteryLife 中与"数据集整理"直接相关的部分

| 维度 | BatteryLife 具体做法 |
|------|---------------------|
| **整合数据集数量** | 整合 16 个数据集 (13 个已有公开 + 3 个自建), 共 990 颗电池, ~99,000 样本 |
| **电池类型覆盖** | 锂离子 (Li-ion)、锌离子 (Zn-ion)、钠离子 (Na-ion)；实验室测试 + 工业测试 (CALB) |
| **格式多样性** | 8 种封装格式 (18650圆柱、软包、纽扣电池、方形等), 59 种化学体系, 9 种温度, 421 种充放电协议 |
| **数据标准化方式** | 统一存储为 pickle 文件格式, 遵循 BatteryML 的命名规则; 原始数据来自不同格式和命名 |
| **数据预处理流程** | ① 过滤 SOH 未降至 λ+2.5% 的电池 (Li-ion λ=80%, CALB λ=90%); ② SOH 在 (λ, λ+2.5%] 区间的电池使用线性外推估算寿命; ③ 排除寿命 ≤100 圈的电池; ④ BatteryML 标准化的 7 个数据集用中位滤波检测并移除异常循环; ⑤ 其余数据集手动移除 RPT 循环、formation 循环和容量突变循环 |
| **时序数据重采样** | 每个循环充放电各重采样到 150 个点 (共 300 点/循环), 含电流、电压、容量三个变量 |
| **归一化方法** | 容量和电流除以标称容量 Q_nominal; 电压除以每圈最大电压 max(v_i) |
| **数据分域策略** | 分为 Li-ion、Zn-ion、Na-ion、CALB 四个 domain, 分别训练和评估 |
| **SOH / 寿命定义** | SOH = Q_i / Q_0 (Q_0 用标称容量或首圈容量); 寿命 = SOH 首次 ≤80% 时的循环数 (CALB 用 90%) |
| **数据划分** | 训练:验证:测试 = 6:2:2, 随机划分 |
| **开源地址** | https://github.com/Ruifeng-Tan/BatteryLife |

---

## 表 2: BatteryLife 特点/贡献 vs BatteryTwin 特点/贡献 对比表

| 对比维度 | BatteryLife (KDD 2025) | BatteryTwin (我们的项目) |
|---------|----------------------|----------------------|
| **项目定位** | 面向电池寿命预测 (BLP) 的统一数据集+基准 | 面向电池数据标准化的 curation 平台, 支持可查询、可扩展的数据湖 |
| **核心目标** | 提供最大最多样的 BLP benchmark, 评估 18 种模型 | 建立标准化 ETL 流程, 统一 schema, 提供 web 可视化查询界面 |
| **数据集数量** | 16 个 (截至论文发表) | 目前 5+ 个, 持续扩展中 |
| **电池数量** | 990 颗 | 持续增长, 目前已处理 NASA(34) + CALCE(13) + Stanford-MIT-TRI(~170) + Oxford(20) + RWTH(48) 等 |
| **数据存储格式** | 统一 pickle 格式 (遵循 BatteryML 命名) | 统一 CSV 格式 (metadata.csv + cycle_summary.csv + timeseries 样本), 更通用易读 |
| **Schema 设计** | 无显式 schema 字典; 依赖 BatteryML 的隐式结构 | 显式 schema: dataset_registry.csv 统一字段, 每个数据集有 metadata/cycle_summary/timeseries 三层结构 |
| **字段标准化** | 统一为 voltage, current, capacity 三变量, 重采样到 300 点/循环 | 保留原始分辨率, 通过 ETL 脚本统一列名和单位, 不强制重采样 |
| **QC 流程** | 中位滤波 + 手动移除异常循环 + SOH 阈值过滤 | ETL 内嵌 QC (RPT 标记、异常检测), 生成 QC 报告 (degradation_curves.png) |
| **数据预处理透明度** | 预处理代码开源, 但处理细节需读论文附录 | 每个数据集有独立 ETL 脚本 + 中英文 dataset note + DOWNLOAD.md, 全流程可追溯 |
| **前端/可视化** | 无 web 前端; 数据通过 GitHub 下载 | 提供 BatteryLake web dashboard, 支持在线浏览 dataset_registry 和元数据 |
| **模型基准** | 提供 18 种方法的 benchmark (MLP, Transformer, LSTM, GRU, CNN, CyclePatch 等) | 不含模型基准 (数据 curation 导向, 非模型导向) |
| **创新方法** | 提出 CyclePatch (intra-cycle + inter-cycle encoder) 插件技术 | 不涉及模型方法; 创新在于标准化流程和 web 可查询能力 |
| **可扩展性** | 新增数据集需修改代码 + 重新预处理 | 模板化 ETL + registry 设计, 新增数据集只需写 ETL 脚本并注册 |
| **License 管理** | 论文中列出数据来源, 但未逐个标注 license | dataset_registry.csv 中逐个记录每个数据集的 license |
| **区块链溯源** | 无 | (研究方向) 结合 NBC'26 论文, 探索基于区块链的数据完整性验证 |

---

## 表 3: 对 BatteryTwin 后续工作的改进建议

| 改进方向 | 具体建议 | 参考 BatteryLife 的经验 |
|---------|--------|---------------------|
| **扩大数据集覆盖** | 优先整合 BatteryLife 中包含但我们尚未处理的数据集 (如 HUST、Tongji、ISU_ILCC、BatteryArchive、XJTU), 以及非锂离子数据 (Zn-ion, Na-ion) | BatteryLife 的 16 个数据集覆盖面远超 BatteryML, 说明数据集数量和多样性是核心竞争力 |
| **统一字段字典 (Schema)** | 建立显式的字段字典文档 (field_dictionary.md), 定义每个标准列名的含义、单位、数据类型, 避免 ETL 脚本间不一致 | BatteryLife 隐式依赖 BatteryML 格式, 缺乏独立字段文档; 我们可以做得更好 |
| **单位统一规范** | 制定并执行单位规范: 容量统一用 Ah, 电流统一用 A, 电压统一用 V, 时间统一用 s, 温度统一用 °C; 在 ETL 脚本中加入单位验证断言 | BatteryLife 的归一化 (除以 Q_nominal) 是为了模型输入; 我们的标准化应保留原始物理量, 同时保证单位一致 |
| **QC 流程标准化** | 开发统一的 QC 模块: ① 容量异常检测 (中位滤波或 IQR); ② RPT 自动识别; ③ formation 循环标记; ④ 生成标准化 QC 报告 | BatteryLife 对 BatteryML 的 7 个数据集用中位滤波, 其余手动处理 — 不够系统化 |
| **数据分域 (Domain) 标签** | 在 metadata 中增加 domain 标签 (如 chemistry_type, test_source), 支持按域查询和模型评估 | BatteryLife 将数据分为 Li-ion/Zn-ion/Na-ion/CALB 四个 domain, 对跨域评估很有价值 |
| **Preprocessing Pipeline 自动化** | 开发统一的 `run_all_etl.py` 脚本, 一键处理所有数据集, 支持增量更新 (只处理新增/变更的数据集) | BatteryLife 的预处理是一次性的; 我们需要支持持续扩展 |
| **Web 可查询能力** | 前端实现: ① dataset_registry 表格渲览 + 排序/筛选; ② 每个数据集的 metadata 下钻; ③ degradation curve 在线可视化; ④ 数据下载入口 | BatteryLife 无 web 前端; 这是 BatteryTwin 的差异化优势 |
| **数据版本管理** | 对 processed 数据引入版本号 (v1, v2...), 在 registry 中记录当前版本和变更日志 | BatteryLife 无版本管理概念; 随着数据集增多, 变更追踪变得必要 |
| **多语言文档** | 继续保持中英文双语 dataset note, 降低中文学术社区的使用门槛 | BatteryLife 仅有英文文档 |
| **与 BatteryLife 的兼容性** | 考虑提供 BatteryLife pickle 格式的导出选项, 让用户可以直接将 BatteryTwin 的数据用于 BatteryLife 的模型基准 | 增加互操作性, 扩大项目影响力 |
