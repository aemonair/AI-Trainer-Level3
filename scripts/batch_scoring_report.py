#!/usr/bin/env python3
"""
批量生成评分报告

功能：
1. 查找所有章节的练习文件
2. 使用 AST 评分标准进行评分
3. 生成汇总报告（Markdown + CSV）

用法:
  python3 scripts/batch_scoring_report.py
  python3 scripts/batch_scoring_report.py --chapters 2.2.2,2.2.3,2.2.4
  python3 scripts/batch_scoring_report.py --mode practice
"""
from pathlib import Path
import json
import argparse
import logging
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SCORING_DIR = ROOT / 'scoring'
REPORTS_DIR = ROOT / 'reports'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='批量生成评分报告')
    parser.add_argument('--chapters', type=str, help='指定章节号，逗号分隔')
    parser.add_argument('--mode', type=str, default='exam', choices=['exam', 'practice'], help='评分模式')
    return parser.parse_args()


def find_latest_practice(chapter: str) -> Path:
    """查找章节的最新练习文件"""
    materials_dir = ROOT / f'{chapter}-materials'
    if not materials_dir.exists():
        return None
    
    # 查找所有练习文件（排除 test_ 开头的）
    practice_files = list(materials_dir.glob('*practice*.ipynb'))
    practice_files = [f for f in practice_files if not f.name.startswith('test_')]
    
    if not practice_files:
        return None
    
    # 按修改时间排序，返回最新的
    return sorted(practice_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]


def score_chapter(chapter: str, practice_file: Path, mode: str) -> Dict:
    """对单个章节进行评分"""
    import sys
    sys.path.insert(0, 'scripts')
    from scoring_validator import (
        load_scoring_schema,
        score_practice_v2,
    )
    
    schema = load_scoring_schema(chapter)
    if not schema:
        return None
    
    result = score_practice_v2(schema, practice_file, mode=mode)
    if not result:
        return None
    
    result['chapter'] = chapter
    result['practice_file'] = str(practice_file)
    
    return result


def generate_markdown_report(results: List[Dict], mode: str) -> str:
    """生成 Markdown 格式的报告"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    md = []
    md.append(f"# 批量评分报告 - {mode.upper()} 模式\n")
    md.append(f"生成时间: {now}\n")
    md.append(f"评分章节数: {len(results)}\n")
    
    # 汇总表
    md.append("## 📊 汇总\n")
    md.append("| 章节 | 总分 | 得分 | 正确率 | 练习文件 |")
    md.append("|------|------|------|--------|----------|")
    
    for r in results:
        chapter = r['chapter']
        total = r['total_score']
        earned = r['earned_score']
        pct = r['percentage']
        practice_file = Path(r['practice_file']).name
        md.append(f"| {chapter} | {total} | {earned} | {pct:.1f}% | {practice_file} |")
    
    # 详细报告
    md.append("\n## 📝 详细评分\n")
    
    for r in results:
        chapter = r['chapter']
        items = r.get('details', [])
        md.append(f"\n### {chapter} 章\n")
        md.append(f"- **总分**: {r['earned_score']}/{r['total_score']} ({r['percentage']}%)\n")
        md.append(f"- **练习文件**: `{r['practice_file']}`\n")
        
        # 难度分布
        difficulty_stats = {}
        for item in items:
            diff = item.get('difficulty', 'unknown')
            if diff not in difficulty_stats:
                difficulty_stats[diff] = {'passed': 0, 'total': 0}
            difficulty_stats[diff]['total'] += 1
            if item.get('correct'):
                difficulty_stats[diff]['passed'] += 1
        
        if difficulty_stats:
            md.append(f"- **难度分布**:\n")
            for diff, stats in difficulty_stats.items():
                md.append(f"  - {diff}: {stats['passed']}/{stats['total']}\n")
        
        # 题目详情
        md.append(f"\n| 题号 | 难度 | 描述 | 得分 | 状态 |\n")
        md.append(f"|------|------|------|------|------|\n")
        
        for item in items:
            status = '✅' if item.get('correct') else '❌'
            desc = item.get('description', '')[:30]
            md.append(f"| {item.get('item_id', '?')} | {item.get('difficulty', '?')} | {desc} | {item.get('earned', 0)}/{item.get('max', 0)} | {status} |\n")
    
    return '\n'.join(md)


def generate_csv_report(results: List[Dict]) -> str:
    """生成 CSV 格式的报告"""
    lines = []
    lines.append("chapter,total_score,earned_score,percentage,practice_file,item_id,description,difficulty,earned,max,correct")
    
    for r in results:
        chapter = r['chapter']
        total = r['total_score']
        earned = r['earned_score']
        pct = r['percentage']
        practice_file = r['practice_file']
        items = r.get('details', [])
        
        for item in items:
            lines.append(f"{chapter},{total},{earned},{pct:.1f},{practice_file},{item.get('item_id','')},{item.get('description','')},{item.get('difficulty','')},{item.get('earned',0)},{item.get('max',0)},{item.get('correct',False)}")
    
    return '\n'.join(lines)


def main():
    args = parse_args()
    
    # 确定要评分的章节
    if args.chapters:
        chapters = [c.strip() for c in args.chapters.split(',')]
    else:
        # 自动查找所有章节
        v2_files = list(SCORING_DIR.glob('*_ast.json'))
        chapters = [f.stem.replace('_ast', '') for f in sorted(v2_files)]
    
    logger.info(f"\n{'='*70}")
    logger.info(f"批量评分报告生成")
    logger.info(f"{'='*70}")
    logger.info(f"评分章节: {len(chapters)}")
    logger.info(f"评分模式: {args.mode}")
    logger.info(f"章节列表: {', '.join(chapters)}\n")
    
    results = []
    skipped = []
    
    for chapter in chapters:
        practice_file = find_latest_practice(chapter)
        
        if not practice_file:
            logger.warning(f"⚠️  跳过: {chapter} - 未找到练习文件")
            skipped.append(chapter)
            continue
        
        logger.info(f"📝 评分: {chapter} -> {practice_file.name}")
        result = score_chapter(chapter, practice_file, args.mode)
        
        if result:
            results.append(result)
            logger.info(f"   ✅ 得分: {result['earned_score']}/{result['total_score']} ({result['percentage']}%)")
        else:
            logger.warning(f"   ❌ 评分失败")
            skipped.append(chapter)
    
    # 生成报告
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Markdown 报告
    md_report = generate_markdown_report(results, args.mode)
    md_path = REPORTS_DIR / f'batch_scoring_{args.mode}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    logger.info(f"\n💾 Markdown 报告: {md_path}")
    
    # CSV 报告
    csv_report = generate_csv_report(results)
    csv_path = REPORTS_DIR / f'batch_scoring_{args.mode}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_report)
    logger.info(f"💾 CSV 报告: {csv_path}")
    
    # 汇总统计
    logger.info(f"\n{'='*70}")
    logger.info(f"评分完成: {len(results)} 个章节已评分, {len(skipped)} 个跳过")
    if results:
        avg_score = sum(r['percentage'] for r in results) / len(results)
        logger.info(f"平均得分: {avg_score:.1f}%")
    logger.info(f"{'='*70}\n")


if __name__ == '__main__':
    main()