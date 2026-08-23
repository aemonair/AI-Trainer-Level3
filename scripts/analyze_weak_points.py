#!/usr/bin/env python3
"""
薄弱点分析 & 再练习建议

分析所有历史session的practice数据，识别：
1. 各章节的掌握程度
2. 高频错误题目
3. 薄弱知识点
4. 需要再练习的题目清单

用法:
  python3 scripts/analyze_weak_points.py
  python3 scripts/analyze_weak_points.py --output reports/weak_points_analysis.md
"""
from pathlib import Path
import json
import re
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='薄弱点分析')
    parser.add_argument('--output', type=Path, help='输出文件路径')
    return parser.parse_args()


def extract_chapter(session_name: str) -> Optional[str]:
    """从session名称提取章节号"""
    match = re.search(r'chapter(\d+\.\d+\.\d+)', session_name)
    if match:
        return match.group(1)
    return None


def load_all_reports() -> List[Dict]:
    """加载所有report.json文件"""
    reports = []
    
    for report_path in SESSIONS_DIR.rglob('report.json'):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                report['source'] = str(report_path)
                report['session_name'] = report_path.parent.name
                report['chapter'] = extract_chapter(report_path.parent.name)
                reports.append(report)
        except Exception as e:
            logger.warning(f"加载失败 {report_path}: {e}")
    
    return reports


def load_all_review_files() -> List[Dict]:
    """加载所有review.md文件"""
    reviews = []
    
    for review_path in SESSIONS_DIR.rglob('*review.md'):
        try:
            content = review_path.read_text(encoding='utf-8')
            review = {
                'path': str(review_path),
                'session_name': review_path.parent.parent.name,
                'chapter': extract_chapter(review_path.parent.parent.name),
                'content': content,
                'errors': parse_review_errors(content),
                'score': parse_review_score(content),
            }
            reviews.append(review)
        except Exception as e:
            logger.warning(f"加载失败 {review_path}: {e}")
    
    return reviews


def load_all_scoring_results() -> List[Dict]:
    """加载所有scoring_result_v2_*.json文件"""
    results = []
    
    for scoring_path in SESSIONS_DIR.rglob('scoring_result_v2_*.json'):
        try:
            with open(scoring_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['source'] = str(scoring_path)
                data['session_name'] = scoring_path.parent.parent.name
                data['chapter'] = extract_chapter(scoring_path.parent.parent.name)
                data['scoring_type'] = 'exam' if 'exam' in scoring_path.name else 'practice'
                
                if not data.get('chapter'):
                    data['chapter'] = data.get('chapter')
                
                results.append(data)
        except Exception as e:
            logger.warning(f"加载失败 {scoring_path}: {e}")
    
    return results


def parse_review_errors(content: str) -> List[Dict]:
    """从review文件解析错误"""
    errors = []
    
    error_pattern = re.compile(
        r'### 错误\d+：(.*?)\n'
        r'- \*\*错误代码\*\*：`(.*?)`\n'
        r'- \*\*正确写法\*\*：`(.*?)`\n'
        r'- \*\*原因\*\*：(.*?)(?=\n###|\n##|$)',
        re.DOTALL
    )
    
    for match in error_pattern.finditer(content):
        errors.append({
            'type': match.group(1).strip(),
            'wrong_code': match.group(2).strip(),
            'correct_code': match.group(3).strip(),
            'reason': match.group(4).strip(),
        })
    
    return errors


def parse_review_score(content: str) -> Optional[Dict]:
    """从review文件解析分数"""
    score_match = re.search(r'总分:\s*(\d+)\s*/\s*(\d+)', content)
    if score_match:
        return {
            'earned': int(score_match.group(1)),
            'total': int(score_match.group(2)),
            'percentage': int(score_match.group(1)) / int(score_match.group(2)) * 100,
        }
    return None


def analyze_by_chapter(reports: List[Dict], scoring_results: List[Dict]) -> Dict:
    """按章节分析掌握程度"""
    chapter_stats = defaultdict(lambda: {
        'sessions': 0,
        'scores': [],
        'errors': [],
        'failed_items': [],
        'total_items': 0,
    })
    
    for report in reports:
        chapter = report.get('chapter')
        if not chapter:
            continue
        
        chapter_stats[chapter]['sessions'] += 1
        
        score = report.get('score')
        total = report.get('total_score')
        if score is not None and total is not None:
            chapter_stats[chapter]['scores'].append({
                'score': score,
                'total': total,
                'percentage': score / total * 100,
                'session': report.get('session_name', ''),
                'time': report.get('end_time', ''),
            })
        
        for error in report.get('errors', []):
            chapter_stats[chapter]['errors'].append(error)
    
    for result in scoring_results:
        chapter = result.get('chapter')
        if not chapter:
            continue
        
        chapter_stats[chapter]['sessions'] += 1
        
        score = result.get('earned_score') or result.get('score')
        total = result.get('total_score')
        if score is not None and total is not None:
            chapter_stats[chapter]['scores'].append({
                'score': score,
                'total': total,
                'percentage': score / total * 100,
                'session': result.get('session_name', ''),
                'time': result.get('end_time') or result.get('graded_at', ''),
                'type': result.get('scoring_type') or result.get('mode', ''),
            })
        
        details = result.get('details') or result.get('schema_details', [])
        for detail in details:
            chapter_stats[chapter]['total_items'] += 1
            if not detail.get('correct', True):
                chapter_stats[chapter]['failed_items'].append({
                    'item_id': detail.get('item_id'),
                    'description': detail.get('description'),
                    'session': result.get('session_name', ''),
                    'details': detail.get('details', ''),
                })
    
    return dict(chapter_stats)


def analyze_failed_items(scoring_results: List[Dict]) -> Dict:
    """分析错误题目频率"""
    item_errors = defaultdict(lambda: {
        'count': 0,
        'chapters': set(),
        'descriptions': set(),
        'sessions': [],
        'failed_rules': [],
    })
    
    for result in scoring_results:
        chapter = result.get('chapter', 'unknown')
        details = result.get('details') or result.get('schema_details', [])
        
        for detail in details:
            if not detail.get('correct', True):
                item_id = detail.get('item_id', 'unknown')
                key = f"{chapter}_{item_id}"
                
                item_errors[key]['count'] += 1
                item_errors[key]['chapters'].add(chapter)
                item_errors[key]['descriptions'].add(detail.get('description', ''))
                item_errors[key]['sessions'].append(result.get('session_name', ''))
                if detail.get('details'):
                    item_errors[key]['failed_rules'].append(detail.get('details', ''))
    
    for result in scoring_results:
        for error in result.get('errors', []):
            item_id = error.get('item_id')
            if item_id:
                chapter = result.get('chapter', 'unknown')
                key = f"{chapter}_{item_id}"
                if 'failed_rules' in error:
                    item_errors[key]['failed_rules'].extend(error.get('failed_rules', []))
    
    return dict(item_errors)


def analyze_error_types(reviews: List[Dict], scoring_results: List[Dict]) -> Dict:
    """分析错误类型分布"""
    error_types = defaultdict(lambda: {
        'count': 0,
        'examples': [],
        'chapters': set(),
    })
    
    for review in reviews:
        for error in review.get('errors', []):
            error_type = error.get('type', '未知')
            error_types[error_type]['count'] += 1
            error_types[error_type]['examples'].append({
                'wrong': error.get('wrong_code', ''),
                'correct': error.get('correct_code', ''),
                'reason': error.get('reason', ''),
            })
            if review.get('chapter'):
                error_types[error_type]['chapters'].add(review['chapter'])
    
    for result in scoring_results:
        for error in result.get('errors', []):
            kp = error.get('knowledge_point', '其他')
            error_type = f"知识点: {kp}"
            error_types[error_type]['count'] += 1
            if result.get('chapter'):
                error_types[error_type]['chapters'].add(result['chapter'])
    
    return dict(error_types)


def generate_recommendations(chapter_stats: Dict, failed_items: Dict, error_types: Dict) -> List[Dict]:
    """生成再练习建议"""
    recommendations = []
    
    for chapter, stats in sorted(chapter_stats.items()):
        if not stats['scores']:
            continue
        
        avg_score = sum(s['percentage'] for s in stats['scores']) / len(stats['scores'])
        max_score = max(s['percentage'] for s in stats['scores'])
        min_score = min(s['percentage'] for s in stats['scores'])
        
        failed_count = len(stats['failed_items'])
        
        if avg_score < 80 or failed_count > 2:
            priority = '高' if avg_score < 70 or failed_count > 5 else '中'
            
            failed_item_ids = set()
            for item in stats['failed_items']:
                failed_item_ids.add(item['item_id'])
            
            recommendations.append({
                'chapter': chapter,
                'priority': priority,
                'avg_score': avg_score,
                'max_score': max_score,
                'min_score': min_score,
                'practice_count': stats['sessions'],
                'failed_count': failed_count,
                'failed_items': sorted(failed_item_ids),
                'reason': f"平均分{avg_score:.1f}%，{failed_count}道题目出错",
            })
    
    recommendations.sort(key=lambda x: (0 if x['priority'] == '高' else 1, x['avg_score']))
    
    return recommendations


def generate_markdown_report(
    chapter_stats: Dict,
    failed_items: Dict,
    error_types: Dict,
    recommendations: List[Dict],
    reviews: List[Dict],
    scoring_results: List[Dict],
) -> str:
    """生成Markdown分析报告"""
    lines = []
    
    lines.append("# 📊 薄弱点分析报告")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    lines.append("\n## 📈 总体概况\n")
    
    total_sessions = len(set(r.get('session_name', '') for r in scoring_results))
    total_chapters = len(chapter_stats)
    total_errors = sum(len(r.get('errors', [])) for r in scoring_results)
    
    all_scores = []
    for stats in chapter_stats.values():
        for s in stats['scores']:
            all_scores.append(s['percentage'])
    
    if all_scores:
        avg_overall = sum(all_scores) / len(all_scores)
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 总练习次数 | {total_sessions} |")
        lines.append(f"| 涉及章节 | {total_chapters} |")
        lines.append(f"| 平均得分率 | {avg_overall:.1f}% |")
        lines.append(f"| 总错误次数 | {total_errors} |")
        lines.append("")
    
    lines.append("\n## 🎯 章节掌握度分析\n")
    lines.append("| 章节 | 练习次数 | 平均分 | 最高分 | 最低分 | 错误题目数 | 掌握度 |\n")
    lines.append("|------|---------|--------|--------|--------|-----------|--------|\n")
    
    for chapter in sorted(chapter_stats.keys()):
        stats = chapter_stats[chapter]
        if not stats['scores']:
            continue
        
        avg_score = sum(s['percentage'] for s in stats['scores']) / len(stats['scores'])
        max_score = max(s['percentage'] for s in stats['scores'])
        min_score = min(s['percentage'] for s in stats['scores'])
        failed_count = len(stats['failed_items'])
        
        if avg_score >= 90:
            level = "✅ 优秀"
        elif avg_score >= 80:
            level = "✅ 良好"
        elif avg_score >= 70:
            level = "🟡 一般"
        else:
            level = "⚠️ 需加强"
        
        lines.append(
            f"| {chapter} | {stats['sessions']} | "
            f"{avg_score:.1f}% | {max_score:.1f}% | {min_score:.1f}% | "
            f"{failed_count} | {level} |"
        )
    
    lines.append("\n\n## 🚨 高频错误题目 TOP 20\n")
    
    sorted_items = sorted(failed_items.items(), key=lambda x: x[1]['count'], reverse=True)[:20]
    
    lines.append("| 排名 | 章节-题号 | 错误次数 | 题目描述 | 常见错误原因 |\n")
    lines.append("|------|----------|---------|---------|-------------|\n")
    
    for i, (key, data) in enumerate(sorted_items, 1):
        chapters = ', '.join(data['chapters'])
        desc = ', '.join(data['descriptions'])
        failed_rules = data['failed_rules'][:1] if data['failed_rules'] else []
        reason = failed_rules[0][:50] if failed_rules else ''
        
        lines.append(f"| {i} | {key} | {data['count']} | {desc} | {reason} |")
    
    lines.append("\n\n## 🔍 错误类型分布\n")
    
    sorted_errors = sorted(error_types.items(), key=lambda x: x[1]['count'], reverse=True)
    
    lines.append("| 错误类型 | 出现次数 | 涉及章节 | 典型示例 |\n")
    lines.append("|---------|---------|---------|---------|\n")
    
    for error_type, data in sorted_errors[:15]:
        chapters = ', '.join(data['chapters'])
        example = data['examples'][0] if data['examples'] else {}
        wrong = example.get('wrong', '')[:30]
        
        lines.append(f"| {error_type} | {data['count']} | {chapters} | `{wrong}` |")
    
    lines.append("\n\n## 💡 再练习建议\n")
    
    if recommendations:
        lines.append("### 优先练习清单\n")
        lines.append("| 优先级 | 章节 | 平均分 | 练习次数 | 错误题目 | 建议 |\n")
        lines.append("|--------|------|--------|---------|---------|------|\n")
        
        for rec in recommendations:
            priority_icon = "🔴" if rec['priority'] == '高' else "🟡"
            failed_items_str = ', '.join(rec['failed_items'][:5])
            if len(rec['failed_items']) > 5:
                failed_items_str += f" 等{len(rec['failed_items'])}题"
            
            lines.append(
                f"| {priority_icon} {rec['priority']} | {rec['chapter']} | "
                f"{rec['avg_score']:.1f}% | {rec['practice_count']} | "
                f"{failed_items_str} | 重点练习错误题目，复习相关知识点 |"
            )
        
        lines.append("\n\n### 详细建议\n")
        
        for rec in recommendations:
            lines.append(f"\n#### {rec['chapter']} 章节\n")
            lines.append(f"- **平均分**: {rec['avg_score']:.1f}%")
            lines.append(f"- **练习次数**: {rec['practice_count']}")
            lines.append(f"- **错误题目**: {', '.join(rec['failed_items'])}")
            lines.append(f"- **建议**: 重新练习该章节，重点关注以下题目：")
            
            for item_id in rec['failed_items']:
                lines.append(f"  - 题目 {item_id}")
    else:
        lines.append("\n✅ 所有章节掌握良好，暂无需要特别练习的章节！\n")
    
    lines.append("\n\n## 📝 详细错误记录\n")
    
    for review in sorted(reviews, key=lambda x: x.get('chapter') or ''):
        if not review.get('errors'):
            continue
        
        chapter = review.get('chapter', '未知')
        lines.append(f"\n### {chapter} - {review['session_name']}\n")
        
        if review.get('score'):
            score = review['score']
            lines.append(f"得分: {score['earned']}/{score['total']} ({score['percentage']:.1f}%)\n")
        
        for i, error in enumerate(review['errors'], 1):
            lines.append(f"**错误{i}**: {error['type']}")
            lines.append(f"- 错误: `{error['wrong_code'][:80]}`")
            lines.append(f"- 正确: `{error['correct_code'][:80]}`")
            lines.append(f"- 原因: {error['reason'][:100]}\n")
    
    return '\n'.join(lines)


def main():
    args = parse_args()
    
    logger.info("加载所有报告文件...")
    reports = load_all_reports()
    logger.info(f"  找到 {len(reports)} 个report.json")
    
    logger.info("加载所有review文件...")
    reviews = load_all_review_files()
    logger.info(f"  找到 {len(reviews)} 个review.md")
    
    logger.info("加载所有评分结果...")
    scoring_results = load_all_scoring_results()
    logger.info(f"  找到 {len(scoring_results)} 个scoring_result文件")
    
    logger.info("\n分析章节掌握度...")
    chapter_stats = analyze_by_chapter(reports, scoring_results)
    
    logger.info("分析错误题目...")
    failed_items = analyze_failed_items(scoring_results)
    
    logger.info("分析错误类型...")
    error_types = analyze_error_types(reviews, scoring_results)
    
    logger.info("生成再练习建议...")
    recommendations = generate_recommendations(chapter_stats, failed_items, error_types)
    
    logger.info("生成报告...")
    report_content = generate_markdown_report(
        chapter_stats, failed_items, error_types, recommendations, reviews, scoring_results
    )
    
    output_path = args.output if args.output else ROOT / 'reports' / 'weak_points_analysis.md'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding='utf-8')
    
    logger.info(f"\n✅ 报告已生成: {output_path}")
    
    print("\n" + "="*60)
    print("📊 薄弱点分析摘要")
    print("="*60)
    
    all_scores = []
    for stats in chapter_stats.values():
        for s in stats['scores']:
            all_scores.append(s['percentage'])
    
    if all_scores:
        print(f"\n总体平均得分率: {sum(all_scores)/len(all_scores):.1f}%")
    
    print(f"\n涉及章节: {len(chapter_stats)}")
    print(f"错误题目总数: {len(failed_items)}")
    
    if recommendations:
        print(f"\n🔴 需要重点练习的章节: {len([r for r in recommendations if r['priority'] == '高'])}")
        print(f"🟡 建议复习的章节: {len([r for r in recommendations if r['priority'] == '中'])}")
        
        print("\n优先练习清单:")
        for rec in recommendations[:5]:
            icon = "🔴" if rec['priority'] == '高' else "🟡"
            print(f"  {icon} {rec['chapter']}: 平均{rec['avg_score']:.1f}%, {len(rec['failed_items'])}道题目出错")
    
    print(f"\n完整报告: {output_path}")


if __name__ == '__main__':
    main()