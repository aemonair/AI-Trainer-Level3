#!/usr/bin/env python3
"""
使用PyMuPDF提取PDF中单选和多选题的带颜色答案
"""
import fitz  # PyMuPDF
import os
import re
import json

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'

print("="*60)
print("使用PyMuPDF提取单选和多选题答案")
print("="*60)

doc = fitz.open(pdf_path)
print(f"总页数: {len(doc)}")

single_answers = {}
multiple_answers = {}

# 提取单选题（第20-34页，索引19-33）
print("\n提取单选题答案...")
for page_num in range(19, 34):
    if page_num >= len(doc):
        break
    page = doc[page_num]
    
    # 获取所有文本块
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            # 检查是否有彩色文本
            colored_text = ""
            for span in line["spans"]:
                # 检查颜色（RGB格式，0是黑色）
                color = span.get("color", 0)
                if color != 0:  # 非黑色
                    colored_text += span["text"]
            
            if colored_text:
                # 查找题号和答案
                match = re.search(r'(\d+)\s*[\.．]\s*([A-D])', colored_text)
                if match:
                    num = int(match.group(1))
                    answer = match.group(2)
                    single_answers[num] = answer

print(f"提取到 {len(single_answers)} 个单选题答案")
if single_answers:
    print(f"题号范围: {min(single_answers.keys())} - {max(single_answers.keys())}")
    print(f"前5个: {dict(list(single_answers.items())[:5])}")

# 提取多选题（第35-43页，索引34-42）
print("\n提取多选题答案...")
for page_num in range(34, 43):
    if page_num >= len(doc):
        break
    page = doc[page_num]
    
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            colored_text = ""
            for span in line["spans"]:
                color = span.get("color", 0)
                if color != 0:
                    colored_text += span["text"]
            
            if colored_text:
                match = re.search(r'(\d+)\s*[\.．]\s*([A-E]{2,5})', colored_text)
                if match:
                    num = int(match.group(1))
                    answer = match.group(2)
                    multiple_answers[num] = answer

print(f"提取到 {len(multiple_answers)} 个多选题答案")
if multiple_answers:
    print(f"题号范围: {min(multiple_answers.keys())} - {max(multiple_answers.keys())}")
    print(f"前5个: {dict(list(multiple_answers.items())[:5])}")

# 保存答案
os.makedirs('answers', exist_ok=True)

if single_answers:
    with open('answers/single_choice_answers.json', 'w', encoding='utf-8') as f:
        json.dump(single_answers, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 单选题答案已保存: answers/single_choice_answers.json")

if multiple_answers:
    with open('answers/multiple_choice_answers.json', 'w', encoding='utf-8') as f:
        json.dump(multiple_answers, f, ensure_ascii=False, indent=2)
    print(f"✅ 多选题答案已保存: answers/multiple_choice_answers.json")

doc.close()