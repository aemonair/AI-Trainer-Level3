#!/usr/bin/env python3
"""
生成评分标准结构化文件（Scoring Schema Generator）

核心功能：
1. 从代码题目汇总.md中提取评分标准
2. 从模板.ipynb中提取填空位置和分值对应关系
3. 生成 scoring/{chapter}.json 评分标准文件

用法:
  python3 scripts/generate_scoring_schema.py 1.1.1          # 生成单个章节
  python3 scripts/generate_scoring_schema.py --all           # 生成所有章节
  python3 scripts/generate_scoring_schema.py --chapter 1.1.1 --dry-run  # 预览不生成
"""
from pathlib import Path
import json
import re
import argparse
import logging
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SCORING_DIR = ROOT / 'scoring'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='生成评分标准结构化文件')
    parser.add_argument('chapter', type=str, nargs='?', help='章节号（如 1.1.1）')
    parser.add_argument('--all', action='store_true', help='生成所有章节的评分标准')
    parser.add_argument('--dry-run', action='store_true', help='预览不生成文件')
    return parser.parse_args()


def load_notebook(nb_path: Path) -> Optional[Dict]:
    """加载 notebook 文件"""
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取文件失败 {nb_path}: {e}")
        return None


def extract_blanks_with_scores(chapter: str) -> List[Dict[str, Any]]:
    """
    从模板文件中提取填空，并结合评分标准分配分值
    
    核心逻辑：
    1. 逐行扫描，找到含填空的行
    2. 向上查找最近的注释行（含"X分"标记）
    3. 同一行的多个填空共享该注释的分值
    4. 从答案文件中提取标准答案
    
    返回: [
        {
            'id': 'M1',
            'cell_index': 0,
            'blank_index': 0,
            'line_index': 4,
            'type': 'api_call',
            'description': '读取数据集',
            'score': 1,
            'answer': 'pd.read_csv("patient_data.csv")',
            'template_line': 'data = _____________',
        },
        ...
    ]
    """
    template_path = ROOT / f'{chapter}-materials' / f'{chapter}.ipynb'
    answer_path = ROOT / 'answers' / '1.1.1 - 4.2.5参考答案' / chapter / f'{chapter}.ipynb'
    
    if not template_path.exists():
        logger.error(f"模板文件不存在: {template_path}")
        return []
    
    template_nb = load_notebook(template_path)
    if not template_nb:
        return []
    
    answer_nb = None
    if answer_path.exists():
        answer_nb = load_notebook(answer_path)
    
    scoring_items = []
    blank_counter = 0
    blank_pattern = r'_{3,}'
    
    for i, cell in enumerate(template_nb.get('cells', [])):
        if cell.get('cell_type') != 'code':
            continue
        
        source = ''.join(cell.get('source', []))
        lines = source.split('\n')
        
        answer_lines = []
        if answer_nb and i < len(answer_nb.get('cells', [])):
            answer_cell = answer_nb['cells'][i]
            answer_source = ''.join(answer_cell.get('source', []))
            answer_lines = answer_source.split('\n')
        
        for line_idx, line in enumerate(lines):
            blanks_in_line = list(re.finditer(blank_pattern, line))
            if not blanks_in_line:
                continue
            
            comment_score, comment_desc = find_line_comment(lines, line_idx)
            
            blanks_count = len(blanks_in_line)
            score_per_blank = comment_score // blanks_count if blanks_count > 0 else 1
            if score_per_blank < 1:
                score_per_blank = 1
            
            for blank_idx, match in enumerate(blanks_in_line):
                blank_counter += 1
                
                answer = ''
                if answer_lines and line_idx < len(answer_lines):
                    answer = answer_lines[line_idx].strip()
                
                item = {
                    'id': f'M{blank_counter}',
                    'cell_index': i,
                    'blank_index': blank_idx,
                    'line_index': line_idx,
                    'type': classify_blank_type(line),
                    'description': comment_desc,
                    'score': score_per_blank,
                    'answer': answer,
                    'template_line': line.strip(),
                }
                
                scoring_items.append(item)
    
    return scoring_items


def find_line_comment(lines: List[str], target_idx: int) -> tuple:
    """
    从目标行向上查找最近的注释行（含"X分"标记）
    
    返回: (分值, 描述)
    """
    for idx in range(target_idx, max(0, target_idx - 5), -1):
        line = lines[idx].strip()
        if not line.startswith('#'):
            continue
        
        score_match = re.search(r'(\d+)分', line)
        if score_match:
            score = int(score_match.group(1))
            desc = line.lstrip('#').strip()
            desc = re.sub(r'\s*\d+分\s*$', '', desc).strip()
            return score, desc
    
    return 1, '未知'


def classify_blank_type(line: str) -> str:
    """分类填空类型"""
    if 'read_csv' in line or 'read_excel' in line:
        return 'data_loading'
    if 'groupby' in line:
        return 'groupby'
    if 'pd.cut' in line:
        return 'binning'
    if 'np.where' in line:
        return 'conditional'
    if 'fillna' in line:
        return 'missing_value'
    if 'dropna' in line:
        return 'missing_value'
    if 'value_counts' in line:
        return 'aggregation'
    if 'to_csv' in line:
        return 'data_saving'
    if 'train_test_split' in line:
        return 'data_split'
    if 'fit' in line or 'predict' in line:
        return 'model_training'
    if 'import' in line:
        return 'import'
    return 'api_call'


def generate_chapter_schema(chapter: str, dry_run: bool = False) -> Optional[Dict]:
    """生成单个章节的评分标准"""
    logger.info(f"\n{'='*60}")
    logger.info(f"生成 {chapter} 评分标准")
    logger.info(f"{'='*60}")
    
    scoring_items = extract_blanks_with_scores(chapter)
    
    if not scoring_items:
        logger.warning(f"未找到 {chapter} 的填空")
        return None
    
    total_score = sum(item['score'] for item in scoring_items)
    
    schema = {
        'chapter': chapter,
        'total_score': total_score,
        'items': scoring_items,
        'metadata': {
            'generated_at': __import__('datetime').datetime.now().isoformat(),
            'template_file': f'{chapter}-materials/{chapter}.ipynb',
            'answer_file': f'answers/1.1.1 - 4.2.5参考答案/{chapter}/{chapter}.ipynb',
        }
    }
    
    if dry_run:
        logger.info(f"\n[预览模式] {chapter} 评分标准:")
        logger.info(f"总分: {total_score}")
        logger.info(f"评分项数: {len(scoring_items)}")
        for item in scoring_items:
            logger.info(f"  {item['id']}: [{item['type']}] {item['description']} - {item['score']}分")
        return schema
    
    SCORING_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SCORING_DIR / f'{chapter}.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n✅ 已生成: {output_path}")
    logger.info(f"总分: {total_score}")
    logger.info(f"评分项数: {len(scoring_items)}")
    
    return schema


def get_all_chapters() -> List[str]:
    """获取所有章节号"""
    chapters = []
    for d in ROOT.iterdir():
        if d.is_dir() and d.name.endswith('-materials'):
            chapter = d.name.replace('-materials', '')
            if re.match(r'^\d+\.\d+\.\d+$', chapter):
                chapters.append(chapter)
    return sorted(chapters)


def main():
    args = parse_args()
    
    if args.all:
        chapters = get_all_chapters()
        logger.info(f"找到 {len(chapters)} 个章节: {', '.join(chapters)}")
        
        for chapter in chapters:
            generate_chapter_schema(chapter, dry_run=args.dry_run)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ 共生成 {len(chapters)} 个评分标准文件")
        logger.info(f"{'='*60}")
    
    elif args.chapter:
        generate_chapter_schema(args.chapter, dry_run=args.dry_run)
    
    else:
        logger.error("请指定章节或使用 --all 参数")
        logger.info("用法: python3 scripts/generate_scoring_schema.py 1.1.1")
        logger.info("      python3 scripts/generate_scoring_schema.py --all")


if __name__ == '__main__':
    main()