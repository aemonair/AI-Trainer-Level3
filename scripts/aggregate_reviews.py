#!/usr/bin/env python3
"""
聚合仓库中所有 `*_review.md` 文件为 CSV 和 Markdown 报告。
用法: 在仓库根目录运行 `python3 scripts/aggregate_reviews.py`
"""
from pathlib import Path
import csv
import re

ROOT = Path('.').resolve()
rows = []
for md in ROOT.rglob('*_review.md'):
    rel = md.relative_to(ROOT)
    notebook = md.stem  # 使用文件名（不含扩展名）
    text = md.read_text(encoding='utf-8')
    
    # 解析Review文件（支持新旧两种格式）
    # 1. 提取日期（从标题中）
    date_match = (
        re.search(r'# .+ Review - (\d{4}-\d{2}-\d{2})', text) or  # 格式：2026-08-01 16:59
        re.search(r'# .+ Review - (\d{12})', text) or              # 格式：202608011659
        re.search(r'# .+ review \((\d{12})\)', text)               # 格式：(202608011659)
    )
    if date_match:
        raw_date = date_match.group(1)
        if '-' in raw_date:
            date = raw_date  # 已经是 YYYY-MM-DD 格式
        else:
            date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    else:
        date = ''
    
    # 2. 提取错误（支持新旧两种格式）
    errors = []
    # 新格式：### 错误1：...（带bullet points）
    new_errors = re.findall(r'### (错误\d+：.+?)\n', text)
    if new_errors:
        for err in new_errors:
            errors.append(err.strip())
    else:
        # 旧格式：#### 错误1：...（带代码块）
        error_blocks = re.findall(r'#### (错误\d+：.+?)\n```python\n(.*?)```\n.*?正确写法.*?```python\n(.*?)```', text, re.DOTALL)
        for err_name, wrong_code, right_code in error_blocks:
            errors.append(f"{err_name.strip()}: {wrong_code.strip()} → {right_code.strip()}")
    
    # 3. 提取评分（从表格中）
    score_match = re.search(r'\|\s*\*\*总计\*\*\s*\|\s*\*{0,2}(\d+(?:\.\d+)?)\*{0,2}\s*\|\s*\*{0,2}(\d+(?:\.\d+)?)\*{0,2}\s*\|\s*\*{0,2}([\d.]+)%.*?\|', text)
    if score_match:
        total = score_match.group(1)
        score_val = score_match.group(2)
        pct = score_match.group(3)
        score = f"{score_val}/{total} ({pct}%)"
    else:
        score = ''
    
    # 4. 统计任务完成情况（旧格式）或从评分表格提取（新格式）
    total_tasks_match = re.findall(r'### 任务\d+：', text)
    if total_tasks_match:
        total_tasks = len(total_tasks_match)
        completed_tasks = len(re.findall(r'### 任务\d+：.+? ✅', text))
        completed_str = f'{completed_tasks}/{total_tasks} 任务完成'
    elif score_match:
        # 新格式：从评分表格推断
        completed_str = f'{score_val}/{total} 得分'
    else:
        completed_tasks = 0
        total_tasks = 0
        completed_str = '未知'
    
    error_summary = '\n'.join(errors) if errors else '无错误'
    
    rows.append({
        'path': str(rel),
        'notebook': notebook,
        'date': date,
        'completed': completed_str,
        'errors': error_summary,
        'score': score,
    })

outdir = ROOT / 'reports'
outdir.mkdir(exist_ok=True)
csvfile = outdir / 'reviews_summary.csv'
mdfile = outdir / 'reviews_summary.md'
with csvfile.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['date','notebook','path','completed','errors','score'])
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k,'') for k in writer.fieldnames})

with mdfile.open('w', encoding='utf-8') as f:
    f.write('# 复盘聚合报告\n\n')
    f.write('| Date | Notebook | 完成情况 | 错误详情 | 评分 | Path |\n')
    f.write('|---|---|---|---|---|---|\n')
    for r in rows:
        errors_short = r['errors'].replace('\n', '<br>')[:100]
        f.write(f"| {r['date']} | {r['notebook']} | {r['completed']} | {errors_short} | {r['score']} | {r['path']} |\n")

print(f'Found {len(rows)} review file(s), wrote {csvfile} and {mdfile}')