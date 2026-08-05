#!/usr/bin/env python3
"""
创建考试会话（Exam Session）

核心功能：
1. 从模板创建带时间戳的练习文件（放在原来的materials目录）
2. 生成manifest.json记录考试元数据
3. 支持旧模式兼容

用法:
  python3 scripts/create_timestamped_practice.py 1.1.1
  python3 scripts/create_timestamped_practice.py 1.1.1 --review
"""
import argparse
import csv
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('.').resolve()

parser = argparse.ArgumentParser(description='创建考试会话（Exam Session）')
parser.add_argument('chapter', nargs='?', default='1.1.1', help='章节编号，如 1.1.1')
parser.add_argument('--review', action='store_true', help='同时创建 review 复盘文件（仅在有错误需要记录时使用）')
args = parser.parse_args()

chapter = args.chapter
do_review = args.review

item_dir = ROOT / f'{chapter}-materials'
base_nb = item_dir / f'{chapter}.ipynb'

if not item_dir.exists():
    raise SystemExit(f'Missing chapter folder: {item_dir}')
if not base_nb.exists():
    raise SystemExit(f'Missing base template notebook: {base_nb}')

now = datetime.datetime.now()
now_str = now.strftime('%Y%m%d%H%M')

# 创建带时间戳的练习文件（放在原来的materials目录）
practice_nb = item_dir / f'{chapter}_practice_{now_str}.ipynb'

# 创建专属执行日志文件（与practice文件时间戳对应）
execution_log_path = item_dir / f'{chapter}_practice_{now_str}_execution_log.json'
execution_log_init = {
    'session_start': now.isoformat(),
    'last_updated': now.isoformat(),
    'total_executions': 0,
    'practice_file': str(practice_nb),
    'exam_id': f'{chapter}_{now_str}',
    'entries': [],
}
execution_log_path.write_text(json.dumps(execution_log_init, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# 直接复制模板文件，不添加额外单元格
nb = json.loads(base_nb.read_text(encoding='utf-8'))

# 自动在第一个Cell前插入日志初始化Cell（用户无感知）
log_path_str = str(execution_log_path)

# 使用字符串模板避免f-string中的逗号问题
code_template = """# 自动初始化执行日志记录器（请勿删除）
import sys
from pathlib import Path
try:
    log_path = Path('{LOG_PATH}')
    # 智能查找scripts目录（兼容Jupyter）
    scripts_dir = Path.cwd() / 'scripts'
    if not scripts_dir.exists():
        # 向上查找直到找到包含scripts/execution_logger.py的目录
        for parent in Path.cwd().parents:
            if (parent / 'scripts' / 'execution_logger.py').exists():
                scripts_dir = parent / 'scripts'
                break
    if scripts_dir.exists():
        sys.path.insert(0, str(scripts_dir))
    from execution_logger import ExecutionLogger
    logger = ExecutionLogger(log_path=log_path, auto_save=True)
    logger.start()
    print('✅ 执行日志记录器已自动启动')
except Exception as e:
    print(f'⚠️ 日志记录器初始化失败（不影响练习）: {{e}}')
"""

log_init_code = code_template.format(LOG_PATH=log_path_str)
log_init_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {
        "tags": ["auto-init-execution-logger"],
        "description": "自动初始化执行日志记录器（无需手动运行）"
    },
    "outputs": [],
    "source": [line + '\n' for line in log_init_code.strip().split('\n')]
}

# 插入到第一个Cell之前
nb['cells'].insert(0, log_init_cell)

practice_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'Created: {practice_nb.name}')
print(f'✅ 已自动注入日志初始化Cell（用户无感知）')

# 创建manifest.json（考试元数据）
manifest = {
    'exam_id': f'{chapter}_{now_str}',
    'chapter': chapter,
    'start_time': now.isoformat(),
    'practice_file': str(practice_nb),
    'status': 'in_progress',
    'template_file': str(base_nb),
}

manifest_path = item_dir / f'{chapter}_practice_{now_str}_manifest.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Manifest saved: {manifest_path.name}')
print(f'Execution log initialized: {execution_log_path.name}')

if do_review:
    practice_md = item_dir / f'{chapter}_practice_{now_str}_review.md'
    review_content = f'''# {chapter} 练习 review ({now_str})

- 考试ID：`{chapter}_{now_str}`
- 练习 notebook：`{practice_nb.name}`
- 模板 notebook：`{base_nb.name}`（保持填空原样）

## 练习目标
- 在 `{practice_nb.name}` 中完成所有下划线填空
- 运行 notebook，确认计算结果没有异常
- 和 `_guide.md` 对照，记录差异与错误点

## 练习步骤
1. 打开 `{practice_nb.name}`，完成所有下划线填空
2. 运行 notebook，确认计算结果没有异常
3. 与 `_guide.md` 对照，补充差异记录

## 练习结果记录
- 问题点：
  - 
- 与标准答案不同之处：
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
    
    log_csv = ROOT / 'daily_practice_log.csv'
    if not log_csv.exists():
        with log_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date','notebook','summary','completed_steps','errors_found','error_rate','error_points','improvement_actions','fixed','notes'])
    row = [
        datetime.date.today().isoformat(),
        f'{chapter}_{now_str}',
        f'创建 {chapter} 考试会话并生成 review 记录',
        '创建练习 notebook->生成复盘 md',
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
    
    subprocess.run(['python3', 'scripts/aggregate_reviews.py'], check=True)
    subprocess.run(['git', 'add', str(practice_nb), str(manifest_path), str(execution_log_path), str(log_csv), 'reports/reviews_summary.csv', 'reports/reviews_summary.md'], check=True)
    subprocess.run(['git', 'commit', '-m', f'Create exam session for {chapter} with review ({now_str})'], check=True)
    print('review_added')
else:
    subprocess.run(['git', 'add', str(practice_nb), str(manifest_path), str(execution_log_path)], check=True)
    subprocess.run(['git', 'commit', '-m', f'Create exam session for {chapter} ({now_str})'], check=True)
    print('session_created')