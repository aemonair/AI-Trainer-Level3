#!/usr/bin/env python3
"""
Review 聚合报告生成器

从所有 *_review.md 文件中提取错误信息，生成聚合报告。

用法：
    uv run python3 scripts/review_summary.py

输出：
    reports/reviews_summary.md  - Markdown 汇总报告
    reports/reviews_summary.csv - CSV 数据文件
"""

import os
import re
import glob
import csv
from collections import defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT, 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)


def parse_review_file(filepath):
    """解析单个 Review 文件，提取关键信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    info = {
        'filepath': filepath,
        'chapter': 'unknown',
        'timestamp': 'unknown',
        'score': '?/?',
        'percentage': 0,
        'errors': [],
        'error_count': 0,
    }

    # 提取章节号和标题
    title_match = re.search(r'^#\s+([\d.]+)\s+练习\s+Review\s*[-–]\s*(\S+)', content, re.MULTILINE)
    if title_match:
        info['chapter'] = title_match.group(1)
        info['timestamp'] = title_match.group(2)

    # 提取总分
    score_match = re.search(r'\*\*总分:\s*([\d.]+)\s*/\s*([\d.]+)\s*\(([\d.]+)%\)\*\*', content)
    if score_match:
        info['score'] = f"{score_match.group(1)}/{score_match.group(2)}"
        info['percentage'] = float(score_match.group(3))
        info['earned'] = float(score_match.group(1))
        info['total'] = float(score_match.group(2))

    # 提取错误记录
    error_blocks = re.findall(
        r'### 错误\d+[：:]\s*(.+?)\n'
        r'- \*\*错误代码\*\*[：:]\s*`(.+?)`\n'
        r'- \*\*正确写法\*\*[：:]\s*`(.+?)`\n'
        r'- \*\*原因\*\*[：:]\s*(.+?)(?:\n|$)',
        content, re.DOTALL
    )

    for item_id, err_code, correct_code, reason in error_blocks:
        info['errors'].append({
            'item_id': item_id.strip(),
            'error_code': err_code.strip()[:60],
            'correct_code': correct_code.strip()[:60],
            'reason': reason.strip()[:80],
        })

    info['error_count'] = len(info['errors'])
    return info


def classify_error(reason):
    """根据原因描述分类错误类型"""
    if '参数' in reason:
        return '参数错误'
    if '拼写' in reason:
        return '拼写错误'
    if '语法' in reason:
        return '语法错误'
    if '逻辑' in reason or '索引' in reason:
        return '逻辑/索引错误'
    if '格式' in reason or '匹配' in reason:
        return '格式不匹配'
    if '函数' in reason:
        return '函数使用错误'
    return '其他'


def main():
    search_paths = [
        os.path.join(ROOT, 'sessions', '**', '*_review.md'),
        os.path.join(ROOT, 'backup', '**', '*_review.md'),
    ]

    all_reviews = []
    seen = set()
    for pattern in search_paths:
        for f in glob.glob(pattern, recursive=True):
            if f in seen:
                continue
            seen.add(f)
            try:
                info = parse_review_file(f)
                all_reviews.append(info)
            except Exception as e:
                print(f'⚠️ 解析失败: {f} - {e}')

    # 按章节和时间排序
    all_reviews.sort(key=lambda x: (x['chapter'], x['timestamp']))

    # 按章节分组
    chapters = defaultdict(list)
    for r in all_reviews:
        chapters[r['chapter']].append(r)

    # ── 生成 Markdown ──
    md_lines = []
    md_lines.append('# 📊 练习 Review 聚合报告')
    md_lines.append('')
    md_lines.append(f'> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}')
    md_lines.append(f'> 共计 **{len(all_reviews)}** 个 Review 文件，覆盖 **{len(chapters)}** 个章节')
    md_lines.append('')
    md_lines.append('---')
    md_lines.append('')

    # 总体概览表
    md_lines.append('## 📈 总体概览')
    md_lines.append('')
    md_lines.append('| 章节 | Review数 | 平均分 | 最高分 | 最低分 | 总错误数 |')
    md_lines.append('|:----:|:--------:|:------:|:------:|:------:|:--------:|')

    for chapter in sorted(chapters.keys()):
        reviews = chapters[chapter]
        scores = [r['percentage'] for r in reviews if 'percentage' in r]
        errors = sum(r['error_count'] for r in reviews)
        avg = sum(scores) / len(scores) if scores else 0
        high = max(scores) if scores else 0
        low = min(scores) if scores else 0
        md_lines.append(f'| {chapter} | {len(reviews)} | {avg:.1f}% | {high:.1f}% | {low:.1f}% | {errors} |')

    md_lines.append('')
    md_lines.append('---')
    md_lines.append('')

    # 详细记录
    md_lines.append('## 📝 详细记录')
    md_lines.append('')

    for chapter in sorted(chapters.keys()):
        reviews = chapters[chapter]
        md_lines.append(f'### {chapter}')
        md_lines.append('')
        md_lines.append('| 时间 | 评分 | 错误数 | 错误详情 |')
        md_lines.append('|:----:|:----:|:------:|---------|')

        for r in reviews:
            score_display = r.get('score', '?/?')
            pct = f'({r.get("percentage", 0):.0f}%)' if 'percentage' in r else ''
            error_detail = '；'.join(
                f"{e['item_id']}: {e['reason'][:40]}"
                for e in r['errors']
            ) if r['errors'] else '无'

            file_link = f'[{r["timestamp"]}](file:///{r["filepath"]})'
            md_lines.append(f'| {file_link} | {score_display} {pct} | {r["error_count"]} | {error_detail} |')

        md_lines.append('')

    # 错误类型统计
    md_lines.append('---')
    md_lines.append('')
    md_lines.append('## 🔍 常见错误类型统计')
    md_lines.append('')

    error_categories = defaultdict(int)
    for r in all_reviews:
        for e in r['errors']:
            cat = classify_error(e['reason'])
            error_categories[cat] += 1

    md_lines.append('| 错误类型 | 出现次数 |')
    md_lines.append('|:--------:|:--------:|')
    for cat in sorted(error_categories.keys(), key=lambda x: -error_categories[x]):
        md_lines.append(f'| {cat} | {error_categories[cat]} |')

    md_lines.append('')

    md_path = os.path.join(REPORTS_DIR, 'reviews_summary.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    print(f'✅ Markdown 报告: {md_path}')

    # ── 生成 CSV ──
    csv_path = os.path.join(REPORTS_DIR, 'reviews_summary.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['章节', '时间戳', '得分', '得分率', '错误数', '错误详情', '文件路径'])
        for r in all_reviews:
            error_detail = '; '.join(
                f"{e['item_id']}: {e['reason']}"
                for e in r['errors']
            )
            writer.writerow([
                r['chapter'],
                r['timestamp'],
                r.get('score', ''),
                f"{r.get('percentage', 0):.1f}%",
                r['error_count'],
                error_detail,
                r['filepath'],
            ])
    print(f'✅ CSV 数据: {csv_path}')

    print(f'\n📊 统计摘要:')
    print(f'   总 Review 文件: {len(all_reviews)}')
    print(f'   覆盖章节: {len(chapters)}')
    print(f'   总错误数: {sum(r["error_count"] for r in all_reviews)}')
    scores = [r['percentage'] for r in all_reviews if 'percentage' in r]
    if scores:
        print(f'   平均得分率: {sum(scores) / len(scores):.1f}%')


if __name__ == '__main__':
    main()