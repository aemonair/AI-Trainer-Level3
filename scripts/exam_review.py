#!/usr/bin/env python3
"""
考试分析报告生成器

核心功能：
1. 读取Session的report.json
2. 生成面向考生的考试分析报告
3. 提供学习建议和改进方向

用法:
  python3 scripts/exam_review.py --session 2026-08-05-1430-chapter1.1.1
  python3 scripts/exam_review.py --latest
  python3 scripts/exam_review.py --chapter 1.1.1
"""
from pathlib import Path
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='生成考试分析报告'
    )
    parser.add_argument(
        '--session',
        type=str,
        default=None,
        help='指定Session ID'
    )
    parser.add_argument(
        '--latest',
        action='store_true',
        help='分析最新的Session'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        default=None,
        help='只分析特定章节'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='输出文件路径（默认：Session目录下的summary.md）'
    )
    return parser.parse_args()


def load_session_report(session_id: str) -> Optional[Dict]:
    """加载指定Session的报告"""
    session_dir = SESSIONS_DIR / session_id
    
    if not session_dir.exists():
        logger.error(f"Session不存在: {session_dir}")
        return None
    
    report_path = session_dir / 'report.json'
    if not report_path.exists():
        logger.error(f"报告文件不存在: {report_path}")
        return None
    
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_latest_session(chapter: Optional[str] = None) -> Optional[str]:
    """获取最新的Session ID"""
    if not SESSIONS_DIR.exists():
        return None
    
    sessions = []
    for session_dir in sorted(SESSIONS_DIR.iterdir()):
        if not session_dir.is_dir():
            continue
        
        session_id = session_dir.name
        if chapter and chapter not in session_id:
            continue
        
        report_path = session_dir / 'report.json'
        if report_path.exists():
            sessions.append(session_id)
    
    return sessions[-1] if sessions else None


def generate_exam_report(report: Dict) -> str:
    """
    生成考试分析报告（Markdown格式）
    
    参数:
        report: 评分报告字典
    
    返回:
        Markdown格式的考试分析报告
    """
    lines = []
    
    # 标题
    chapter = report.get('chapter', '未知')
    session_id = report.get('session_id', '未知')
    score = report.get('score', 0)
    total_score = report.get('total_score', 100)
    
    lines.append(f"# 📋 考试分析报告\n")
    lines.append(f"**章节**: {chapter}\n")
    lines.append(f"**会话ID**: {session_id}\n")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 本次考试概况
    lines.append("\n## 📊 本次考试\n")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 得分 | {score}/{total_score} |")
    
    duration = report.get('duration_minutes')
    if duration:
        lines.append(f"| 耗时 | {duration}分钟 |")
    
    start_time = report.get('start_time')
    end_time = report.get('end_time')
    if start_time and end_time:
        lines.append(f"| 开始时间 | {start_time[:16]} |")
        lines.append(f"| 结束时间 | {end_time[:16]} |")
    
    # 目标分数判断
    target_score = 90
    gap = score - target_score
    lines.append(f"| 目标分数 | {target_score} |")
    lines.append(f"| 差距 | {gap:+d} {'✅' if gap >= 0 else '❌'} |\n")
    
    # 错误分析
    errors = report.get('errors', [])
    warnings = report.get('warnings', [])
    
    if errors or warnings:
        lines.append("\n## ❌ 主要失分点\n")
        
        all_issues = errors + warnings
        all_issues.sort(key=lambda x: x.get('deduction', 0), reverse=True)
        
        for i, issue in enumerate(all_issues, 1):
            issue_type = issue.get('type', '未知')
            topic = issue.get('topic', '未知')
            kp = issue.get('knowledge_point', '其他')
            deduction = issue.get('deduction', 0)
            count = issue.get('count', 1)
            
            lines.append(f"### {i}. {kp} - {topic} (扣{deduction}分)\n")
            lines.append(f"- **错误类型**: {issue_type}\n")
            lines.append(f"- **错误次数**: {count}次\n")
            
            # 显示具体错误详情
            details = issue.get('details', [])
            if details and len(details) > 0:
                detail = details[0]
                if 'expected_answer' in detail and 'filled_answer' in detail:
                    lines.append(f"- **期望答案**: `{detail['expected_answer']}`\n")
                    lines.append(f"- **你的答案**: `{detail['filled_answer']}`\n")
                elif 'missing' in detail:
                    lines.append(f"- **缺少函数**: {detail['missing']}\n")
            
            lines.append("")
    
    if not errors and not warnings:
        lines.append("\n## ✅ 恭喜！完全正确！\n")
        lines.append("本次考试没有发现错误，继续保持！\n")
    
    # 学习建议
    lines.append("\n## 💡 学习建议\n")
    
    if errors:
        # 按知识点分组
        kp_errors = {}
        for error in errors:
            kp = error.get('knowledge_point', '其他')
            if kp not in kp_errors:
                kp_errors[kp] = []
            kp_errors[kp].append(error)
        
        lines.append("建议优先复习以下知识点：\n")
        for kp, kp_errs in sorted(kp_errors.items(), key=lambda x: len(x[1]), reverse=True):
            error_count = sum(e.get('count', 1) for e in kp_errs)
            lines.append(f"1. **{kp}** - {error_count}个错误\n")
        
        lines.append("\n具体建议：\n")
        for kp, kp_errs in kp_errors.items():
            for err in kp_errs:
                topic = err.get('topic', '未知')
                lines.append(f"- 复习 {kp} 的 {topic} 相关知识点\n")
    else:
        lines.append("本次表现优秀！建议：\n")
        lines.append("- 继续保持当前学习状态\n")
        lines.append("- 可以尝试更高难度的练习\n")
        lines.append("- 帮助其他同学解答问题\n")
    
    # 进步趋势（如果有历史数据）
    lines.append("\n## 📈 进步趋势\n")
    
    # 查找同一章节的历史Session
    chapter_sessions = []
    if SESSIONS_DIR.exists():
        for session_dir in sorted(SESSIONS_DIR.iterdir()):
            if not session_dir.is_dir():
                continue
            
            session_id = session_dir.name
            if chapter not in session_id:
                continue
            
            report_path = session_dir / 'report.json'
            if report_path.exists():
                with open(report_path, 'r', encoding='utf-8') as f:
                    session_report = json.load(f)
                    if 'score' in session_report:
                        chapter_sessions.append({
                            'session_id': session_id,
                            'score': session_report['score'],
                            'end_time': session_report.get('end_time', ''),
                        })
    
    if len(chapter_sessions) >= 2:
        lines.append(f"本章练习次数: {len(chapter_sessions)}\n")
        
        first_score = chapter_sessions[0]['score']
        latest_score = chapter_sessions[-1]['score']
        improvement = latest_score - first_score
        
        lines.append(f"首次得分: {first_score}\n")
        lines.append(f"最近得分: {latest_score}\n")
        lines.append(f"提升: {improvement:+d}分 {'📈' if improvement > 0 else '📉'}\n")
        
        lines.append("\n成绩变化:\n")
        score_trend = [str(s['score']) for s in chapter_sessions]
        lines.append(" → ".join(score_trend) + "\n")
    else:
        lines.append("暂无历史数据，继续练习后将显示进步趋势。\n")
    
    return '\n'.join(lines)


def main():
    args = parse_args()
    
    # 确定要分析的Session
    session_id = args.session
    
    if not session_id:
        if args.latest:
            session_id = get_latest_session(chapter=args.chapter)
            if not session_id:
                logger.error("未找到任何Session")
                return
        elif args.chapter:
            session_id = get_latest_session(chapter=args.chapter)
            if not session_id:
                logger.error(f"未找到章节 {args.chapter} 的Session")
                return
    
    if not session_id:
        logger.error("请指定 --session 或 --latest 参数")
        return
    
    # 加载报告
    report = load_session_report(session_id)
    if not report:
        return
    
    # 生成报告
    summary_text = generate_exam_report(report)
    
    # 输出
    if args.output:
        output_path = args.output
    else:
        session_dir = SESSIONS_DIR / session_id
        output_path = session_dir / 'summary.md'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(summary_text, encoding='utf-8')
    
    logger.info(f"考试分析报告已保存: {output_path}")
    
    # 打印到控制台
    print("\n" + "="*60)
    print(summary_text)


if __name__ == '__main__':
    main()