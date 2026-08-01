#!/usr/bin/env python3
import argparse
import csv
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('.').resolve()

parser = argparse.ArgumentParser(description='创建带时间戳的练习 notebook')
parser.add_argument('chapter', nargs='?', default='1.1.1', help='章节编号，如 1.1.1')
parser.add_argument('--review', action='store_true', help='同时创建 review 复盘文件（仅在有错误需要记录时使用）')
args = parser.parse_args()

chapter = args.chapter
do_review = args.review
item_dir = ROOT / f'{chapter}-素材'
base_nb = item_dir / f'{chapter}.ipynb'
ref_candidates = sorted(item_dir.glob(f'{chapter}_andy*.ipynb'))

if not item_dir.exists():
    raise SystemExit(f'Missing chapter folder: {item_dir}')
if not base_nb.exists():
    raise SystemExit(f'Missing base template notebook: {base_nb}')
if not ref_candidates:
    raise SystemExit(f'Missing reference notebook for chapter {chapter} in {item_dir}')

ref_nb = ref_candidates[0]
now = datetime.datetime.now().strftime('%Y%m%d%H%M')
practice_nb = item_dir / f'{chapter}_practice_{now}.ipynb'
practice_md = item_dir / f'{chapter}_practice_{now}_review.md'

nb = json.loads(base_nb.read_text(encoding='utf-8'))
if do_review:
    review_cell = {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            f'# {chapter} 练习 review 入口\n',
            '\n',
            f'- 练习 notebook：{practice_nb.name}\n',
            f'- review 文件：[{practice_md.name}]({practice_md.name})\n',
            '\n',
            '## 本次 review 建议\n',
            '- 记录本次遇到的问题\n',
            '- 记录错误点和原因\n',
            '- 记录改进建议\n',
        ],
    }
    nb['cells'] = [review_cell] + nb.get('cells', [])
practice_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'Created: {practice_nb.name}')

if do_review:
    review_content = f'''# {chapter} 练习 review ({now})

- 练习 notebook：`{practice_nb.name}`
- 模板 notebook：`{base_nb.name}`（保持填空原样）
- 参考实现 notebook：`{ref_nb.name}`

## 练习目标
- 在 `{practice_nb.name}` 中完成下划线填空题
- 运行并验证结果是否正确
- 和参考实现进行对比，记录差异与错误点

## 练习步骤
1. 打开 `{practice_nb.name}`，完成所有下划线填空
2. 运行 notebook，确认计算结果没有异常
3. 与参考实现 `{ref_nb.name}` 对照，补充差异记录

## 练习结果记录
- 问题点：
  - 
- 与参考实现不同之处：
  - 
- 发现的错误：
  - 
- 改进建议：
  - 

## review 结论
- 做得对的地方：
  - 
- 需要改进的地方：
  - 
'''
    practice_md.write_text(review_content, encoding='utf-8')
    print(f'Created: {practice_md.name}')

if do_review:
    log_csv = ROOT / 'daily_practice_log.csv'
    if not log_csv.exists():
        with log_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date','notebook','summary','completed_steps','errors_found','error_rate','error_points','improvement_actions','fixed','notes'])
    row = [
        datetime.date.today().isoformat(),
        practice_nb.stem,
        f'创建 {chapter} 练习版本并生成 review 记录',
        '复制模板->生成练习 notebook->生成复盘 md',
        '0',
        '0%',
        '待练习后补充',
        '完成基本练习版本创建',
        'no',
        str(practice_md)
    ]
    with log_csv.open('a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

if do_review:
    subprocess.run(['python3', 'scripts/aggregate_reviews.py'], check=True)
    subprocess.run(['git', 'add', str(practice_nb), str(practice_md), str(log_csv), 'reports/reviews_summary.csv', 'reports/reviews_summary.md'], check=True)
    subprocess.run(['git', 'commit', '-m', f'Create practice notebook for {chapter} with review ({now})'], check=True)
    print('review_added')
else:
    subprocess.run(['git', 'add', str(practice_nb)], check=True)
    subprocess.run(['git', 'commit', '-m', f'Create practice notebook for {chapter} ({now})'], check=True)
    print('notebook_only')