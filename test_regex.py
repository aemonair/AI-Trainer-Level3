import re
from pathlib import Path

for f in ['1.1.4-materials/1.1.4_practice_202608011746_review.md',
          '2.1.1-materials/2.1.1_practice_202608011914_review.md']:
    content = Path(f).read_text()
    print(f'=== {f} ===')
    # 简单查找
    errors = re.findall(r'### 错误\d+', content)
    print(f'  错误数: {len(errors)} -> {errors}')
    print()