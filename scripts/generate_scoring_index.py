#!/usr/bin/env python3
"""
生成评分标准汇总索引文件
读取 scoring/*.json 并生成 scoring/scoring_index.json
"""
import json
import os
from pathlib import Path

scoring_dir = Path(__file__).resolve().parent.parent / 'scoring'
all_chapters = {}

for json_file in sorted(scoring_dir.glob('*.json')):
    if json_file.name == 'scoring_index.json':
        continue
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chapter = data['chapter']
    all_chapters[chapter] = {
        'chapter': chapter,
        'total_score': data['total_score'],
        'items_count': len(data['items']),
        'items': data['items']
    }

summary = {
    'metadata': {
        'total_chapters': len(all_chapters),
        'total_items': sum(c['items_count'] for c in all_chapters.values()),
        'total_score': sum(c['total_score'] for c in all_chapters.values()),
        'generated_at': '2026-08-06'
    },
    'chapters': all_chapters
}

output_path = scoring_dir / 'scoring_index.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"已生成: {output_path}")
print(f"章节数: {summary['metadata']['total_chapters']}")
print(f"评分项: {summary['metadata']['total_items']}")
print(f"总分: {summary['metadata']['total_score']}")

modules = {
    '1.1': '业务数据处理流程设计',
    '2.1': '数据清洗和标注流程设计',
    '2.2': '模型开发与测试',
    '3.2': '模型交互流程设计'
}

for module_prefix, module_name in modules.items():
    module_chapters = {k: v for k, v in all_chapters.items() if k.startswith(module_prefix)}
    if module_chapters:
        module_score = sum(c['total_score'] for c in module_chapters.values())
        module_items = sum(c['items_count'] for c in module_chapters.values())
        print(f"\n{module_prefix} {module_name}")
        print(f"  章节: {len(module_chapters)}, 评分项: {module_items}, 总分: {module_score}")
        for ch in sorted(module_chapters.keys()):
            info = module_chapters[ch]
            print(f"  - {ch}: {info['items_count']}项, {info['total_score']}分")