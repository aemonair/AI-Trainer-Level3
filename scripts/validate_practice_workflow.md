# AI训练师考试平台 - 完整使用指南

## 📋 系统架构

```
sessions/
└── 2026-08-05-1430-chapter1.1.1/
    ├── practice.ipynb      # 考生的答卷
    ├── metadata.json       # 会话元数据（开始时间、状态等）
    ├── report.json         # validate_practice.py 生成的评分报告
    └── summary.md          # exam_review.py 生成的考试分析
```

## 🔄 完整考试流程

### 阶段1：创建考试会话

```bash
# 创建新的考试会话
uv run python3 scripts/create_timestamped_practice.py 1.1.1

# 输出：
# Created session: 2026-08-05-1430-chapter1.1.1
# Practice notebook: sessions/2026-08-05-1430-chapter1.1.1/practice.ipynb
# Metadata saved: sessions/2026-08-05-1430-chapter1.1.1/metadata.json
```

### 阶段2：完成练习

在 Jupyter 中打开 `sessions/2026-08-05-1430-chapter1.1.1/practice.ipynb`，完成所有填空。

### 阶段3：自动阅卷

```bash
# 方式1：使用Session ID（推荐）
uv run python3 scripts/validate_practice.py --session sessions/2026-08-05-1430-chapter1.1.1

# 方式2：使用文件路径（兼容旧模式）
uv run python3 scripts/validate_practice.py --file sessions/2026-08-05-1430-chapter1.1.1/practice.ipynb

# 方式3：验证所有章节
uv run python3 scripts/validate_practice.py --latest

# 输出：
# 📊 练习验证报告
# ────────────────────────────────────────────────────────────────────────────────
# 📁 章节: 1.1.1
# 📄 文件: practice.ipynb
# 💯 得分: 85/100
# ...
# JSON报告已保存: sessions/2026-08-05-1430-chapter1.1.1/report.json
```

### 阶段4：生成考试分析报告

```bash
# 分析指定Session
uv run python3 scripts/exam_review.py --session 2026-08-05-1430-chapter1.1.1

# 分析最新的Session
uv run python3 scripts/exam_review.py --latest

# 分析特定章节的最新Session
uv run python3 scripts/exam_review.py --chapter 1.1.1

# 输出：
# 📋 考试分析报告
# ==================
# 章节: 1.1.1
# 得分: 85/100
# 目标分数: 90
# 差距: -5 ❌
# ...
```

### 阶段5：成绩中心统计

```bash
# 生成综合成绩报告
uv run python3 scripts/aggregate_reviews.py

# 只统计特定章节
uv run python3 scripts/aggregate_reviews.py --chapter 1.1.1

# 输出JSON格式
uv run python3 scripts/aggregate_reviews.py --format json

# 输出CSV格式
uv run python3 scripts/aggregate_reviews.py --format csv

# 输出：
# 📊 成绩中心摘要
# ============================================================
# 考试次数: 15
# 平均分: 82.5
# 最高分: 96
# 最低分: 65
# 通过率: 73.3%
# 
# 成绩趋势: 72 → 74 → 79 → 81 → 85 → 89 → 91
# 
# 高频错题:
#   1. Pandas.填空错误 - 错误5次
#   2. Pandas.输出不匹配 - 错误3次
```

## 📊 脚本职责说明

| 脚本 | 核心职责 | 输入 | 输出 |
|------|---------|------|------|
| `create_timestamped_practice.py` | 创建考试会话 | 章节号 | Session目录 + practice.ipynb |
| `validate_practice.py` | **自动阅卷** | practice.ipynb | report.json（结构化评分） |
| `exam_review.py` | 考试分析报告 | report.json | summary.md（面向考生） |
| `aggregate_reviews.py` | **成绩中心** | 所有report.json | 统计报告（趋势/知识点/错题） |

## 🎯 核心功能

### 1. 结构化JSON评分报告

`validate_practice.py` 输出的 `report.json` 包含：

```json
{
  "session_id": "2026-08-05-1430-chapter1.1.1",
  "chapter": "1.1.1",
  "score": 85,
  "total_score": 100,
  "start_time": "2026-08-05T14:30:00",
  "end_time": "2026-08-05T15:15:00",
  "duration_minutes": 45,
  "errors": [
    {
      "type": "fill_incorrect",
      "knowledge_point": "Pandas",
      "topic": "fillna",
      "deduction": 8,
      "count": 1,
      "details": [...]
    }
  ],
  "warnings": [...]
}
```

### 2. 知识点分类

系统自动将错误分类到知识点：

- **Python基础**：1.1, 1.2章节
- **Pandas**：2.1, 2.2章节
- **数据清洗**：2.3章节
- **NumPy**：3.1, 3.2章节
- **数据可视化**：4.1, 4.2章节

### 3. 成绩趋势分析

`aggregate_reviews.py` 提供：

- 最近10次成绩趋势
- 平均分、最高分、最低分
- 通过率统计
- 知识点掌握度排名
- 高频错题统计

### 4. 考试分析报告

`exam_review.py` 生成：

- 本次考试概况（得分、耗时、目标差距）
- 主要失分点（按扣分排序）
- 学习建议（按知识点优先级）
- 进步趋势（同一章节多次练习对比）

## 🚀 日常练习流程

```bash
# 1. 创建考试会话
uv run python3 scripts/create_timestamped_practice.py 1.1.1

# 2. 在Jupyter中完成练习

# 3. 自动阅卷
uv run python3 scripts/validate_practice.py --session sessions/2026-08-05-1430-chapter1.1.1

# 4. 查看考试分析
uv run python3 scripts/exam_review.py --latest

# 5. 查看成绩统计
uv run python3 scripts/aggregate_reviews.py
```

## 📈 阶段性复习

```bash
# 查看所有章节的最新版本
uv run python3 scripts/validate_practice.py --latest

# 查看特定章节的所有版本（看进步）
uv run python3 scripts/validate_practice.py --chapter 1.1.1 --all-versions

# 生成完整成绩报告
uv run python3 scripts/aggregate_reviews.py --format markdown
```

## 🔧 兼容旧模式

如果需要使用旧模式（在materials目录创建练习文件）：

```bash
uv run python3 scripts/create_timestamped_practice.py 1.1.1 --legacy
```

## 💡 最佳实践

1. **每次练习都创建新的Session**：这样可以跟踪历史进步
2. **定期运行aggregate_reviews.py**：查看成绩趋势和知识点掌握度
3. **关注exam_review.py的建议**：优先复习错误率高的知识点
4. **一题多练**：同一章节多次练习，观察进步趋势

## 📝 文件说明

- `session_manager.py`：Session管理核心模块
- `validate_practice.py`：自动阅卷器（核心）
- `aggregate_reviews.py`：成绩中心
- `exam_review.py`：考试分析报告生成器
- `create_timestamped_practice.py`：创建考试会话