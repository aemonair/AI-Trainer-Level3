#!/usr/bin/env python3
"""
验证 PDF 提取结果是否完整
检查：
1. 生成的 MD 文件数量是否与 PDF 章节数匹配
2. 每个章节是否都有对应的 MD 文件
3. MD 文件内容是否完整（包含关键信息）
"""

import os
import re
from pathlib import Path

OUTPUT_DIR = Path("/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_三级_操作技能试题")

# 期望的 40 个章节列表
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


def verify_files():
    """验证所有文件是否存在且内容完整"""
    print("=" * 70)
    print("🔍 开始验证 PDF 提取结果")
    print("=" * 70)

    total_chapters = len(EXPECTED_CHAPTERS)
    found_count = 0
    missing_count = 0
    empty_count = 0
    missing_files = []
    empty_files = []

    # 检查每个期望的文件
    for folder_name, file_name in EXPECTED_CHAPTERS:
        file_path = OUTPUT_DIR / folder_name / f"{file_name}.md"

        if not file_path.exists():
            missing_count += 1
            missing_files.append(f"{folder_name}/{file_name}.md")
            print(f"❌ 缺失: {folder_name}/{file_name}.md")
            continue

        # 检查文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查文件是否为空
            if len(content.strip()) == 0:
                empty_count += 1
                empty_files.append(str(file_path))
                print(f"⚠️  空文件: {folder_name}/{file_name}.md")
                continue

            # 检查是否包含关键内容
            has_content = len(content) > 100  # 至少100字符
            if not has_content:
                print(f"⚠️  内容过少: {folder_name}/{file_name}.md ({len(content)} 字符)")

            found_count += 1
            print(f"✅ 正常: {folder_name}/{file_name}.md ({len(content)} 字符)")

        except Exception as e:
            print(f"❌ 读取失败: {folder_name}/{file_name}.md - {e}")

    # 统计结果
    print("\n" + "=" * 70)
    print("📊 验证结果汇总")
    print("=" * 70)
    print(f"📚 期望章节数: {total_chapters}")
    print(f"✅ 正常文件: {found_count}")
    print(f"❌ 缺失文件: {missing_count}")
    print(f"⚠️  空文件: {empty_count}")

    if missing_files:
        print(f"\n❌ 缺失的文件列表:")
        for f in missing_files:
            print(f"  - {f}")

    if empty_files:
        print(f"\n⚠️  空文件列表:")
        for f in empty_files:
            print(f"  - {f}")

    # 检查是否有额外文件
    print(f"\n📁 检查输出目录中的实际文件...")
    actual_files = []
    for folder_name, _ in EXPECTED_CHAPTERS:
        folder_path = OUTPUT_DIR / folder_name
        if folder_path.exists():
            for md_file in folder_path.glob("*.md"):
                actual_files.append(md_file.name)

    # 去重
    unique_actual = set(actual_files)
    print(f"📄 实际找到 {len(unique_actual)} 个 MD 文件")

    # 最终结论
    print("\n" + "=" * 70)
    if missing_count == 0 and empty_count == 0 and found_count == total_chapters:
        print("✅ 验证通过！所有 40 个章节都已完整提取，没有遗漏。")
    else:
        print("⚠️  验证发现问题，请检查上述列出的缺失或空文件。")
    print("=" * 70)

    return missing_count == 0 and empty_count == 0 and found_count == total_chapters


if __name__ == "__main__":
    success = verify_files()
    exit(0 if success else 1)
