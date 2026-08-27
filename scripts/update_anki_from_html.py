#!/usr/bin/env python3
"""
从HTML文件中提取完整题目描述，更新Anki卡片
"""
from bs4 import BeautifulSoup
import csv
import os

def extract_html_questions():
    """从HTML文件中提取所有题目"""
    html_questions = {}
    for prefix in ['1.2', '4.1', '4.2']:
        for i in range(1, 6):
            filepath = f'html_questions/{prefix}.{i}.html'
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                h3 = soup.find('h3', string='工作任务')
                if h3:
                    next_elem = h3.find_next_sibling()
                    if next_elem:
                        key = f'{prefix}.{i}'
                        html_questions[key] = next_elem.get_text().strip()
    return html_questions

def update_anki_cards(html_questions):
    """更新Anki卡片CSV文件"""
    input_file = 'anki_1.2.X_4.1.X_4.2.X_题目答案.csv'
    output_file = 'anki_1.2.X_4.1.X_4.2.X_题目答案_updated.csv'
    
    updated_cards = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                front = row[0]
                back = row[1]
                
                # 提取题号（如 1.2.1）
                import re
                match = re.search(r'【(\d+\.\d+\.\d+)】', front)
                if match:
                    question_num = match.group(1)
                    if question_num in html_questions:
                        # 更新正面：使用HTML中的完整题目描述
                        new_front = f'【{question_num}】{front.split("】")[1].split("<br>")[0]}<br><br>📋 工作任务：<br>{html_questions[question_num].replace(chr(9), "<br>")}<br><br>💡 提示：请将答案写在对应题号的答题卷上'
                        updated_cards.append([new_front, back])
                        print(f'✅ 更新 {question_num}')
                    else:
                        updated_cards.append(row)
                else:
                    updated_cards.append(row)
    
    # 写入更新后的CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(updated_cards)
    
    print(f'\n✅ 已更新 {len(updated_cards)} 张卡片')
    print(f'📁 输出文件：{output_file}')
    return output_file

if __name__ == '__main__':
    print('='*60)
    print('从HTML提取题目并更新Anki卡片')
    print('='*60)
    
    html_questions = extract_html_questions()
    print(f'✅ 提取了 {len(html_questions)} 个HTML题目')
    
    output_file = update_anki_cards(html_questions)