#!/usr/bin/env python3
"""
从 .doc 文件中提取所有题目内容，保存到 questions/ 目录

用法:
  python3 scripts/extract_questions_from_doc.py
"""
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / 'questions'
DOC_PATH = ROOT / '4-04-05-05_3_20250701' / '第4部分_人工智能训练师_3级_操作技能复习题.doc'


def extract_questions_from_text(text: str) -> list:
    """从文本中提取所有题目"""
    questions = []
    
    # 匹配试题单模式：试题代码：X.X.X（有数字的）
    # 格式：试题代码：1.1.4\n试题名称：...\n考核时间：...
    pattern = r'试题代码[：:]\s*([\d.]+)\s*\n试题名称[：:]\s*(.+?)\s*\n考核时间[：:]\s*(.+?)(?=\n|$)'
    
    for match in re.finditer(pattern, text):
        code = match.group(1).strip()
        name = match.group(2).strip()
        time = match.group(3).strip()
        
        # 提取该试题的完整内容
        # 从"试题代码"开始到下一个"试题代码"或文件结尾
        start = match.start()
        next_match = re.search(r'试题代码[：:]\s*[\d.]+', text[start + 10:])
        if next_match:
            end = start + 10 + next_match.start()
        else:
            end = len(text)
        
        content = text[start:end].strip()
        
        questions.append({
            'code': code,
            'name': name,
            'time': time,
            'content': content
        })
    
    return questions


def clean_content(content: str) -> str:
    """清理内容格式"""
    # 移除多余的空格和换行
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content


def main():
    # 使用 textutil 转换 .doc 为文本
    result = subprocess.run(
        ['textutil', '-convert', 'txt', '-stdout', str(DOC_PATH)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ 转换失败: {result.stderr}")
        sys.exit(1)
    
    text = result.stdout
    
    # 提取题目
    questions = extract_questions_from_text(text)
    
    if not questions:
        print("❌ 没有找到题目")
        sys.exit(1)
    
    # 创建 questions 目录
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 保存每个题目
    for q in questions:
        # 清理文件名中的非法字符
        safe_name = q['name'].replace('/', '_').replace('\\', '_')
        filename = f"{q['code']}_{safe_name}.md"
        filepath = QUESTIONS_DIR / filename
        
        # 生成 Markdown 格式
        md_content = f"""# 人工智能训练师(三级)操作技能考核 试题单

**准考证号**: __________  
**试题代码**: {q['code']}  
**试题名称**: {q['name']}  
**考核时间**: {q['time']}

---

{clean_content(q['content'])}
"""
        filepath.write_text(md_content, encoding='utf-8')
        print(f"✅ 已生成: {filename}")
    
    print(f"\n📊 共提取 {len(questions)} 个题目")


if __name__ == '__main__':
    main()