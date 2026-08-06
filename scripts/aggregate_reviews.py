#!/usr/bin/env python3
"""
成绩中心（Score Center）

核心功能：
1. 读取所有Session的report.json
2. 统计分析：成绩趋势、知识点掌握度、通过率、错题本
3. 生成综合性成绩报告

用法:
  python3 scripts/aggregate_reviews.py
  python3 scripts/aggregate_reviews.py --chapter 1.1.1
  python3 scripts/aggregate_reviews.py --output-dir reports
  python3 scripts/aggregate_reviews.py --format markdown
  python3 scripts/aggregate_reviews.py --format json
"""
from pathlib import Path
import csv
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
        description='成绩中心：聚合所有Session报告为统计分析'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        default=None,
        help='只统计特定章节（如 1.1.1）'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='输出目录（默认：ROOT/reports）'
    )
    parser.add_argument(
        '--format',
        choices=['markdown', 'json', 'csv'],
        default='markdown',
        help='输出格式（默认：markdown）'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制显示的Session数量'
    )
    return parser.parse_args()


def load_session_reports(chapter: Optional[str] = None) -> List[Dict]:
    """
    加载所有Session的report.json
    
    参数:
        chapter: 章节过滤（可选）
    
    返回:
        报告列表
    """
    if not SESSIONS_DIR.exists():
        logger.warning(f"Sessions目录不存在: {SESSIONS_DIR}")
        return []
    
    reports = []
    
    for session_dir in sorted(SESSIONS_DIR.iterdir()):
        if not session_dir.is_dir():
            continue
        
        session_id = session_dir.name
        
        if chapter and chapter not in session_id:
            continue
        
        report_path = session_dir / 'report.json'
        if not report_path.exists():
            continue
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                report['session_id'] = session_id
                report['session_dir'] = str(session_dir)
                reports.append(report)
        except Exception as e:
            logger.warning(f"加载报告失败 {report_path}: {e}")
    
    # 按时间排序
    reports.sort(key=lambda x: x.get('end_time', ''), reverse=True)
    
    return reports


def calculate_statistics(reports: List[Dict]) -> Dict:
    """
    计算综合统计信息
    
    返回:
        统计信息字典
    """
    if not reports:
        return {
            'total_sessions': 0,
            'avg_score': 0,
            'max_score': 0,
            'min_score': 0,
            'pass_rate': 0,
            'score_trend': [],
            'knowledge_points': {},
            'frequent_errors': [],
        }
    
    scores = [r['score'] for r in reports if 'score' in r]
    pass_threshold = 60
    passed = sum(1 for s in scores if s >= pass_threshold)
    
    # 成绩趋势（最近10次）
    score_trend = [r['score'] for r in reports[:10] if 'score' in r]
    score_trend.reverse()
    
    # 稳定性指标统计（从process_audit中提取）
    stability_scores = []
    process_penalties = []
    error_attempts_list = []
    
    for report in reports:
        audit = report.get('process_audit')
        if audit:
            stability_scores.append(audit.get('stability_score', 100))
            process_penalties.append(audit.get('process_penalty', 0))
            error_attempts_list.append(audit.get('error_attempts', 0))
    
    avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else None
    avg_process_penalty = sum(process_penalties) / len(process_penalties) if process_penalties else 0
    avg_error_attempts = sum(error_attempts_list) / len(error_attempts_list) if error_attempts_list else 0
    
    # 知识点统计
    kp_stats = defaultdict(lambda: {'scores': [], 'errors': 0})
    for report in reports:
        for error in report.get('errors', []):
            kp = error.get('knowledge_point', '其他')
            kp_stats[kp]['errors'] += 1
            kp_stats[kp]['scores'].append(report.get('score', 0))
    
    knowledge_points = {}
    for kp, stats in kp_stats.items():
        avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
        knowledge_points[kp] = {
            'avg_score': avg_score,
            'error_count': stats['errors'],
            'practice_count': len(stats['scores']),
        }
    
    # 高频错题
    error_counter = defaultdict(int)
    for report in reports:
        for error in report.get('errors', []):
            topic = error.get('topic', '未知')
            kp = error.get('knowledge_point', '其他')
            error_counter[f"{kp}.{topic}"] += 1
    
    frequent_errors = sorted(
        [{'topic': k, 'count': v} for k, v in error_counter.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:10]
    
    return {
        'total_sessions': len(reports),
        'avg_score': sum(scores) / len(scores) if scores else 0,
        'max_score': max(scores) if scores else 0,
        'min_score': min(scores) if scores else 0,
        'pass_rate': passed / len(scores) * 100 if scores else 0,
        'score_trend': score_trend,
        'knowledge_points': knowledge_points,
        'frequent_errors': frequent_errors,
        # 新增：稳定性指标
        'avg_stability_score': avg_stability,
        'avg_process_penalty': avg_process_penalty,
        'avg_error_attempts': avg_error_attempts,
        'stability_data_count': len(stability_scores),
    }


def generate_markdown_report(stats: Dict, reports: List[Dict], output_path: Path):
    """生成Markdown格式的成绩报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 📊 成绩中心报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 总体统计
        f.write("## 📈 总体统计\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 考试次数 | {stats['total_sessions']} |\n")
        f.write(f"| 平均分 | {stats['avg_score']:.1f} |\n")
        f.write(f"| 最高分 | {stats['max_score']} |\n")
        f.write(f"| 最低分 | {stats['min_score']} |\n")
        f.write(f"| 通过率 | {stats['pass_rate']:.1f}% |\n\n")
        
        # 稳定性指标（新增）
        if stats.get('stability_data_count', 0) > 0:
            f.write("## 🎯 稳定性指标\n\n")
            f.write(f"| 指标 | 数值 |\n")
            f.write(f"|------|------|\n")
            f.write(f"| 平均稳定性得分 | {stats['avg_stability_score']:.1f}/100 |\n")
            f.write(f"| 平均过程罚分 | {stats['avg_process_penalty']:.1f}分 |\n")
            f.write(f"| 平均错误尝试次数 | {stats['avg_error_attempts']:.1f}次 |\n")
            f.write(f"| 有审计数据的考试 | {stats['stability_data_count']}次 |\n\n")
            
            # 稳定性评级
            if stats['avg_stability_score'] >= 90:
                stability_level = "✅ 稳定发挥（考试时不易紧张）"
            elif stats['avg_stability_score'] >= 70:
                stability_level = "🟡 中等稳定（偶尔会犯小错）"
            else:
                stability_level = "⚠️ 波动较大（需要加强熟练度）"
            
            f.write(f"**稳定性评级**: {stability_level}\n\n")
        
        # 成绩趋势
        if stats['score_trend']:
            f.write("## 📊 成绩趋势（最近10次）\n\n")
            trend_str = " → ".join([str(s) for s in stats['score_trend']])
            f.write(f"{trend_str}\n\n")
        
        # 知识点掌握度
        if stats['knowledge_points']:
            f.write("## 🎯 知识点掌握度\n\n")
            f.write("| 知识点 | 平均分 | 练习次数 | 错误次数 | 掌握度 |\n")
            f.write("|--------|--------|---------|---------|--------|\n")
            
            for kp, kp_stats in sorted(stats['knowledge_points'].items()):
                avg = kp_stats['avg_score']
                if avg >= 85:
                    level = "✅ 优秀"
                elif avg >= 70:
                    level = "✅ 良好"
                elif avg >= 60:
                    level = "🟡 一般"
                else:
                    level = "⚠️ 需加强"
                
                f.write(
                    f"| {kp} | {avg:.1f} | "
                    f"{kp_stats['practice_count']} | "
                    f"{kp_stats['error_count']} | "
                    f"{level} |\n"
                )
            f.write("\n")
        
        # 高频错题
        if stats['frequent_errors']:
            f.write("## 🚨 高频错题\n\n")
            for i, err in enumerate(stats['frequent_errors'], 1):
                f.write(f"{i}. {err['topic']} - 错误{err['count']}次\n")
            f.write("\n")
        
        # 最近考试记录
        f.write("## 📝 最近考试记录\n\n")
        f.write("| 会话ID | 章节 | 得分 | 耗时 | 时间 |\n")
        f.write("|--------|------|------|------|------|\n")
        
        for report in reports[:10]:
            session_id = report.get('session_id', '未知')
            chapter = report.get('chapter', '未知')
            score = report.get('score', 'N/A')
            duration = report.get('duration_minutes', 'N/A')
            end_time = report.get('end_time', '未知')[:16]
            
            duration_str = f"{duration}分钟" if duration != 'N/A' else 'N/A'
            
            f.write(
                f"| {session_id} | {chapter} | "
                f"{score} | {duration_str} | "
                f"{end_time} |\n"
            )


def generate_json_report(stats: Dict, reports: List[Dict], output_path: Path):
    """生成JSON格式的成绩报告"""
    report_data = {
        'generated_at': datetime.now().isoformat(),
        'statistics': stats,
        'recent_sessions': [
            {
                'session_id': r.get('session_id'),
                'chapter': r.get('chapter'),
                'score': r.get('score'),
                'duration_minutes': r.get('duration_minutes'),
                'end_time': r.get('end_time'),
            }
            for r in reports[:10]
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)


def generate_csv_report(reports: List[Dict], output_path: Path):
    """生成CSV格式的成绩报告"""
    fieldnames = [
        'session_id', 'chapter', 'score', 'total_score',
        'duration_minutes', 'end_time', 'errors_count'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for report in reports:
            writer.writerow({
                'session_id': report.get('session_id', ''),
                'chapter': report.get('chapter', ''),
                'score': report.get('score', ''),
                'total_score': report.get('total_score', ''),
                'duration_minutes': report.get('duration_minutes', ''),
                'end_time': report.get('end_time', ''),
                'errors_count': len(report.get('errors', [])),
            })


def main():
    args = parse_args()
    
    global ROOT
    ROOT = Path('.').resolve()
    SESSIONS_DIR = ROOT / 'sessions'
    
    # 确定输出目录
    outdir = args.output_dir if args.output_dir else ROOT / 'reports'
    outdir.mkdir(parents=True, exist_ok=True)
    
    # 加载所有Session报告
    logger.info(f"加载Session报告...")
    reports = load_session_reports(chapter=args.chapter)
    
    if not reports:
        logger.warning("未找到任何Session报告")
        logger.info("请先使用 create_timestamped_practice.py 创建Session，然后使用 validate_practice.py --session 进行评分")
        return
    
    logger.info(f"成功加载 {len(reports)} 个Session报告")
    
    # 计算统计信息
    stats = calculate_statistics(reports)
    
    # 生成报告
    if args.format == 'markdown':
        output_path = outdir / 'score_center_report.md'
        generate_markdown_report(stats, reports, output_path)
        logger.info(f"Markdown报告已生成: {output_path}")
    
    elif args.format == 'json':
        output_path = outdir / 'score_center_report.json'
        generate_json_report(stats, reports, output_path)
        logger.info(f"JSON报告已生成: {output_path}")
    
    elif args.format == 'csv':
        output_path = outdir / 'score_center_report.csv'
        generate_csv_report(reports, output_path)
        logger.info(f"CSV报告已生成: {output_path}")
    
    # 打印摘要
    print("\n" + "="*60)
    print("📊 成绩中心摘要")
    print("="*60)
    print(f"考试次数: {stats['total_sessions']}")
    print(f"平均分: {stats['avg_score']:.1f}")
    print(f"最高分: {stats['max_score']}")
    print(f"最低分: {stats['min_score']}")
    print(f"通过率: {stats['pass_rate']:.1f}%")
    
    if stats['score_trend']:
        print(f"\n成绩趋势: {' → '.join([str(s) for s in stats['score_trend']])}")
    
    # 稳定性指标摘要
    if stats.get('stability_data_count', 0) > 0:
        print(f"\n🎯 稳定性指标:")
        print(f"  平均稳定性得分: {stats['avg_stability_score']:.1f}/100")
        print(f"  平均过程罚分: {stats['avg_process_penalty']:.1f}分")
        print(f"  平均错误尝试: {stats['avg_error_attempts']:.1f}次")
    
    if stats['frequent_errors']:
        print(f"\n高频错题:")
        for i, err in enumerate(stats['frequent_errors'][:5], 1):
            print(f"  {i}. {err['topic']} - 错误{err['count']}次")


if __name__ == '__main__':
    main()