#!/usr/bin/env python3
"""
根据官方答案更新Anki卡片
- 判断题：使用PDF提取的263题答案
- 单选题：使用官方提供的参考答案
- 标注答案差异
"""
import csv
import os

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

print("="*60)
print("根据官方答案更新Anki卡片")
print("="*60)

# 官方单选题答案（从您提供的对比分析中提取）
official_single_answers = {
    1: 'A', 2: 'B', 3: 'B', 4: 'C', 5: 'D',
    6: 'D', 7: 'B', 8: 'D', 9: 'B', 10: 'D',
    11: 'A', 12: 'C', 13: 'B', 14: 'B', 15: 'D',
    16: 'D', 17: 'A', 18: 'A', 19: 'A', 20: 'A',
    21: 'D', 22: 'A', 23: 'A', 24: 'D', 25: 'A',
    26: 'A', 27: 'B', 28: 'B', 29: 'C', 30: 'D',
    31: 'B', 32: 'D', 33: 'A', 34: 'C', 35: 'C',
    36: 'D', 37: 'D', 38: 'D', 39: 'D', 40: 'C',
    41: 'B', 42: 'A', 43: 'B', 44: 'D', 45: 'C',
    46: 'A', 47: 'A', 48: 'D', 49: 'C', 50: 'A',
    51: 'C', 52: 'D', 53: 'C', 54: 'A', 55: 'A',
    56: 'A', 57: 'C', 58: 'A', 59: 'A', 60: 'B',
    61: 'A', 62: 'B', 63: 'A', 64: 'B', 65: 'D',
    66: 'A', 67: 'C', 68: 'B', 69: 'C', 70: 'D',
    71: 'C', 72: 'C', 73: 'D', 74: 'C', 75: 'D',
    76: 'A', 77: 'D', 78: 'A', 79: 'B', 80: 'A',
    81: 'A', 82: 'C', 83: 'B', 84: 'A', 85: 'C',
    86: 'A', 87: 'C', 88: 'A', 89: 'D', 90: 'D',
    91: 'C', 92: 'D', 93: 'B', 94: 'A', 95: 'B',
    96: 'A', 97: 'A', 98: 'C', 99: 'B', 100: 'A',
    101: 'B', 102: 'B', 103: 'A', 104: 'D', 105: 'C',
    106: 'A', 107: 'A', 108: 'D', 109: 'A', 110: 'A',
    111: 'B', 112: 'C', 113: 'B', 114: 'A', 115: 'B',
    116: 'B', 117: 'A', 118: 'A', 119: 'C', 120: 'B',
    121: 'C', 122: 'D', 123: 'B', 124: 'B', 125: 'A',
    126: 'A', 127: 'D', 128: 'A', 129: 'A', 130: 'B',
    131: 'D', 132: 'B', 133: 'D', 134: 'A', 135: 'B',
    136: 'B', 137: 'B', 138: 'A', 139: 'A', 140: 'A',
    141: 'B', 142: 'C', 143: 'A', 144: 'B', 145: 'C',
    146: 'A', 147: 'B', 148: 'C', 149: 'B', 150: 'C',
    151: 'D', 152: 'D', 153: 'A', 154: 'C', 155: 'B',
    156: 'A', 157: 'C', 158: 'A', 159: 'A', 160: 'A',
    161: 'C', 162: 'B', 163: 'D', 164: 'C', 165: 'C',
    166: 'C', 167: 'C', 168: 'B', 169: 'C', 170: 'B',
    171: 'A', 172: 'B', 173: 'C', 174: 'A', 175: 'A',
    176: 'A', 177: 'D', 178: 'B', 179: 'A', 180: 'A',
    181: 'A', 182: 'C', 183: 'C', 184: 'B', 185: 'C',
    186: 'B', 187: 'D', 188: 'D', 189: 'B', 190: 'B',
    191: 'C', 192: 'A', 193: 'D', 194: 'A', 195: 'C',
    196: 'B', 197: 'B', 198: 'C', 199: 'B', 200: 'A',
    201: 'C', 202: 'C', 203: 'A', 204: 'A', 205: 'C',
    206: 'D', 207: 'D', 208: 'B', 209: 'D', 210: 'C',
    211: 'D', 212: 'A', 213: 'C', 214: 'A', 215: 'A',
    216: 'A', 217: 'A', 218: 'A', 219: 'B', 220: 'B',
    221: 'A', 222: 'D', 223: 'D', 224: 'B', 225: 'B',
    226: 'A', 227: 'C', 228: 'B', 229: 'A', 230: 'A',
    231: 'C', 232: 'C', 233: 'D', 234: 'B', 235: 'B',
    236: 'A', 237: 'A', 238: 'C', 239: 'B', 240: 'B',
    241: 'B', 242: 'A', 243: 'A', 244: 'B', 245: 'B',
    246: 'A', 247: 'B', 248: 'B', 249: 'C', 250: 'D',
    251: 'D', 252: 'A', 253: 'A', 254: 'A', 255: 'C',
    256: 'C', 257: 'A', 258: 'B', 259: 'B', 260: 'B',
    261: 'C', 262: 'C', 263: 'B', 264: 'A', 265: 'C',
    266: 'B', 267: 'C', 268: 'A', 269: 'D', 270: 'C',
    271: 'D', 272: 'A', 273: 'C', 274: 'C', 275: 'A',
    276: 'C', 277: 'C', 278: 'A', 279: 'B', 280: 'B',
    281: 'A', 282: 'C', 283: 'A', 284: 'C', 285: 'A',
    286: 'A', 287: 'C', 288: 'B', 289: 'C', 290: 'A',
    291: 'C', 292: 'A', 293: 'D', 294: 'A', 295: 'B',
    296: 'C', 297: 'C', 298: 'C', 299: 'B', 300: 'B'
}

print(f"官方单选题答案: {len(official_single_answers)} 题")

# DeepSeek单选题答案（从原脚本中复制）
deepseek_single_answers = {
    1: 'A', 2: 'B', 3: 'B', 4: 'C', 5: 'D',
    6: 'D', 7: 'B', 8: 'D', 9: 'B', 10: 'D',
    11: 'A', 12: 'C', 13: 'B', 14: 'B', 15: 'D',
    16: 'D', 17: 'A', 18: 'A', 19: 'A', 20: 'A',
    21: 'D', 22: 'A', 23: 'A', 24: 'D', 25: 'A',
    26: 'A', 27: 'B', 28: 'B', 29: 'D', 30: 'D',
    31: 'B', 32: 'D', 33: 'A', 34: 'C', 35: 'C',
    36: 'D', 37: 'D', 38: 'D', 39: 'D', 40: 'C',
    41: 'B', 42: 'A', 43: 'B', 44: 'D', 45: 'C',
    46: 'A', 47: 'A', 48: 'D', 49: 'C', 50: 'A',
    51: 'C', 52: 'D', 53: 'C', 54: 'A', 55: 'A',
    56: 'A', 57: 'C', 58: 'A', 59: 'A', 60: 'B',
    61: 'A', 62: 'D', 63: 'A', 64: 'B', 65: 'D',
    66: 'A', 67: 'C', 68: 'B', 69: 'C', 70: 'D',
    71: 'C', 72: 'C', 73: 'D', 74: 'C', 75: 'A',
    76: 'A', 77: 'D', 78: 'A', 79: 'B', 80: 'A',
    81: 'A', 82: 'C', 83: 'B', 84: 'A', 85: 'C',
    86: 'A', 87: 'C', 88: 'A', 89: 'D', 90: 'D',
    91: 'C', 92: 'D', 93: 'B', 94: 'A', 95: 'B',
    96: 'A', 97: 'A', 98: 'C', 99: 'B', 100: 'A',
    101: 'B', 102: 'B', 103: 'A', 104: 'D', 105: 'C',
    106: 'A', 107: 'A', 108: 'D', 109: 'A', 110: 'A',
    111: 'B', 112: 'C', 113: 'B', 114: 'A', 115: 'B',
    116: 'B', 117: 'A', 118: 'A', 119: 'C', 120: 'B',
    121: 'C', 122: 'D', 123: 'B', 124: 'B', 125: 'A',
    126: 'A', 127: 'D', 128: 'A', 129: 'A', 130: 'B',
    131: 'D', 132: 'B', 133: 'D', 134: 'A', 135: 'B',
    136: 'B', 137: 'B', 138: 'A', 139: 'A', 140: 'A',
    141: 'B', 142: 'C', 143: 'A', 144: 'B', 145: 'C',
    146: 'A', 147: 'B', 148: 'C', 149: 'B', 150: 'C',
    151: 'D', 152: 'D', 153: 'A', 154: 'C', 155: 'B',
    156: 'A', 157: 'C', 158: 'A', 159: 'A', 160: 'A',
    161: 'C', 162: 'B', 163: 'D', 164: 'C', 165: 'C',
    166: 'C', 167: 'C', 168: 'B', 169: 'C', 170: 'B',
    171: 'A', 172: 'B', 173: 'C', 174: 'A', 175: 'A',
    176: 'A', 177: 'D', 178: 'B', 179: 'A', 180: 'A',
    181: 'A', 182: 'C', 183: 'C', 184: 'B', 185: 'C',
    186: 'B', 187: 'D', 188: 'D', 189: 'B', 190: 'B',
    191: 'C', 192: 'A', 193: 'D', 194: 'A', 195: 'C',
    196: 'B', 197: 'B', 198: 'C', 199: 'B', 200: 'A',
    201: 'C', 202: 'C', 203: 'A', 204: 'A', 205: 'C',
    206: 'D', 207: 'D', 208: 'B', 209: 'D', 210: 'C',
    211: 'D', 212: 'A', 213: 'C', 214: 'A', 215: 'A',
    216: 'A', 217: 'A', 218: 'A', 219: 'A', 220: 'B',
    221: 'A', 222: 'D', 223: 'D', 224: 'B', 225: 'B',
    226: 'A', 227: 'C', 228: 'B', 229: 'A', 230: 'A',
    231: 'C', 232: 'C', 233: 'D', 234: 'B', 235: 'B',
    236: 'A', 237: 'A', 238: 'C', 239: 'A', 240: 'B',
    241: 'B', 242: 'A', 243: 'A', 244: 'B', 245: 'B',
    246: 'A', 247: 'B', 248: 'B', 249: 'C', 250: 'D',
    251: 'D', 252: 'A', 253: 'A', 254: 'A', 255: 'C',
    256: 'C', 257: 'A', 258: 'B', 259: 'B', 260: 'B',
    261: 'C', 262: 'C', 263: 'B', 264: 'A', 265: 'C',
    266: 'B', 267: 'C', 268: 'A', 269: 'D', 270: 'C',
    271: 'D', 272: 'A', 273: 'C', 274: 'C', 275: 'A',
    276: 'C', 277: 'C', 278: 'A', 279: 'B', 280: 'B',
    281: 'A', 282: 'C', 283: 'A', 284: 'C', 285: 'A',
    286: 'A', 287: 'C', 288: 'B', 289: 'C', 290: 'A',
    291: 'C', 292: 'A', 293: 'D', 294: 'A', 295: 'B',
    296: 'C', 297: 'C', 298: 'C', 299: 'B', 300: 'B'
}

print(f"DeepSeek单选题答案: {len(deepseek_single_answers)} 题")

# 统计差异
same_count = 0
diff_count = 0
diff_questions = []

for i in range(1, 301):
    ds = deepseek_single_answers.get(i)
    off = official_single_answers.get(i)
    if ds and off:
        if ds == off:
            same_count += 1
        else:
            diff_count += 1
            diff_questions.append((i, ds, off))

print(f"\n答案对比统计:")
print(f"一致: {same_count} 题")
print(f"差异: {diff_count} 题")
print(f"差异题号: {[q[0] for q in diff_questions]}")

# 更新单选题Anki卡片
os.makedirs('anki_cards_updated', exist_ok=True)

input_file = 'anki_cards/理论知识_单选题.csv'
output_file = 'anki_cards_updated/理论知识_单选题_含官方答案.csv'

with open(input_file, 'r', encoding='utf-8') as fin, \
     open(output_file, 'w', encoding='utf-8', newline='') as fout:
    
    reader = csv.reader(fin, delimiter=';')
    writer = csv.writer(fout, delimiter=';')
    
    header = next(reader)
    writer.writerow(header)
    
    for row in reader:
        if len(row) >= 2:
            front = row[0]
            back = row[1]
            
            # 提取题号
            import re
            match = re.search(r'【单选题】.*?(\d+)', front)
            if match:
                # 重新生成背面内容
                question_num = int(match.group(1))
                ds_answer = deepseek_single_answers.get(question_num)
                off_answer = official_single_answers.get(question_num)
                
                # 提取原题目
                question_match = re.search(r'【题目】\n(.+)', back, re.DOTALL)
                question_text = question_match.group(1) if question_match else ""
                
                back_parts = []
                
                if ds_answer:
                    back_parts.append(f"【DeepSeek答案】{ds_answer}")
                
                if off_answer:
                    back_parts.append(f"【官方答案】{off_answer}")
                
                if ds_answer and off_answer:
                    if ds_answer == off_answer:
                        back_parts.append("✅ 两者答案一致")
                    else:
                        back_parts.append("⚠️ 答案不一致，请重点复习！")
                        back_parts.append(f"📌 DeepSeek选{ds_answer}，官方选{off_answer}")
                elif ds_answer and not off_answer:
                    back_parts.append("⚠️ 官方答案缺失，此为AI预测答案")
                elif off_answer and not ds_answer:
                    back_parts.append("⚠️ DeepSeek答案缺失")
                
                if not ds_answer and not off_answer:
                    back_parts.append("⚠️ 暂无答案，请人工确认")
                
                back_parts.append(f"\n【题目】\n{question_text}")
                new_back = '\n\n'.join(back_parts)
                
                writer.writerow([front, new_back])

print(f"\n✅ 已更新单选题Anki卡片: {output_file}")

# 生成差异题目专项复习卡片
diff_output = 'anki_cards_updated/单选题_差异题目专项复习.csv'

with open(diff_output, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['正面', '背面'])
    
    for q_num, ds_ans, off_ans in diff_questions:
        front = f"【差异题{q_num}】DeepSeek选{ds_ans} vs 官方选{off_ans}，正确答案是？"
        back = f"【官方答案】{off_ans}\n"
        back += f"【DeepSeek答案】{ds_ans}\n"
        back += f"⚠️ 此题答案有差异，请以官方答案为准\n"
        back += f"\n建议：查阅教材或课程讲义确认正确答案"
        
        writer.writerow([front, back])

print(f"✅ 已生成差异题目专项复习卡片: {diff_output}")
print(f"   共 {len(diff_questions)} 道差异题")

print("\n" + "="*60)
print("✅ 完成！")
print("="*60)