import json
import re
from pathlib import Path

def extract_fill_blanks(source):
    return re.findall(r'_{3,}', source)

def split_cell_into_questions(source):
    pattern = r'(^|\n)(\s*#\s*.+?\s+\d+分\s*\n)'
    splits = []
    for match in re.finditer(pattern, source):
        splits.append(match.start())
    
    if not splits:
        return [{'title': '', 'source': source}] if extract_fill_blanks(source) else []
    
    questions = []
    for i, start in enumerate(splits):
        end = splits[i + 1] if i + 1 < len(splits) else len(source)
        question_source = source[start:end].strip()
        title_match = re.match(r'\s*#\s*(.+?\s+\d+分)', question_source)
        title = title_match.group(1).strip() if title_match else ''
        questions.append({'title': title, 'source': question_source})
    
    return [q for q in questions if extract_fill_blanks(q['source'])]

# 测试练习文件
practice_path = Path('1.1.1-materials/1.1.1.ipynb')
answer_path = Path('answers/1.1.1 - 4.2.5参考答案/1.1.1/1.1.1.ipynb')

with open(practice_path, 'r') as f:
    p_nb = json.load(f)
with open(answer_path, 'r') as f:
    a_nb = json.load(f)

print(f"Practice cells: {len(p_nb['cells'])}")
print(f"Answer cells: {len(a_nb['cells'])}")

for i, (p_cell, a_cell) in enumerate(zip(p_nb['cells'], a_nb['cells'])):
    if p_cell.get('cell_type') != 'code':
        continue
    
    p_src = ''.join(p_cell['source']) if isinstance(p_cell['source'], list) else p_cell['source']
    a_src = ''.join(a_cell['source']) if isinstance(a_cell['source'], list) else a_cell['source']
    
    p_subs = split_cell_into_questions(p_src)
    a_subs = split_cell_into_questions(a_src)
    
    print(f"\nCell {i}:")
    print(f"  Practice sub-questions: {len(p_subs)}")
    print(f"  Answer sub-questions: {len(a_subs)}")
    
    for j, (p_sub, a_sub) in enumerate(zip(p_subs, a_subs)):
        blanks = extract_fill_blanks(p_sub['source'])
        print(f"  Q{j+1}: {p_sub['title'][:50]} - {len(blanks)} blanks")