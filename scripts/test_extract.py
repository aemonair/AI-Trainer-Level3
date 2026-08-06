import json
import re

with open('1.1.1-materials/1.1.1.ipynb', 'r') as f:
    nb = json.load(f)

cell = nb['cells'][1]
src = ''.join(cell['source'])

blanks = re.findall(r'_{3,}', src)
print(f"Cell 1 blanks: {len(blanks)}")

pattern = r'(^|\n)(\s*#\s*.+?\s+\d+分\s*\n)'
splits = []
for match in re.finditer(pattern, src):
    splits.append(match.start())

print(f"Splits: {splits}")

for i, start in enumerate(splits):
    end = splits[i+1] if i+1 < len(splits) else len(src)
    qs = src[start:end].strip()
    blanks = re.findall(r'_{3,}', qs)
    print(f"Q{i+1}: {len(blanks)} blanks, text={qs[:80]}")