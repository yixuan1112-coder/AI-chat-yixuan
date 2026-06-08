# Git Usage Guide for Capstone Students

## Purpose

This document explains how to pull the latest updates from GitHub and push your own changes back to the shared repository:

`BatteryTwin-Benchmark-DataPrep`

This repository is jointly maintained by two capstone students. Please follow the workflow below to avoid overwriting each other's work.

---

## Where This Document Should Be Placed

Put this file under:

```text
docs/project_plan/student_git_guide.md
```

This location is appropriate because the file is a project collaboration and execution guide, rather than a dataset note or schema document.

---

## Basic Principle

The GitHub repository is the **remote repository**.  
The copy on the server is your **local working repository**.

That means:

- when someone updates files on GitHub, you need to **pull**
- when you modify files on the server, you need to **commit and push**

Do not assume the server directory updates automatically after changes are made on GitHub.

---

## Recommended Collaboration Rule

Before starting any work each day:

1. enter the repository directory
2. pull the latest version from GitHub
3. then start your own work

After finishing your work:

1. check changed files
2. commit your changes with a clear message
3. push to GitHub

This avoids most collaboration conflicts.

---

## Step 1: Enter the Repository

After connecting to the server, go to the repository directory:

```bash
cd ~/BatteryTwin-Benchmark-DataPrep
```

If your repository is stored elsewhere, use the actual path.

---

## Step 2: Pull the Latest Version from GitHub

Before editing anything, always run:

```bash
git pull origin main
```

This downloads the newest updates from GitHub to the server.

If the pull succeeds, you can start your work safely.

---

## Step 3: Check Your Current Status

At any time, you can check the repository status with:

```bash
git status
```

Typical meanings:

- `nothing to commit, working tree clean` means no local changes
- `modified:` means you changed some files but have not committed them yet
- `untracked files:` means new files were created but not added to Git yet

---

## Step 4: Add Your Changes

After you finish editing files, add them with:

```bash
git add .
```

This stages all changed files in the current repository.

If you only want to add one specific file, use:

```bash
git add path/to/file
```

Example:

```bash
git add dataset_registry.csv
git add docs/dataset_notes/dataset_01_note.md
```

---

## Step 5: Commit Your Changes

After `git add`, create a commit:

```bash
git commit -m "your message"
```

Use short and specific messages. Good examples:

```bash
git commit -m "Add metadata for dataset_01"
git commit -m "Update QC log for dataset_03"
git commit -m "Fix unit conversion in dataset_02"
git commit -m "Complete cycle summary for dataset_04"
```

Avoid vague messages such as:

```bash
git commit -m "update"
git commit -m "fix"
git commit -m "change files"
```

A clear commit message makes collaboration much easier.

---

## Step 6: Push Your Changes to GitHub

After committing, upload your changes to GitHub:

```bash
git push origin main
```

If the push succeeds, your changes are now visible on GitHub and available to others after they pull.

---

## Standard Daily Workflow

Please follow this order every time:

```bash
cd ~/BatteryTwin-Benchmark-DataPrep
git pull origin main
# do your work
git status
git add .
git commit -m "clear message"
git push origin main
```

This is the standard workflow for this project.

---

## Recommended Commit Scope

Try to keep each commit focused on one small task. For example:

- one dataset metadata update
- one QC log update
- one field-mapping fix
- one new script

Do not mix too many unrelated changes into one commit.

---

## What Each Student Should Modify

Each student should mainly update:

- the datasets assigned to them in `dataset_registry.csv`
- their own dataset notes in `docs/dataset_notes/`
- their own QC records in `docs/qc_reports/`
- the relevant processing scripts if needed

Do not modify another student's dataset outputs unless discussed with the supervisor.

---

## If GitHub Has New Files but the Server Does Not

This usually means the server has not pulled the latest changes yet.

Run:

```bash
git pull origin main
```

Again, the server does not update automatically just because files were uploaded through the GitHub webpage.

---

## If `git push` Fails

A push may fail because GitHub has newer commits that are not yet on the server.

In that case, run:

```bash
git pull origin main
```

Then resolve any conflict if Git asks you to, and push again:

```bash
git push origin main
```

---

## If `git pull` Reports a Conflict

This means both you and someone else changed the same file.

Typical files where this may happen:

- `dataset_registry.csv`
- shared scripts
- shared documentation

What to do:

1. open the conflicted file
2. find the conflict markers:
   - `<<<<<<<`
   - `=======`
   - `>>>>>>>`
3. manually keep the correct content
4. save the file
5. add and commit again

Commands after fixing:

```bash
git add .
git commit -m "Resolve merge conflict"
git push origin main
```

If you are unsure, stop and contact the supervisor before deleting any content.

---

## If You Want to Discard Local Changes

Use this only if you are sure your local edits are not needed.

Discard all uncommitted changes:

```bash
git reset --hard HEAD
```

Then pull again:

```bash
git pull origin main
```

Be careful. This will permanently remove local uncommitted edits.

---

## Automatic Push Script

If the repository already contains `git_push.sh`, you may also use:

```bash
./git_push.sh "your commit message"
```

Example:

```bash
./git_push.sh "Add metadata for dataset_01"
```

This script is only a shortcut. You still need to understand the normal Git workflow above.

---

## Good Collaboration Practice

Please follow these rules:

1. pull before starting work
2. push after finishing work
3. use clear commit messages
4. update `dataset_registry.csv` whenever dataset status changes
5. do not overwrite another student's work
6. record issues in the proper note or QC file
7. ask before modifying shared core scripts

---

## Minimal Commands to Remember

If you only remember four commands, remember these:

```bash
git pull origin main
git status
git add .
git commit -m "your message"
git push origin main
```

---

## Example

A complete example for one student:

```bash
cd ~/BatteryTwin-Benchmark-DataPrep
git pull origin main

# edit files
# for example:
# docs/dataset_notes/dataset_01_note.md
# dataset_registry.csv

git status
git add .
git commit -m "Update dataset_01 note and registry"
git push origin main
```

---

## Contact Rule

If any Git error message is unclear, do not repeatedly try random commands.

Instead:

1. copy the exact error message
2. send it to the supervisor
3. wait for confirmation before using destructive commands such as `reset --hard`

This is especially important for shared repositories.

---

## Summary

The project workflow is simple:

- before work: `pull`
- after work: `add`, `commit`, `push`

Use Git carefully and consistently. A clean workflow will save a large amount of time later during integration and final delivery.
