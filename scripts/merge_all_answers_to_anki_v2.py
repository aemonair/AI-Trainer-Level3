#!/usr/bin/env python3
"""
提取个人答案PDF并整合到Anki卡片中
包含：AI预测答案 + 个人答案
解决全角/半角字符不匹配问题
"""
import pdfplumber
import os
import re
import csv
import logging
import unicodedata

logging.getLogger('pdfplumber').setLevel(logging.ERROR)

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

print("="*60)
print("提取个人答案并整合到Anki卡片")
print("="*60)

# 文本规范化函数
def normalize_text(text):
    """规范化文本：全角转半角，统一字符"""
    # NFKC规范化：全角转半角
    text = unicodedata.normalize('NFKC', text)
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 1. 提取个人答案PDF
answers_pdf = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'
personal_answers = {}

print("\n提取个人答案PDF...")
with pdfplumber.open(answers_pdf) as pdf:
    print(f"总页数: {len(pdf.pages)}")
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
    
    # 提取判断题答案：题目 答案：√/×
    judgment_pattern = r'([^\n]+?)\s*答案[：:]\s*([√×])'
    for match in re.finditer(judgment_pattern, full_text):
        question = match.group(1).strip()
        answer = match.group(2).strip()
        
        # 规范化题目文本
        normalized_q = normalize_text(question)
        
        # 提取题号
        num_match = re.match(r'(\d+)\.', normalized_q)
        if num_match:
            num = int(num_match.group(1))
            # 用题号作为key
            personal_answers[num] = {
                'answer': answer,
                'full_question': normalized_q
            }
    
    print(f"提取到 {len(personal_answers)} 个判断题答案")
    print(f"题号范围: {min(personal_answers.keys())} - {max(personal_answers.keys())}")

# 2. 提取题目PDF
questions_pdf = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

print("\n提取题目PDF...")
with pdfplumber.open(questions_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

# 3. 分类提取题目
questions = {
    '判断题': [],
    '单选题': [],
    '多选题': []
}

# 判断题
judgment_pattern = r'[（(]\s*[）)]\s*\d+\.\s*([^\n]+)'
questions['判断题'] = re.findall(judgment_pattern, full_text)

# 单选题
single_choice_section = re.search(r'二、单选题.*?(?=三、|四、|$)', full_text, re.DOTALL)
if single_choice_section:
    single_text = single_choice_section.group()
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
print(f"个人答案: {len(personal_answers)} 题")

# 4. AI答案生成函数
def generate_judgment_answer(question):
    """生成判断题AI答案"""
    false_keywords = ['可以不经', '无需', '只', '只能', '完全', '绝对', '一定', 
                      '不需要', '不必', '都可以', '全部', '所有', '仅仅', '只是',
                      '随意', '任意', '随时', '立即', '必须', '禁止', '不能',
                      '不允许', '不应该', '无法', '不可能']
    true_keywords = ['应该', '应当', '需要', '必须', '可以', '能够', '有助于',
                     '有利于', '提高', '促进', '保障', '确保', '保护', '遵守',
                     '符合', '遵循', '尊重', '重视', '关注', '考虑', '合理',
                     '适当', '有效', '规范', '标准', '原则']
    
    for kw in false_keywords:
        if kw in question:
            if '可以不经用户同意' in question or '无需考虑' in question or '只需要' in question:
                return '×', '表述过于绝对或违反常识'
            if '都不存在' in question or '完全没有' in question:
                return '×', '表述过于绝对'
    
    for kw in true_keywords:
        if kw in question:
            if '应该' in question or '应当' in question or '需要' in question:
                return '√', '符合常规要求'
    
    return '?', '需要人工确认'

def generate_single_choice_answer(question):
    """生成单选题AI答案"""
    options = re.findall(r'([A-E])[\.．\s]*([^\n]+)', question)
    if not options:
        return '?', '无法提取选项'
    
    positive_keywords = ['正确', '合理', '有效', '全面', '准确', '规范', '标准', '安全']
    for opt_letter, opt_text in options:
        for kw in positive_keywords:
            if kw in opt_text:
                return opt_letter, f'选项包含积极关键词"{kw}"'
    
    return 'A', '默认答案，需要人工确认'

def generate_multiple_choice_answer(question):
    """生成多选题AI答案"""
    options = re.findall(r'([A-E])[\.．\s]*([^\n]+)', question)
    if not options:
        return '?', '无法提取选项'
    
    positive_keywords = ['正确', '合理', '有效', '全面', '准确', '规范', '标准', '安全', '保护', '提高']
    negative_keywords = ['错误', '不合理', '无效', '片面', '不准确', '不规范', '危险', '降低']
    
    selected = []
    for opt_letter, opt_text in options:
        is_positive = any(kw in opt_text for kw in positive_keywords)
        is_negative = any(kw in opt_text for kw in negative_keywords)
        if is_positive and not is_negative:
            selected.append(opt_letter)
    
    if not selected:
        selected = ['A', 'B']
    if len(selected) == len(options):
        selected = selected[:-1]
    
    return ','.join(selected), '基于关键词选择'

# 5. 生成Anki卡片（含AI答案+个人答案）
print("\n" + "="*60)
print("生成Anki卡片（含AI预测答案+个人答案）...")
print("="*60)

os.makedirs('anki_cards', exist_ok=True)

# 统计
stats = {
    'judgment': {'ai': 0, 'personal': 0, 'both': 0, 'none': 0},
}

# 判断题
if questions['判断题']:
    with open('anki_cards/理论知识_判断题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['判断题']):
            front = f"【判断题】{q}"
            
            # AI答案
            ai_answer, ai_reason = generate_judgment_answer(q)
            
            # 个人答案（用题号匹配）
            question_num = i + 1  # 题号从1开始
            personal_answer = personal_answers.get(question_num, {}).get('answer')
            
            # 构建背面
            back_parts = []
            
            if personal_answer:
                back_parts.append(f"【个人答案】{personal_answer}")
                stats['judgment']['personal'] += 1
            
            if ai_answer != '?':
                back_parts.append(f"【AI预测答案】{ai_answer}")
                back_parts.append(f"【AI分析】{ai_reason}")
                stats['judgment']['ai'] += 1
            
            if personal_answer and ai_answer != '?':
                stats['judgment']['both'] += 1
                if personal_answer == ai_answer:
                    back_parts.append("✅ AI与个人答案一致")
                else:
                    back_parts.append(f"⚠️ AI与个人答案不一致，请确认！")
            
            if not personal_answer and ai_answer == '?':
                stats['judgment']['none'] += 1
                back_parts.append("⚠️ 暂无答案，请人工确认")
            
            back_parts.append(f"\n【题目】\n{q}")
            back = '\n\n'.join(back_parts)
            
            writer.writerow([front, back])
    
    print(f"✅ 判断题: {len(questions['判断题'])}题")
    print(f"   - AI预测: {stats['judgment']['ai']}题")
    print(f"   - 个人答案: {stats['judgment']['personal']}题")
    print(f"   - 两者都有: {stats['judgment']['both']}题")
    print(f"   - 都无答案: {stats['judgment']['none']}题")

# 单选题
if questions['单选题']:
    with open('anki_cards/理论知识_单选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['单选题']):
            front = f"【单选题】{q}"
            ai_answer, ai_reason = generate_single_choice_answer(q)
            
            back_parts = [
                f"【AI预测答案】{ai_answer}",
                f"【AI分析】{ai_reason}",
                f"\n【题目】\n{q}"
            ]
            back = '\n\n'.join(back_parts)
            writer.writerow([front, back])
    
    print(f"\n✅ 单选题: {len(questions['单选题'])}题（AI预测）")

# 多选题
if questions['多选题']:
    with open('anki_cards/理论知识_多选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['多选题']):
            front = f"【多选题】{q}"
            ai_answer, ai_reason = generate_multiple_choice_answer(q)
            
            back_parts = [
                f"【AI预测答案】{ai_answer}",
                f"【AI分析】{ai_reason}",
                f"\n【题目】\n{q}"
            ]
            back = '\n\n'.join(back_parts)
            writer.writerow([front, back])
    
    print(f"✅ 多选题: {len(questions['多选题'])}题（AI预测）")

# 合并版
with open('anki_cards/理论知识_全部题目.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['正面', '背面'])
    for qtype, qlist in questions.items():
        for i, q in enumerate(qlist):
            front = f"【{qtype}】{q}"
            
            if qtype == '判断题':
                ai_answer, ai_reason = generate_judgment_answer(q)
                question_num = i + 1
                personal_answer = personal_answers.get(question_num, {}).get('answer')
            elif qtype == '单选题':
                ai_answer, ai_reason = generate_single_choice_answer(q)
                personal_answer = None
            else:
                ai_answer, ai_reason = generate_multiple_choice_answer(q)
                personal_answer = None
            
            back_parts = []
            if personal_answer:
                back_parts.append(f"【个人答案】{personal_answer}")
            if ai_answer != '?':
                back_parts.append(f"【AI预测答案】{ai_answer}")
                back_parts.append(f"【AI分析】{ai_reason}")
            if not personal_answer and ai_answer == '?':
                back_parts.append("⚠️ 暂无答案，请人工确认")
            back_parts.append(f"\n【题目】\n{q}")
            back = '\n\n'.join(back_parts)
            
            writer.writerow([front, back])

print(f"\n✅ 合并版: {total}题 → anki_cards/理论知识_全部题目.csv")

# 显示示例
print("\n" + "="*60)
print("判断题示例（前10题）:")
print("="*60)
for i, q in enumerate(questions['判断题'][:10]):
    ai_answer, ai_reason = generate_judgment_answer(q)
    question_num = i + 1
    personal_answer = personal_answers.get(question_num, {}).get('answer')
    
    print(f"\n{i+1}. {q[:80]}")
    if personal_answer:
        print(f"   个人答案: {personal_answer}")
    print(f"   AI答案: {ai_answer} - {ai_reason}")
    if personal_answer and ai_answer != '?':
        if personal_answer == ai_answer:
            print(f"   ✅ 一致")
        else:
            print(f"   ⚠️ 不一致")

print("\n" + "="*60)
print("✅ 完成！")
print("="*60)