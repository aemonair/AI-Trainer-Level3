# 执行日志与回溯审计使用指南

## 📋 功能概述

本系统现在支持**记录考试过程中的所有代码尝试**（包括错误的），并在阅卷时进行**回溯审计**，生成"过程罚分"和"稳定性指标"。

---

## 🚀 使用流程

### 1️⃣ 创建考试会话（自动生成日志文件）

```bash
uv run python3 scripts/create_timestamped_practice.py 1.1.1
```

输出示例：
```
Created: 1.1.1_practice_202608051430.ipynb
Manifest saved: 1.1.1_practice_202608051430_manifest.json
Execution log initialized: 1.1.1_practice_202608051430_execution_log.json
💡 在Jupyter第一个Cell中运行: %run scripts/execution_logger.py --init --log-path 1.1.1-materials/1.1.1_practice_202608051430_execution_log.json
```

### 2️⃣ 在Jupyter中启用日志记录

打开生成的练习文件，在**第一个Cell**中运行：

```python
%run scripts/execution_logger.py --init --log-path 1.1.1-materials/1.1.1_practice_202608051430_execution_log.json
```

这会：
- ✅ 初始化执行日志记录器
- ✅ 注册 `%%log_execution` magic命令（可选使用）
- ✅ 自动记录后续所有Cell的执行

### 3️⃣ 正常完成练习

像往常一样完成所有填空题，运行所有Cell。**所有执行过的代码都会被自动记录**，包括：
- 第一次尝试的错误代码
- 调试过程中的中间版本
- 最终的正确答案

### 4️⃣ 阅卷（启用回溯审计）

```bash
# 启用回溯审计
uv run python3 scripts/validate_practice.py --file 1.1.1-materials/1.1.1_practice_202608051430.ipynb --audit-process

# 或使用Session模式
uv run python3 scripts/validate_practice.py --session sessions/2026-08-05-1430-chapter1.1.1 --audit-process
```

输出示例：
```
🔍 启用回溯审计: 1.1.1_practice_202608051430_execution_log.json
   ⚠️ 过程罚分: -5分 (检测到3次错误尝试)

📊 练习验证报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 章节: 1.1.1
📄 文件: 1.1.1_practice_202608051430.ipynb
💯 得分: 92/100 (原始分97，过程罚分-5)
```

### 5️⃣ 查看成绩统计（含稳定性指标）

```bash
uv run python3 scripts/aggregate_reviews.py
```

输出示例：
```
📊 成绩中心摘要
============================================================
考试次数: 15
平均分: 82.5
最高分: 96
最低分: 65
通过率: 73.3%

🎯 稳定性指标:
  平均稳定性得分: 78.5/100
  平均过程罚分: 4.2分
  平均错误尝试: 2.8次

成绩趋势: 72 → 74 → 79 → 81 → 85 → 89 → 91
```

---

## 📊 回溯审计规则

### 过程罚分计算

| 错误严重程度 | 每次扣分 | 示例 |
|------------|---------|------|
| **High**（语法错误） | -3分 | `SyntaxError`, `NameError` |
| **Medium**（运行时错误） | -2分 | `TypeError`, `ValueError` |
| **Low**（逻辑错误） | -1分 | 无明显报错但结果不对 |

**最多扣20分**（避免过度惩罚）

### 稳定性得分计算

```
稳定性得分 = 100 - (错误尝试次数 / 总尝试次数 × 100)
```

- **90-100分**: ✅ 稳定发挥（考试时不易紧张）
- **70-89分**: 🟡 中等稳定（偶尔会犯小错）
- **0-69分**: ⚠️ 波动较大（需要加强熟练度）

---

## 🔧 高级用法

### 手动记录特定Cell

在Jupyter中，可以使用 `%%log_execution` magic命令：

```python
%%log_execution
# 这个Cell的执行会被详细记录
data = pd.read_csv("data.csv")
data.head()
```

### 查看执行日志

```python
import json
from pathlib import Path

log_path = Path("1.1.1-materials/1.1.1_practice_202608051430_execution_log.json")
with open(log_path, 'r', encoding='utf-8') as f:
    log_data = json.load(f)

print(f"总执行次数: {log_data['total_executions']}")
for entry in log_data['entries']:
    if entry.get('error'):
        print(f"❌ Cell {entry['cell_index']}: {entry['error']}")
```

### 单独运行审计工具

```bash
uv run python3 scripts/process_auditor.py \
  --log 1.1.1-materials/1.1.1_practice_202608051430_execution_log.json \
  --practice 1.1.1-materials/1.1.1_practice_202608051430.ipynb \
  --answer answers/1.1.1\ -\ 4.2.5参考答案/1.1.1/1.1.1.ipynb
```

---

## 📁 文件结构

```
1.1.1-materials/
├── 1.1.1.ipynb                              # 模板文件
├── 1.1.1_practice_202608051430.ipynb        # 练习文件（最终答案）
├── 1.1.1_practice_202608051430_manifest.json # 元数据
├── 1.1.1_practice_202608051430_execution_log.json # 执行日志（所有尝试）
└── 1.1.1_practice_202608051430_result.json   # 阅卷结果（含process_audit）
```

---

## ⚠️ 注意事项

1. **日志文件是追加模式**：如果多次运行同一个练习文件，日志会累积
2. **不区分Cell ID**：通过Cell索引匹配，确保不要删除或重排Cell
3. **不影响最终得分逻辑**：过程罚分是额外扣分，不影响原有的填空/实现/结果对比
4. **可选功能**：如果不启用 `--audit-process`，完全不影响现有阅卷流程

---

## 🎯 实际应用场景

### 场景1：识别"虽然做对但过程很挣扎"的题目

```
题目P-02: 
  最终得分: 100/100 ✅
  过程罚分: -8分
  错误尝试: 4次
  稳定性: 60/100 ⚠️
  
结论：虽然最终做对了，但考试时浪费了时间，需要加强熟练度
```

### 场景2：错题本升级

原来的错题本只记录"最终做错的题"，现在可以额外记录：
- "虽然做对但过程很挣扎的题"
- "第一次就一次通过的题"（稳定性100分）

### 场景3：进步趋势分析

```
章节1.1.1练习历史：
  第1次: 72分 (稳定性65，错误5次)
  第2次: 85分 (稳定性78，错误3次)
  第3次: 92分 (稳定性88，错误1次)
  
结论：不仅分数提高，稳定性也在提升！
```