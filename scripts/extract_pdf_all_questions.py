#!/usr/bin/env python3
"""
从PDF中提取所有题目并分类统计
"""
import pdfplumber
import os
import re
import csv

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

print("="*60)
print("从PDF提取所有题目")
print("="*60)

# 提取所有文本
all_text = []
with pdfplumber.open(pdf_path) as pdf:
    print(f"总页数: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            all_text.append(text)

full_text = '\n'.join(all_text)

# 查找所有题型标题
sections = re.findall(r'([一二三四五六七八九十]+、[^\n]+)', full_text)
print(f"\n找到 {len(sections)} 个题型部分:")
for s in sections:
    print(f"  {s}")

# 分类提取题目
questions = {
    '判断题': [],
    '单选题': [],
    '多选题': []
}

# 判断题：（    ）或 (    )
judgment_pattern = r'[（(]\s*[）)]\s*\d+\.\s*([^\n]+)'
questions['判断题'] = re.findall(judgment_pattern, full_text)

# 单选题：有A/B/C/D选项
# 先找单选题部分
single_choice_section = re.search(r'二、单选题.*?(?=三、|四、|$)', full_text, re.DOTALL)
if single_choice_section:
    single_text = single_choice_section.group()
    # 提取题目
    single_questions = re.findall(r'\d+\.\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\d+\.|\n\s*[A-Z][\.．])', single_text)
    questions['单选题'] = single_questions

# 多选题
multiple_choice_section = re.search(r'三、多选题.*?(?=四、|五、|$)', full_text, re.DOTALL)
if multiple_choice_section:
    multiple_text = multiple_choice_section.group()
    multiple_questions = re.findall(r'\d+\.\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\d+\.|\n\s*[A-Z][\.．])', multiple_text)
    questions['多选题'] = multiple_questions

# 统计
print("\n" + "="*60)
print("题目数量统计")
print("="*60)
total = 0
for qtype, qlist in questions.items():
    count = len(qlist)
    total += count
    print(f"{qtype}: {count} 题")
print(f"总计: {total} 题")

# 生成Anki卡片
print("\n" + "="*60)
print("生成Anki卡片...")
print("="*60)

os.makedirs('anki_cards', exist_ok=True)

# 判断题
if questions['判断题']:
    with open('anki_cards/理论知识_判断题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['判断题']):
            front = f"【判断题】{q}"
            back = f"【答案】\n\n（请手动填写√或×）\n\n【题目】\n{q}"
            writer.writerow([front, back])
    print(f"✅ 判断题: {len(questions['判断题'])}题 → anki_cards/理论知识_判断题.csv")

# 单选题
if questions['单选题']:
    with open('anki_cards/理论知识_单选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['单选题']):
            front = f"【单选题】{q}"
            back = f"【答案】\n\n（请手动填写答案）\n\n【题目】\n{q}"
            writer.writerow([front, back])
    print(f"✅ 单选题: {len(questions['单选题'])}题 → anki_cards/理论知识_单选题.csv")

# 多选题
if questions['多选题']:
    with open('anki_cards/理论知识_多选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['多选题']):
            front = f"【多选题】{q}"
            back = f"【答案】\n\n（请手动填写答案）\n\n【题目】\n{q}"
            writer.writerow([front, back])
    print(f"✅ 多选题: {len(questions['多选题'])}题 → anki_cards/理论知识_多选题.csv")

# 合并版
with open('anki_cards/理论知识_全部题目.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['正面', '背面'])
    for qtype, qlist in questions.items():
        for q in qlist:
            front = f"【{qtype}】{q}"
            back = f"【答案】\n\n（请手动填写答案）\n\n【题目】\n{q}"
            writer.writerow([front, back])

print(f"\n✅ 合并版: {total}题 → anki_cards/理论知识_全部题目.csv")

# 显示示例
print("\n" + "="*60)
print("判断题示例（前3题）:")
print("="*60)
for i, q in enumerate(questions['判断题'][:3]):
    print(f"\n{i+1}. {q}")

print("\n" + "="*60)
print("单选题示例（前2题）:")
print("="*60)
if questions['单选题']:
    for i, q in enumerate(questions['单选题'][:2]):
        print(f"\n{i+1}. {q[:200]}")
else:
    print("（无单选题）")

print("\n" + "="*60)
print("多选题示例（前2题）:")
print("="*60)
if questions['多选题']:
    for i, q in enumerate(questions['多选题'][:2]):
        print(f"\n{i+1}. {q[:200]}")
else:
    print("（无多选题）")

print("\n" + "="*60)
print("✅ 完成！")
print("="*60)