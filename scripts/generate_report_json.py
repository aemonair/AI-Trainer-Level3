#!/usr/bin/env python3
"""
为缺失 report.json 的 Session 生成报告文件
从 scoring_result_v2_exam.json 转换数据

用法：
    uv run python3 scripts/generate_report_json.py
    uv run python3 scripts/generate_report_json.py --chapter 2.1.4
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'


def parse_args():
    parser = argparse.ArgumentParser(description='生成缺失的 report.json')
    parser.add_argument('--chapter', type=str, default=None, help='只处理特定章节')
    return parser.parse_args()


def extract_chapter(session_name):
    """从 session 目录名提取章节号"""
    m = re.search(r'chapter([\d.]+)', session_name)
    return m.group(1) if m else 'unknown'


def generate_report(scoring_path, session_dir):
    """从 scoring_result_v2_exam.json 生成 report.json"""
    with open(scoring_path, 'r', encoding='utf-8') as f:
        scoring = json.load(f)

    chapter = scoring.get('chapter', extract_chapter(session_dir.name))
    earned = scoring.get('earned_score', 0)
    total = scoring.get('total_score', 0)

    # 从 scoring details 转换 schema_details
    schema_details = []
    for item in scoring.get('details', []):
        schema_details.append({
            'item_id': item.get('item_id', ''),
            'description': item.get('description', ''),
            'max_score': item.get('max', 1),
            'earned_score': item.get('earned', 0),
            'correct': item.get('correct', False),
            'type': 'ast_check',
        })

    # 查找同目录下的 practice.ipynb
    workspace_dir = scoring_path.parent
    ipynb_path = workspace_dir / 'practice.ipynb'
    ipynb_rel = str(ipynb_path.relative_to(ROOT)) if ipynb_path.exists() else ''

    report = {
        'file': ipynb_rel,
        'chapter': chapter,
        'errors': [],
        'warnings': [],
        'score': earned,
        'total_score': total,
        'total_blanks': 0,
        'score_per_blank': (earned / total * 100) if total > 0 else 0,
        'fill_comparison': [],
        'implementation_comparison': [],
        'result_comparison': [],
        'knowledge_points': {},
        'start_time': None,
        'end_time': scoring.get('graded_at', datetime.now().isoformat()),
        'process_audit': None,
        'ipython_history': None,
        'scoring_mode': scoring.get('mode', 'ast'),
        'schema_details': schema_details,
    }

    report_path = session_dir / 'report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_path, earned, total


def main():
    args = parse_args()
    generated = 0
    skipped = 0

    for session_dir in sorted(SESSIONS_DIR.iterdir()):
        if not session_dir.is_dir():
            continue

        # 跳过非 session 目录
        if 'chapter' not in session_dir.name:
            continue

        # 章节过滤
        if args.chapter and args.chapter not in session_dir.name:
            continue

        # 已有 report.json 则跳过
        if (session_dir / 'report.json').exists():
            skipped += 1
            continue

        # 查找 scoring_result 文件
        scoring_files = list(session_dir.glob('workspace/scoring_result*.json'))
        if not scoring_files:
            continue

        scoring_path = scoring_files[0]
        try:
            report_path, earned, total = generate_report(scoring_path, session_dir)
            print(f'✅ [{session_dir.name}] {earned}/{total} -> report.json')
            generated += 1
        except Exception as e:
            print(f'❌ [{session_dir.name}] 生成失败: {e}')

    print(f'\n📊 完成: 生成 {generated} 个, 已存在跳过 {skipped} 个')


if __name__ == '__main__':
    main()