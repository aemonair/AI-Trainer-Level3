#!/usr/bin/env python3
"""测试精确提取填空答案 - 改进版"""
import json
import re

# 读取文件
with open('1.1.1-materials/1.1.1.ipynb', 'r') as f:
    template = json.load(f)

with open('answers/1.1.1 - 4.2.5参考答案/1.1.1/1.1.1.ipynb', 'r') as f:
    answer = json.load(f)

print("=" * 80)
print("精确提取填空答案测试 - 改进版")
print("=" * 80)

for i, (t_cell, a_cell) in enumerate(zip(template['cells'], answer['cells'])):
    if t_cell['cell_type'] != 'code':
        continue
    
    t_source = ''.join(t_cell['source'])
    a_source = ''.join(a_cell['source'])
    
    t_lines = t_source.split('\n')
    a_lines = a_source.split('\n')
    
    # 查找模板中的填空
    for j, (t_line, a_line) in enumerate(zip(t_lines, a_lines)):
        blanks = list(re.finditer(r'_{3,}', t_line))
        if blanks:
            print(f"\n📝 Cell {i}, Line {j}:")
            print(f"  模板: {t_line.strip()}")
            print(f"  答案: {a_line.strip()}")
            
            # 改进：逐个填空提取
            prev_end = 0
            for b_idx, blank in enumerate(blanks):
                # 获取填空前后的内容
                before = t_line[prev_end:blank.start()]
                after_blank = t_line[blank.end():]
                
                # 查找下一个填空的位置
                if b_idx + 1 < len(blanks):
                    next_blank_start = blanks[b_idx + 1].start()
                    after = t_line[blank.end():next_blank_start]
                else:
                    after = after_blank
                
                # 在答案行中定位
                if before.strip() in a_line:
                    start_idx = a_line.index(before.strip()) + len(before.strip())
                    
                    if after.strip() and after.strip() in a_line[start_idx:]:
                        end_idx = a_line.index(after.strip(), start_idx)
                        answer_text = a_line[start_idx:end_idx].strip()
                    else:
                        # 最后一个填空，取到行尾
                        answer_text = a_line[start_idx:].strip()
                    
                    print(f"  ✓ 填空{b_idx}: '{answer_text}'")
                else:
                    print(f"  ✗ 填空{b_idx}: 无法匹配 (before='{before.strip()}')")
                
                prev_end = blank.end()