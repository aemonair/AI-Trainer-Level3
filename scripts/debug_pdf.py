#!/usr/bin/env python3
"""调试 PDF 文本格式"""

import fitz
from pathlib import Path

PDF_PATH = Path("/Users/air/Downloads/GUIDE_AI_3/第4部分_人工智能训练师_3级_操作技能复习题.pdf")

doc = fitz.open(str(PDF_PATH))

# 查看前 10 页的内容
for i in range(min(10, len(doc))):
    page = doc[i]
    text = page.get_text()

    print(f"\n{'='*60}")
    print(f"第 {i+1} 页")
    print(f"{'='*60}")

    # 打印前 50 行
    lines = text.split('\n')
    for j, line in enumerate(lines[:50]):
        print(f"{j:3d}: [{line}]")

    print(f"... (共 {len(lines)} 行)")

doc.close()
