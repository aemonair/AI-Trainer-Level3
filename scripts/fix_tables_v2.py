#!/usr/bin/env python3
"""
修复表格数据行：将评分表的数据行转换为标准Markdown表格格式
"""

import re
from pathlib import Path

BASE_DIR = Path("/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_三级_操作技能试题1")


def fix_table_data(content: str) -> str:
    """将评分表的数据行转换为Markdown表格格式"""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 检测表格开始（已有表头和分隔线）
        if re.match(r'^\| 细则编号 \| 配分 \| 评分细则描述 \|$', line):
            result.append(line)
            i += 1

            # 添加分隔线（如果还没有）
            if i < len(lines) and re.match(r'^\| --- \| --- \| --- \|$', lines[i].strip()):
                result.append(lines[i])
                i += 1

            # 收集并转换数据行
            table_rows = []
            current_row = []

            while i < len(lines):
                current_line = lines[i].strip()

                # 检测表格结束
                if '合计得分' in current_line or '合计配分' in current_line:
                    # 输出已收集的行
                    for row in table_rows:
                        if len(row) >= 3:
                            result.append('| ' + ' | '.join(row[:3]) + ' |')
                        elif len(row) == 2:
                            result.append('| ' + ' | '.join(row) + ' | |')
                        elif len(row) == 1:
                            result.append('| ' + row[0] + ' | | |')

                    # 添加合计行
                    result.append(f'| {current_line} |  |  |')
                    i += 1
                    break

                # 检测是否跳出表格（新标题或空行过多）
                if re.match(r'^#{1,2} ', current_line) or (current_line == '' and i + 1 < len(lines) and re.match(r'^#{1,2} ', lines[i + 1].strip())):
                    # 输出已收集的行
                    for row in table_rows:
                        if len(row) >= 3:
                            result.append('| ' + ' | '.join(row[:3]) + ' |')
                        elif len(row) == 2:
                            result.append('| ' + ' | '.join(row) + ' | |')
                        elif len(row) == 1:
                            result.append('| ' + row[0] + ' | | |')
                    break

                # 识别数据行模式：
                # M1, M2, etc. 或 实际值/得分 或 具体描述文本
                if re.match(r'^M\d+$', current_line):
                    # 新的评分项开始
                    if current_row:
                        table_rows.append(current_row)
                    current_row = [current_line]
                elif current_line in ['实际值', '得分', '规定或', '标称值', '结果或', '实测值']:
                    # 这些是表头的一部分，跳过（已在表头中）
                    pass
                elif current_line and not re.match(r'^\d+ / 116$', current_line):
                    # 其他文本，添加到当前行
                    if not current_row:
                        current_row = ['', '', current_line]
                    elif len(current_row) == 1:
                        current_row.append('')
                        current_row.append(current_line)
                    elif len(current_row) == 2:
                        current_row.append(current_line)
                    else:
                        # 已有3列，可能是多行描述，追加到第三列
                        current_row[2] += ' ' + current_line

                i += 1

            # 处理最后一行
            if current_row:
                table_rows.append(current_row)

            # 输出所有表格行
            for row in table_rows:
                if len(row) >= 3:
                    result.append('| ' + ' | '.join(row[:3]) + ' |')
                elif len(row) == 2:
                    result.append('| ' + ' | '.join(row) + ' | |')
                elif len(row) == 1:
                    result.append('| ' + row[0] + ' | | |')

            continue

        result.append(lines[i])
        i += 1

    return '\n'.join(result)


def main():
    print("=" * 70)
    print("🔧 修复表格数据行")
    print("=" * 70)

    processed = 0
    for md_file in BASE_DIR.rglob("*.md"):
        if md_file.name == "README.md":
            continue

        content = md_file.read_text(encoding='utf-8')
        fixed = fix_table_data(content)

        if fixed != content:
            md_file.write_text(fixed, encoding='utf-8')
            print(f"✅ 已修复: {md_file.relative_to(BASE_DIR)}")
            processed += 1

    print(f"\n✨ 共修复 {processed} 个文件")


if __name__ == "__main__":
    main()
