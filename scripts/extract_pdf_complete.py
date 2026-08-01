#!/usr/bin/env python3
"""
从 PDF 完整提取内容并拆分为独立的 Markdown 文件
保留 PDF 的所有原始内容，按章节自动拆分
"""

import os
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ 缺少 PyMuPDF 库，请运行: uv add pymupdf")
    sys.exit(1)

# ==================== 配置 ====================
PDF_PATH = Path("/Users/air/Downloads/GUIDE_AI_3/第4部分_人工智能训练师_3级_操作技能复习题.pdf")
OUTPUT_DIR = Path("/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_三级_操作技能试题")

# 章节名称映射
CHAPTER_NAMES = {
    "1.1": "数据处理流程设计",
    "1.2": "业务模块效果优化",
    "2.1": "特征工程",
    "2.2": "模型训练与评估",
    "3.1": "语音识别系统部署与调试",
    "3.2": "图像识别系统部署与调试",
    "4.1": "智能客服系统优化",
    "4.2": "智能推荐系统优化",
}


def extract_all_text(pdf_path):
    """从 PDF 提取所有文本内容"""
    print(f"📖 正在读取 PDF: {pdf_path}")

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        sys.exit(1)

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    print(f"📄 PDF 共 {total_pages} 页")

    pages_text = []
    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        pages_text.append({
            'page_num': page_num + 1,
            'text': text
        })

    doc.close()
    return pages_text


def is_score_table_page(text):
    """判断当前页是否为评分表页"""
    score_markers = [
        '试题评分表',
        '测量分评分表',
        '评分细则',
        '配分',
        '评分细则描述',
    ]
    return any(marker in text for marker in score_markers)


def is_question_page(text):
    """判断当前页是否为题目页"""
    if is_score_table_page(text):
        return False
    if '试题名称' not in text:
        return False
    return any(marker in text for marker in ['试题单', '场地设备要求', '工作任务', '考核时间'])


def find_chapters(pages_text):
    """按 PDF 中的“试题名称”字段切分成独立题目块"""
    print("\n🔍 正在分析章节结构...")

    chapters = []
    current_title = None
    current_start_page = None
    current_end_page = None

    for page_info in pages_text:
        page_num = page_info['page_num']
        text = page_info['text']

        if not is_question_page(text):
            continue

        match = re.search(r'试题名称[：:]\s*(.+)', text)
        if not match:
            continue

        title = match.group(1).strip()
        if current_title is not None and title != current_title:
            chapters.append({
                'title': current_title,
                'start_page': current_start_page,
                'end_page': current_end_page,
            })

        if current_title is None or title != current_title:
            current_title = title
            current_start_page = page_num
            current_end_page = page_num
        else:
            current_end_page = page_num

    if current_title is not None:
        chapters.append({
            'title': current_title,
            'start_page': current_start_page,
            'end_page': current_end_page,
        })

    group_prefixes = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2"]
    group_size = 5

    for idx, chapter in enumerate(chapters):
        group_idx = idx // group_size
        if group_idx >= len(group_prefixes):
            group_idx = len(group_prefixes) - 1
        chapter_prefix = group_prefixes[group_idx]
        chapter_num = f"{chapter_prefix}.{(idx % group_size) + 1}"
        chapter['chapter_num'] = chapter_num
        chapter['chapter_prefix'] = chapter_prefix

    print(f"✅ 找到 {len(chapters)} 个章节")
    for ch in chapters:
        print(f"  📑 {ch['chapter_num']} {ch['title']} (第 {ch['start_page']} 页)")

    return chapters


def extract_chapter_content(pages_text, chapters):
    """提取每个章节的完整内容（包含评分表，修正边界）"""
    print("\n📝 正在提取章节内容...")

    extracted = []

    for idx, chapter in enumerate(chapters):
        start_page = chapter['start_page']

        if idx + 1 < len(chapters):
            end_page = chapters[idx + 1]['start_page'] - 1
        else:
            end_page = len(pages_text)

        content_parts = []
        for page_idx in range(start_page - 1, end_page):
            page_info = pages_text[page_idx]
            content_parts.append(f"\n--- 第 {page_info['page_num']} 页 ---\n")
            content_parts.append(page_info['text'])

        chapter_content = '\n'.join(content_parts)

        chapter_prefix = chapter['chapter_prefix']
        chapter_name = CHAPTER_NAMES.get(chapter_prefix, "未知章节")
        safe_title = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', chapter['title']).strip('_')
        filepath = f"{chapter_prefix}_{chapter_name}/{chapter['chapter_num']}_{safe_title}.md"

        extracted.append({
            'filepath': filepath,
            'content': chapter_content,
            'chapter_num': chapter['chapter_num'],
            'title': chapter['title']
        })

    return extracted


def save_chapters(extracted_chapters, output_dir):
    """保存章节到 Markdown 文件"""
    print(f"\n💾 正在保存到: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    for chapter_info in extracted_chapters:
        filepath = Path(output_dir) / chapter_info['filepath']
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chapter_info['content'])

        print(f"✅ 已生成: {chapter_info['filepath']}")

    print(f"\n🎉 全部 {len(extracted_chapters)} 个章节已保存到: {output_dir}")


def main():
    print("=" * 60)
    print("📚 PDF 完整提取与拆分工具")
    print("=" * 60)

    pages_text = extract_all_text(PDF_PATH)

    chapters = find_chapters(pages_text)

    if not chapters:
        print("❌ 未找到任何章节，请检查 PDF 内容")
        sys.exit(1)

    extracted = extract_chapter_content(pages_text, chapters)

    save_chapters(extracted, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("✨ 完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
