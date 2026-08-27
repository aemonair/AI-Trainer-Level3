#!/usr/bin/env python3
"""
提取个人答案PDF并整合到Anki卡片中
"""
import pdfplumber
import os
import re
import logging

# 抑制pdfplumber的警告
logging.getLogger('pdfplumber').setLevel(logging.ERROR)

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'

print("="*60)
print("提取个人答案PDF")
print("="*60)
print(f"PDF文件: {pdf_path}")
print(f"文件存在: {os.path.exists(pdf_path)}")

if os.path.exists(pdf_path):
    print(f"文件大小: {os.path.getsize(pdf_path) / 1024 / 1024:.1f}MB")
    
    # 提取所有文本
    with pdfplumber.open(pdf_path) as pdf:
        print(f"\n总页数: {len(pdf.pages)}")
        
        # 提取前5页查看结构
        print("\n前5页内容预览:")
        for i in range(min(5, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text()
            if text:
                print(f"\n--- 第{i+1}页 ---")
                print(text[:500])
        
        # 搜索包含"答案"的页面
        print("\n\n搜索包含'答案'的页面:")
        answer_pages = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and ('答案' in text or '参考答案' in text):
                answer_pages.append(i+1)
                if len(answer_pages) <= 5:
                    print(f"  第{i+1}页: {text[:200]}")
        
        print(f"\n共找到 {len(answer_pages)} 页包含'答案'关键词")
        print(f"答案页码: {answer_pages[:20]}...")
else:
    print("❌ 文件不存在")