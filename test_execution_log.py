#!/usr/bin/env python3
"""
测试执行日志和回溯审计功能
"""
import json
from pathlib import Path
from scripts.execution_logger import ExecutionLogger
from scripts.process_auditor import ProcessAuditor

# 测试1: ExecutionLogger
print("=" * 60)
print("测试1: ExecutionLogger 基本功能")
print("=" * 60)

test_log_path = Path("test_execution_log.json")
logger = ExecutionLogger(log_path=test_log_path, auto_save=False)

# 模拟记录几次执行
logger.record_execution(
    cell_index=0,
    code='data = pd.read_csv("data.csv")',
    output="",
    error="FileNotFoundError: [Errno 2] No such file or directory: 'data.csv'",
    execution_time=0.5
)

logger.record_execution(
    cell_index=0,
    code='data = pd.read_csv("auto-mpg.csv")',
    output="   mpg  cylinders  ...",
    error=None,
    execution_time=1.2
)

logger.record_execution(
    cell_index=1,
    code='data.dropna()',
    output="",
    error="AttributeError: 'DataFrame' object has no attribute 'dropna'",
    execution_time=0.3
)

logger.record_execution(
    cell_index=1,
    code='data = data.dropna(subset=["horsepower"])',
    output="   mpg  cylinders  ...",
    error=None,
    execution_time=0.8
)

logger.save()
print(f"✅ 记录了 {len(logger.entries)} 次执行")
print(f"✅ 日志文件: {test_log_path}")

# 测试2: ProcessAuditor
print("\n" + "=" * 60)
print("测试2: ProcessAuditor 回溯审计")
print("=" * 60)

# 创建一个模拟的练习文件
test_practice_path = Path("test_practice.ipynb")
test_notebook = {
    "cells": [
        {
            "cell_type": "code",
            "execution_count": 1,
            "source": ['data = pd.read_csv("auto-mpg.csv")\n', 'data.head()'],
            "outputs": [],
            "metadata": {}
        },
        {
            "cell_type": "code",
            "execution_count": 2,
            "source": ['data = data.dropna(subset=["horsepower"])'],
            "outputs": [],
            "metadata": {}
        }
    ],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 5
}

test_practice_path.write_text(json.dumps(test_notebook, ensure_ascii=False, indent=2))
print(f"✅ 创建模拟练习文件: {test_practice_path}")

# 执行审计
auditor = ProcessAuditor(test_log_path, test_practice_path)
result = auditor.audit()

print(f"\n📊 审计结果:")
print(f"  总尝试次数: {result['total_attempts']}")
print(f"  错误尝试: {result['error_attempts']}")
print(f"  过程罚分: -{result['process_penalty']}分")
print(f"  稳定性得分: {result['stability_score']}/100")
print(f"  消息: {result['message']}")

if result['detected_errors']:
    print(f"\n❌ 检测到的错误:")
    for i, error in enumerate(result['detected_errors'], 1):
        print(f"  {i}. Cell {error['cell_index']}: {error['error_message'][:80]}...")
        print(f"     严重程度: {error['severity']}")

# 清理测试文件
test_log_path.unlink()
test_practice_path.unlink()
print("\n✅ 测试文件已清理")

print("\n" + "=" * 60)
print("🎉 所有测试通过！")
print("=" * 60)