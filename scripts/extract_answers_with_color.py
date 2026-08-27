#!/usr/bin/env python3
"""
提取PDF中单选和多选题的带颜色答案
使用更精确的颜色检测方法
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
    
    # 提取单选题答案（第20-34页）
    print("\n提取单选题答案...")
    for page_num in range(19, 34):
        page = pdf.pages[page_num]
        chars = page.chars
        
        # 按行分组字符
        lines = {}
        for char in chars:
            y0 = round(char['y0'], 1)
            if y0 not in lines:
                lines[y0] = []
            lines[y0].append(char)
        
        # 查找每行中有颜色的字符
        for y0, chars_in_line in lines.items():
            # 检查是否有非黑色字符
            colored_chars = []
            for char in chars_in_line:
                if 'non_stroking_color' in char:
                    color = char['non_stroking_color']
                    if color and color != (0, 0, 0):
                        colored_chars.append(char)
            
            if colored_chars:
                # 提取有颜色的文本
                colored_text = ''.join([c['text'] for c in sorted(colored_chars, key=lambda x: x['x0'])])
                
                # 查找题号和答案
                match = re.search(r'(\d+)\s*[\.．]\s*([A-D])', colored_text)
                if match:
                    num = int(match.group(1))
                    answer = match.group(2)
                    single_answers[num] = answer
    
    print(f"提取到 {len(single_answers)} 个单选题答案")
    if single_answers:
        print(f"题号范围: {min(single_answers.keys())} - {max(single_answers.keys())}")
    
    # 提取多选题答案（第35-43页）
    print("\n提取多选题答案...")
    for page_num in range(34, 43):
        page = pdf.pages[page_num]
        chars = page.chars
        
        lines = {}
        for char in chars:
            y0 = round(char['y0'], 1)
            if y0 not in lines:
                lines[y0] = []
            lines[y0].append(char)
        
        for y0, chars_in_line in lines.items():
            colored_chars = []
            for char in chars_in_line:
                if 'non_stroking_color' in char:
                    color = char['non_stroking_color']
                    if color and color != (0, 0, 0):
                        colored_chars.append(char)
            
            if colored_chars:
                colored_text = ''.join([c['text'] for c in sorted(colored_chars, key=lambda x: x['x0'])])
                
                # 查找题号和答案（多选通常是2-5个字母）
                match = re.search(r'(\d+)\s*[\.．]\s*([A-E]{2,5})', colored_text)
                if match:
                    num = int(match.group(1))
                    answer = match.group(2)
                    multiple_answers[num] = answer
    
    print(f"提取到 {len(multiple_answers)} 个多选题答案")
    if multiple_answers:
        print(f"题号范围: {min(multiple_answers.keys())} - {max(multiple_answers.keys())}")

# 保存答案
if single_answers:
    with open('answers/single_choice_answers.json', 'w', encoding='utf-8') as f:
        json.dump(single_answers, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 单选题答案已保存: answers/single_choice_answers.json")

if multiple_answers:
    with open('answers/multiple_choice_answers.json', 'w', encoding='utf-8') as f:
        json.dump(multiple_answers, f, ensure_ascii=False, indent=2)
    print(f"✅ 多选题答案已保存: answers/multiple_choice_answers.json")

# 显示示例
print("\n" + "="*60)
print("单选题答案示例（前10题）:")
print("="*60)
for num in sorted(single_answers.keys())[:10]:
    print(f"  {num}. {single_answers[num]}")

print("\n" + "="*60)
print("多选题答案示例（前10题）:")
print("="*60)
for num in sorted(multiple_answers.keys())[:10]:
    print(f"  {num}. {multiple_answers[num]}")