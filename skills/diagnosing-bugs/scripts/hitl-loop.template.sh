#!/usr/bin/env bash
# HITL loop template（人介入循环模板）
# 当必须有人工点击才能触发 bug 时，用结构化脚本驱动"人"，
# 把捕获的输出回灌给 agent，使循环仍然结构化、可重复。
#
# 用法：把"触发 bug 的人工步骤"包成下面的函数，循环 N 次并捕获输出。
#       bash hitl-loop.template.sh 100
set -euo pipefail

RUNS="${1:-100}"   # 默认循环 100 次，抬高非确定 bug 的复现率

for i in $(seq 1 "$RUNS"); do
  echo "=== run $i ==="
  # TODO: 在这里调用会触发 bug 的人工步骤（或包装它的脚本）
  # 例如：node ./scripts/click-and-capture.js >> "run-$i.log" 2>&1
  # 捕获与 bug 症状相关的输出行，供 agent 分析
  :
done

echo "done: $RUNS runs captured"
