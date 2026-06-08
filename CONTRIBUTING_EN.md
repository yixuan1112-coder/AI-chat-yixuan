
# Contributing Guidelines

This repository supports the **BatteryTwin Benchmark Data Preparation** project.
Two capstone students collaborate on the same repository. These guidelines ensure
that contributions remain organized, traceable, and conflict-free.

---

# 1. Repository Purpose

This repository focuses on:

- battery dataset integration
- schema standardization
- quality control (QC)
- benchmark dataset preparation

It is **not primarily a model development repository**.

---

# 2. Basic Collaboration Principles

All contributors must follow these principles:

1. Always **pull before starting work**
2. Always **push after finishing work**
3. Write **clear commit messages**
4. Update **dataset_registry.csv** whenever dataset status changes
5. Do not overwrite another student's dataset without discussion
6. Record issues in dataset notes or QC logs

---

# 3. Daily Workflow

Before starting work:

```bash
cd ~/BatteryTwin-Benchmark-DataPrep
git pull origin main
```

Do your work.

After finishing work:

```bash
git status
git add .
git commit -m "clear commit message"
git push origin main
```

---

# 4. Commit Message Format

Use the following format:

```
[type] dataset_or_module: short description
```

Examples:

```
[data] dataset_01: generate metadata file
[data] dataset_02: generate timeseries
[qc] dataset_03: add QC visualization
[doc] dataset_01: update dataset note
[fix] dataset_02: fix unit conversion
[script] processing: add unit conversion script
```

Commit types:

| Type | Meaning |
|-----|------|
| data | dataset processing results |
| qc | quality control updates |
| doc | documentation |
| script | scripts or code |
| fix | bug fixes |
| config | configuration updates |

Avoid vague messages such as:

```
update
fix
change
work
```

---

# 5. Dataset Responsibility

Each dataset should have a **single assigned student** listed in:

```
dataset_registry.csv
```

Students should mainly modify:

- datasets assigned to them
- their dataset notes
- their QC logs
- their processing scripts

---

# 6. Dataset Integration Requirements

A dataset is considered integrated when the following files exist:

```
metadata file
timeseries file
cycle_summary file
schema description
QC check completed
```

These should be stored under:

```
data/processed/<dataset_id>/
```

---

# 7. Documentation Updates

Documentation must be updated whenever datasets change.

Relevant directories:

```
docs/schema/
docs/dataset_notes/
docs/qc_reports/
docs/project_plan/
```

Every dataset should have a dataset note file:

```
docs/dataset_notes/dataset_xx_note.md
```

---

# 8. Handling Git Conflicts

If `git push` fails:

```bash
git pull origin main
```

Then push again.

If a merge conflict occurs:

1. open the conflicted file
2. resolve the conflict manually
3. run:

```bash
git add .
git commit -m "[fix] resolve merge conflict"
git push origin main
```

If unsure, contact the supervisor.

---

# 9. Large Data Files

Large raw datasets should **not be committed directly** to GitHub unless necessary.

Recommended approach:

- store raw data on the server
- commit only metadata or processed summaries if needed

---

# 10. Communication

If you encounter:

- Git errors
- unclear dataset schema
- processing inconsistencies

Contact the supervisor before making major changes.

---

# 11. Summary

The collaboration workflow is simple:

```
pull → work → add → commit → push
```

Follow the workflow and maintain clear commit messages to keep the repository organized.
