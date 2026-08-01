#!/bin/bash
# 批量重命名：-素材 → -materials，_代码详解.md → _guide.md

cd /Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai

echo "=== 重命名目录：-素材 → -materials ==="
for dir in *-素材; do
    if [ -d "$dir" ]; then
        new_name="${dir%-素材}-materials"
        mv "$dir" "$new_name"
        echo "  $dir → $new_name"
    fi
done

echo ""
echo "=== 重命名文件：_代码详解.md → _guide.md ==="
for file in */*_代码详解.md; do
    if [ -f "$file" ]; then
        new_file="${file%_代码详解.md}_guide.md"
        mv "$file" "$new_file"
        echo "  $file → $new_file"
    fi
done

echo ""
echo "✅ 重命名完成！"