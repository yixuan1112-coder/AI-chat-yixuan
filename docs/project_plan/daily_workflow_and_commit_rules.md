
# Capstone Project Daily Workflow and Commit Message Guidelines

This document defines the **daily workflow** and **commit message rules** for students working on the repository:

`BatteryTwin-Benchmark-DataPrep`

The purpose is to ensure that two students can collaborate safely without overwriting each other's work and to keep the repository history clean and understandable.

Recommended location in the repository:

```
docs/project_plan/daily_workflow_and_commit_rules.md
```

---

# 1. Daily Work Workflow

Every student should follow the same workflow each day.

## Step 1: Enter the repository

```bash
cd ~/BatteryTwin-Benchmark-DataPrep
```

## Step 2: Pull the latest version

Always pull before starting work.

```bash
git pull origin main
```

This ensures your local repository includes updates from GitHub.

---

# 2. Do Your Work

Typical work includes:

- updating `dataset_registry.csv`
- editing dataset notes in `docs/dataset_notes/`
- writing QC logs
- generating metadata / timeseries / cycle summary files
- updating scripts

Try to modify only the datasets assigned to you.

---

# 3. Check What Changed

Before committing, check modified files:

```bash
git status
```

You should review what you changed before committing.

---

# 4. Add Files

Add modified files:

```bash
git add .
```

Or add specific files:

```bash
git add dataset_registry.csv
git add docs/dataset_notes/dataset_01_note.md
```

---

# 5. Commit Changes

Create a commit with a **clear message**.

```bash
git commit -m "your message"
```

Commit messages must follow the format described below.

---

# 6. Push Changes

Upload your changes to GitHub:

```bash
git push origin main
```

Now the other student can see your changes after pulling.

---

# 7. Standard Daily Command Sequence

Typical workflow:

```bash
cd ~/BatteryTwin-Benchmark-DataPrep

git pull origin main

# do your work

git status
git add .
git commit -m "clear message"
git push origin main
```

---

# 8. Commit Message Format

Use the following format:

```
[type] dataset_or_module: short description
```

Examples:

```
[data] dataset_01: add metadata mapping
[data] dataset_02: generate timeseries file
[qc] dataset_03: update QC report
[fix] dataset_02: fix unit conversion
[doc] dataset_01: update dataset note
[script] processing: add unit conversion script
```

---

# 9. Commit Types

Use one of the following prefixes.

| Type | Meaning |
|-----|------|
| data | dataset processing results |
| qc | quality control updates |
| doc | documentation updates |
| script | code or processing scripts |
| fix | bug fix |
| config | configuration updates |

Example:

```
[data] dataset_01: generate cycle summary
```

---

# 10. Good Commit Messages

Good examples:

```
[data] dataset_01: generate metadata file
[data] dataset_02: build timeseries parquet
[qc] dataset_03: add visualization checks
[doc] dataset_02: update dataset note
```

Bad examples:

```
update
fix
change files
work
```

These messages do not explain what was changed.

---

# 11. Commit Scope

Each commit should represent **one logical task**.

Good practice:

- metadata generation
- QC update
- dataset note update
- script fix

Avoid mixing multiple unrelated tasks in a single commit.

---

# 12. When to Update dataset_registry.csv

Whenever dataset progress changes.

Examples:

- metadata completed
- timeseries generated
- QC finished
- dataset finished

Example commit:

```
[data] dataset_01: update registry status
```

---

# 13. Conflict Prevention

To reduce conflicts:

Always:

1. pull before starting work
2. commit frequently
3. push after finishing work

Do not modify datasets assigned to another student without discussion.

---

# 14. If Push Fails

This usually means the remote repository has new commits.

Run:

```bash
git pull origin main
```

Then push again:

```bash
git push origin main
```

---

# 15. If Merge Conflict Occurs

Open the conflicted file.

You will see:

```
<<<<<<<
=======
>>>>>>>
```

Manually choose the correct content.

Then run:

```bash
git add .
git commit -m "[fix] resolve merge conflict"
git push origin main
```

---

# 16. Minimum Commands You Must Remember

If you only remember a few commands, remember these:

```bash
git pull origin main
git status
git add .
git commit -m "message"
git push origin main
```

---

# 17. Collaboration Rules

Students must follow these rules:

1. pull before starting work
2. push after finishing work
3. use clear commit messages
4. update dataset_registry.csv regularly
5. do not overwrite another student's work
6. record issues in dataset notes or QC logs

---

# 18. Summary

Daily workflow:

```
pull → work → add → commit → push
```

Clear commit messages and consistent workflow make collaboration much easier.
