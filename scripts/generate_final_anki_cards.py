#!/usr/bin/env python3
"""
生成最终Anki卡片（含DeepSeek判断题答案）
单选和多选题待补充答案
"""
import pdfplumber
import os
import re
import csv
import logging

logging.getLogger('pdfplumber').setLevel(logging.ERROR)

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

print("="*60)
print("生成最终Anki卡片")
print("="*60)

# DeepSeek判断题答案
deepseek_answers_str = """1√ 2× 3× 4× 5× 6× 7× 8× 9× 10×
11√ 12× 13× 14× 15√ 16√ 17√ 18√ 19√ 20√
21√ 22√ 23√ 24√ 25√ 26√ 27√ 28× 29× 30√
31× 32√ 33× 34√ 35√ 36√ 37× 38× 39√ 40√
41√ 42√ 43√ 44× 45× 46√ 47√ 48× 49√ 50√
51√ 52√ 53√ 54× 55× 56× 57× 58√ 59√ 60×
61× 62× 63√ 64√ 65√ 66× 67√ 68√ 69√ 70√
71× 72√ 73√ 74√ 75× 76√ 77√ 78× 79√ 80×
81√ 82√ 83√ 84× 85√ 86× 87√ 88√ 89× 90√
91√ 92√ 93× 94√ 95√ 96× 97× 98√ 99× 100√
101× 102√ 103√ 104√ 105× 106√ 107√ 108× 109√ 110√
111√ 112√ 113√ 114√ 115√ 116√ 117√ 118√ 119× 120√
121× 122√ 123× 124× 125√ 126√ 127√ 128× 129√ 130√
131× 132× 133× 134× 135√ 136× 137√ 138√ 139× 140√
141√ 142× 143√ 144√ 145√ 146√ 147√ 148× 149√ 150√
151√ 152√ 153√ 154√ 155× 156√ 157× 158× 159√ 160×
161√ 162√ 163× 164× 165√ 166√ 167√ 168× 169× 170×
171× 172√ 173√ 174× 175× 176× 177√ 178√ 179× 180√
181√ 182× 183√ 184√ 185√ 186× 187√ 188× 189√ 190√
191× 192√ 193× 194√ 195× 196√ 197√ 198× 199√ 200√
201√ 202× 203× 204√ 205√ 206× 207× 208× 209√ 210×
211√ 212× 213√ 214√ 215√ 216× 217× 218√ 219√ 220√
221× 222√ 223√ 224√ 225× 226√ 227√ 228× 229× 230√
231√ 232√ 233√ 234√ 235× 236× 237√ 238× 239√ 240√
241× 242√ 243√ 244√ 245× 246× 247× 248× 249× 250√
251√ 252√ 253√ 254√ 255× 256√ 257× 258× 259× 260√
261× 262√ 263× 264× 265× 266× 267√ 268× 269√ 270√
271√ 272√ 273× 274√ 275√ 276× 277√ 278√ 279× 280√
281√ 282× 283√ 284√ 285√ 286√ 287√ 288× 289× 290√
291× 292× 293√ 294√ 295× 296× 297√ 298× 299√ 300√"""

# 解析DeepSeek答案
deepseek_answers = {}
pattern = r'(\d+)([√×])'
for match in re.finditer(pattern, deepseek_answers_str):
    num = int(match.group(1))
    answer = match.group(2)
    deepseek_answers[num] = answer

print(f"解析DeepSeek答案: {len(deepseek_answers)} 题")

# 提取个人答案
answers_pdf = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'
personal_answers = {}

print("\n提取个人答案PDF...")
with pdfplumber.open(answers_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
    judgment_pattern = r'(\d+)\.\s*([^\n]+?)\s*答案[：:]\s*([√×])'
    for match in re.finditer(judgment_pattern, full_text):
        num = int(match.group(1))
        answer = match.group(3).strip()
        personal_answers[num] = answer

print(f"提取个人答案: {len(personal_answers)} 题")

# 提取题目PDF
questions_pdf = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

print("\n提取题目PDF...")
with pdfplumber.open(questions_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

# 分类提取题目
questions = {
    '判断题': [],
    '单选题': [],
    '多选题': []
}

judgment_pattern = r'[（(]\s*[）)]\s*\d+\.\s*([^\n]+)'
questions['判断题'] = re.findall(judgment_pattern, full_text)

single_choice_section = re.search(r'二、单选题.*?(?=三、|四、|$)', full_text, re.DOTALL)
if single_choice_section:
    single_text = single_choice_section.group()
    single_questions = re.findall(r'\d+\.\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\d+\.|\n\s*[A-Z][\.．])', single_text)
    questions['单选题'] = single_questions

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
            
            question_num = i + 1
            deepseek_answer = deepseek_answers.get(question_num)
            personal_answer = personal_answers.get(question_num)
            
            back_parts = []
            
            if deepseek_answer:
                back_parts.append(f"【DeepSeek答案】{deepseek_answer}")
            
            if personal_answer:
                back_parts.append(f"【个人答案】{personal_answer}")
            
            if deepseek_answer and personal_answer:
                if deepseek_answer == personal_answer:
                    back_parts.append("✅ 两者答案一致")
                else:
                    back_parts.append("⚠️ 答案不一致，请确认！")
            
            if not deepseek_answer and not personal_answer:
                back_parts.append("⚠️ 暂无答案，请人工确认")
            
            back_parts.append(f"\n【题目】\n{q}")
            back = '\n\n'.join(back_parts)
            
            writer.writerow([front, back])
    
    print(f"✅ 判断题: {len(questions['判断题'])}题 → anki_cards/理论知识_判断题.csv")

# 单选题
if questions['单选题']:
    with open('anki_cards/理论知识_单选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['单选题']):
            front = f"【单选题】{q}"
            back = f"【题目】\n{q}\n\n⚠️ 答案待补充（PDF中为颜色标记）"
            writer.writerow([front, back])
    
    print(f"✅ 单选题: {len(questions['单选题'])}题 → anki_cards/理论知识_单选题.csv")

# 多选题
if questions['多选题']:
    with open('anki_cards/理论知识_多选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['多选题']):
            front = f"【多选题】{q}"
            back = f"【题目】\n{q}\n\n⚠️ 答案待补充（PDF中为颜色标记）"
            writer.writerow([front, back])
    
    print(f"✅ 多选题: {len(questions['多选题'])}题 → anki_cards/理论知识_多选题.csv")

# 合并版
with open('anki_cards/理论知识_全部题目.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['正面', '背面'])
    for qtype, qlist in questions.items():
        for i, q in enumerate(qlist):
            front = f"【{qtype}】{q}"
            
            if qtype == '判断题':
                question_num = i + 1
                deepseek_answer = deepseek_answers.get(question_num)
                personal_answer = personal_answers.get(question_num)
            else:
                deepseek_answer = None
                personal_answer = None
            
            back_parts = []
            if deepseek_answer:
                back_parts.append(f"【DeepSeek答案】{deepseek_answer}")
            if personal_answer:
                back_parts.append(f"【个人答案】{personal_answer}")
            if deepseek_answer and personal_answer:
                if deepseek_answer == personal_answer:
                    back_parts.append("✅ 两者答案一致")
                else:
                    back_parts.append("⚠️ 答案不一致，请确认！")
            if not deepseek_answer and not personal_answer:
                if qtype == '判断题':
                    back_parts.append("⚠️ 暂无答案，请人工确认")
                else:
                    back_parts.append("⚠️ 答案待补充（PDF中为颜色标记）")
            back_parts.append(f"\n【题目】\n{q}")
            back = '\n\n'.join(back_parts)
            
            writer.writerow([front, back])

print(f"\n✅ 合并版: {total}题 → anki_cards/理论知识_全部题目.csv")

# 统计
deepseek_count = len([q for q in questions['判断题'] if deepseek_answers.get(questions['判断题'].index(q) + 1)])
personal_count = len([q for q in questions['判断题'] if personal_answers.get(questions['判断题'].index(q) + 1)])
agree_count = 0
disagree_count = 0
for i, q in enumerate(questions['判断题']):
    question_num = i + 1
    deepseek_answer = deepseek_answers.get(question_num)
    personal_answer = personal_answers.get(question_num)
    if deepseek_answer and personal_answer:
        if deepseek_answer == personal_answer:
            agree_count += 1
        else:
            disagree_count += 1

print("\n" + "="*60)
print("判断题答案统计")
print("="*60)
print(f"DeepSeek答案: {deepseek_count}题")
print(f"个人答案: {personal_count}题")
print(f"两者一致: {agree_count}题")
print(f"两者不一致: {disagree_count}题")

print("\n" + "="*60)
print("✅ 完成！")
print("="*60)