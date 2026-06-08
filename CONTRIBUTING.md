
# 贡献指南（CONTRIBUTING.md 中文版）

本仓库用于 **BatteryTwin Benchmark 数据准备项目**。  
两个 capstone 学生将在同一个仓库中协作完成数据集整理、标准化和质量检查工作。

本文件用于说明在该仓库中协作开发时需要遵守的基本规则，以保证代码历史清晰、避免冲突并保持数据结构一致。

---

# 1. 仓库目标

本仓库主要用于以下任务：

- 电池数据集整理与统一
- BatteryTwin Schema 标准化
- 数据质量检查（QC）
- benchmark 数据准备

本仓库 **不是主要用于模型训练**。

---

# 2. 基本协作原则

所有贡献者必须遵守以下规则：

1. **开始工作前先 pull**
2. **工作完成后必须 push**
3. commit message 必须清晰
4. 数据集状态变化必须更新 `dataset_registry.csv`
5. 不要覆盖另一位学生负责的数据
6. 所有问题必须记录在 dataset note 或 QC log 中

---

# 3. 每日工作流程

开始工作前：

```bash
cd ~/BatteryTwin-Benchmark-DataPrep
git pull origin main
```

完成工作后：

```bash
git status
git add .
git commit -m "clear commit message"
git push origin main
```

标准流程为：

```
pull → work → add → commit → push
```

---

# 4. Commit Message 规范

所有 commit message 必须使用以下格式：

```
[type] dataset_or_module: 简要描述
```

示例：

```
[data] dataset_01: generate metadata file
[data] dataset_02: generate timeseries
[qc] dataset_03: add QC visualization
[doc] dataset_01: update dataset note
[fix] dataset_02: fix unit conversion
[script] processing: add unit conversion script
```

---

# 5. Commit 类型说明

| 类型 | 含义 |
|-----|------|
| data | 数据处理结果 |
| qc | 数据质量检查 |
| doc | 文档更新 |
| script | 脚本或代码 |
| fix | bug 修复 |
| config | 配置更新 |

避免使用模糊 commit message，例如：

```
update
fix
change
work
```

---

# 6. 数据集责任分工

每个 dataset 应该在：

```
dataset_registry.csv
```

中指定负责人。

每位学生主要修改：

- 自己负责的数据集
- 对应的 dataset note
- 自己的 QC 记录
- 对应的数据处理脚本

不要随意修改另一位学生负责的数据。

---

# 7. 数据集集成完成标准

一个数据集被视为完成整理需要满足：

- metadata 文件生成
- timeseries 文件生成
- cycle_summary 文件生成
- schema 说明完成
- QC 检查完成

这些文件应存放在：

```
data/processed/<dataset_id>/
```

---

# 8. 文档更新要求

当数据集发生变化时，必须同步更新相关文档。

相关目录：

```
docs/schema/
docs/dataset_notes/
docs/qc_reports/
docs/project_plan/
```

每个 dataset 应有对应说明文件：

```
docs/dataset_notes/dataset_xx_note.md
```

---

# 9. Git 冲突处理

如果 `git push` 失败：

```bash
git pull origin main
```

然后再次 push：

```bash
git push origin main
```

如果出现 merge conflict：

1. 打开冲突文件
2. 手动保留正确内容
3. 删除冲突标记
4. 执行：

```bash
git add .
git commit -m "[fix] resolve merge conflict"
git push origin main
```

如果不确定如何处理，请联系导师。

---

# 10. 大文件管理

原始数据文件通常较大，不建议直接上传 GitHub。

推荐方式：

- 原始数据保存在服务器
- GitHub 只保存结构、脚本和必要的处理结果

---

# 11. 问题沟通

如果遇到以下情况：

- Git 报错
- schema 不确定
- 数据处理逻辑不一致

请先联系导师再进行修改。

---

# 12. 总结

本项目的协作流程非常简单：

```
pull → work → add → commit → push
```

保持清晰的 commit message 和规范的工作流程，可以极大减少协作问题。
