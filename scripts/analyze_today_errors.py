#!/usr/bin/env python3
"""
分析今天(2026-08-23)所有做题过程中的错误
包括：execution_log中的执行错误 + scoring_result中的评分错误
"""
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'
OUTPUT_DIR = ROOT / 'analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_chapter(name):
    m = re.search(r'chapter(\d+\.\d+\.\d+)', name)
    return m.group(1) if m else 'unknown'

def analyze_today():
    today_sessions = []
    for d in SESSIONS_DIR.iterdir():
        if d.is_dir() and '20260823' in d.name:
            today_sessions.append(d)
    
    today_sessions.sort(key=lambda x: x.name)
    
    print(f"找到 {len(today_sessions)} 个今天的session")
    
    all_errors = []
    
    for session_dir in today_sessions:
        chapter = extract_chapter(session_dir.name)
        
        # 1. 读取execution_log
        exec_log_path = session_dir / 'logs' / 'execution_log.json'
        exec_errors = []
        if exec_log_path.exists():
            with open(exec_log_path, 'r', encoding='utf-8') as f:
                try:
                    exec_log = json.load(f)
                    for entry in exec_log:
                        if entry.get('status') == 'error' or entry.get('error'):
                            exec_errors.append({
                                'item_id': entry.get('item_id', ''),
                                'error': entry.get('error', ''),
                                'code': entry.get('code', entry.get('user_code', '')),
                                'type': 'execution_error',
                            })
                except:
                    pass
        
        # 2. 读取scoring_result
        scoring_errors = []
        for scoring_path in session_dir.rglob('scoring_result_v2_*.json'):
            with open(scoring_path, 'r', encoding='utf-8') as f:
                try:
                    scoring = json.load(f)
                    for detail in scoring.get('details', []):
                        if not detail.get('correct', True):
                            scoring_errors.append({
                                'item_id': detail.get('item_id', ''),
                                'description': detail.get('description', ''),
                                'code': detail.get('user_code', ''),
                                'earned': detail.get('earned', 0),
                                'max': detail.get('max', 0),
                                'type': 'scoring_error',
                            })
                except:
                    pass
        
        if exec_errors or scoring_errors:
            all_errors.append({
                'session': session_dir.name,
                'chapter': chapter,
                'exec_errors': exec_errors,
                'scoring_errors': scoring_errors,
            })
    
    return all_errors

def generate_report(all_errors):
    lines = []
    lines.append("# 📝 今日(2026-08-23)做题错误分析")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    total_sessions_with_errors = len(all_errors)
    total_exec_errors = sum(len(e['exec_errors']) for e in all_errors)
    total_scoring_errors = sum(len(e['scoring_errors']) for e in all_errors)
    
    lines.append(f"\n## 📊 总体统计\n")
    lines.append(f"- 有错误的session数: {total_sessions_with_errors}")
    lines.append(f"- 执行错误总数: {total_exec_errors}")
    lines.append(f"- 评分错误总数: {total_scoring_errors}")
    lines.append(f"- 总错误数: {total_exec_errors + total_scoring_errors}\n")
    
    # 按章节分组
    chapter_errors = defaultdict(lambda: {'exec': [], 'scoring': []})
    for e in all_errors:
        ch = e['chapter']
        chapter_errors[ch]['exec'].extend(e['exec_errors'])
        chapter_errors[ch]['scoring'].extend(e['scoring_errors'])
        chapter_errors[ch]['session'] = e['session']
    
    lines.append(f"\n## 📋 各章节错误详情\n")
    
    for ch in sorted(chapter_errors.keys()):
        ce = chapter_errors[ch]
        total = len(ce['exec']) + len(ce['scoring'])
        if total == 0:
            continue
        
        lines.append(f"\n---\n")
        lines.append(f"\n### 章节 {ch}\n")
        lines.append(f"- Session: {ce['session']}")
        lines.append(f"- 执行错误: {len(ce['exec'])}个")
        lines.append(f"- 评分错误: {len(ce['scoring'])}个")
        lines.append(f"- 总错误: {total}个\n")
        
        if ce['exec']:
            lines.append(f"\n#### 执行错误\n")
            for i, err in enumerate(ce['exec'], 1):
                lines.append(f"{i}. **{err['item_id']}**: `{err['error'][:100]}`")
                lines.append(f"   - 代码: `{err['code'][:80]}`\n")
        
        if ce['scoring']:
            lines.append(f"\n#### 评分错误\n")
            for i, err in enumerate(ce['scoring'], 1):
                lines.append(f"{i}. **{err['item_id']}** - {err['description']}")
                lines.append(f"   - 得分: {err['earned']}/{err['max']}")
                lines.append(f"   - 代码: `{err['code'][:100]}`\n")
    
    return '\n'.join(lines)

def generate_summary(all_errors):
    """生成简洁的错误汇总"""
    lines = []
    lines.append("# 🎯 今日错误汇总（简洁版）\n")
    
    error_types = defaultdict(list)
    
    for e in all_errors:
        ch = e['chapter']
        for err in e['scoring_errors']:
            error_types[ch].append(err)
        for err in e['exec_errors']:
            error_types[ch].append(err)
    
    total_errors = sum(len(v) for v in error_types.values())
    lines.append(f"**总错误数**: {total_errors}\n")
    lines.append(f"**涉及章节**: {len(error_types)}个\n")
    
    lines.append("## 错误列表\n")
    lines.append("| 章节 | 题号 | 描述 | 错误代码 | 错误类型 |\n")
    lines.append("|------|------|------|---------|---------|\n")
    
    for ch in sorted(error_types.keys()):
        for err in error_types[ch]:
            item_id = err.get('item_id', '')
            desc = err.get('description', err.get('error', ''))[:50]
            code = err.get('code', '')[:60]
            etype = '评分错误' if err.get('type') == 'scoring_error' else '执行错误'
            lines.append(f"| {ch} | {item_id} | {desc} | `{code}` | {etype} |")
    
    return '\n'.join(lines)

def main():
    print("分析今天的做题记录...")
    all_errors = analyze_today()
    
    print(f"找到 {len(all_errors)} 个有错误的session")
    
    report = generate_report(all_errors)
    report_path = OUTPUT_DIR / 'today_errors_detailed.md'
    report_path.write_text(report, encoding='utf-8')
    print(f"已生成详细报告: {report_path}")
    
    summary = generate_summary(all_errors)
    summary_path = OUTPUT_DIR / 'today_errors_summary.md'
    summary_path.write_text(summary, encoding='utf-8')
    print(f"已生成汇总报告: {summary_path}")
    
    # 打印简要统计
    total_scoring = sum(len(e['scoring_errors']) for e in all_errors)
    total_exec = sum(len(e['exec_errors']) for e in all_errors)
    print(f"\n📊 今日错误统计:")
    print(f"  执行错误: {total_exec}")
    print(f"  评分错误: {total_scoring}")
    print(f"  总错误: {total_exec + total_scoring}")

if __name__ == '__main__':
    main()