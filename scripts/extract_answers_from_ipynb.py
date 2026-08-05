#!/usr/bin/env python3
"""
从练习文件和答案文件中提取填空题答案，生成复习题目列表

用法:
  python3 scripts/extract_answers_from_ipynb.py --chapter 1.1.1
  python3 scripts/extract_answers_from_ipynb.py --all
  python3 scripts/extract_answers_from_ipynb.py --all --output reports/all_chapters_review.md
"""
import json
import re
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='从ipynb提取填空题答案')
    parser.add_argument('--chapter', type=str, help='分析特定章节（如 1.1.1）')
    parser.add_argument('--all', action='store_true', help='分析所有章节')
    parser.add_argument('--output', type=str, help='输出Markdown文件路径')
    return parser.parse_args()


def load_ipynb(path: Path) -> List[Dict]:
    """加载ipynb文件，返回cells列表"""
    with open(path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    return nb.get('cells', [])


def extract_fill_blanks(source: str) -> List[str]:
    """从代码中提取下划线填空的数量"""
    return re.findall(r'_{3,}', source)


def find_chapter_pairs(chapter: Optional[str] = None) -> List[Tuple[str, Path, Path]]:
    """
    找到练习文件和答案文件的配对
    
    返回:
        [(chapter_num, practice_path, answer_path), ...]
    """
    pairs = []
    
    # 查找所有materials目录下的.ipynb文件（非practice文件）
    materials_dirs = sorted(ROOT.glob('*-materials'))
    
    for md in materials_dirs:
        # 提取章节号
        chapter_num = md.name.replace('-materials', '')
        
        if chapter and chapter_num != chapter:
            continue
        
        # 查找练习文件（原始.ipynb，非practice_*.ipynb）
        practice_files = []
        for f in md.glob('*.ipynb'):
            if 'practice' not in f.name and '_andy' not in f.name and 'checkpoint' not in f.name.lower():
                practice_files.append(f)
        
        if not practice_files:
            continue
        
        # 取第一个匹配的练习文件
        practice_path = practice_files[0]
        
        # 查找答案文件
        answer_paths = []
        for answers_dir in ROOT.glob('answers/*参考答案'):
            for f in answers_dir.rglob(f'{chapter_num}.ipynb'):
                if 'checkpoint' not in f.name.lower():
                    answer_paths.append(f)
        
        if not answer_paths:
            logger.warning(f"未找到 {chapter_num} 的答案文件")
            continue
        
        answer_path = answer_paths[0]
        pairs.append((chapter_num, practice_path, answer_path))
    
    return pairs


def extract_questions_from_pair(chapter_num: str, practice_path: Path, answer_path: Path) -> List[Dict]:
    """
    从练习-答案配对中提取题目（按单元格对比）
    
    返回:
        [{
            'question_num': int,
            'question_text': str,
            'practice_source': str,
            'answer_source': str,
            'blank_count': int,
        }, ...]
    """
    practice_cells = load_ipynb(practice_path)
    answer_cells = load_ipynb(answer_path)
    
    questions = []
    question_num = 0
    
    for p_cell, a_cell in zip(practice_cells, answer_cells):
        if p_cell.get('cell_type') != 'code':
            continue
        
        p_source = p_cell.get('source', '')
        a_source = a_cell.get('source', '')
        
        if isinstance(p_source, list):
            p_source = ''.join(p_source)
        if isinstance(a_source, list):
            a_source = ''.join(a_source)
        
        blanks = extract_fill_blanks(p_source)
        if not blanks:
            continue
        
        question_num += 1
        
        # 提取题目描述（注释中的说明）
        question_text = ''
        for line in p_source.split('\n'):
            line = line.strip()
            if line.startswith('#') and '分' in line:
                question_text = line.replace('#', '').strip()
                break
        
        questions.append({
            'question_num': question_num,
            'question_text': question_text,
            'practice_source': p_source,
            'answer_source': a_source,
            'blank_count': len(blanks),
        })
    
    return questions


def generate_markdown_report(all_questions: Dict[str, List[Dict]], output_path: Path):
    """生成Markdown格式的复习报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 📚 所有章节复习题目列表\n\n")
        f.write("> 包含所有章节的完整复习题目，无论对错都列出，帮助你全面复习\n\n")
        f.write("---\n\n")
        
        # 总体统计
        f.write("## 📊 所有章节概览\n\n")
        f.write("| 章节 | 题目数 | 核心考点 |\n")
        f.write("|------|--------|----------|\n")
        
        for chapter_num, questions in all_questions.items():
            # 提取核心考点
            key_funcs = set()
            for q in questions:
                src = q['answer_source']
                for func in ['read_csv', 'groupby', 'agg', 'isin', 'between', 'value_counts', 
                           'dropna', 'fillna', 'astype', 'pd.cut', 'np.where', 'to_csv',
                           'StandardScaler', 'train_test_split', 'fit_transform', 'to_numeric',
                           'head', 'isnull', 'sum', 'drop', 'apply', 'unstack', 'ort.InferenceSession',
                           'Image.open', 'softmax', 'argsort', 'predict', 'fit', 'score',
                           'LogisticRegression', 'RandomForestClassifier', 'GradientBoostingClassifier',
                           'XGBClassifier', 'accuracy_score', 'classification_report', 'confusion_matrix',
                           'GridSearchCV', 'cross_val_score', 'MinMaxScaler', 'LabelEncoder']:
                    if func in src:
                        key_funcs.add(func)
            
            core_points = ', '.join(sorted(key_funcs)[:8])
            f.write(f"| {chapter_num} | {len(questions)} | {core_points} |\n")
        
        total_q = sum(len(qs) for qs in all_questions.values())
        f.write(f"\n**总计**: {total_q} 道题目\n\n")
        f.write("---\n\n")
        
        # 详细题目
        for chapter_num, questions in all_questions.items():
            f.write(f"## {chapter_num}\n\n")
            
            for q in questions:
                f.write(f"### 题目{q['question_num']}")
                if q['question_text']:
                    f.write(f"：{q['question_text']}")
                f.write("\n\n")
                
                # 练习源码（显示填空）
                f.write("**练习代码**：\n```python\n")
                f.write(q['practice_source'].strip())
                f.write("\n```\n\n")
                
                # 答案源码
                f.write("**答案代码**：\n```python\n")
                f.write(q['answer_source'].strip())
                f.write("\n```\n\n")
                
                f.write("---\n\n")


def main():
    args = parse_args()
    
    if not args.all and not args.chapter:
        logger.error("请指定 --chapter 或 --all")
        return
    
    pairs = find_chapter_pairs(chapter=args.chapter)
    
    if not pairs:
        logger.warning("未找到匹配的章节")
        return
    
    logger.info(f"找到 {len(pairs)} 个章节配对")
    
    all_questions = {}
    for chapter_num, practice_path, answer_path in pairs:
        logger.info(f"\n处理: {chapter_num}")
        logger.info(f"  练习: {practice_path.name}")
        logger.info(f"  答案: {answer_path.name}")
        
        questions = extract_questions_from_pair(chapter_num, practice_path, answer_path)
        all_questions[chapter_num] = questions
        logger.info(f"  提取 {len(questions)} 道题目")
    
    # 生成报告
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = ROOT / 'reports' / f"all_chapters_review_{Path(__file__).stem}.md"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_markdown_report(all_questions, output_path)
    logger.info(f"\n报告已生成: {output_path}")
    
    # 打印摘要
    print("\n" + "="*80)
    print("📚 提取结果摘要")
    print("="*80)
    
    total_questions = 0
    for chapter_num, questions in all_questions.items():
        print(f"\n{chapter_num}: {len(questions)} 道题目")
        total_questions += len(questions)
    
    print(f"\n总计: {total_questions} 道题目")


if __name__ == '__main__':
    main()