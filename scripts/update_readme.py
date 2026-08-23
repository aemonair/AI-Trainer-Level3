#!/usr/bin/env python3
"""
自动更新 README.md - 从 session 数据和已知评分结果生成详细练习报告
包含：练习时间、耗时、错误记录、注意事项、历史错误
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
SESSIONS_DIR = BASE_DIR / "sessions"
README_PATH = BASE_DIR / "README.md"


def parse_session_dir(dir_name):
    """解析 session 目录名获取章节号和时间戳"""
    match = re.match(r'(\d{8}_\d{6})_\w+_chapter(\d+\.\d+\.\d+)', dir_name)
    if match:
        timestamp_str = match.group(1)
        chapter = match.group(2)
        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        return chapter, timestamp
    return None, None


# 已知评分数据（从对话中记录）
KNOWN_SCORES = {
    '1.1.1': {'score': 22, 'max': 22, 'errors': 6, 'time': '17:23', 'duration': '8.2分钟',
              'key_errors': ['np.cut → np.where', 'pd.where → np.where', 'pd.split → pd.cut']},
    '1.1.2': {'score': 34, 'max': 34, 'errors': 5, 'time': '17:34', 'duration': '11.5分钟',
              'key_errors': ['agg avg → mean', 'groupby括号嵌套', 'isin需要列表']},
    '1.1.3': {'score': 13, 'max': 13, 'errors': 0, 'time': '17:47', 'duration': '1.3分钟',
              'key_errors': []},
    '1.1.4': {'score': 27, 'max': 27, 'errors': 1, 'time': '17:51', 'duration': '3.5分钟',
              'key_errors': ['groupby[] → groupby()']},
    '1.1.5': {'score': 40, 'max': 40, 'errors': 0, 'time': '17:56', 'duration': '4.4分钟',
              'key_errors': []},
    '2.1.1': {'score': 20, 'max': 20, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.1.2': {'score': 15, 'max': 15, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.1.3': {'score': 17, 'max': 17, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.1.4': {'score': 19, 'max': 19, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.1.5': {'score': 16, 'max': 16, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.2.1': {'score': 13, 'max': 13, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.2.2': {'score': 21, 'max': 21, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.2.3': {'score': 23, 'max': 23, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.2.4': {'score': 24, 'max': 24, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '2.2.5': {'score': 17, 'max': 17, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '3.2.1': {'score': 16, 'max': 16, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '3.2.2': {'score': 17, 'max': 17, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
    '3.2.3': {'score': 17, 'max': 17, 'errors': 2, 'time': '17:07', 'duration': '6.5分钟',
              'key_errors': ['InferenceSessioin拼写', 'dict.keys()索引→list转换']},
    '3.2.4': {'score': 15, 'max': 15, 'errors': 2, 'time': '17:12', 'duration': '2.5分钟',
              'key_errors': ['list(labels)→np.argmax', 'accuracy[0]→accuracy[0][idx]*100']},
    '3.2.5': {'score': 17, 'max': 17, 'errors': 0, 'time': '-', 'duration': '-', 'key_errors': []},
}

CHAPTER_INFO = {
    '1.1.1': '智能医疗系统中的业务数据处理流程设计',
    '1.1.2': '智能农业系统中的业务数据采集和处理流程设计',
    '1.1.3': '金融机构信用评估系统中的业务数据审核流程设计',
    '1.1.4': '电商平台用户行为分析系统的数据采集与处理流程设计',
    '1.1.5': '智能交通系统的数据采集、处理和审核流程设计',
    '2.1.1': '智慧交通中燃油效率模型的数据清洗和标注流程设计',
    '2.1.2': '低碳生活行为影响因素数据清洗和标注流程设计',
    '2.1.3': '信用评分模型数据清洗和标注流程设计',
    '2.1.4': '医疗研究数据清洗和标注设计',
    '2.1.5': '健康与营养咨询数据预处理与数据规范设计',
    '2.2.1': '智能信用评分Logistic回归模型开发与测试',
    '2.2.2': '智慧交通中燃油效率随机森林模型开发与测试',
    '2.2.3': '日常运动量随机森林预测模型开发与测试',
    '2.2.4': '低碳生活行为影响因素预测线性回归模型开发与测试',
    '2.2.5': '智能步数预测模型开发与测试',
    '3.2.1': '手写数字识别',
    '3.2.2': '手写数字识别系统',
    '3.2.3': '面部表情识别',
    '3.2.4': '花朵智能识别',
    '3.2.5': '智能医疗影像分类',
}


def generate_detailed_readme():
    """生成详细版 README"""
    chapters = list(KNOWN_SCORES.keys())
    
    total_score = sum(v['score'] for v in KNOWN_SCORES.values())
    total_max = sum(v['max'] for v in KNOWN_SCORES.values())
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    content = f"""# 人工智能训练师（三级）练习题库

## 📊 练习进度总览

| 章节 | 已完成 | 满分 | 总计 |
|------|--------|------|------|
| 1.1.x | 5/5 ✅ | 136/136 | 5 |
| 2.1.x | 5/5 ✅ | 87/87 | 5 |
| 2.2.x | 5/5 ✅ | 98/98 | 5 |
| 3.2.x | 5/5 ✅ | 82/82 | 5 |
| **总计** | **20/20** | **{total_score}/{total_max} (100%)** | **20** |

> 📅 最后更新：{now} | 🏆 全部满分通过！

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
.venv\\Scripts\\activate           # Windows

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
| `update_readme.py` | 自动更新README（本脚本） |

## 🌿 分支策略

| 分支 | 内容 | 用途 |
|------|------|------|
| `main` | 生产代码（脚本+Review+答案） | 发布版本，不含sessions |
| `practice` | 完整工作区（含840个session文件） | 日常练习 |
| `archive-scripts` | 临时调试脚本归档 | 保留以防有用 |

## 📊 详细练习记录

### 1.1 数据处理基础

| 章节 | 题目 | 练习时间 | 耗时 | 分数 | 错误数 | 关键错误/注意事项 |
|------|------|---------|------|------|--------|------------------|
"""
    
    for ch in chapters:
        if not ch.startswith('1.1'):
            continue
        info = KNOWN_SCORES[ch]
        errors_str = f"{info['errors']}次" if info['errors'] > 0 else "0"
        notes_str = '；'.join(info['key_errors']) if info['key_errors'] else "一次通过"
        content += f"| {ch} | {CHAPTER_INFO[ch]} | {info['time']} | {info['duration']} | {info['score']}/{info['max']} | {errors_str} | {notes_str} |\n"
    
    content += """
### 2.1 数据清洗和标注

| 章节 | 题目 | 练习时间 | 耗时 | 分数 | 错误数 | 关键错误/注意事项 |
|------|------|---------|------|------|--------|------------------|
"""
    
    for ch in chapters:
        if not ch.startswith('2.1'):
            continue
        info = KNOWN_SCORES[ch]
        errors_str = f"{info['errors']}次" if info['errors'] > 0 else "0"
        notes_str = '；'.join(info['key_errors']) if info['key_errors'] else "一次通过"
        content += f"| {ch} | {CHAPTER_INFO[ch]} | {info['time']} | {info['duration']} | {info['score']}/{info['max']} | {errors_str} | {notes_str} |\n"
    
    content += """
### 2.2 模型开发

| 章节 | 题目 | 练习时间 | 耗时 | 分数 | 错误数 | 关键错误/注意事项 |
|------|------|---------|------|------|--------|------------------|
"""
    
    for ch in chapters:
        if not ch.startswith('2.2'):
            continue
        info = KNOWN_SCORES[ch]
        errors_str = f"{info['errors']}次" if info['errors'] > 0 else "0"
        notes_str = '；'.join(info['key_errors']) if info['key_errors'] else "一次通过"
        content += f"| {ch} | {CHAPTER_INFO[ch]} | {info['time']} | {info['duration']} | {info['score']}/{info['max']} | {errors_str} | {notes_str} |\n"
    
    content += """
### 3.2 图像识别

| 章节 | 题目 | 练习时间 | 耗时 | 分数 | 错误数 | 关键错误/注意事项 |
|------|------|---------|------|------|--------|------------------|
"""
    
    for ch in chapters:
        if not ch.startswith('3.2'):
            continue
        info = KNOWN_SCORES[ch]
        errors_str = f"{info['errors']}次" if info['errors'] > 0 else "0"
        notes_str = '；'.join(info['key_errors']) if info['key_errors'] else "一次通过"
        content += f"| {ch} | {CHAPTER_INFO[ch]} | {info['time']} | {info['duration']} | {info['score']}/{info['max']} | {errors_str} | {notes_str} |\n"
    
    content += """
## 📝 状态说明

| 状态 | 说明 |
|------|------|
| ✅ | 已完成练习（满分） |
| ⏳ | 待练习 |
| ❌ | 练习中有错误（见Review文件） |

## 📖 常见错误速查

### numpy/pandas 函数混淆

| 错误写法 | 正确写法 | 说明 | 出现章节 |
|---------|---------|------|---------|
| `np.cut(条件, 'A', 'B')` | `np.where(条件, 'A', 'B')` | `np.cut` 用于区间划分 | 1.1.1 |
| `pd.cut(条件, 'A', 'B')` | `np.where(条件, 'A', 'B')` | `pd.cut` 用于区间划分 | 1.1.1 |
| `pd.where(...)` | `np.where(...)` | pandas 没有 where 函数 | 1.1.1 |
| `pd.split(...)` | `pd.cut(...)` | pandas 没有 split 函数 | 1.1.1 |
| `pd.range(...)` | `pd.cut(...)` | pandas 没有 range 函数 | 1.1.1 |
| `np.clip(...)` | `pd.cut(...)` | `np.clip` 是裁剪值范围 | 1.1.1 |

### groupby 语法

| 错误写法 | 正确写法 | 说明 | 出现章节 |
|---------|---------|------|---------|
| `data.groupby['列']` | `data.groupby('列')` | groupby 是方法调用，用圆括号 | 1.1.4 |
| `.agg('count', 'avg')` | `.agg(['count', 'mean'])` | 需要列表，且用 mean 不是 avg | 1.1.2 |
| `isin('A','B')` | `isin(['A','B'])` | isin 需要列表参数 | 1.1.2 |

### 字典操作

| 错误写法 | 正确写法 | 说明 | 出现章节 |
|---------|---------|------|---------|
| `dict.keys()[0]` | `list(dict.keys())[0]` | Python 3 中 dict.keys() 返回 view，不支持索引 | 3.2.3 |
| `dict.get_keys()` | `dict.keys()` | dict 没有 get_keys 方法 | 3.2.3 |

### ONNX 推理

| 错误写法 | 正确写法 | 说明 | 出现章节 |
|---------|---------|------|---------|
| `ort.InferenceSessioin(...)` | `ort.InferenceSession(...)` | 拼写错误 | 3.2.3 |
| `np.argmax(accuracy)` | `np.argmax(accuracy[0])` | 需要取第一个元素 | 3.2.4 |
| `accuracy[0]` | `accuracy[0][idx] * 100` | 需要取出对应概率并转百分比 | 3.2.4 |

### 模型参数

| 错误写法 | 正确写法 | 说明 | 出现章节 |
|---------|---------|------|---------|
| `XGBRegressor(max_iter=1000)` | `XGBRegressor(n_estimators=1000)` | XGBoost 用 n_estimators | 2.2.4 |
| `fillna('bfill')` | `fillna(method='bfill')` | 需要 method 参数 | 2.1.4 |

## 📈 练习统计

### 最难章节（迭代最多）

| 章节 | 迭代次数 | 耗时 | 主要错误 |
|------|---------|------|---------|
| 1.1.2 | 17次 | 11.5分钟 | groupby括号嵌套、agg函数名 |
| 1.1.1 | 11次 | 8.2分钟 | np.where vs np.cut 混淆 |
| 3.2.3 | 7次 | 6.5分钟 | dict.keys()索引访问 |
| 3.2.4 | 2次 | 2.5分钟 | np.argmax、概率百分比 |

### 最顺利章节

| 章节 | 迭代次数 | 耗时 | 状态 |
|------|---------|------|------|
| 1.1.5 | 3次 | 4.4分钟 | 一次通过 |
| 1.1.3 | 4次 | 1.3分钟 | 一次通过 |
| 1.1.4 | 4次 | 3.5分钟 | 仅1次括号错误 |
"""
    
    return content


if __name__ == '__main__':
    content = generate_detailed_readme()
    README_PATH.write_text(content)
    print(f"✅ README.md 已更新！")
    print(f"📅 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")