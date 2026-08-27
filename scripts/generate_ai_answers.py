#!/usr/bin/env python3
"""
为理论知识复习题生成AI预测答案
基于题目内容的关键词和常识进行判断
"""
import pdfplumber
import os
import re
import csv

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

pdf_path = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

print("="*60)
print("提取题目并生成AI预测答案")
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

# 分类提取题目
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

# AI答案生成函数
def generate_judgment_answer(question):
    """生成判断题AI答案"""
    # 通常错误的关键词
    false_keywords = [
        '可以不经', '无需', '只', '只能', '完全', '绝对', '一定', 
        '不需要', '不必', '都可以', '全部', '所有', '仅仅', '只是',
        '随意', '任意', '随时', '立即', '必须', '禁止', '不能',
        '不允许', '不应该', '无法', '不可能'
    ]
    
    # 通常正确的关键词
    true_keywords = [
        '应该', '应当', '需要', '必须', '可以', '能够', '有助于',
        '有利于', '提高', '促进', '保障', '确保', '保护', '遵守',
        '符合', '遵循', '尊重', '重视', '关注', '考虑', '合理',
        '适当', '有效', '规范', '标准', '原则'
    ]
    
    # 检查是否有明显错误的表述
    for kw in false_keywords:
        if kw in question:
            # 进一步判断语境
            if '可以不经用户同意' in question or '无需考虑' in question or '只需要' in question:
                return '×', '表述过于绝对或违反常识'
            if '都不存在' in question or '完全没有' in question:
                return '×', '表述过于绝对'
    
    # 检查是否有明显正确的表述
    for kw in true_keywords:
        if kw in question:
            if '应该' in question or '应当' in question or '需要' in question:
                return '√', '符合常规要求'
    
    # 默认答案（需要人工确认）
    return '?', '需要人工确认'

def generate_single_choice_answer(question):
    """生成单选题AI答案"""
    # 提取选项
    options = re.findall(r'([A-E])[\.．\s]*([^\n]+)', question)
    if not options:
        return '?', '无法提取选项'
    
    # 简单启发式：选择包含积极词汇的选项
    positive_keywords = ['正确', '合理', '有效', '全面', '准确', '规范', '标准', '安全']
    
    for opt_letter, opt_text in options:
        for kw in positive_keywords:
            if kw in opt_text:
                return opt_letter, f'选项包含积极关键词"{kw}"'
    
    # 默认选A（需要人工确认）
    return 'A', '默认答案，需要人工确认'

def generate_multiple_choice_answer(question):
    """生成多选题AI答案"""
    # 提取选项
    options = re.findall(r'([A-E])[\.．\s]*([^\n]+)', question)
    if not options:
        return '?', '无法提取选项'
    
    # 多选题通常选2-4个选项
    # 简单启发式：选择包含积极词汇的选项
    positive_keywords = ['正确', '合理', '有效', '全面', '准确', '规范', '标准', '安全', '保护', '提高']
    negative_keywords = ['错误', '不合理', '无效', '片面', '不准确', '不规范', '危险', '降低']
    
    selected = []
    for opt_letter, opt_text in options:
        is_positive = any(kw in opt_text for kw in positive_keywords)
        is_negative = any(kw in opt_text for kw in negative_keywords)
        
        if is_positive and not is_negative:
            selected.append(opt_letter)
    
    # 如果没有选中任何选项，默认选前两个
    if not selected:
        selected = ['A', 'B']
    
    # 如果选了所有选项，去掉最后一个
    if len(selected) == len(options):
        selected = selected[:-1]
    
    return ','.join(selected), f'基于关键词选择'

# 生成Anki卡片
print("\n" + "="*60)
print("生成Anki卡片（含AI预测答案）...")
print("="*60)

os.makedirs('anki_cards', exist_ok=True)

# 判断题
judgment_count = 0
if questions['判断题']:
    with open('anki_cards/理论知识_判断题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['判断题']):
            front = f"【判断题】{q}"
            ai_answer, ai_reason = generate_judgment_answer(q)
            back = f"【AI预测答案】{ai_answer}\n\n【AI分析】{ai_reason}\n\n⚠️ 此为AI预测答案，请人工确认！\n\n【题目】\n{q}"
            writer.writerow([front, back])
            if ai_answer != '?':
                judgment_count += 1
    print(f"✅ 判断题: {len(questions['判断题'])}题（AI预测{judgment_count}题）→ anki_cards/理论知识_判断题.csv")

# 单选题
single_count = 0
if questions['单选题']:
    with open('anki_cards/理论知识_单选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['单选题']):
            front = f"【单选题】{q}"
            ai_answer, ai_reason = generate_single_choice_answer(q)
            back = f"【AI预测答案】{ai_answer}\n\n【AI分析】{ai_reason}\n\n⚠️ 此为AI预测答案，请人工确认！\n\n【题目】\n{q}"
            writer.writerow([front, back])
            if ai_answer != '?':
                single_count += 1
    print(f"✅ 单选题: {len(questions['单选题'])}题（AI预测{single_count}题）→ anki_cards/理论知识_单选题.csv")

# 多选题
multiple_count = 0
if questions['多选题']:
    with open('anki_cards/理论知识_多选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['多选题']):
            front = f"【多选题】{q}"
            ai_answer, ai_reason = generate_multiple_choice_answer(q)
            back = f"【AI预测答案】{ai_answer}\n\n【AI分析】{ai_reason}\n\n⚠️ 此为AI预测答案，请人工确认！\n\n【题目】\n{q}"
            writer.writerow([front, back])
            if ai_answer != '?':
                multiple_count += 1
    print(f"✅ 多选题: {len(questions['多选题'])}题（AI预测{multiple_count}题）→ anki_cards/理论知识_多选题.csv")

# 合并版
with open('anki_cards/理论知识_全部题目.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['正面', '背面'])
    for qtype, qlist in questions.items():
        for q in qlist:
            front = f"【{qtype}】{q}"
            if qtype == '判断题':
                ai_answer, ai_reason = generate_judgment_answer(q)
            elif qtype == '单选题':
                ai_answer, ai_reason = generate_single_choice_answer(q)
            else:
                ai_answer, ai_reason = generate_multiple_choice_answer(q)
            back = f"【AI预测答案】{ai_answer}\n\n【AI分析】{ai_reason}\n\n⚠️ 此为AI预测答案，请人工确认！\n\n【题目】\n{q}"
            writer.writerow([front, back])

print(f"\n✅ 合并版: {total}题 → anki_cards/理论知识_全部题目.csv")

# 显示示例
print("\n" + "="*60)
print("判断题示例（前5题）:")
print("="*60)
for i, q in enumerate(questions['判断题'][:5]):
    ai_answer, ai_reason = generate_judgment_answer(q)
    print(f"\n{i+1}. {q[:80]}")
    print(f"   AI答案: {ai_answer} - {ai_reason}")

print("\n" + "="*60)
print("单选题示例（前3题）:")
print("="*60)
for i, q in enumerate(questions['单选题'][:3]):
    ai_answer, ai_reason = generate_single_choice_answer(q)
    print(f"\n{i+1}. {q[:100]}...")
    print(f"   AI答案: {ai_answer} - {ai_reason}")

print("\n" + "="*60)
print("多选题示例（前3题）:")
print("="*60)
for i, q in enumerate(questions['多选题'][:3]):
    ai_answer, ai_reason = generate_multiple_choice_answer(q)
    print(f"\n{i+1}. {q[:100]}...")
    print(f"   AI答案: {ai_answer} - {ai_reason}")

print("\n" + "="*60)
print("✅ 完成！")
print("="*60)
print("\n⚠️ 重要提示：")
print("  - AI答案基于简单启发式规则生成")
print("  - 准确率有限，仅供复习参考")
print("  - 建议人工核对标准答案")
print("  - 标记为'?'的题目需要特别注意")