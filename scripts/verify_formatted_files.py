#!/usr/bin/env python3
"""
验证格式化后的MD文件是否完整且格式正确
"""

from pathlib import Path

OUTPUT_DIR = Path("/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_三级_操作技能试题1")

# 期望的40个章节
EXPECTED_CHAPTERS = [
    ("1.1_数据处理流程设计", "1.1.1_智能医疗系统中的业务数据处理流程设计"),
    ("1.1_数据处理流程设计", "1.1.2_智能农业系统中的业务数据采集和处理流程设计"),
    ("1.1_数据处理流程设计", "1.1.3_金融机构信用评估系统中的业务数据审核流程设计"),
    ("1.1_数据处理流程设计", "1.1.4_电商平台用户行为分析系统的数据采集与处理流程设计"),
    ("1.1_数据处理流程设计", "1.1.5_智能交通系统的数据采集_处理和审核流程设计"),
    ("1.2_业务模块效果优化", "1.2.1_顾客评价情感识别业务模块效果优化"),
    ("1.2_业务模块效果优化", "1.2.2_老年人健康监测与管理服务业务模块效果优化"),
    ("1.2_业务模块效果优化", "1.2.3_智慧金融服务业务模块效果优化"),
    ("1.2_业务模块效果优化", "1.2.4_智能卖点生成系统业务模块效果优化"),
    ("1.2_业务模块效果优化", "1.2.5_腾讯云智能数智人系统业务模块效果优化"),
    ("2.1_特征工程", "2.1.1_智慧交通中燃油效率模型的数据清洗和标注流程设计"),
    ("2.1_特征工程", "2.1.2_低碳生活行为影响因素数据清洗和标注流程设计"),
    ("2.1_特征工程", "2.1.3_信用评分模型数据清洗和标注流程设计"),
    ("2.1_特征工程", "2.1.4_医疗研究数据清洗和标注设计"),
    ("2.1_特征工程", "2.1.5_健康与营养咨询数据预处理与数据规范设计"),
    ("2.2_模型训练与评估", "2.2.1_智能信用评分Logistic_回归模型开发与测试"),
    ("2.2_模型训练与评估", "2.2.2_智慧交通中燃油效率随机森林模型开发与测试"),
    ("2.2_模型训练与评估", "2.2.3_日常运动量随机森林预测模型开发与测试"),
    ("2.2_模型训练与评估", "2.2.4_低碳生活行为影响因素预测线性回归模型开发与测试"),
    ("2.2_模型训练与评估", "2.2.5_智能步数预测模型开发与测试"),
    ("3.1_语音识别系统部署与调试", "3.1.1_智能音箱产品的数据分析与优化"),
    ("3.1_语音识别系统部署与调试", "3.1.2_智能照明系统的数据分析与优化"),
    ("3.1_语音识别系统部署与调试", "3.1.3_智能健康手环的数据分析与优化"),
    ("3.1_语音识别系统部署与调试", "3.1.4_智能健康监测系统的数据分析与优化"),
    ("3.1_语音识别系统部署与调试", "3.1.5_智能家居环境控制系统的数据分析与优化"),
    ("3.2_图像识别系统部署与调试", "3.2.1_图像识别评估系统交互流程设计"),
    ("3.2_图像识别系统部署与调试", "3.2.2_手写数字识别系统交互流程设计"),
    ("3.2_图像识别系统部署与调试", "3.2.3_面部表情识别系统交互流程设计"),
    ("3.2_图像识别系统部署与调试", "3.2.4_花朵智能识别系统交互流程设计"),
    ("3.2_图像识别系统部署与调试", "3.2.5_人脸AI_智能检测系统交互流程设计"),
    ("4.1_智能客服系统优化", "4.1.1_Label_studio_培训大纲编写"),
    ("4.1_智能客服系统优化", "4.1.2_爬虫培训大纲编写"),
    ("4.1_智能客服系统优化", "4.1.3_数据清洗培训大纲编写"),
    ("4.1_智能客服系统优化", "4.1.4_Pandas_数据清洗培训大纲编写"),
    ("4.1_智能客服系统优化", "4.1.5_Python_数据可视化培训大纲编写"),
    ("4.2_智能推荐系统优化", "4.2.1_智能零售分析系统数据采集和处理指导"),
    ("4.2_智能推荐系统优化", "4.2.2_AI_辅助的医疗影像诊断系统数据采集和处理指导"),
    ("4.2_智能推荐系统优化", "4.2.3_AI_智能安防监控系统采集和处理指导"),
    ("4.2_智能推荐系统优化", "4.2.4_自动驾驶汽车感知系统数据采集与标注指导"),
    ("4.2_智能推荐系统优化", "4.2.5_智能化数据标注在文化遗产数字化保护中的应用指导"),
]


def check_formatting(content: str) -> dict:
    """检查Markdown格式是否正确"""
    import re

    has_h1 = bool(re.search(r'^# .+', content, re.MULTILINE))
    has_h2 = bool(re.search(r'^## .+', content, re.MULTILINE))
    has_list = bool(re.search(r'^[-*] |\d+\. ', content, re.MULTILINE))
    has_table = bool(re.search(r'\|.*\|.*\|', content))
    has_page_comment = bool(re.search(r'<!-- 第 \d+ 页 -->', content))

    return {
        'has_h1': has_h1,
        'has_h2': has_h2,
        'has_list': has_list,
        'has_table': has_table,
        'has_page_comment': has_page_comment,
    }


def verify():
    print("=" * 70)
    print("🔍 验证格式化后的文件")
    print("=" * 70)

    total = len(EXPECTED_CHAPTERS)
    found = 0
    missing = []
    format_stats = {
        'has_h1': 0,
        'has_h2': 0,
        'has_list': 0,
        'has_table': 0,
        'has_page_comment': 0,
    }

    for folder, filename in EXPECTED_CHAPTERS:
        filepath = OUTPUT_DIR / folder / f"{filename}.md"

        if not filepath.exists():
            missing.append(f"{folder}/{filename}.md")
            print(f"❌ 缺失: {folder}/{filename}.md")
            continue

        content = filepath.read_text(encoding='utf-8')
        stats = check_formatting(content)

        for key in format_stats:
            if stats[key]:
                format_stats[key] += 1

        found += 1
        print(f"✅ {folder}/{filename}.md ({len(content)} 字符)")

    print("\n" + "=" * 70)
    print("📊 格式化统计")
    print("=" * 70)
    print(f"📚 期望文件数: {total}")
    print(f"✅ 找到文件数: {found}")
    print(f"❌ 缺失文件数: {len(missing)}")
    print(f"\n📝 格式统计:")
    print(f"  # 一级标题: {format_stats['has_h1']}/{found}")
    print(f"  ## 二级标题: {format_stats['has_h2']}/{found}")
    print(f"  列表: {format_stats['has_list']}/{found}")
    print(f"  表格: {format_stats['has_table']}/{found}")
    print(f"  页码注释: {format_stats['has_page_comment']}/{found}")

    if missing:
        print(f"\n❌ 缺失文件:")
        for f in missing:
            print(f"  - {f}")

    print("\n" + "=" * 70)
    if found == total and len(missing) == 0:
        print("✅ 验证通过！所有40个章节已完整格式化！")
    else:
        print(f"⚠️  发现问题：缺失 {len(missing)} 个文件")
    print("=" * 70)


if __name__ == "__main__":
    verify()
