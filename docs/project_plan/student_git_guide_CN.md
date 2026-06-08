
# 学生 Git 使用指南（BatteryTwin-Benchmark-DataPrep 项目）

## 文档目的

本指南用于说明两位 capstone 学生如何在服务器上与 GitHub 仓库进行协作，包括：

- 如何从 GitHub **拉取 (pull)** 最新代码
- 如何把自己的修改 **提交并推送 (commit + push)** 到 GitHub
- 如何避免覆盖他人的工作
- 如何处理常见 Git 问题

本项目使用的仓库为：

`BatteryTwin-Benchmark-DataPrep`

该仓库由两名学生共同维护，因此请严格按照本指南的流程操作。


---

# Git 基本概念

在本项目中存在两个仓库：

**GitHub 仓库**
- 远程仓库 (remote repository)
- 所有人共享的代码和数据结构

**服务器仓库**
- 本地仓库 (local repository)
- 你在服务器上实际工作的目录

两者不会自动同步。

因此需要使用 Git 命令：

- `git pull` 从 GitHub 下载更新
- `git push` 将服务器上的修改上传到 GitHub

---

# 每天工作的推荐流程

每天开始工作前：

1. 进入项目目录
2. 从 GitHub 拉取最新版本
3. 再开始修改文件

每天工作完成后：

1. 查看修改的文件
2. 提交 commit
3. push 到 GitHub

这样可以避免大部分协作冲突。

---

# 第一步：进入仓库目录

登录服务器后进入项目目录：

```bash
cd ~/BatteryTwin-Benchmark-DataPrep
```

如果你的仓库在其它路径，请使用实际路径。

---

# 第二步：从 GitHub 拉取最新代码

开始工作之前必须执行：

```bash
git pull origin main
```

这一步会把 GitHub 上的最新版本下载到服务器。

只有在 pull 成功之后才可以开始修改文件。

---

# 第三步：查看当前仓库状态

可以使用：

```bash
git status
```

常见结果说明：

```
nothing to commit, working tree clean
```

表示当前没有修改。

```
modified:
```

表示文件已经修改但还没有提交。

```
untracked files:
```

表示新文件还没有加入 Git 管理。

---

# 第四步：添加修改文件

完成编辑后，需要先把修改加入 Git：

```bash
git add .
```

这会添加所有修改的文件。

如果只想添加某个文件：

```bash
git add path/to/file
```

例如：

```bash
git add dataset_registry.csv
git add docs/dataset_notes/dataset_01_note.md
```

---

# 第五步：提交修改

添加文件后需要创建 commit：

```bash
git commit -m "commit message"
```

建议使用清晰的 commit 信息，例如：

```bash
git commit -m "Add metadata for dataset_01"
git commit -m "Update QC log for dataset_03"
git commit -m "Fix unit conversion in dataset_02"
git commit -m "Complete cycle summary for dataset_04"
```

避免使用模糊信息，例如：

```
update
fix
change
```

清晰的 commit 信息有助于项目管理。

---

# 第六步：推送到 GitHub

提交之后执行：

```bash
git push origin main
```

这一步会把服务器上的修改上传到 GitHub。

push 成功后，其他人 pull 就能看到你的更新。

---

# 标准日常流程

每次工作推荐使用以下顺序：

```bash
cd ~/BatteryTwin-Benchmark-DataPrep

git pull origin main

# 开始你的工作

git status
git add .
git commit -m "clear commit message"
git push origin main
```

---

# commit 的推荐粒度

建议每个 commit 只完成一个小任务，例如：

- 一个 dataset metadata 更新
- 一个 QC 记录更新
- 一个脚本修复
- 一个字段映射修改

不要把很多不相关的修改放在同一个 commit 中。

---

# 每个学生主要修改的内容

学生主要修改：

- `dataset_registry.csv`
- `docs/dataset_notes/` 中自己负责的数据集说明
- `docs/qc_reports/` 中自己的 QC 记录
- 对应数据处理脚本

不要随意修改其他学生负责的数据集内容。

---

# GitHub 有新文件但服务器没有

如果你在 GitHub 网页上传了文件，但服务器没有看到：

执行：

```bash
git pull origin main
```

服务器不会自动更新。

---

# push 失败的常见原因

如果 push 报错，通常是因为 GitHub 上有新的提交。

解决方法：

```bash
git pull origin main
```

然后再执行：

```bash
git push origin main
```

---

# pull 出现冲突 (merge conflict)

如果两个学生修改了同一个文件，Git 会报告冲突。

冲突文件中会出现：

```
<<<<<<<
=======
>>>>>>>
```

处理方法：

1. 打开冲突文件
2. 手动选择正确内容
3. 删除冲突标记
4. 保存文件

然后执行：

```bash
git add .
git commit -m "Resolve merge conflict"
git push origin main
```

如果不确定如何处理，请联系导师。

---

# 丢弃本地修改

如果你想放弃所有未提交修改：

```bash
git reset --hard HEAD
```

然后重新拉取：

```bash
git pull origin main
```

注意：该操作会永久删除未提交修改。

---

# 自动提交脚本

如果仓库中有脚本 `git_push.sh`，也可以使用：

```bash
./git_push.sh "commit message"
```

例如：

```bash
./git_push.sh "Update dataset_01 metadata"
```

---

# 协作基本规则

请遵守以下原则：

1. 每天工作前先 pull
2. 工作完成后 push
3. commit 信息必须清晰
4. 更新 dataset 状态时必须修改 `dataset_registry.csv`
5. 不要覆盖他人的数据
6. 所有问题写入 dataset note 或 QC log

---

# 必须记住的 Git 命令

如果只记住最重要的命令：

```bash
git pull origin main
git status
git add .
git commit -m "message"
git push origin main
```

---

# 完整示例

```bash
cd ~/BatteryTwin-Benchmark-DataPrep

git pull origin main

# 编辑文件
# dataset_registry.csv
# docs/dataset_notes/dataset_01_note.md

git status
git add .
git commit -m "Update dataset_01 note"
git push origin main
```

---

# 遇到 Git 错误时

不要随意执行不理解的命令。

正确做法：

1. 复制完整错误信息
2. 发送给导师
3. 等待确认

尤其不要随意使用：

```
git reset --hard
```

---

# 总结

项目 Git 工作流程非常简单：

**开始工作前：**

pull

**完成工作后：**

add → commit → push

严格按照流程操作即可避免绝大多数问题。
