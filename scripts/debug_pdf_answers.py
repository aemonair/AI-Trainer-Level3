#!/usr/bin/env python3
"""
调试PDF中答案的标记方式
"""
import fitz  # PyMuPDF
import os
import re

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'

print("="*60)
print("调试PDF中答案标记方式")
print("="*60)

doc = fitz.open(pdf_path)

# 查看第20页（单选题开始）
print("\n第20页（单选题开始）:")
page = doc[19]
text = page.get_text()
print(text[:800])

# 查看第27页（多选题开始）
print("\n\n第27页（多选题开始）:")
page = doc[26]
text = page.get_text()
print(text[:800])

# 检查是否有注释或高亮
print("\n\n检查注释和高亮...")
for page_num in [19, 20, 26, 27]:
    if page_num < len(doc):
        page = doc[page_num]
        annots = page.annots()
        if annots:
            print(f"第{page_num+1}页有注释/高亮")
            for annot in annots:
                print(f"  类型: {annot.type}")

doc.close()