#!/usr/bin/env python3
"""
提取PDF中单选和多选题的带颜色答案
使用pdfplumber的字符颜色信息
"""
import pdfplumber
import os
import re
import json

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'

print("="*60)
print("提取单选和多选题答案（基于颜色）")
print("="*60)

single_answers = {}
multiple_answers = {}

with pdfplumber.open(pdf_path) as pdf:
    print(f"总页数: {len(pdf.pages)}")
    
    # 检查第20-35页（单选题部分）
    print("\n提取单选题答案（第20-35页）...")
    for page_num in range(19, min(35, len(pdf.pages))):
        page = pdf.pages[page_num]
        chars = page.chars
        
        # 查找有颜色的字符（非黑色）
        colored_chars = []
        for char in chars:
            # 检查是否有stroking_color或non_stroking_color
            if 'non_stroking_color' in char:
                color = char['non_stroking_color']
                # 黑色通常是(0,0,0)或None
                if color and color != (0, 0, 0):
                    colored_chars.append(char)
        
        if colored_chars:
            # 提取有颜色的文本
            colored_text = ''.join([c['text'] for c in colored_chars])
            if colored_text.strip():
                print(f"  第{page_num+1}页: 找到颜色文本 '{colored_text[:100]}'")
    
    # 检查第35-50页（多选题部分）
    print("\n提取多选题答案（第35-50页）...")
    for page_num in range(34, min(50, len(pdf.pages))):
        page = pdf.pages[page_num]
        chars = page.chars
        
        colored_chars = []
        for char in chars:
            if 'non_stroking_color' in char:
                color = char['non_stroking_color']
                if color and color != (0, 0, 0):
                    colored_chars.append(char)
        
        if colored_chars:
            colored_text = ''.join([c['text'] for c in colored_chars])
            if colored_text.strip():
                print(f"  第{page_num+1}页: 找到颜色文本 '{colored_text[:100]}'")

# 尝试另一种方法：直接查找答案模式
print("\n\n方法2：查找答案模式...")
with pdfplumber.open(pdf_path) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
    
    # 查找单选题答案：如 "1. A" 或 "1.A" 或 "1. (A)"
    single_answer_pattern = r'(\d+)\.\s*[\(\（]?\s*([A-D])\s*[\)\）]?'
    single_matches = re.findall(single_answer_pattern, full_text)
    print(f"找到 {len(single_matches)} 个单选题答案")
    if single_matches:
        print(f"前10个: {single_matches[:10]}")
    
    # 查找多选题答案：如 "1. ABC" 或 "1.ABC"
    multiple_answer_pattern = r'(\d+)\.\s*[\(\（]?\s*([A-E]{2,5})\s*[\)\）]?'
    multiple_matches = re.findall(multiple_answer_pattern, full_text)
    print(f"找到 {len(multiple_matches)} 个多选题答案")
    if multiple_matches:
        print(f"前10个: {multiple_matches[:10]}")