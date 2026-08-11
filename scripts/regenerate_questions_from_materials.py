#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 materials 目录重新生成 questions 目录
使用PDF原始内容 + Markdown清晰格式
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATERIALS_DIR = ROOT
QUESTIONS_DIR = ROOT / 'questions'
QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)

def extract_chapter(filename: str) -> str:
    """从文件名提取章节号"""
    match = re.search(r'(\d+\.\d+\.\d+)', filename)
    return match.group(1) if match else None

def clean_materials_content(content: str) -> str:
    """清理materials中的原始内容"""
    # 移除分页标记
    content = re.sub(r'<!-- 第 \d+ 页 -->', '', content)
    # 移除"第X 部分"等前缀
    content = re.sub(r'^第\d+\s*部分\s*$', '', content, flags=re.MULTILINE)
    # 移除"操作技能复习题"
    content = re.sub(r'操作技能复习题', '', content)
    # 移除重复的标题
    content = re.sub(r'人工智能训练师[（(]三级[）)]操作技能考核\s*\n试题单', '', content)
    # 移除"准考证号："行
    content = re.sub(r'^准考证号：.*$', '', content, flags=re.MULTILINE)
    # 移除"试题代码："行
    content = re.sub(r'^试题代码：.*$', '', content, flags=re.MULTILINE)
    # 移除"测量分评分表"
    content = re.sub(r'测量分评分表', '', content)
    # 移除"试题评分表"
    content = re.sub(r'试题评分表', '', content)
    # 清理多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()

def extract_sections(content: str) -> dict:
    """提取各个部分"""
    sections = {}
    
    # 提取标题
    title_match = re.search(r'# (.+?)\n', content)
    if title_match:
        sections['title'] = title_match.group(1).strip()
    
    # 提取考核时间
    time_match = re.search(r'考核时间[：:]\s*(\d+min)', content)
    if time_match:
        sections['time'] = time_match.group(1)
    
    # 提取场地设备要求
    equipment_match = re.search(r'## 1\. 场地设备要求\s*\n(.*?)(?=## 2\. 工作任务|$)', content, re.DOTALL)
    if equipment_match:
        sections['equipment'] = equipment_match.group(1).strip()
    
    # 提取工作任务
    task_match = re.search(r'## 2\. 工作任务\s*\n(.*?)(?=## 3\. 技能要求|$)', content, re.DOTALL)
    if task_match:
        sections['task'] = task_match.group(1).strip()
    
    # 提取技能要求
    skills_match = re.search(r'## 3\. 技能要求\s*\n(.*?)(?=## 4\. 质量指标|$)', content, re.DOTALL)
    if skills_match:
        sections['skills'] = skills_match.group(1).strip()
    
    # 提取质量指标
    quality_match = re.search(r'## 4\. 质量指标\s*\n(.*?)(?=##|$)', content, re.DOTALL)
    if quality_match:
        sections['quality'] = quality_match.group(1).strip()
    
    # 提取评分细则（表格部分）
    scoring_match = re.search(r'\| 细则编号.*?(?=\n\n|\Z)', content, re.DOTALL)
    if scoring_match:
        sections['scoring'] = scoring_match.group(0).strip()
    
    return sections

def format_equipment(equipment: str) -> str:
    """格式化场地设备要求"""
    # 如果已经是列表格式，直接返回
    if '(1)' in equipment or '1.' in equipment:
        return equipment
    # 否则按分号或顿号分割
    if '；' in equipment:
        items = equipment.split('；')
    elif ';' in equipment:
        items = equipment.split(';')
    elif '、' in equipment:
        items = equipment.split('、')
    else:
        return equipment
    
    formatted = []
    for i, item in enumerate(items, 1):
        item = item.strip()
        if item:
            formatted.append(f"({i}) {item}")
    
    return '\n'.join(formatted)

def format_skills(skills: str) -> str:
    """格式化技能要求"""
    # 如果已经是列表格式，直接返回
    if '(1)' in skills or '1.' in skills:
        return skills
    # 否则按分号分割
    items = re.split(r'[;；]', skills)
    formatted = []
    for i, item in enumerate(items, 1):
        item = item.strip()
        if item:
            formatted.append(f"({i}) {item}")
    
    return '\n'.join(formatted) if formatted else skills

def format_quality(quality: str) -> str:
    """格式化质量指标"""
    # 如果已经是列表格式，直接返回
    if '(1)' in quality or '1.' in quality:
        return quality
    # 否则按分号分割
    items = re.split(r'[;；]', quality)
    formatted = []
    for i, item in enumerate(items, 1):
        item = item.strip()
        if item:
            formatted.append(f"({i}) {item}")
    
    return '\n'.join(formatted) if formatted else quality

def format_scoring_table(scoring: str) -> str:
    """格式化评分细则表格"""
    if not scoring:
        return ""
    
    lines = scoring.split('\n')
    formatted_lines = []
    
    for line in lines:
        if '|' not in line:
            continue
        # 清理"根据数据"等标记
        line = re.sub(r'根据数据.*$', '', line)
        # 清理"合计配分 XX"
        line = re.sub(r'合计配分\s*\d+', '', line)
        # 清理"合计得分"
        line = re.sub(r'合计得分', '', line)
        # 清理空单元格
        line = re.sub(r'\|\s*\|', '| |', line)
        
        cleaned = line.strip()
        if cleaned and '|' in cleaned:
            formatted_lines.append(cleaned)
    
    return '\n'.join(formatted_lines)

def generate_markdown(chapter: str, sections: dict) -> str:
    """生成Markdown格式的题目文件"""
    title = sections.get('title', '未知题目')
    time = sections.get('time', '20min')
    equipment = format_equipment(sections.get('equipment', ''))
    task = sections.get('task', '')
    skills = format_skills(sections.get('skills', ''))
    quality = format_quality(sections.get('quality', ''))
    scoring = format_scoring_table(sections.get('scoring', ''))
    
    lines = [
        f'# 人工智能训练师(三级)操作技能考核 试题单',
        '',
        f'**准考证号**: __________  ',
        f'**试题代码**: {chapter}  ',
        f'**试题名称**: {title}  ',
        f'**考核时间**: {time}',
        '',
        '---',
        '',
        '## 1. 场地设备要求',
        '',
        equipment,
        '',
        '---',
        '',
        '## 2. 工作任务',
        '',
        task,
        '',
        '---',
        '',
        '## 3. 技能要求',
        '',
        skills,
        '',
        '---',
        '',
        '## 4. 质量指标',
        '',
        quality,
        '',
        '---',
        '',
        '## 5. 评分细则',
        '',
    ]
    
    if scoring:
        # 添加表头（如果没有）
        if '| 细则编号 |' not in scoring and '| 编号 |' not in scoring:
            lines.append('| 编号 | 配分 | 评分细则描述 | 得分 |')
            lines.append('|------|------|-------------|------|')
        
        lines.append(scoring)
    
    lines.append('')
    
    return '\n'.join(lines)

def main():
    """主函数"""
    # 查找所有 materials 目录中的题目文件
    materials_files = {}
    for md_file in MATERIALS_DIR.glob('*-materials/*.md'):
        # 跳过不需要的文件
        if any(skip in md_file.name for skip in ['review', 'result', 'manifest', 'execution_log', '_guide']):
            continue
        
        chapter = extract_chapter(md_file.name)
        if chapter:
            materials_files[chapter] = md_file
    
    print(f"找到 {len(materials_files)} 个题目文件")
    
    generated = 0
    for chapter in sorted(materials_files.keys()):
        md_path = materials_files[chapter]
        
        # 读取并清理内容
        content = md_path.read_text(encoding='utf-8')
        cleaned = clean_materials_content(content)
        
        # 提取各个部分
        sections = extract_sections(cleaned)
        
        if not sections:
            print(f"⚠️ 跳过 {chapter}: 无法提取内容")
            continue
        
        # 生成Markdown
        md_content = generate_markdown(chapter, sections)
        
        # 保存文件
        title = sections.get('title', '未知题目')
        safe_name = title.replace('/', '_').replace('\\', '_')
        filename = f"{chapter}_{safe_name}.md"
        filepath = QUESTIONS_DIR / filename
        
        filepath.write_text(md_content, encoding='utf-8')
        print(f"✅ 已生成: {filename}")
        generated += 1
    
    print(f"\n📊 共生成 {generated} 个题目文件")

if __name__ == '__main__':
    main()