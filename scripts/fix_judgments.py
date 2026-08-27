#!/usr/bin/env python3
"""
检查并修复判断题CSV - 合并v2答案，添加PDF答案和判断理由
"""

import csv
import re
from pathlib import Path

def analyze_and_fix():
    orig_file = Path('anki_cards/理论知识_判断题.csv')
    v2_file = Path('anki_cards/理论知识_判断题_v2.csv')
    output_file = Path('anki_cards/理论知识_判断题_fixed.csv')
    
    # 1. 读取v2版本获取完整题目和答案
    v2_data = {}
    with open(v2_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            if len(row) < 2:
                continue
            front = row[0]
            back = row[1]
            
            # 提取题号
            num_match = re.match(r'第(\d+)题', front)
            if not num_match:
                continue
            q_num = int(num_match.group(1))
            
            # 提取答案
            ans_match = re.search(r'【答案】([√×])', back)
            pdf_ans = ans_match.group(1) if ans_match else '?'
            
            # 提取完整题目（去掉题号前缀）
            full_question = re.sub(r'^第\d+题\n', '', front)
            
            v2_data[q_num] = {
                'question': full_question,
                'answer': pdf_ans
            }
    
    print(f"✅ 从v2版本读取了 {len(v2_data)} 题")
    
    # 2. 读取原始文件，合并答案
    total = 0
    fixed_count = 0
    truncated_count = 0
    
    with open(orig_file, 'r', encoding='utf-8') as f_in, \
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
            
            if front.strip() == '正面':
                continue
            
            q_num += 1
            total += 1
            
            # 判断原题目是否被截断
            orig_question = front
            last_char = orig_question.rstrip()[-1]
            is_truncated = last_char not in ['。', '？', '）', '"', '：', '，', '；', '、', '．', '”', '！', '。', '?', ')', '】']
            if is_truncated:
                truncated_count += 1
            
            # 从v2获取完整题目和答案
            v2_info = v2_data.get(q_num, {})
            full_question = v2_info.get('question', orig_question)
            pdf_ans = v2_info.get('answer', '?')
            
            # 提取原始文件中的答案
            orig_standard = '?'
            std_match = re.search(r'【标准答案】([√×])', back)
            if std_match:
                orig_standard = std_match.group(1)
            
            # 提取DeepSeek答案
            deepseek_ans = '?'
            ds_match = re.search(r'【DeepSeek答案】([√×])', back)
            if ds_match:
                deepseek_ans = ds_match.group(1)
            
            # 构建判断理由
            reasons = {
                '√': '该说法符合相关规范/标准',
                '×': '该说法不符合相关规范/标准'
            }
            reason = reasons.get(pdf_ans, '需根据实际情况判断')
            
            # 如果原题被截断，使用完整题目
            new_front = full_question
            
            # 构建新的背面内容
            new_back = f"""【PDF答案】{pdf_ans}
【标准答案】{orig_standard}
【DeepSeek答案】{deepseek_ans}
【判断理由】{reason}

【题目】
{full_question}"""
            
            writer.writerow([new_front, new_back])
            fixed_count += 1
    
    print(f"\n📊 统计:")
    print(f"   总题数: {total}")
    print(f"   原截断题目: {truncated_count}")
    print(f"   已修复: {fixed_count}")
    print(f"\n💾 输出文件: {output_file}")

if __name__ == '__main__':
    analyze_and_fix()