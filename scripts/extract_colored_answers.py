#!/usr/bin/env python3
"""
提取PDF中单选和多选题的带颜色答案
"""
import pdfplumber
import os
import re

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'

print("="*60)
print("提取单选和多选题答案（带颜色标记）")
print("="*60)

with pdfplumber.open(pdf_path) as pdf:
    print(f"总页数: {len(pdf.pages)}")
    
    # 查看第20-30页（可能是单选/多选题部分）
    print("\n检查第20-30页...")
    for i in range(19, min(30, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text()
        if text:
            # 查找包含选项的页面
            if re.search(r'[A-D][\.．]', text):
                print(f"\n--- 第{i+1}页 ---")
                print(text[:300])
    
    # 查找所有包含"答案"或"参考答案"的页面
    print("\n\n搜索包含'答案'或'参考答案'的页面:")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text and ('答案' in text or '参考答案' in text or '正确答案' in text):
            print(f"  第{i+1}页")