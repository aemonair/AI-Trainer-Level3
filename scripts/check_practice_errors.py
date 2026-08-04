#!/usr/bin/env python3
"""
自动检查所有 practice 文件中的错误，并生成 review 文件

用法:
  python3 scripts/check_practice_errors.py
  python3 scripts/check_practice_errors.py --dry-run  # 只显示不生成
  python3 scripts/check_practice_errors.py --chapter 1.1.2  # 只检查特定章节
"""
from pathlib import Path
import json
import re
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='检查 practice 文件中的错误')
    parser.add_argument('--dry-run', action='store_true', help='只显示错误，不生成文件')
    parser.add_argument('--chapter', type=str, help='只检查特定章节（如 1.1.2）')
    return parser.parse_args()


def find_practice_files(chapter: Optional[str] = None) -> List[Path]:
    """查找所有 practice 文件"""
    pattern = '*_practice_*.ipynb'
    files = []
    
    for md in ROOT.rglob(pattern):
        if md.is_file():
            # 跳过已有的 review 文件
            if '_review.md' in md.name:
                continue
            
            # 如果指定了章节，只检查该章节
            if chapter:
                if not md.name.startswith(chapter):
                    continue
            
            files.append(md)
    
    return sorted(files)


def check_notebook_errors(nb_path: Path) -> Tuple[List[Dict], bool]:
    """
    检查 notebook 中的错误
    
    返回: (错误列表, 是否有错误)
    """
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except Exception as e:
        logger.error(f"读取文件失败 {nb_path}: {e}")
        return [], False
    
    errors = []
    has_errors = False
    
    for i, cell in enumerate(nb.get('cells', [])):
        if cell.get('cell_type') != 'code':
            continue
        
        source = ''.join(cell.get('source', []))
        outputs = cell.get('outputs', [])
        
        # 检查输出中的错误
        for output in outputs:
            if output.get('output_type') == 'error':
                has_errors = True
                errors.append({
                    'cell_index': i,
                    'error_type': '执行错误',
                    'error_name': output.get('ename', 'Unknown'),
                    'error_msg': output.get('evalue', ''),
                    'code': source[:200]
                })
        
        # 检查代码中的明显语法错误（未运行的单元格）
        if not outputs:
            syntax_errors = check_syntax_errors(source, i)
            if syntax_errors:
                has_errors = True
                errors.extend(syntax_errors)
    
    return errors, has_errors


def check_syntax_errors(code: str, cell_index: int) -> List[Dict]:
    """检查代码中的明显语法错误"""
    errors = []
    
    # 常见错误模式
    patterns = [
        # 缺少逗号：{'count''mean'} 应该是 {'count', 'mean'}
        (r"['\"][a-zA-Z_]+['\"]\s*['\"][a-zA-Z_]+['\"]", 
         '缺少逗号', '字典或列表中缺少逗号分隔'),
        
        # 错误的函数调用：data(columns=[...]) 应该是 data.drop(columns=[...])
        (r"\bdata\s*\(\s*columns\s*=", 
         'DataFrame调用错误', 'DataFrame不是函数，不能用()直接调用'),
        
        # fillna 参数错误：fillna('bfill') 应该是 fillna(method='bfill')
        (r"fillna\s*\(\s*['\"](?:bfill|ffill)['\"]", 
         'fillna参数错误', 'fillna的第一个参数是value，不是method'),
        
        # np.where 参数缺少逗号
        (r"np\.where\s*\([^)]+\n\s+[A-Z]", 
         'np.where参数错误', 'np.where的参数之间缺少逗号'),
        
        # print 参数缺少逗号
        (r"print\s*\([^)]+['\"][^,)]+['\"]\s+[a-zA-Z_]", 
         'print参数错误', 'print的参数之间缺少逗号'),
        
        # to_csv 参数缺少逗号
        (r"to_csv\s*\([^)]+index\s*=", 
         'to_csv参数错误', 'to_csv的参数之间缺少逗号'),
    ]
    
    for pattern, error_type, description in patterns:
        matches = re.finditer(pattern, code, re.MULTILINE)
        for match in matches:
            errors.append({
                'cell_index': cell_index,
                'error_type': error_type,
                'error_msg': description,
                'code': match.group(0)[:100]
            })
    
    return errors


def load_guide(chapter: str) -> Optional[str]:
    """加载对应的 guide 文件"""
    guide_path = ROOT / f'{chapter}-materials' / f'{chapter}_guide.md'
    if guide_path.exists():
        return guide_path.read_text(encoding='utf-8')
    return None


def generate_review_file(nb_path: Path, errors: List[Dict], chapter: str, dry_run: bool = False):
    """生成 review 文件"""
    # 从文件名提取时间戳
    match = re.search(r'practice_(\d{8,14})', nb_path.name)
    if match:
        timestamp = match.group(1)
    else:
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
    
    # 构建 review 文件路径
    review_name = nb_path.stem + '_review.md'
    review_path = nb_path.parent / review_name
    
    # 如果 review 文件已存在，跳过
    if review_path.exists():
        logger.info(f"  ⏭️  review 文件已存在: {review_path.name}")
        return
    
    # 计算评分
    total_score = 0
    max_score = 0
    
    # 从代码中提取分数（如果有）
    code = nb_path.read_text(encoding='utf-8')
    score_matches = re.findall(r'(\d+)分', code)
    if score_matches:
        max_score = sum(int(s) for s in score_matches)
        # 假设有错误的题目不得分
        error_cells = set(e['cell_index'] for e in errors)
        # 简化计算
        total_score = max(0, max_score - len(errors) * 5)
    
    # 生成 review 内容
    content = f"""# {chapter} 练习 Review - {timestamp}

## 练习文件
[{nb_path.name}](file://{nb_path.resolve()})

---

## ❌ 错误记录
"""
    
    for i, err in enumerate(errors, 1):
        content += f"""
### 错误{i}：{err['error_type']}
- **错误代码**：`{err['code'][:100]}`
- **错误信息**：{err['error_msg']}
- **单元格**：第 {err['cell_index'] + 1} 个代码单元格
"""
    
    content += f"""
---

## 📊 评分
| 任务 | 满分 | 得分 | 说明 |
|------|------|------|------|
| 总计 | {max_score} | {total_score} | {total_score/max_score*100 if max_score > 0 else 0:.1f}% |
"""
    
    if not dry_run:
        review_path.write_text(content, encoding='utf-8')
        logger.info(f"  ✅ 生成 review 文件: {review_path.name}")
    else:
        logger.info(f"  📝 [DRY RUN] 将生成: {review_path.name}")


def main():
    args = parse_args()
    
    logger.info("🔍 开始检查 practice 文件...")
    
    files = find_practice_files(args.chapter)
    logger.info(f"找到 {len(files)} 个 practice 文件")
    
    checked = 0
    with_errors = 0
    generated = 0
    
    for nb_path in files:
        chapter = nb_path.name.split('_')[0]
        
        errors, has_errors = check_notebook_errors(nb_path)
        checked += 1
        
        if has_errors:
            with_errors += 1
            logger.info(f"\n❌ {nb_path.name}: {len(errors)} 个错误")
            for err in errors[:3]:  # 只显示前3个错误
                logger.info(f"   - {err['error_type']}: {err['error_msg'][:50]}")
            
            if not args.dry_run:
                generate_review_file(nb_path, errors, chapter, dry_run=False)
                generated += 1
            else:
                logger.info(f"   [DRY RUN] 将生成 review 文件")
        else:
            logger.info(f"✅ {nb_path.name}: 无错误")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 检查完成:")
    logger.info(f"   - 检查文件数: {checked}")
    logger.info(f"   - 有错误的文件: {with_errors}")
    logger.info(f"   - 生成 review 文件: {generated}")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()