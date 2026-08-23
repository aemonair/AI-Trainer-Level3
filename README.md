# 人工智能训练师（三级）练习题库

## 📊 练习进度总览

| 章节 | 已完成 | 满分 | 总计 |
|------|--------|------|------|
| 1.1.x | 5/5 ✅ | 106/106 | 5 |
| 2.1.x | 5/5 ✅ | 87/87 | 5 |
| 2.2.x | 5/5 ✅ | 98/98 | 5 |
| 3.2.x | 5/5 ✅ | 82/82 | 5 |
| **总计** | **20/20** | **373/373 (100%)** | **20** |

> 📅 最后更新：2026-08-23 | 🏆 全部满分通过！

---

## 📁 项目结构

```
├── sessions/                    # 练习Session（practice分支）
│   ├── 20260823_172344_f599a5_chapter1.1.1/
│   │   └── workspace/
│   │       ├── practice.ipynb   # 练习文件
│   │       ├── scoring_report.md  # 评分报告
│   │       └── *_review.md      # 错误复盘（仅错误时生成）
│   └── ...
├── scripts/                     # 自动化脚本
├── reports/                     # 聚合报告
├── answers/                     # 官方参考答案
└── questions/                   # 题目文件
```

## 🚀 环境搭建

### 1. 安装 uv
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 克隆仓库并创建环境
```bash
git clone <仓库地址>
cd 人工智能训练师_3级_sucai

# 创建虚拟环境
uv venv

# 激活环境
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 安装依赖（自动适配当前平台）
uv pip install . --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

> **跨平台说明**：`pyproject.toml` 已配置平台特定的依赖版本，uv 会自动根据当前系统（Windows/macOS ARM64/macOS Intel/Linux）选择合适的包版本。

### 3. 验证环境
```bash
python -c "import pandas, sklearn, onnx; print('环境安装成功！')"
```

## 📝 练习流程

### 完整练习示例

```bash
# 1. 创建练习文件
uv run python3 scripts/create_timestamped_practice.py 2.1.1
# 输出：sessions/20260823_172344_f599a5_chapter2.1.1/workspace/practice.ipynb

# 2. 在Jupyter中完成练习
jupyter notebook sessions/20260823_172344_f599a5_chapter2.1.1/workspace/practice.ipynb

# 3. 评分
uv run python3 scripts/scoring_validator.py sessions/20260823_172344_f599a5_chapter2.1.1/workspace/practice.ipynb
# 输出：scoring_report.md, scoring_result_v2_exam.json

# 4. 如果有错误，生成Review文件
# （脚本会自动检测错误并生成 *_review.md）

# 5. 生成聚合报告
uv run python3 scripts/review_summary.py          # Review摘要
uv run python3 scripts/aggregate_reviews.py        # 成绩统计
uv run python3 scripts/analyze_practice_process.py --date 20260823  # 练习过程分析
```

### 创建练习文件
```bash
uv run python3 scripts/create_timestamped_practice.py <章节号>
# 例如：uv run python3 scripts/create_timestamped_practice.py 2.1.1
```

### 评分
```bash
uv run python3 scripts/scoring_validator.py <session目录>/workspace/practice.ipynb
# 例如：uv run python3 scripts/scoring_validator.py sessions/20260823_172344_f599a5_chapter2.1.1/workspace/practice.ipynb
```

### 生成聚合报告
```bash
# 从 *_review.md 文件生成Review摘要
uv run python3 scripts/review_summary.py

# 从 session report.json 生成成绩统计
uv run python3 scripts/aggregate_reviews.py

# 分析练习过程和耗时
uv run python3 scripts/analyze_practice_process.py --date 20260823
```

## 🔧 可用脚本

| 脚本 | 功能 |
|------|------|
| `create_timestamped_practice.py` | 创建带时间戳的练习文件 |
| `scoring_validator.py` | AST模式评分脚本 |
| `aggregate_reviews.py` | 成绩中心，从report.json生成统计分析 |
| `review_summary.py` | 聚合所有Review文件生成摘要报告 |
| `analyze_practice_process.py` | 分析练习耗时和迭代过程 |
| `analyze_weak_points.py` | 薄弱点分析 |
| `practice_logger.py` | 练习日志记录 |
| `generate_report_json.py` | 生成JSON报告 |
| `rename_materials.sh` | 批量重命名目录和文件 |

## 🌿 分支策略

| 分支 | 内容 | 用途 |
|------|------|------|
| `main` | 生产代码（脚本+Review+答案） | 发布版本，不含sessions |
| `practice` | 完整工作区（含840个session文件） | 日常练习 |
| `archive-scripts` | 临时调试脚本归档 | 保留以防有用 |

## 📊 练习统计

### 今日练习（2026-08-23）

| 章节 | 分数 | 迭代次数 | 耗时 | 状态 |
|------|------|---------|------|------|
| 1.1.1 | 22/22 | 11次 | 8.2分钟 | ✅ |
| 1.1.2 | 34/34 | 17次 | 11.5分钟 | ✅ |
| 1.1.3 | 13/13 | 4次 | 1.3分钟 | ✅ |
| 1.1.4 | 27/27 | 4次 | 3.5分钟 | ✅ |
| 1.1.5 | 40/40 | 3次 | 4.4分钟 | ✅ |
| 2.1.1 | 20/20 | - | - | ✅ |
| 2.1.2 | 15/15 | - | - | ✅ |
| 2.1.3 | 17/17 | - | - | ✅ |
| 2.1.4 | 19/19 | - | - | ✅ |
| 2.1.5 | 16/16 | - | - | ✅ |
| 2.2.1 | 13/13 | - | - | ✅ |
| 2.2.2 | 21/21 | - | - | ✅ |
| 2.2.3 | 23/23 | - | - | ✅ |
| 2.2.4 | 24/24 | - | - | ✅ |
| 2.2.5 | 17/17 | - | - | ✅ |
| 3.2.1 | 16/16 | - | - | ✅ |
| 3.2.2 | 17/17 | - | - | ✅ |
| 3.2.3 | 17/17 | 7次 | 6.5分钟 | ✅ |
| 3.2.4 | 15/15 | 2次 | 2.5分钟 | ✅ |
| 3.2.5 | 17/17 | - | - | ✅ |

### 最难章节（迭代最多）

| 章节 | 迭代次数 | 主要错误 |
|------|---------|---------|
| 1.1.2 | 17次 | groupby括号嵌套、agg函数名 |
| 1.1.1 | 11次 | np.where vs np.cut 混淆 |
| 3.2.3 | 7次 | dict.keys()索引访问 |

## 📝 状态说明

| 状态 | 说明 |
|------|------|
| ✅ | 已完成练习（满分） |
| ⏳ | 待练习 |
| ❌ | 练习中有错误（见Review文件） |