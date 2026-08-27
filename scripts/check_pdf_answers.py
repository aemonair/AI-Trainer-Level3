#!/usr/bin/env python3
"""
检查PDF中是否有答案部分
"""
import pdfplumber
import os
import re

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

print("="*60)
print("检查PDF中是否有答案部分")
print("="*60)

with pdfplumber.open(pdf_path) as pdf:
    print(f"总页数: {len(pdf.pages)}")
    
    # 检查最后10页是否有答案
    print("\n检查最后10页...")
    for i in range(max(0, len(pdf.pages)-10), len(pdf.pages)):
        page = pdf.pages[i]
        text = page.extract_text()
        if text and ('答案' in text or '参考答案' in text or '正确答案' in text):
            print(f"\n--- 第{i+1}页（找到答案相关关键词）---")
            print(text[:500])
    
    # 搜索所有包含"答案"的页面
    print("\n\n搜索所有包含'答案'的页面:")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text and ('答案' in text or '参考答案' in text):
            print(f"  第{i+1}页: 包含'答案'关键词")
            if i < 5:  # 只显示前5个
                print(f"    内容预览: {text[:200]}")