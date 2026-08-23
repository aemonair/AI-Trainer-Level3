#!/usr/bin/env python3
"""
练习过程分析器

核心功能：
1. 读取所有Session的execution_log.json和scoring_result_v2_exam.json
2. 分析每道题目的耗时、迭代次数、错误记录
3. 生成练习过程报告

用法:
  python3 scripts/analyze_practice_process.py
  python3 scripts/analyze_practice_process.py --chapter 1.1.1
  python3 scripts/analyze_practice_process.py --date 20260823
  python3 scripts/analyze_practice_process.py --output reports/practice_process.md
"""
from pathlib import Path
import json
import re
import argparse
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='练习过程分析器：分析每道题目的耗时和迭代过程'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        default=None,
        help='只分析特定章节（如 1.1.1）'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='只分析特定日期的练习（如 20260823）'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='输出文件路径（默认：打印到控制台）'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细的代码迭代过程'
    )
    return parser.parse_args()


def extract_chapter(session_id: str) -> Optional[str]:
    """从session_id中提取章节号"""
    match = re.search(r'chapter(\d+\.\d+\.\d+)', session_id)
    return match.group(1) if match else None


def load_execution_log(session_dir: Path) -> Optional[Dict]:
    """加载执行日志"""
    log_path = session_dir / 'logs' / 'execution_log.json'
    if not log_path.exists():
        return None
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"加载执行日志失败: {log_path}, 错误: {e}")
        return None


def load_scoring_result(session_dir: Path) -> Optional[Dict]:
    """加载评分结果"""
    result_path = session_dir / 'workspace' / 'scoring_result_v2_exam.json'
    if not result_path.exists():
        return None
    
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"加载评分结果失败: {result_path}, 错误: {e}")
        return None


def analyze_session(session_dir: Path, verbose: bool = False) -> Optional[Dict]:
    """分析单个Session的练习过程"""
    session_id = session_dir.name
    chapter = extract_chapter(session_id)
    if not chapter:
        return None
    
    exec_log = load_execution_log(session_dir)
    scoring = load_scoring_result(session_dir)
    
    if not exec_log or not scoring:
        return None
    
    events = exec_log.get('events', [])
    if not events:
        return None
    
    # 计算时间信息
    created_at = datetime.fromisoformat(exec_log.get('created_at', ''))
    first_event = datetime.fromisoformat(events[0].get('timestamp', ''))
    last_event = datetime.fromisoformat(events[-1].get('timestamp', ''))
    
    total_time = (last_event - first_event).total_seconds()
    
    # 分析每个cell的迭代情况
    cell_groups = defaultdict(list)
    for event in events:
        cell_groups[event['cell_index']].append(event)
    
    cell_analysis = []
    total_iterations = 0
    total_errors = 0
    
    for cell_idx in sorted(cell_groups.keys()):
        cell_events = cell_groups[cell_idx]
        iterations = len(cell_events)
        total_iterations += iterations
        
        # 提取题目信息（从source中提取注释）
        source = cell_events[-1]['source']
        questions = re.findall(r'#.*?(\d+)分', source)
        question_desc = re.findall(r'#\s*(.+?)\s*\d+分', source)
        
        # 计算该cell的时间跨度
        if len(cell_events) > 1:
            cell_start = datetime.fromisoformat(cell_events[0]['timestamp'])
            cell_end = datetime.fromisoformat(cell_events[-1]['timestamp'])
            cell_time = (cell_end - cell_start).total_seconds()
        else:
            cell_time = 0
        
        cell_info = {
            'cell_index': cell_idx,
            'iterations': iterations,
            'time_seconds': cell_time,
            'questions': question_desc[-len(questions):] if question_desc else [],
            'scores': questions,
            'has_error': iterations > 1,
        }
        
        if verbose and iterations > 1:
            cell_info['iterations_detail'] = []
            for i, event in enumerate(cell_events):
                # 提取关键代码行
                lines = event['source'].split('\n')
                key_lines = [l for l in lines if not l.strip().startswith('#') and l.strip() and '=' in l]
                cell_info['iterations_detail'].append({
                    'version': i + 1,
                    'timestamp': event['timestamp'],
                    'key_code': key_lines[:5]  # 只显示前5行关键代码
                })
        
        cell_analysis.append(cell_info)
    
    return {
        'session_id': session_id,
        'chapter': chapter,
        'total_score': scoring.get('total_score', 0),
        'earned_score': scoring.get('earned_score', 0),
        'percentage': scoring.get('percentage', 0),
        'total_cells': len(cell_groups),
        'total_iterations': total_iterations,
        'total_time_seconds': total_time,
        'first_attempt': first_event.strftime('%H:%M:%S'),
        'last_attempt': last_event.strftime('%H:%M:%S'),
        'cell_analysis': cell_analysis,
    }


def generate_report(sessions_analysis: List[Dict], verbose: bool = False) -> str:
    """生成Markdown格式的报告"""
    lines = []
    lines.append('# 练习过程分析报告\n')
    lines.append(f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    # 总览
    lines.append('## 📊 总览\n')
    total_sessions = len(sessions_analysis)
    total_time = sum(s['total_time_seconds'] for s in sessions_analysis)
    total_iterations = sum(s['total_iterations'] for s in sessions_analysis)
    avg_score = sum(s['percentage'] for s in sessions_analysis) / total_sessions if total_sessions > 0 else 0
    
    lines.append(f'| 指标 | 数值 |')
    lines.append(f'|------|------|')
    lines.append(f'| 练习章节数 | {total_sessions} |')
    lines.append(f'| 总耗时 | {total_time/60:.1f} 分钟 |')
    lines.append(f'| 总迭代次数 | {total_iterations} |')
    lines.append(f'| 平均得分率 | {avg_score:.1f}% |')
    lines.append('')
    
    # 详细分析
    lines.append('## 📝 各章节详细分析\n')
    
    for session in sessions_analysis:
        lines.append(f'### {session["chapter"]} - {session["session_id"]}\n')
        lines.append(f'**得分**: {session["earned_score"]}/{session["total_score"]} ({session["percentage"]:.1f}%)  ')
        lines.append(f'**耗时**: {session["total_time_seconds"]/60:.1f} 分钟 ({session["first_attempt"]} → {session["last_attempt"]})  ')
        lines.append(f'**迭代次数**: {session["total_iterations"]} 次执行  ')
        lines.append('')
        
        # 表格
        lines.append('| Cell | 题目 | 迭代次数 | 耗时(秒) | 状态 |')
        lines.append('|------|------|---------|---------|------|')
        
        for cell in session['cell_analysis']:
            status = '❌ 有错误' if cell['has_error'] else '✅ 一次通过'
            questions = ', '.join(cell['questions']) if cell['questions'] else '-'
            lines.append(f'| {cell["cell_index"]} | {questions} | {cell["iterations"]} | {cell["time_seconds"]:.1f} | {status} |')
        
        lines.append('')
        
        # 详细迭代过程（verbose模式）
        if verbose:
            for cell in session['cell_analysis']:
                if cell.get('iterations_detail'):
                    lines.append(f'#### Cell {cell["cell_index"]} 迭代过程\n')
                    for detail in cell['iterations_detail']:
                        lines.append(f'**版本 {detail["version"]}** ({detail["timestamp"]})')
                        lines.append('```python')
                        for code_line in detail['key_code']:
                            lines.append(code_line)
                        lines.append('```\n')
                    lines.append('')
        
        lines.append('---\n')
    
    return '\n'.join(lines)


def main():
    args = parse_args()
    
    # 收集所有Session
    sessions = []
    for session_dir in sorted(SESSIONS_DIR.iterdir()):
        if not session_dir.is_dir():
            continue
        
        session_id = session_dir.name
        chapter = extract_chapter(session_id)
        if not chapter:
            continue
        
        if args.chapter and chapter != args.chapter:
            continue
        
        if args.date and not session_id.startswith(args.date):
            continue
        
        analysis = analyze_session(session_dir, verbose=args.verbose)
        if analysis:
            sessions.append(analysis)
    
    if not sessions:
        logger.warning("没有找到符合条件的练习记录")
        return
    
    # 生成报告
    report = generate_report(sessions, verbose=args.verbose)
    
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"报告已保存: {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()