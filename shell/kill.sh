#!/bin/bash

# 检查是否提供了进程名称作为参数
PROCESS_NAME=""

if [ -z "$1" ]; then
    PROCESS_NAME="app.py"
else
    PROCESS_NAME=$1
fi

# 查找所有匹配的进程ID并强制终止
PIDS=$(pgrep -f "$PROCESS_NAME")

if [ -z "$PIDS" ]; then
    echo "No process found with name: $PROCESS_NAME"
else
    echo "Killing processes with name: $PROCESS_NAME"
    echo "$PIDS" | xargs kill -9
    echo "Processes terminated."
fi