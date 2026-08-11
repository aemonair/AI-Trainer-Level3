#!/usr/bin/env python3
"""
合并两个素材目录为统一的 template
- 备份不同的 .docx 文件为版本2
- 保留上网素材作为基础 template
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path("/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai")
PREV_DIR = BASE_DIR / "人工智能训练师_3级_sucai_prev"
ONLINE_DIR = BASE_DIR / "人工智能训练师上网/人工智能训练师三级上网素材"
TEMPLATE_DIR = BASE_DIR / "template"
BACKUP_DIR = BASE_DIR / "docx_version2_backup"

def main():
    print("=== 开始合并素材目录 ===\n")
    
    # 1. 创建备份目录
    BACKUP_DIR.mkdir(exist_ok=True)
    print(f"✓ 创建备份目录: {BACKUP_DIR}")
    
    # 2. 找出不同的 .docx 文件并备份
    print("\n--- 备份不同的 .docx 文件（版本2）---")
    docx_files_to_backup = [
        "2.1.1-素材/2.1.1.docx",
        "2.1.2-素材/2.1.2.docx",
        "2.1.3-素材/2.1.3.docx",
        "2.1.4-素材/2.1.4.docx",
        "2.1.5-素材/2.1.5.docx",
        "2.2.1-素材/2.2.1.docx",
        "2.2.2-素材/2.2.2.docx",
        "2.2.3-素材/2.2.3.docx",
        "2.2.4-素材/2.2.4.docx",
        "2.2.5-素材/2.2.5.docx",
        "4.2.1-素材/4.2.1.docx",
        "4.2.2-素材/4.2.2.docx",
        "4.2.3-素材/4.2.3.docx",
        "4.2.4-素材/4.2.4.docx",
        "4.2.5-素材/4.2.5.docx",
    ]
    
    for rel_path in docx_files_to_backup:
        prev_file = PREV_DIR / rel_path
        if prev_file.exists():
            # 创建对应的备份子目录
            chapter = rel_path.split("-")[0]  # 如 2.1.1
            backup_chapter_dir = BACKUP_DIR / chapter
            backup_chapter_dir.mkdir(exist_ok=True)
            
            # 复制文件，添加 _v2 后缀
            backup_file = backup_chapter_dir / prev_file.name.replace(".docx", "_v2.docx")
            shutil.copy2(prev_file, backup_file)
            print(f"  ✓ 备份: {rel_path} -> {backup_file.name}")
    
    # 3. 创建 template 目录（基于上网素材）
    print("\n--- 创建 template 目录 ---")
    if TEMPLATE_DIR.exists():
        print(f"  ⚠ template 目录已存在，将覆盖")
        shutil.rmtree(TEMPLATE_DIR)
    
    shutil.copytree(ONLINE_DIR, TEMPLATE_DIR)
    print(f"  ✓ 复制上网素材到 template: {len(list(TEMPLATE_DIR.rglob('*')))} 个文件")
    
    # 4. 统一目录命名（去掉 -素材 后缀，如果有的话）
    print("\n--- 检查目录命名 ---")
    for item in TEMPLATE_DIR.iterdir():
        if item.is_dir() and item.name.endswith("-素材"):
            new_name = item.name.replace("-素材", "")
            item.rename(TEMPLATE_DIR / new_name)
            print(f"  ✓ 重命名: {item.name} -> {new_name}")
    
    print("\n=== 合并完成 ===")
    print(f"\n结果：")
    print(f"  📁 template 目录: {TEMPLATE_DIR}")
    print(f"  📁 docx 版本2备份: {BACKUP_DIR}")
    print(f"\n建议：")
    print(f"  1. 检查 template 目录内容是否完整")
    print(f"  2. 确认 docx_version2_backup 中的文件是否需要保留")
    print(f"  3. 确认无误后可删除 人工智能训练师_3级_sucai_prev 目录")

if __name__ == "__main__":
    main()