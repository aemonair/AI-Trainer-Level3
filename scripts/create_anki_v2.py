#!/usr/bin/env python3
"""
创建理论知识_单选题_v2.csv - 包含题号标号
- 正面添加题号
- 背面显示PDF答案和AI答案对比
"""

import csv
import json
import re
from pathlib import Path

def load_ai_results():
    """加载AI答题结果"""
    with open('reports/ai_vs_pdf_complete.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ai_answers = {}
    for w in data['wrong_questions']:
        ai_answers[w['num']] = w['ai']
    
    return ai_answers, data

def create_v2_csv():
    """创建v2版本CSV"""
    ai_answers, ai_data = load_ai_results()
    
    csv_file = Path('anki_cards/理论知识_单选题.csv')
    output_file = Path('anki_cards/理论知识_单选题_v2.csv')
    
    consistent_count = 0
    inconsistent_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.reader(f_in, delimiter=';')
        writer = csv.writer(f_out, delimiter=';')
        
        # 写入表头
        writer.writerow(['正面', '背面'])
        
        # 逐行处理（跳过表头行）
        q_num = 0
        for row in reader:
            if len(row) < 2:
                continue
            
            front = row[0]
            back = row[1]
            
            # 跳过表头
            if front.strip() == '正面':
                continue
            
            q_num += 1
            
            # 提取PDF答案
            pdf_match = re.search(r'【PDF答案】([A-E])', back)
            pdf_ans = pdf_match.group(1) if pdf_match else '?'
            
            # 正面添加题号
            new_front = f"第{q_num}题\n{front}"
            
            # 判断是否一致
            if q_num in ai_answers:
                ai_ans = ai_answers[q_num]
                if ai_ans != pdf_ans:
                    # 不一致
                    inconsistent_count += 1
                    new_back = f"""⚠️ AI与PDF答案不一致

【PDF答案】{pdf_ans}
【AI答案】{ai_ans}

💡 请重点复习此题！

━━━━━━━━━━━━━━━━━━
【完整题目】
{front}"""
                else:
                    # 一致（理论上不会出现）
                    consistent_count += 1
                    new_back = f"""【答案】{pdf_ans}

【题目】
{front}"""
            else:
                # AI未作答或一致
                consistent_count += 1
                new_back = f"""【答案】{pdf_ans}

【题目】
{front}"""
            
            writer.writerow([new_front, new_back])
    
    print(f"✅ v2版本创建完成！")
    print(f"   总题数: 299")
    print(f"   ✅ 答案一致: {consistent_count}")
    print(f"   ⚠️ 答案不一致: {inconsistent_count}")
    print(f"\n💾 新文件: {output_file}")

if __name__ == '__main__':
    create_v2_csv()