#!/usr/bin/env python3
"""
IPython历史命令分析器

核心功能：
1. 从 ~/.ipython/profile_default/history.sqlite 读取命令历史
2. 根据时间戳匹配练习文件的session
3. 分析答题过程中的命令演化、修正次数、错误类型
4. 生成"题目-命令-修正建议"对照报告

用法:
  python3 scripts/analyze_ipython_history.py --chapter 1.1.1
  python3 scripts/analyze_ipython_history.py --practice 1.1.1-materials/1.1.1_practice_202608052255.ipynb
  python3 scripts/analyze_ipython_history.py --all
  python3 scripts/analyze_ipython_history.py --output-report
"""
import os
import sqlite3
import json
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='IPython历史命令分析器')
    parser.add_argument('--chapter', type=str, help='分析特定章节（如 1.1.1）')
    parser.add_argument('--practice', type=str, help='分析特定练习文件')
    parser.add_argument('--all', action='store_true', help='分析所有练习文件')
    parser.add_argument('--output-report', action='store_true', help='生成Markdown报告')
    parser.add_argument('--output-json', action='store_true', help='生成JSON报告')
    return parser.parse_args()


def load_ipython_history() -> List[Tuple[int, int, str]]:
    """
    加载IPython历史命令
    
    返回:
        [(session, line, source), ...]
    """
    history_path = os.path.expanduser('~/.ipython/profile_default/history.sqlite')
    
    if not os.path.exists(history_path):
        logger.warning(f"IPython历史数据库不存在: {history_path}")
        return []
    
    try:
        conn = sqlite3.connect(history_path)
        cur = conn.cursor()
        cur.execute('SELECT session, line, source FROM history ORDER BY session, line')
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"读取IPython历史失败: {e}")
        return []


def load_ipython_session_timestamps() -> Dict[int, datetime]:
    """
    从IPython历史数据库加载session的时间戳映射
    
    修复：读取 sessions 表的 start_time 字段，建立 session_id -> timestamp 映射
    
    返回:
        {session_id: start_time_datetime, ...}
    """
    history_path = os.path.expanduser('~/.ipython/profile_default/history.sqlite')
    
    if not os.path.exists(history_path):
        return {}
    
    try:
        conn = sqlite3.connect(history_path)
        cur = conn.cursor()
        
        # 尝试读取 sessions 表（IPython 的 session 表结构）
        # sessions 表包含: session, start_time, end_time, num_cmds, remark
        cur.execute('SELECT session, start_time FROM sessions ORDER BY session')
        rows = cur.fetchall()
        conn.close()
        
        session_times = {}
        for session_id, start_time_raw in rows:
            if start_time_raw:
                # IPython 存储的时间格式可能是浮点时间戳或 ISO 字符串
                try:
                    # 尝试作为浮点时间戳解析
                    start_time = datetime.fromtimestamp(float(start_time_raw))
                    session_times[session_id] = start_time
                except (ValueError, TypeError, OSError):
                    # 尝试作为 ISO 字符串解析
                    try:
                        start_time = datetime.fromisoformat(str(start_time_raw))
                        session_times[session_id] = start_time
                    except ValueError:
                        pass
        
        return session_times
    except Exception as e:
        logger.warning(f"读取session时间戳失败: {e}")
        return {}


def group_history_by_session(history_rows: List[Tuple[int, int, str]]) -> Dict[int, List[str]]:
    """
    按session分组历史命令
    
    返回:
        {session_id: [command1, command2, ...], ...}
    """
    sessions = defaultdict(list)
    for session, line, source in history_rows:
        if source.strip():
            sessions[session].append(source.strip())
    return dict(sessions)


def find_practice_files(chapter: Optional[str] = None, practice_path: Optional[str] = None) -> List[Path]:
    """查找练习文件"""
    if practice_path:
        p = Path(practice_path)
        if p.exists():
            return [p]
        return []
    
    pattern = '*_practice_*.ipynb'
    files = []
    
    for md in ROOT.rglob(pattern):
        if md.is_file() and '_review.md' not in md.name:
            if chapter and not md.name.startswith(chapter):
                continue
            files.append(md)
    
    return sorted(files)


def extract_timestamp_from_practice(practice_path: Path) -> Optional[datetime]:
    """从练习文件名提取时间戳"""
    match = re.search(r'practice_(\d{12})', practice_path.name)
    if match:
        timestamp_str = match.group(1)
        return datetime.strptime(timestamp_str, '%Y%m%d%H%M')
    return None


def match_session_to_practice(practice_path: Path, sessions: Dict[int, List[str]]) -> Optional[int]:
    """
    将练习文件匹配到对应的IPython session
    
    策略：
    1. 从execution_log.json获取session_start时间
    2. 从文件名提取时间戳
    3. 通过SQLite sessions表精确匹配时间戳
    
    返回:
        session_id 或 None
    """
    return match_session_by_timestamp(practice_path, sessions)


def find_closest_session(target_time: datetime, sessions: Dict[int, List[str]]) -> Optional[int]:
    """
    通过IPython SQLite的sessions表匹配最接近target_time的session
    """
    import os
    import sqlite3
    from datetime import datetime
    
    history_path = os.path.expanduser('~/.ipython/profile_default/history.sqlite')
    if not os.path.exists(history_path):
        return None
    
    try:
        conn = sqlite3.connect(history_path)
        cur = conn.cursor()
        # 读取sessions表获取时间戳
        cur.execute('SELECT session, start FROM sessions ORDER BY session')
        session_times = cur.fetchall()
        conn.close()
    except Exception:
        # 如果sessions表不存在（旧版本IPython），降级为按session顺序估算
        if sessions:
            # 返回最大的session（最新的）
            return max(sessions.keys())
        return None
    
    # 将target_time转为时间戳（秒）
    target_ts = target_time.timestamp()
    
    closest_session = None
    min_diff = float('inf')
    
    for session_id, start_str in session_times:
        if not start_str:
            continue
        try:
            # IPython存储的是ISO格式或浮点数时间戳，尝试解析
            if isinstance(start_str, (int, float)):
                start_ts = start_str
            else:
                # 尝试解析ISO格式
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                start_ts = start_dt.timestamp()
            
            diff = abs(target_ts - start_ts)
            # 只考虑1小时内的匹配
            if diff < 3600 and diff < min_diff:
                min_diff = diff
                closest_session = session_id
        except Exception:
            continue
    
    # 如果时间匹配失败，返回最新的session
    if closest_session is None and sessions:
        return max(sessions.keys())
    
    return closest_session


def match_session_by_timestamp(practice_path: Path, sessions: Dict[int, List[str]]) -> Optional[int]:
    """通过时间戳匹配练习文件到IPython session（重构版）"""
    import re
    import json
    from datetime import datetime
    
    practice_name = practice_path.stem
    log_path = practice_path.parent / f'{practice_name}_execution_log.json'
    
    target_time = None
    
    # 策略1：从execution_log.json获取
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                if 'session_start' in log_data:
                    target_time = datetime.fromisoformat(log_data['session_start'])
        except Exception:
            pass
    
    # 策略2：从文件名提取时间戳
    if not target_time:
        match = re.search(r'practice_(\d{12})', practice_path.name)
        if match:
            timestamp_str = match.group(1)
            try:
                target_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M')
            except Exception:
                pass
    
    if not target_time:
        return None
    
    return find_closest_session(target_time, sessions)


def analyze_session_commands(session_id: int, commands: List[str]) -> Dict:
    """
    分析单个session的命令
    
    返回:
        分析结果字典
    """
    analysis = {
        'session_id': session_id,
        'total_commands': len(commands),
        'key_commands': [],
        'error_patterns': [],
        'correction_count': 0,
        'suggestions': [],
    }
    
    # 提取关键命令
    key_patterns = [
        (r'groupby', '分组操作'),
        (r'isin\(', '布尔过滤'),
        (r'dropna', '缺失值处理'),
        (r'between\(', '区间判断'),
        (r'value_counts', '计数统计'),
        (r'agg\(', '聚合操作'),
        (r'np\.where', '条件替换'),
        (r'pd\.cut', '区间分组'),
        (r'fillna', '缺失值填充'),
        (r'read_csv', '数据读取'),
    ]
    
    for cmd in commands:
        for pattern, desc in key_patterns:
            if re.search(pattern, cmd):
                analysis['key_commands'].append({
                    'command': cmd[:100],
                    'type': desc,
                })
    
    # 检测错误模式
    error_patterns = [
        (r'pd\.dropna\(\)', '错误：应写为 data = data.dropna()'),
        (r'\.bewteen\(', '拼写错误：应为 .between()'),
        (r'data\.length', '错误：应使用 len(data)'),
        (r'\|\|', '错误：Pandas中应使用 | 而不是 ||'),
        (r"data\['\w+'\]\['\w+','\w+'\]", '错误：应使用 .isin([...])'),
    ]
    
    for cmd in commands:
        for pattern, desc in error_patterns:
            if re.search(pattern, cmd):
                analysis['error_patterns'].append({
                    'command': cmd[:100],
                    'error_type': desc,
                })
    
    # 计算修正次数（通过检测相似命令的重复出现）
    command_groups = defaultdict(int)
    for cmd in commands:
        # 标准化命令（去除空格、统一引号）
        normalized = re.sub(r'\s+', ' ', cmd).replace("'", '"').strip()[:50]
        command_groups[normalized] += 1
    
    analysis['correction_count'] = sum(1 for count in command_groups.values() if count > 1)
    
    # 生成建议
    if any('pd.dropna()' in cmd for cmd in commands):
        analysis['suggestions'].append('缺失值处理：应写为 data = data.dropna()，不要把 dropna 写成 pd.dropna()')
    
    if any('isin(' in cmd for cmd in commands):
        analysis['suggestions'].append('布尔过滤：先定义 mask = data[col].isin([...])，再用 data[mask] 做筛选')
    
    if any('between(' in cmd for cmd in commands):
        analysis['suggestions'].append('区间判断：检查列名与拼写，常见写法是 data[col].between(18, 70)')
    
    if any('groupby' in cmd and 'agg' in cmd for cmd in commands):
        analysis['suggestions'].append('分组聚合：优先用 groupby(...).agg({...}) 或 groupby(...)[col].agg([...])')
    
    if any('pd.cut' in cmd for cmd in commands):
        analysis['suggestions'].append('区间分组：先定义 bins 和 labels，再用 pd.cut() 分组')
    
    return analysis


def generate_history_report(practice_path: Path, session_id: Optional[int], 
                           session_analysis: Optional[Dict]) -> Dict:
    """
    生成练习文件的历史命令分析报告
    
    返回:
        报告字典
    """
    chapter = practice_path.name.split('_practice_')[0]
    
    report = {
        'chapter': chapter,
        'practice_file': str(practice_path),
        'session_id': session_id,
        'session_analysis': session_analysis,
        'timestamp': datetime.now().isoformat(),
    }
    
    return report


def generate_markdown_report(reports: List[Dict], output_path: Path):
    """生成Markdown格式的报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 📊 IPython历史命令分析报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 总体统计
        f.write("## 📈 总体统计\n\n")
        total_sessions = sum(1 for r in reports if r.get('session_id'))
        total_commands = sum(r.get('session_analysis', {}).get('total_commands', 0) for r in reports)
        total_corrections = sum(r.get('session_analysis', {}).get('correction_count', 0) for r in reports)
        
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 分析的题目数 | {len(reports)} |\n")
        f.write(f"| 匹配的session数 | {total_sessions} |\n")
        f.write(f"| 总命令数 | {total_commands} |\n")
        f.write(f"| 总修正次数 | {total_corrections} |\n\n")
        
        # 详细分析
        f.write("## 📝 详细分析\n\n")
        
        for report in reports:
            chapter = report.get('chapter', '未知')
            session_id = report.get('session_id')
            analysis = report.get('session_analysis')
            
            f.write(f"### {chapter}\n\n")
            
            if not session_id or not analysis:
                f.write("⚠️ 未找到对应的IPython session\n\n")
                continue
            
            f.write(f"**Session ID**: {session_id}\n\n")
            f.write(f"**命令数量**: {analysis['total_commands']}\n\n")
            f.write(f"**修正次数**: {analysis['correction_count']}\n\n")
            
            # 关键命令
            if analysis['key_commands']:
                f.write("#### 关键命令\n\n")
                for cmd in analysis['key_commands'][:10]:
                    f.write(f"- `{cmd['command']}` ({cmd['type']})\n")
                f.write("\n")
            
            # 错误模式
            if analysis['error_patterns']:
                f.write("#### ❌ 错误模式\n\n")
                for err in analysis['error_patterns']:
                    f.write(f"- `{err['command']}` - {err['error_type']}\n")
                f.write("\n")
            
            # 建议
            if analysis['suggestions']:
                f.write("#### 💡 建议\n\n")
                for sug in analysis['suggestions']:
                    f.write(f"- {sug}\n")
                f.write("\n")
            
            f.write("---\n\n")


def main():
    args = parse_args()
    
    # 加载IPython历史
    logger.info("加载IPython历史命令...")
    history_rows = load_ipython_history()
    
    if not history_rows:
        logger.warning("未找到IPython历史命令")
        return
    
    logger.info(f"共加载 {len(history_rows)} 条历史命令")
    
    # 按session分组
    sessions = group_history_by_session(history_rows)
    logger.info(f"共发现 {len(sessions)} 个session")
    
    # 查找练习文件
    practice_files = find_practice_files(
        chapter=args.chapter,
        practice_path=args.practice
    )
    
    if not practice_files:
        logger.warning("未找到练习文件")
        return
    
    logger.info(f"找到 {len(practice_files)} 个练习文件")
    
    # 分析每个练习文件
    reports = []
    for pf in practice_files:
        logger.info(f"\n分析: {pf.name}")
        
        # 匹配session
        session_id = match_session_to_practice(pf, sessions)
        
        if session_id:
            logger.info(f"  匹配到session: {session_id}")
            commands = sessions.get(session_id, [])
            analysis = analyze_session_commands(session_id, commands)
            logger.info(f"  命令数: {analysis['total_commands']}")
            logger.info(f"  修正次数: {analysis['correction_count']}")
        else:
            logger.info(f"  ⚠️ 未匹配到session")
            analysis = None
        
        report = generate_history_report(pf, session_id, analysis)
        reports.append(report)
    
    # 生成报告
    if args.output_report:
        output_path = ROOT / 'reports' / f"ipython_history_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generate_markdown_report(reports, output_path)
        logger.info(f"\nMarkdown报告已生成: {output_path}")
    
    if args.output_json:
        output_path = ROOT / 'reports' / f"ipython_history_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON报告已生成: {output_path}")
    
    # 打印摘要
    print("\n" + "="*80)
    print("📊 IPython历史命令分析摘要")
    print("="*80)
    
    for report in reports:
        chapter = report.get('chapter', '未知')
        analysis = report.get('session_analysis')
        
        print(f"\n{chapter}:")
        if analysis:
            print(f"  Session: {analysis['session_id']}")
            print(f"  命令数: {analysis['total_commands']}")
            print(f"  修正次数: {analysis['correction_count']}")
            if analysis['error_patterns']:
                print(f"  错误模式: {len(analysis['error_patterns'])}个")
            if analysis['suggestions']:
                print(f"  建议: {len(analysis['suggestions'])}条")
        else:
            print(f"  ⚠️ 未匹配到session")


if __name__ == '__main__':
    main()