# Dataset 04 Oxford: 逐步操作指南
> 照着做就行，别跳步

---

## Step 1: 下载原始数据（手动，约 10 分钟）

### 1a. Kokam LCO (Dataset 1)
1. 打开浏览器 → https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac
2. 下载 `Oxford_Battery_Degradation_Dataset_1.mat` 和 `Readme.txt`
3. 放到对应位置：

```bash
cd ~/Projects/BatteryTwin-Benchmark-DataPrep
mkdir -p data/raw/dataset_04_Oxford/kokam_lco/
# 把下载的文件移动过去
mv ~/Downloads/Oxford_Battery_Degradation_Dataset_1.mat data/raw/dataset_04_Oxford/kokam_lco/
mv ~/Downloads/Readme.txt data/raw/dataset_04_Oxford/kokam_lco/
```

### 1b. NCA 18650 Path Dependent (Part 1)
1. 打开 → https://ora.ox.ac.uk/objects/uuid:de62b5d2-6154-426d-bcbb-30253ddb7d1e
2. 下载所有 .mat 文件 + Readme.txt
3. 放到对应位置：

```bash
mkdir -p data/raw/dataset_04_Oxford/nca_18650/
mv ~/Downloads/TPG*.mat data/raw/dataset_04_Oxford/nca_18650/
mv ~/Downloads/Readme.txt data/raw/dataset_04_Oxford/nca_18650/
```

---

## Step 2: 把脚本和文档放到仓库里

```bash
cd ~/Projects/BatteryTwin-Benchmark-DataPrep

# 从 Claude 产出的文件复制过去（替换 SOURCE_DIR 为你保存这些文件的路径）
# 如果你是从 Claude 下载到 ~/Downloads/dataset_04/ 的话：

# 脚本
cp ~/Downloads/dataset_04/explore_oxford.py scripts/
cp ~/Downloads/dataset_04/etl_oxford.py scripts/
cp ~/Downloads/dataset_04/quality_check_oxford.py scripts/

# DOWNLOAD.md
cp ~/Downloads/dataset_04/DOWNLOAD.md data/raw/dataset_04_Oxford/

# Dataset Notes
cp ~/Downloads/dataset_04/dataset_04_Oxford_note.md docs/dataset_notes/
cp ~/Downloads/dataset_04/dataset_04_Oxford_note_EN.md docs/dataset_notes/
```

---

## Step 3: 先跑探索脚本，确认 .mat 结构

```bash
conda activate batterytwin
cd ~/Projects/BatteryTwin-Benchmark-DataPrep
python scripts/explore_oxford.py 2>&1 | tee /tmp/oxford_explore_output.txt
```

**关键：把输出复制粘贴给 Claude！**
如果结构和预期不一样，我帮你调 ETL 脚本。

---

## Step 4: 跑 ETL

```bash
python scripts/etl_oxford.py
```

检查输出目录：
```bash
ls -la data/processed/dataset_04/
ls -la data/processed/dataset_04/kokam_lco/
ls -la data/processed/dataset_04/nca_18650/
```

确认以下文件都在：
- [ ] `data/processed/dataset_04/Oxford_metadata.csv`
- [ ] `data/processed/dataset_04/DATA_LOCATION.txt`
- [ ] `data/processed/dataset_04/kokam_lco/Oxford_kokam_lco_cycle_summary.csv`
- [ ] `data/processed/dataset_04/kokam_lco/*_timeseries.csv.txt` (8 个)
- [ ] `data/processed/dataset_04/nca_18650/Oxford_nca_18650_cycle_summary.csv`
- [ ] `data/processed/dataset_04/nca_18650/*_timeseries.csv.txt` (12 个)

---

## Step 5: 跑 QC

```bash
python scripts/quality_check_oxford.py
```

检查 QC 图：
```bash
ls docs/qc_reports/dataset_04/
open docs/qc_reports/dataset_04/degradation_curves.png  # Mac 预览
```

---

## Step 6: 更新 dataset_registry.csv

```bash
# 用你喜欢的编辑器打开
nano dataset_registry.csv
# 或
code dataset_registry.csv
```

找到 dataset_04 那行，更新 5 列为 `yes`：
- `metadata_done` → yes
- `timeseries_done` → yes
- `cycle_summary_done` → yes
- `dataset_note_done` → yes
- `qc_done` → yes
- `status` → processing

---

## Step 7: Git 推送（最后一步！）

```bash
cd ~/Projects/BatteryTwin-Benchmark-DataPrep

# 0. 先拉最新（防止和曹汉冲突）
git pull origin main

# 1. 强制添加 data/ 下的文件
git add -f data/raw/dataset_04_Oxford/DOWNLOAD.md
git add -f data/processed/dataset_04/Oxford_metadata.csv
git add -f data/processed/dataset_04/DATA_LOCATION.txt
git add -f data/processed/dataset_04/kokam_lco/Oxford_kokam_lco_cycle_summary.csv
git add -f data/processed/dataset_04/kokam_lco/*_timeseries.csv.txt
git add -f data/processed/dataset_04/nca_18650/Oxford_nca_18650_cycle_summary.csv
git add -f data/processed/dataset_04/nca_18650/*_timeseries.csv.txt

# 2. 添加不被 gitignore 的文件
git add scripts/etl_oxford.py
git add scripts/quality_check_oxford.py
git add docs/dataset_notes/dataset_04_Oxford_note.md
git add docs/dataset_notes/dataset_04_Oxford_note_EN.md
git add docs/qc_reports/dataset_04/
git add dataset_registry.csv

# 3. 检查一遍
git status
git diff --cached --stat

# 4. 确认没问题 → 提交
git commit -m "feat: add dataset_04 Oxford Battery Degradation - metadata, cycle_summary, timeseries, notes"

# 5. 推送
git push origin main

# 6. 确认
git log --oneline -3
```

### ⚠️ 千万别 add 的文件
```bash
# 这些是大文件，只存本地，不推 GitHub！
# data/processed/dataset_04/kokam_lco/*_timeseries.csv  （没有 .txt 后缀的）
# data/processed/dataset_04/nca_18650/*_timeseries.csv
# data/raw/dataset_04_Oxford/kokam_lco/*.mat
# data/raw/dataset_04_Oxford/nca_18650/*.mat
```

---

## 遇到问题？

| 问题 | 解决 |
|------|------|
| explore 脚本报错 `NotImplementedError` | .mat 是 HDF5 格式，确保安装了 h5py: `pip install h5py` |
| scipy 和 h5py 都装了还是报错 | 把报错信息发给 Claude |
| ETL 跑出来 0 rows | 把 explore 输出发给 Claude，我帮你调结构解析 |
| git push 被拒绝 | `git pull --rebase origin main` 然后再 push |
| 不确定哪些文件被 track 了 | `git ls-files data/processed/dataset_04/` |

---

**预计总用时：3-4 小时**（下载 30min + 探索/调试 1h + ETL运行 30min + QC + Git 30min）
