#!/usr/bin/env python3
"""
从PDF中提取理论知识复习题
PDF可能包含更多内容（单选、多选）
"""
import os
import sys

# 尝试使用PyPDF2或pdfplumber
try:
    import pdfplumber
    USE_PDFPLUMBER = True
except ImportError:
    try:
        import PyPDF2
        USE_PDFPLUMBER = False
    except ImportError:
        print("❌ 需要安装pdfplumber或PyPDF2")
        print("运行: uv pip install pdfplumber")
        sys.exit(1)

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/4-04-05-05_3_20250701/第3部分-人工智能训练师_3级_理论知识复习题.pdf'
if not os.path.exists(pdf_path):
    # 尝试其他可能的路径
    alt_paths = [
        '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf',
        '/Users/air/Downloads/GUIDE_AI_3/3-_3_.pdf',
    ]
    for p in alt_paths:
        if os.path.exists(p):
            pdf_path = p
            break

print("="*60)
print("从PDF提取理论知识复习题")
print("="*60)
print(f"PDF文件: {pdf_path}")
print(f"文件大小: {os.path.getsize(pdf_path) / 1024 / 1024:.1f}MB")

# 提取PDF文本
if USE_PDFPLUMBER:
    print("\n使用pdfplumber提取...")
    with pdfplumber.open(pdf_path) as pdf:
        print(f"总页数: {len(pdf.pages)}")
        
        # 提取前5页内容查看结构
        print("\n前5页内容预览:")
        for i in range(min(5, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text()
            if text:
                print(f"\n--- 第{i+1}页 ---")
                print(text[:500])
else:
    print("\n使用PyPDF2提取...")
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f"总页数: {len(reader.pages)}")
        
        # 提取前5页内容
        for i in range(min(5, len(reader.pages))):
            text = reader.pages[i].extract_text()
            if text:
                print(f"\n--- 第{i+1}页 ---")
                print(text[:500])

print("\n" + "="*60)
print("提示：请查看输出内容，确认是否有单选题和多选题")
print("="*60)