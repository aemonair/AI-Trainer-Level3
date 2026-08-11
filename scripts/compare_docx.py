#!/usr/bin/env python3
"""比较两个版本的 docx 文件内容差异"""

from docx import Document
import os

BASE_DIR = "/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai"

def extract_docx_text(filepath):
    """提取 docx 文件的文本内容"""
    try:
        doc = Document(filepath)
        texts = []
        for para in doc.paragraphs:
            if para.text.strip():
                texts.append(para.text)
        return '\n'.join(texts)
    except Exception as e:
        return f"Error: {e}"

def compare_docx(chapter, prev_path, template_path):
    """比较两个 docx 文件"""
    print(f"\n{'='*60}")
    print(f"📄 章节 {chapter} 对比")
    print(f"{'='*60}")
    
    prev_text = extract_docx_text(prev_path)
    template_text = extract_docx_text(template_path)
    
    print(f"\n【Prev 版本】字符数: {len(prev_text)}")
    print(f"【Template 版本】字符数: {len(template_text)}")
    
    if len(prev_text) < len(template_text):
        print(f"📊 Template 版本多了 {len(template_text) - len(prev_text)} 个字符")
    else:
        print(f"📊 Prev 版本多了 {len(prev_text) - len(template_text)} 个字符")
    
    # 显示内容差异
    print(f"\n--- Prev 版本内容 ---")
    print(prev_text[:500])
    if len(prev_text) > 500:
        print(f"... (还有 {len(prev_text) - 500} 字符)")
    
    print(f"\n--- Template 版本内容 ---")
    print(template_text[:500])
    if len(template_text) > 500:
        print(f"... (还有 {len(template_text) - 500} 字符)")
    
    # 找出差异部分
    if prev_text != template_text:
        # 找出 template 多出的内容
        if template_text.startswith(prev_text):
            extra = template_text[len(prev_text):]
            print(f"\n➕ Template 额外内容:")
            print(extra[:300])
        elif prev_text.startswith(template_text):
            extra = prev_text[len(template_text):]
            print(f"\n➕ Prev 额外内容:")
            print(extra[:300])
        else:
            print(f"\n⚠️ 内容有实质性差异")

def main():
    # 比较所有不同的 docx 文件
    files_to_compare = [
        ("2.1.1", "2.1.1.docx"),
        ("2.1.2", "2.1.2.docx"),
        ("2.1.3", "2.1.3.docx"),
        ("2.1.4", "2.1.4.docx"),
        ("2.1.5", "2.1.5.docx"),
        ("2.2.1", "2.2.1.docx"),
        ("2.2.2", "2.2.2.docx"),
        ("2.2.3", "2.2.3.docx"),
        ("2.2.4", "2.2.4.docx"),
        ("2.2.5", "2.2.5.docx"),
        ("4.2.1", "4.2.1.docx"),
        ("4.2.2", "4.2.2.docx"),
        ("4.2.3", "4.2.3.docx"),
        ("4.2.4", "4.2.4.docx"),
        ("4.2.5", "4.2.5.docx"),
    ]
    
    for chapter, filename in files_to_compare:
        prev_path = os.path.join(BASE_DIR, "人工智能训练师_3级_sucai_prev", f"{chapter}-素材", filename)
        template_path = os.path.join(BASE_DIR, "template", chapter, filename)
        
        if os.path.exists(prev_path) and os.path.exists(template_path):
            compare_docx(chapter, prev_path, template_path)
        else:
            print(f"\n⚠️ 文件不存在: {chapter}")
            if not os.path.exists(prev_path):
                print(f"  Prev: {prev_path}")
            if not os.path.exists(template_path):
                print(f"  Template: {template_path}")

if __name__ == "__main__":
    main()