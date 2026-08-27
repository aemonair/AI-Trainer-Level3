#!/usr/bin/env python3
"""
验证知识体系覆盖率 - 检查是否覆盖所有20个章节的331道填空题
"""
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'

def get_latest_exam(chapter: str) -> dict:
    """获取指定章节最新的exam评分结果"""
    exam_files = list(SESSIONS_DIR.rglob(f'*{chapter}*/workspace/scoring_result_v2_exam.json'))
    if not exam_files:
        return None
    latest = max(exam_files, key=lambda x: x.stat().st_mtime)
    with open(latest, 'r', encoding='utf-8') as f:
        return json.load(f)

chapters = [
    '1.1.1', '1.1.2', '1.1.3', '1.1.4', '1.1.5',
    '2.1.1', '2.1.2', '2.1.3', '2.1.4', '2.1.5',
    '2.2.1', '2.2.2', '2.2.3', '2.2.4', '2.2.5',
    '3.2.1', '3.2.2', '3.2.3', '3.2.4', '3.2.5'
]

print("="*80)
print("📋 20个章节考试题覆盖率验证")
print("="*80)

total_questions = 0
covered_questions = 0
chapter_stats = []

for ch in chapters:
    exam = get_latest_exam(ch)
    if not exam:
        print(f"\n❌ {ch}: 未找到exam数据")
        continue
    
    details = exam.get('details', [])
    q_count = len(details)
    total_questions += q_count
    
    covered = 0
    for d in details:
        code = d.get('user_code', '')
        if code.strip():
            covered += 1
    
    covered_questions += covered
    chapter_stats.append({
        'chapter': ch,
        'title': exam.get('title', ''),
        'questions': q_count,
        'covered': covered,
        'score': exam.get('earned_score', 0),
        'max_score': exam.get('total_score', 0),
    })

print(f"\n📊 总体统计:")
print(f"  总章节数: {len(chapter_stats)}")
print(f"  总填空题数: {total_questions}")
print(f"  有代码的题目数: {covered_questions}")
print(f"  覆盖率: {covered_questions/total_questions*100:.1f}%")

print(f"\n📋 各章节详情:")
print(f"{'章节':<10} {'题目数':>6} {'有代码':>6} {'得分':>8} {'标题':<40}")
print("-"*80)
for s in chapter_stats:
    print(f"{s['chapter']:<10} {s['questions']:>6} {s['covered']:>6} {s['score']}/{s['max_score']:<6} {s['title'][:38]}")