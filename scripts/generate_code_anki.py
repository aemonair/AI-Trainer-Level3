#!/usr/bin/env python3
"""从 all_chapters_review_full.md 解析代码填空题，生成一张一题的 Anki TSV"""
import re

MARKDOWN_FILE = 'reports/all_chapters_review_full.md'
OUTPUT_FILE = 'anki_cards/代码填空题.tsv'

with open(MARKDOWN_FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 状态机解析
# 状态: idle, in_chapter, in_question_title, in_practice_code, in_answer_code
records = []
chapter = ''
title = ''
practice_lines = []
answer_lines = []
state = 'idle'
total_questions = 0
total_blanks = 0

def highlight_answers(practice_code, answer_code):
    """将答案代码中对应填空位置的内容用红色+下划线高亮"""
    p_lines = practice_code.split('\n')
    a_lines = answer_code.split('\n')
    result_lines = []
    
    for p_line, a_line in zip(p_lines, a_lines):
        if re.search(r'_{5,}', p_line):
            # 按空白分隔，非空白部分作为定位锚点
            parts = re.split(r'_{5,}', p_line)
            pattern = ''
            for i, part in enumerate(parts):
                pattern += re.escape(part)
                if i < len(parts) - 1:
                    pattern += r'(.+)'
            
            m = re.match(pattern, a_line)
            if m:
                new_line = ''
                for i, part in enumerate(parts):
                    new_line += part
                    if i < len(parts) - 1:
                        new_line += f'<span style="color:#c62828;text-decoration:underline;font-weight:bold">{m.group(i + 1)}</span>'
                result_lines.append(new_line)
            else:
                result_lines.append(a_line)
        else:
            result_lines.append(a_line)
    
    return '\n'.join(result_lines)

def save_question():
    global total_questions, total_blanks, title
    if not practice_lines or not answer_lines:
        return
    
    practice_code = '\n'.join(practice_lines).strip()
    answer_code = '\n'.join(answer_lines).strip()
    
    if not practice_code or not answer_code:
        return
    
    # 统计填空数（任意长度下划线）
    blank_count = len(re.findall(r'_{5,}', practice_code))
    if blank_count == 0:
        return
    
    # 如果标题为空，从练习代码首行注释提取
    if not title:
        first_line = practice_lines[0].strip() if practice_lines else ''
        # 匹配注释行如 "# 1. 数据完整性审核" 或 "# 加载数据集"
        cm = re.match(r'^#\s*(?:\d+\.\s*)?(.+)$', first_line)
        if cm:
            title = cm.group(1).strip()
        else:
            # 回退到题目编号
            title = f'代码练习'
    
    # 构建正面（题目）
    front_html = f'''<div style="font-size:14px; color:#666; margin-bottom:8px">【{chapter}】{title}</div>
<pre style="background:#f5f5f5; padding:12px; border-radius:6px; font-size:13px; line-height:1.6; overflow-x:auto; border:1px solid #ddd">
{practice_code}</pre>'''
    
    # 构建背面（答案）— 填空部分加下划线高亮
    highlighted = highlight_answers(practice_code, answer_code)
    back_html = f'''<div style="font-size:14px; color:#666; margin-bottom:8px">【{chapter}】{title} — 共{blank_count}个填空</div>
<pre style="background:#f0faf0; padding:12px; border-radius:6px; font-size:13px; line-height:1.6; overflow-x:auto; border:1px solid #4CAF50; border-left:4px solid #4CAF50">
{highlighted}</pre>'''
    
    records.append((front_html, back_html, f'{chapter}::代码填空题'))
    total_questions += 1
    total_blanks += blank_count

for line in lines:
    stripped = line.rstrip()
    
    # 检测章节标题
    if stripped.startswith('## ') and stripped[3].isdigit():
        save_question()
        chapter = stripped[3:].strip()
        title = ''
        practice_lines = []
        answer_lines = []
        state = 'in_chapter'
        continue
    
    # 检测题目标题
    if stripped.startswith('### 题目'):
        save_question()
        # 提取标题 - 去掉 "### 题目N：" 前缀和分数
        m = re.search(r'^### 题目\d+[\uff1a:]\s*(.*)', stripped)
        if m:
            title = m.group(1).strip()
            # 去掉末尾的分数如 " 1分"
            title = re.sub(r'\s+\d+分\s*$', '', title)
        else:
            # 没有冒号标题（如"### 题目1"），后续从练习代码首行注释提取
            title = ''
        practice_lines = []
        answer_lines = []
        state = 'in_question_title'
        continue
    
    # 检测练习代码开始
    if stripped == '```python' and state in ('in_question_title', 'in_chapter'):
        # 检查上一行是否为 **练习代码**
        state = 'in_practice_code'
        continue
    
    # 检测答案代码开始（在练习代码结束后又遇到 ```python）
    if stripped == '```python' and state == 'after_practice':
        state = 'in_answer_code'
        continue
    
    # 检测代码块结束
    if stripped == '```':
        if state == 'in_practice_code':
            state = 'after_practice'
        elif state == 'in_answer_code':
            state = 'after_answer'
        continue
    
    # 收集代码行
    if state == 'in_practice_code':
        practice_lines.append(line.rstrip('\n'))
    elif state == 'in_answer_code':
        answer_lines.append(line.rstrip('\n'))

# 保存最后一个题目
save_question()

# 写入TSV文件
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write('正面\t背面\t标签\n')
    for front, back, tag in records:
        def quote_field(s):
            if '\n' in s or '\t' in s or '"' in s:
                return '"' + s.replace('"', '""') + '"'
            return s
        f.write(f'{quote_field(front)}\t{quote_field(back)}\t{quote_field(tag)}\n')

print(f'✅ 生成完成！')
print(f'   总题数: {total_questions} 题')
print(f'   总填空数: {total_blanks} 个')
print(f'   文件: {OUTPUT_FILE}')

# 按章节统计
from collections import Counter
chapters = set()
for r in records:
    ch = r[2].split('::')[0]
    chapters.add(ch)
print(f'   覆盖章节: {len(chapters)} 个')