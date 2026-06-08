#!/bin/bash

# 自动提交并推送到 GitHub

# 获取当前时间
TIME=$(date "+%Y-%m-%d %H:%M:%S")

# 如果没有输入 commit message，则使用默认
MSG=${1:-"Auto update: $TIME"}

echo "--------------------------------"
echo "Git Auto Push Script"
echo "Commit message: $MSG"
echo "--------------------------------"

# 添加所有文件
git add .

# 提交
git commit -m "$MSG"

# 推送
git push origin main

echo "--------------------------------"
echo "Push completed"
echo "--------------------------------"
