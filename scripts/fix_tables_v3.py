cd /Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai

python3 - <<'PY'
import re
from pathlib import Path

BASE_DIR = Path("/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_三级_操作技能试题1")

def optimize_table(content: str) -> str:
    # 1. 修复常见分裂文本
    replacements = {
        '根据数 据': '根据数据',
        '规定或 标称值': '规定或标称值',
        '结果或 实际值': '结果或实际值',
        '结果或 实测值': '结果或实测值',
        '合计配 分': '合计配分',
        '合计得 分': '合计得分',
    }
    for old, new in replacements.items():
        content = content.replace(old, new)

    # 2. 修复表头
    content = re.sub(r'\| 细则编号 \| 配分 \| 评分细则描述 \|', '| 细则编号 | 配分 | 评分细则描述 |', content)
    content = re.sub(r'\| --- \| --- \| --- \|', '| --- | --- | --- |', content)

    # 3. 修复数据行列错位
    def fix_row(match):
        code = match.group(1)
        rest = match.group(2).strip()
        if rest:
            parts = rest.split(' ', 1)
            if len(parts) == 2 and parts[0].isdigit():
                return f'| {code} | {parts[0]} | {parts[1]} |'
        return f'| {code} |  | {rest} |'

    content = re.sub(r'\| (M\d+) \|  \| (.*?) \|', fix_row, content)

    # 4. 去重：保留M14等独有行
    matches = list(re.finditer(r'\| M1 \|', content))
    if len(matches) >= 2:
        start_first = matches[0].start()
        start_dup = matches[1].start()
        end_dup_match = re.search(r'合计配分|合计得分', content[start_dup:])
        if end_dup_match:
            end_dup = start_dup + end_dup_match.end()
            end_line = content.find('\n', end_dup)
            if end_line != -1:
                end_dup = end_line + 1

            first_block = content[start_first:start_dup]
            first_m_numbers = set(re.findall(r'\| (M\d+) \|', first_block))

            dup_lines = content[start_dup:end_dup].splitlines()
            filtered_lines = []
            for line in dup_lines:
                m_match = re.match(r'\| (M\d+) \|', line)
                if m_match and m_match.group(1) in first_m_numbers:
                    continue
                filtered_lines.append(line)

            filtered_block = '\n'.join(filtered_lines)
            content = content[:start_dup] + filtered_block + content[end_dup:]

    # 5. 修复合计行
    content = re.sub(r'\| \s*合计得分\s*\|.*?\|', '| 合计得分 |  |  |', content)
    content = re.sub(r'\| \s*合计配分\s*\|.*?\|', '| 合计配分 |  |  |', content)

    return content

print("📝 正在优化表格...")
count = 0
for md_file in BASE_DIR.rglob("*.md"):
    if md_file.name == "README.md":
        continue
    raw = md_file.read_text(encoding='utf-8')
    cleaned = optimize_table(raw)
    if cleaned != raw:
        md_file.write_text(cleaned, encoding='utf-8')
        print(f"✅ 已优化: {md_file.name}")
        count += 1

print(f"\n🎉 共优化 {count} 个文件！")
PY

exit 0
"""
print("📝 正在优化表格...")
count = 0
for md_file in BASE_DIR.rglob("*.md"):
    if md_file.name == "README.md":
        continue
    raw = md_file.read_text(encoding='utf-8')
    cleaned = optimize_table(raw)
    if cleaned != raw:
        md_file.write_text(cleaned, encoding='utf-8')
        print(f"✅ 已优化: {md_file.name}")
        count += 1

print(f"\n🎉 共优化 {count} 个文件！")
PY
📝 正在优化表格...
✅ 已优化: 2.2.4_低碳生活行为影响因素预测线性回归模型开发与测试.md
✅ 已优化: 2.2.1_智能信用评分Logistic_回归模型开发与测试.md
✅ 已优化: 2.2.3_日常运动量随机森林预测模型开发与测试.md
✅ 已优化: 2.2.5_智能步数预测模型开发与测试.md
✅ 已优化: 2.2.2_智慧交通中燃油效率随机森林模型开发与测试.md
✅ 已优化: 3.2.3_面部表情识别系统交互流程设计.md
✅ 已优化: 3.2.4_花朵智能识别系统交互流程设计.md
✅ 已优化: 3.2.5_人脸AI_智能检测系统交互流程设计.md
✅ 已优化: 3.2.1_图像识别评估系统交互流程设计.md
✅ 已优化: 3.2.2_手写数字识别系统交互流程设计.md
✅ 已优化: 2.1.4_医疗研究数据清洗和标注设计.md
✅ 已优化: 2.1.2_低碳生活行为影响因素数据清洗和标注流程设计.md
✅ 已优化: 2.1.5_健康与营养咨询数据预处理与数据规范设计.md
✅ 已优化: 2.1.1_智慧交通中燃油效率模型的数据清洗和标注流程设计.md
✅ 已优化: 2.1.3_信用评分模型数据清洗和标注流程设计.md
✅ 已优化: 3.1.4_智能健康监测系统的数据分析与优化.md
✅ 已优化: 3.1.5_智能家居环境控制系统的数据分析与优化.md
✅ 已优化: 3.1.2_智能照明系统的数据分析与优化.md
✅ 已优化: 3.1.3_智能健康手环的数据分析与优化.md
✅ 已优化: 3.1.1_智能音箱产品的数据分析与优化.md
✅ 已优化: 4.2.5_智能化数据标注在文化遗产数字化保护中的应用指导.md
✅ 已优化: 4.2.1_智能零售分析系统数据采集和处理指导.md
✅ 已优化: 4.2.3_AI_智能安防监控系统采集和处理指导.md
✅ 已优化: 4.2.2_AI_辅助的医疗影像诊断系统数据采集和处理指导.md
✅ 已优化: 4.2.4_自动驾驶汽车感知系统数据采集与标注指导.md
✅ 已优化: 1.1.5_智能交通系统的数据采集_处理和审核流程设计.md
✅ 已优化: 1.1.4_电商平台用户行为分析系统的数据采集与处理流程设计.md
✅ 已优化: 1.1.2_智能农业系统中的业务数据采集和处理流程设计.md
✅ 已优化: 1.1.1_智能医疗系统中的业务数据处理流程设计.md
✅ 已优化: 1.1.3_金融机构信用评估系统中的业务数据审核流程设计.md
✅ 已优化: 1.2.2_老年人健康监测与管理服务业务模块效果优化.md
✅ 已优化: 1.2.4_智能卖点生成系统业务模块效果优化.md
✅ 已优化: 1.2.5_腾讯云智能数智人系统业务模块效果优化.md
✅ 已优化: 1.2.1_顾客评价情感识别业务模块效果优化.md
✅ 已优化: 1.2.3_智慧金融服务业务模块效果优化.md
✅ 已优化: 4.1.4_Pandas_数据清洗培训大纲编写.md
✅ 已优化: 4.1.2_爬虫培训大纲编写.md
✅ 已优化: 4.1.3_数据清洗培训大纲编写.md
✅ 已优化: 4.1.5_Python_数据可视化培训大纲编写.md
✅ 已优化: 4.1.1_Label_studio_培训大纲编写.md

🎉 共优化 40 个文件！
"""
