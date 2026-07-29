#!/usr/bin/env python3
"""
聚合仓库中所有 `复盘.md` 文件为 CSV 和 Markdown 报告。
用法: 在仓库根目录运行 `python3 scripts/aggregate_reviews.py`
"""
from pathlib import Path
import csv
import re

ROOT = Path('.').resolve()
rows = []
for md in ROOT.rglob('复盘.md'):
    rel = md.relative_to(ROOT)
    notebook = rel.parent.name
    text = md.read_text(encoding='utf-8')
    # 简单解析：查找行形如 "- 错误率：..." 等
    def extract(key):
        m = re.search(r"^[-*]\s*" + re.escape(key) + r"：\s*(.*)$", text, flags=re.MULTILINE)
        return m.group(1).strip() if m else ''
    date = extract('日期')
    completed = extract('今日完成内容') or extract('今日完成')
    errors = extract('错误点')
    error_rate = extract('错误率')
    fixed = extract('是否已解决')
    notes = ''
    # 如果无法解析关键字段，把全文放 notes
    if not (date or errors or error_rate):
        notes = text.replace('\n', '\\n')[:1000]
    rows.append({
        'path': str(rel),
        'notebook': notebook,
        'date': date,
        'completed': completed,
        'errors': errors,
        'error_rate': error_rate,
        'fixed': fixed,
        'notes': notes
    })

outdir = ROOT / 'reports'
outdir.mkdir(exist_ok=True)
csvfile = outdir / 'reviews_summary.csv'
mdfile = outdir / 'reviews_summary.md'
with csvfile.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['date','notebook','path','completed','errors','error_rate','fixed','notes'])
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k,'') for k in writer.fieldnames})

with mdfile.open('w', encoding='utf-8') as f:
    f.write('# 复盘聚合报告\n\n')
    f.write('| Date | Notebook | Errors | Error Rate | Fixed | Path |\n')
    f.write('|---|---|---|---|---|---|\n')
    for r in rows:
        f.write(f"| {r['date']} | {r['notebook']} | {r['errors']} | {r['error_rate']} | {r['fixed']} | {r['path']} |\n")

print(f'Found {len(rows)} review file(s), wrote {csvfile} and {mdfile}')
