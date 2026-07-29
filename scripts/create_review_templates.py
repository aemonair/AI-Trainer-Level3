#!/usr/bin/env python3
"""
在每个以 "-素材" 结尾的目录中批量创建 `复盘.md` 模板（如果不存在）。
"""
from pathlib import Path
import datetime

ROOT = Path('.').resolve()
count = 0
for p in sorted(ROOT.iterdir()):
    if p.is_dir() and p.name.endswith('-素材'):
        target = p / '复盘.md'
        if target.exists():
            continue
        content = f"""# 复盘

- 日期：{datetime.date.today().isoformat()}
- Notebook / 题目：{p.name}
- 今日完成内容：
  - 

## 1. 做题成果
- 主要目标：
- 今日完成：
- 结果是否达到预期：

## 2. 发现的问题与错误
- 错误点：
  - 
- 错误类型：
- 错误次数：
- 错误率：

## 3. 复盘结论
- 最关键的错误原因：
- 已采取的修正措施：
- 是否已解决：

## 4. 改进建议
- 本日可以改进的点：
- 明日重点关注：

## 5. 备注
- 额外记录：
- 需要复习的知识点：
"""
        target.write_text(content, encoding='utf-8')
        count += 1
print(f'Created {count} review template(s)')
