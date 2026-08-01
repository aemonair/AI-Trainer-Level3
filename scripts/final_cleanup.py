#!/usr/bin/env python3
"""
最终清理脚本：
1. 清理分页标记（可选）
2. 修复表格格式
3. 生成README总目录
"""

import re
from pathlib import Path

BASE_DIR = Path("/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_三级_操作技能试题1")

# 章节映射
CHAPTER_MAP = {
    "1.1": "数据处理流程设计",
    "1.2": "业务模块效果优化",
    "2.1": "特征工程",
    "2.2": "模型训练与评估",
    "3.1": "语音识别系统部署与调试",
    "3.2": "图像识别系统部署与调试",
    "4.1": "智能客服系统优化",
    "4.2": "智能推荐系统优化",
}

ALL_CHAPTERS = [
    ("1.1.1", "智能医疗系统中的业务数据处理流程设计"),
    ("1.1.2", "智能农业系统中的业务数据采集和处理流程设计"),
    ("1.1.3", "金融机构信用评估系统中的业务数据审核流程设计"),
    ("1.1.4", "电商平台用户行为分析系统的数据采集与处理流程设计"),
    ("1.1.5", "智能交通系统的数据采集_处理和审核流程设计"),
    ("1.2.1", "顾客评价情感识别业务模块效果优化"),
    ("1.2.2", "老年人健康监测与管理服务业务模块效果优化"),
    ("1.2.3", "智慧金融服务业务模块效果优化"),
    ("1.2.4", "智能卖点生成系统业务模块效果优化"),
    ("1.2.5", "腾讯云智能数智人系统业务模块效果优化"),
    ("2.1.1", "智慧交通中燃油效率模型的数据清洗和标注流程设计"),
    ("2.1.2", "低碳生活行为影响因素数据清洗和标注流程设计"),
    ("2.1.3", "信用评分模型数据清洗和标注流程设计"),
    ("2.1.4", "医疗研究数据清洗和标注设计"),
    ("2.1.5", "健康与营养咨询数据预处理与数据规范设计"),
    ("2.2.1", "智能信用评分Logistic_回归模型开发与测试"),
    ("2.2.2", "智慧交通中燃油效率随机森林模型开发与测试"),
    ("2.2.3", "日常运动量随机森林预测模型开发与测试"),
    ("2.2.4", "低碳生活行为影响因素预测线性回归模型开发与测试"),
    ("2.2.5", "智能步数预测模型开发与测试"),
    ("3.1.1", "智能音箱产品的数据分析与优化"),
    ("3.1.2", "智能照明系统的数据分析与优化"),
    ("3.1.3", "智能健康手环的数据分析与优化"),
    ("3.1.4", "智能健康监测系统的数据分析与优化"),
    ("3.1.5", "智能家居环境控制系统的数据分析与优化"),
    ("3.2.1", "图像识别评估系统交互流程设计"),
    ("3.2.2", "手写数字识别系统交互流程设计"),
    ("3.2.3", "面部表情识别系统交互流程设计"),
    ("3.2.4", "花朵智能识别系统交互流程设计"),
    ("3.2.5", "人脸AI_智能检测系统交互流程设计"),
    ("4.1.1", "Label_studio_培训大纲编写"),
    ("4.1.2", "爬虫培训大纲编写"),
    ("4.1.3", "数据清洗培训大纲编写"),
    ("4.1.4", "Pandas_数据清洗培训大纲编写"),
    ("4.1.5", "Python_数据可视化培训大纲编写"),
    ("4.2.1", "智能零售分析系统数据采集和处理指导"),
    ("4.2.2", "AI_辅助的医疗影像诊断系统数据采集和处理指导"),
    ("4.2.3", "AI_智能安防监控系统采集和处理指导"),
    ("4.2.4", "自动驾驶汽车感知系统数据采集与标注指导"),
    ("4.2.5", "智能化数据标注在文化遗产数字化保护中的应用指导"),
]


def fix_tables(content: str) -> str:
    """修复表格格式：识别评分表并转换为Markdown表格"""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 检测表格开始：包含"细则编号"或其拆分形式
        if re.match(r'^细则编$', line) or '细则编号' in line:
            # 收集表格数据
            table_lines = []
            j = i

            # 合并被拆分的表头
            if line == '细则编' and j + 1 < len(lines) and lines[j + 1].strip() == '号':
                table_lines.append('细则编号')
                j += 2
                # 继续收集其他表头
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line in ['配分', '评分细则描述', '规定或', '标称值', '结果或', '实测值', '得分']:
                        table_lines.append(next_line)
                        j += 1
                    elif re.match(r'^\d+/116$', next_line) or next_line == '人工智能训练师（三级）操作技能复习题':
                        j += 1
                        continue
                    else:
                        break
            else:
                # 直接提取包含|的行
                while j < len(lines):
                    next_line = lines[j].strip()
                    if '|' in next_line or next_line in ['配分', '评分细则描述', '细则编号']:
                        table_lines.append(next_line.replace('|', '').strip())
                        j += 1
                    else:
                        break

            # 如果收集到足够的表头，生成Markdown表格
            if len(table_lines) >= 3:
                # 构建表头
                header = '| ' + ' | '.join(table_lines[:3]) + ' |'
                separator = '| --- | --- | --- |'
                result.append(header)
                result.append(separator)

                # 跳过已处理的行
                i = j
                continue

        # 检测表格数据行（包含"合计配分"或"合计得分"的行结束表格）
        if '合计配分' in line or '合计得分' in line:
            result.append(f'| {line} |  |  |')
            i += 1
            continue

        result.append(lines[i])
        i += 1

    return '\n'.join(result)


def clean_page_markers(content: str, remove: bool = True) -> str:
    """清理分页标记"""
    if remove:
        # 将分页标记转为注释
        content = re.sub(r'<!-- 第 (\d+) 页 -->', r'<!-- 第 \1 页 -->', content)
        # 删除页码行（如 "3 / 116"）
        content = re.sub(r'^\d+ / 116\s*$', '', content, flags=re.MULTILINE)
        # 删除"人工智能训练师（三级）操作技能复习题"
        content = re.sub(r'^人工智能训练师（三级）操作技能复习题\s*$', '', content, flags=re.MULTILINE)
    return content


def generate_readme() -> str:
    """生成README总目录"""
    readme = """# 人工智能训练师（三级）操作技能试题

> 共 40 个章节，涵盖数据处理、特征工程、模型训练、系统部署等核心技能

## 📚 目录

"""

    current_group = None

    for chapter_num, title in ALL_CHAPTERS:
        group = chapter_num.rsplit('.', 1)[0]
        group_name = CHAPTER_MAP.get(group, "未知")

        if group != current_group:
            current_group = group
            readme += f"\n### {group} {group_name}\n\n"

        # 构建文件路径
        safe_title = title.replace(' ', '_')
        file_path = f"{group_name.replace(' ', '_')}/{chapter_num}_{safe_title}.md"

        readme += f"- [{chapter_num} {title.replace('_', ' ')}]({file_path})\n"

    readme += """
---

💡 **使用提示：**
- 点击章节链接即可跳转到对应试题
- 每个文件包含完整的题目要求、数据说明和评分标准
- 建议按章节顺序复习，逐步掌握各项技能
"""

    return readme


def main():
    print("=" * 70)
    print("🔧 最终清理脚本")
    print("=" * 70)

    # 1. 处理所有MD文件
    print("\n📝 正在处理MD文件...")
    processed = 0

    for md_file in BASE_DIR.rglob("*.md"):
        if md_file.name == "README.md":
            continue

        content = md_file.read_text(encoding='utf-8')

        # 清理分页标记
        content = clean_page_markers(content, remove=True)

        # 修复表格
        content = fix_tables(content)

        # 写回文件
        md_file.write_text(content, encoding='utf-8')
        processed += 1

    print(f"✅ 已处理 {processed} 个文件")

    # 2. 生成README
    print("\n📖 正在生成README...")
    readme_content = generate_readme()
    readme_path = BASE_DIR / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"✅ 已生成: {readme_path}")

    print("\n" + "=" * 70)
    print("✨ 清理完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
