#!/usr/bin/env python3
"""
调试答案匹配问题
"""
import pdfplumber
import os
import re
import logging

logging.getLogger('pdfplumber').setLevel(logging.ERROR)

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

# 提取个人答案
answers_pdf = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'

print("="*60)
print("调试答案匹配")
print("="*60)

with pdfplumber.open(answers_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
    
    # 查看前10个答案
    judgment_pattern = r'([^\n]+?)\s*答案[：:]\s*([√×])'
    matches = list(re.finditer(judgment_pattern, full_text))
    
    print(f"\n找到 {len(matches)} 个答案")
    print("\n前10个答案:")
    for i, match in enumerate(matches[:10]):
        question = match.group(1).strip()
        answer = match.group(2).strip()
        print(f"\n{i+1}. 答案: {answer}")
        print(f"   题目: {question[:100]}")
        print(f"   前30字符: '{question[:30]}'")

# 提取题目PDF
questions_pdf = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

with pdfplumber.open(questions_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

# 查看前10个题目
judgment_pattern = r'[（(]\s*[）)]\s*\d+\.\s*([^\n]+)'
questions = re.findall(judgment_pattern, full_text)

print(f"\n\n找到 {len(questions)} 个题目")
print("\n前10个题目:")
for i, q in enumerate(questions[:10]):
    print(f"\n{i+1}. 题目: {q[:100]}")
    print(f"   前30字符: '{q[:30]}'")

# 尝试匹配
print("\n\n尝试匹配前5个答案:")
for i, match in enumerate(matches[:5]):
    answer_question = match.group(1).strip()
    answer = match.group(2).strip()
    
    # 尝试用前20个字符匹配
    search_key = answer_question[:20]
    found = False
    for j, q in enumerate(questions):
        if search_key in q:
            print(f"\n答案{i+1}: {answer_question[:50]}... → {answer}")
            print(f"  匹配题目{j+1}: {q[:50]}...")
            found = True
            break
    
    if not found:
        print(f"\n答案{i+1}: {answer_question[:50]}... → {answer}")
        print(f"  ❌ 未找到匹配题目")
        print(f"  搜索key: '{search_key}'")