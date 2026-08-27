#!/usr/bin/env python3
"""
分析判断题并创建v2版本
"""

import csv
import re
from pathlib import Path

def analyze_and_create_v2():
    csv_file = Path('anki_cards/理论知识_判断题.csv')
    output_file = Path('anki_cards/理论知识_判断题_v2.csv')
    
    total = 0
    has_standard = 0
    has_deepseek = 0
    has_personal = 0
    personal_correct = 0
    personal_wrong = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.reader(f_in, delimiter=';')
        writer = csv.writer(f_out, delimiter=';')
        
        # 写入表头
        writer.writerow(['正面', '背面'])
        
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
            total += 1
            
            # 提取标准答案
            standard_match = re.search(r'【标准答案】([√×])', back)
            standard_ans = standard_match.group(1) if standard_match else '?'
            if standard_match:
                has_standard += 1
            
            # 提取DeepSeek答案
            if 'DeepSeek答案' in back:
                has_deepseek += 1
            
            # 提取个人答案
            personal_match = re.search(r'【个人答案】([√×])', back)
            if personal_match:
                has_personal += 1
                if '个人答案正确' in back:
                    personal_correct += 1
                elif '个人答案错误' in back:
                    personal_wrong += 1
            
            # 创建v2格式
            new_front = f"第{q_num}题\n{front}"
            
            # 背面简化
            new_back = f"""【答案】{standard_ans}

【题目】
{front}"""
            
            writer.writerow([new_front, new_back])
    
    print(f"📊 判断题统计:")
    print(f"   总题数: {total}")
    print(f"   有标准答案: {has_standard}")
    print(f"   有DeepSeek答案: {has_deepseek}")
    print(f"   有个人答案: {has_personal}")
    print(f"   个人答对: {personal_correct}")
    print(f"   个人答错: {personal_wrong}")
    print(f"\n✅ v2版本创建完成: {output_file}")

if __name__ == '__main__':
    analyze_and_create_v2()