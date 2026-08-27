#!/usr/bin/env python3
"""
检查PDF中单选和多选题答案的标记方式
"""
import pdfplumber
import os
import re

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'

print("="*60)
print("检查PDF中答案标记方式")
print("="*60)

with pdfplumber.open(pdf_path) as pdf:
    # 查看第27页（单选题开始部分）
    print("\n第27页完整内容:")
    page = pdf.pages[26]
    text = page.extract_text()
    if text:
        print(text[:1000])
    
    # 查看第28页
    print("\n\n第28页完整内容:")
    page = pdf.pages[27]
    text = page.extract_text()
    if text:
        print(text[:1000])
    
    # 查看第42页（多选题部分）
    print("\n\n第42页完整内容:")
    page = pdf.pages[41]
    text = page.extract_text()
    if text:
        print(text[:1000])