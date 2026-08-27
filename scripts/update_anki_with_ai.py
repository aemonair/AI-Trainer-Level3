#!/usr/bin/env python3
"""
更新Anki CSV文件 - 对比AI答案和PDF答案
- 一致：直接使用
- 不一致：同时显示两个答案，标记⚠️
"""

import csv
import json
import re
from pathlib import Path

def load_ai_results():
    """加载AI答题结果"""
    with open('reports/ai_vs_pdf_complete.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建题号到AI答案的映射
    ai_answers = {}
    wrong_nums = set()
    
    for w in data['wrong_questions']:
        ai_answers[w['num']] = w['ai']
        wrong_nums.add(w['num'])
    
    return ai_answers, wrong_nums, data

def update_anki_csv():
    """更新Anki CSV文件"""
    ai_answers, wrong_nums, ai_data = load_ai_results()
    
    csv_file = Path('anki_cards/理论知识_单选题.csv')
    output_file = Path('anki_cards/理论知识_单选题_updated.csv')
    
    updated_count = 0
    consistent_count = 0
    inconsistent_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.reader(f_in, delimiter=';')
        writer = csv.writer(f_out, delimiter=';')
        
        # 写入表头
        header = next(reader)
        writer.writerow(header)
        
        # 逐行处理，使用行号作为题号
        for row_idx, row in enumerate(reader, start=1):
            if len(row) < 2:
                writer.writerow(row)
                continue
            
            front = row[0]
            back = row[1]
            q_num = row_idx  # 行号即题号
            
            # 提取PDF答案
            pdf_match = re.search(r'【PDF答案】([A-E])', back)
            pdf_ans = pdf_match.group(1) if pdf_match else None
            
            if q_num in ai_answers and pdf_ans:
                # AI和PDF答案不一致
                ai_ans = ai_answers[q_num]
                
                if ai_ans != pdf_ans:
                    inconsistent_count += 1
                    
                    # 更新背面内容
                    new_back = f"""⚠️ AI与PDF答案不一致

【PDF答案】{pdf_ans}
【AI答案】{ai_ans}

请重点复习此题！

【题目】
{front.replace('【单选题】', '').strip()}"""
                    
                    writer.writerow([front, new_back])
                    updated_count += 1
                else:
                    # 答案一致（理论上不应该出现，因为wrong_nums只包含不一致的）
                    consistent_count += 1
                    writer.writerow(row)
            else:
                # AI和PDF答案一致，或不在AI答题范围内
                consistent_count += 1
                writer.writerow(row)
    
    print(f"✅ 更新完成！")
    print(f"   总题数: 299")
    print(f"   ✅ 答案一致: {consistent_count}")
    print(f"   ⚠️ 答案不一致: {inconsistent_count}")
    print(f"   已更新: {updated_count}题")
    print(f"\n💾 新文件: {output_file}")

if __name__ == '__main__':
    update_anki_csv()