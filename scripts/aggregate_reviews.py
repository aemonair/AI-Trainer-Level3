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
    notebook = rel.parent.name
    text = md.read_text(encoding='utf-8')
    
    # 解析新格式的Review文件
    # 1. 提取日期（从标题中）
    date_match = re.search(r'# .+ Review - (\d{4}-\d{2}-\d{2})', text)
    date = date_match.group(1) if date_match else ''
    
    # 2. 提取错误（从 ❌ 标记的任务中）
    errors = []
    error_blocks = re.findall(r'#### (错误\d+：.+?)\n```python\n(.*?)```\n.*?正确写法.*?```python\n(.*?)```', text, re.DOTALL)
    for err_name, wrong_code, right_code in error_blocks:
        errors.append(f"{err_name.strip()}: {wrong_code.strip()} → {right_code.strip()}")
    
    # 3. 提取评分（从表格中）
    score_match = re.search(r'\|\s*\*\*总计\*\*\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*([\d.]+)%', text)
    score = f"{score_match.group(1)}/{score_match.group(2)}%" if score_match else ''
    
    # 4. 统计任务完成情况
    total_tasks = len(re.findall(r'### 任务\d+：', text))
    completed_tasks = len(re.findall(r'### 任务\d+：.+? ✅', text))
    
    error_summary = '\n'.join(errors) if errors else '无错误'
    
    rows.append({
        'path': str(rel),
        'notebook': notebook,
        'date': date,
        'completed': f'{completed_tasks}/{total_tasks} 任务完成',
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