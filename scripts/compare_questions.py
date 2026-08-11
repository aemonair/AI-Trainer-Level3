#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比 materials 和 questions 目录中的题目文件
找出差异并生成对比报告
"""
import re
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parent.parent
MATERIALS_DIR = ROOT
QUESTIONS_DIR = ROOT / 'questions'
REPORTS_DIR = ROOT / 'reports'
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def extract_chapter(filename: str) -> str:
    """从文件名提取章节号"""
    match = re.search(r'(\d+\.\d+\.\d+)', filename)
    return match.group(1) if match else None

def clean_text(text: str) -> str:
    """清理文本，移除格式标记"""
    # 移除分页标记
    text = re.sub(r'<!-- 第 \d+ 页 -->', '', text)
    # 移除Markdown格式标记
    text = re.sub(r'[#*\-_`]', '', text)
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度"""
    clean1 = clean_text(text1)
    clean2 = clean_text(text2)
    return SequenceMatcher(None, clean1, clean2).ratio()

def compare_files(materials_file: Path, questions_file: Path) -> dict:
    """对比两个文件"""
    materials_content = materials_file.read_text(encoding='utf-8')
    questions_content = questions_file.read_text(encoding='utf-8')
    
    similarity = calculate_similarity(materials_content, questions_content)
    
    # 提取关键部分进行对比
    materials_clean = clean_text(materials_content)
    questions_clean = clean_text(questions_content)
    
    return {
        'chapter': extract_chapter(materials_file.name),
        'materials_file': materials_file.name,
        'questions_file': questions_file.name,
        'similarity': similarity,
        'materials_length': len(materials_content),
        'questions_length': len(questions_content),
    }

def main():
    """主函数"""
    # 查找materials目录中的题目文件
    materials_files = {}
    for md_file in MATERIALS_DIR.glob('*-materials/*.md'):
        # 跳过review和result文件
        if 'review' in md_file.name or 'result' in md_file.name:
            continue
        if '_guide.md' in md_file.name:
            continue
            
        chapter = extract_chapter(md_file.name)
        if chapter:
            materials_files[chapter] = md_file
    
    # 查找questions目录中的题目文件
    questions_files = {}
    for md_file in QUESTIONS_DIR.glob('*.md'):
        chapter = extract_chapter(md_file.name)
        if chapter:
            questions_files[chapter] = md_file
    
    # 找出共同存在的章节
    common_chapters = set(materials_files.keys()) & set(questions_files.keys())
    
    print(f"📁 materials目录: {len(materials_files)} 个题目文件")
    print(f"📁 questions目录: {len(questions_files)} 个题目文件")
    print(f"📊 共同章节: {len(common_chapters)} 个")
    print()
    
    # 对比文件
    results = []
    for chapter in sorted(common_chapters):
        result = compare_files(materials_files[chapter], questions_files[chapter])
        results.append(result)
    
    # 生成报告
    report_path = REPORTS_DIR / 'questions_comparison.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('# Questions 目录对比报告\n\n')
        f.write(f'**生成时间**: 2026-08-08\n\n')
        f.write(f'## 统计信息\n\n')
        f.write(f'- materials目录: {len(materials_files)} 个题目文件\n')
        f.write(f'- questions目录: {len(questions_files)} 个题目文件\n')
        f.write(f'- 共同章节: {len(common_chapters)} 个\n\n')
        
        f.write('## 详细对比\n\n')
        f.write('| 章节 | 相似度 | materials文件 | questions文件 | 说明 |\n')
        f.write('|------|--------|--------------|---------------|------|\n')
        
        for r in results:
            similarity_pct = f"{r['similarity']*100:.1f}%"
            status = "✅ 高度相似" if r['similarity'] > 0.8 else "⚠️ 有差异" if r['similarity'] > 0.6 else "❌ 差异较大"
            f.write(f"| {r['chapter']} | {similarity_pct} | {r['materials_file']} | {r['questions_file']} | {status} |\n")
        
        f.write('\n---\n\n')
        f.write('## 建议\n\n')
        f.write('- **高度相似 (>80%)**: 内容基本一致，可以保留questions目录（格式更清晰）\n')
        f.write('- **有差异 (60-80%)**: 建议对比具体内容，保留更准确的版本\n')
        f.write('- **差异较大 (<60%)**: 需要手动检查，可能是来源不同\n')
    
    # 打印结果
    for r in results:
        similarity_pct = f"{r['similarity']*100:.1f}%"
        status = "✅ 高度相似" if r['similarity'] > 0.8 else "⚠️ 有差异" if r['similarity'] > 0.6 else "❌ 差异较大"
        print(f"{r['chapter']}: {similarity_pct} - {status}")
    
    print(f"\n📊 详细报告已保存到: {report_path}")

if __name__ == '__main__':
    main()