#!/usr/bin/env python3
"""
测试新版评分结构（v2）

用法:
  python3 scripts/test_v2_scoring.py 2.2.2 --file 2.2.2-materials/xxx.ipynb
  python3 scripts/test_v2_scoring.py 2.2.2 --mode exam
  python3 scripts/test_v2_scoring.py 2.2.2 --mode practice
"""
from pathlib import Path
import json
import re
import argparse
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SCORING_DIR = ROOT / 'scoring'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='测试新版评分结构')
    parser.add_argument('chapter', type=str, help='章节号（如 2.2.2）')
    parser.add_argument('--file', type=str, help='练习文件路径')
    parser.add_argument('--mode', type=str, choices=['exam', 'practice'], default='exam',
                       help='评分模式：exam（严格）或 practice（宽松）')
    return parser.parse_args()


def load_scoring_schema_v2(chapter: str) -> Optional[Dict]:
    """加载新版评分标准（优先加载 v2 版本）"""
    # 先尝试加载 v2 版本
    schema_path = SCORING_DIR / f'{chapter}_v2.json'
    if not schema_path.exists():
        # 回退到旧版本
        schema_path = SCORING_DIR / f'{chapter}.json'
    
    if not schema_path.exists():
        logger.error(f"评分标准不存在: {schema_path}")
        return None
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_notebook(nb_path: Path) -> Optional[Dict]:
    """加载 notebook 文件"""
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取文件失败 {nb_path}: {e}")
        return None


def extract_code_from_cell(cell: Dict) -> str:
    """从 cell 中提取代码"""
    source = cell.get('source', [])
    if isinstance(source, list):
        return ''.join(source)
    return source


def get_line_at_index(code: str, line_index: int, search_window: int = 3) -> str:
    """
    获取指定行号的代码（智能查找）
    
    策略：
    1. 先检查目标行
    2. 如果是注释/空行，向下查找
    3. 在 ±search_window 范围内搜索包含关键词的代码行
    """
    lines = code.split('\n')
    
    if line_index >= len(lines):
        return ''
    
    target_line = lines[line_index].strip()
    
    # 如果目标行是注释或空行，在附近搜索
    if target_line.startswith('#') or not target_line:
        # 向下搜索
        for i in range(line_index + 1, min(line_index + search_window + 1, len(lines))):
            line = lines[i].strip()
            if line and not line.startswith('#'):
                return line
    
    return target_line


def normalize_quotes(text: str) -> str:
    """统一引号为双引号（方便比较）"""
    return text.replace("'", '"')


def check_exact_rule(code_line: str, rule: Dict) -> bool:
    """
    检查 exact 类型的规则
    
    规则类型：
    - must_contain: 必须包含某些字符串
    - must_assign_to: 必须赋值给某个变量
    - must_have_arg: 必须包含某个参数
    - must_call_method: 必须调用某个方法
    """
    # 统一引号后比较
    code_normalized = normalize_quotes(code_line)
    
    # must_contain: 必须包含所有指定的字符串
    if 'must_contain' in rule:
        for pattern in rule['must_contain']:
            pattern_normalized = normalize_quotes(pattern)
            if pattern_normalized not in code_normalized:
                return False
    
    # must_contain_any: 必须包含任意一个
    if 'must_contain_any' in rule:
        if not any(normalize_quotes(pattern) in code_normalized 
                  for pattern in rule['must_contain_any']):
            return False
    
    # must_assign_to: 必须赋值给指定变量
    if 'must_assign_to' in rule:
        var_name = rule['must_assign_to']
        # 匹配 var = ... 或 var(...) 等
        if not re.search(rf'\b{re.escape(var_name)}\s*=', code_line):
            return False
    
    # must_have_arg: 必须包含某个参数（支持单双引号）
    if 'must_have_arg' in rule:
        arg = rule['must_have_arg']
        arg_normalized = normalize_quotes(arg)
        if arg_normalized not in code_normalized:
            return False
    
    # must_call_method: 必须调用某个方法
    if 'must_call_method' in rule:
        method = rule['must_call_method']
        if f'.{method}' not in code_line:
            return False
    
    return True


def check_semantic_rule(code_line: str, code_full: str, rule: Dict) -> bool:
    """
    检查 semantic 类型的规则（宽松匹配）
    
    规则类型：
    - must_contain_any: 包含任意一个关键词
    - allow_variable_rename: 允许变量重命名
    - result_type: 结果类型检查
    """
    # must_contain_any: 包含任意一个即可
    if 'must_contain_any' in rule:
        if not any(pattern in code_line or pattern in code_full 
                  for pattern in rule['must_contain_any']):
            return False
    
    # must_call_method: 必须调用某个方法
    if 'must_call_method' in rule:
        method = rule['must_call_method']
        if f'.{method}(' not in code_full:
            return False
    
    # must_have_param: 必须包含某个参数
    if 'must_have_param' in rule:
        param = rule['must_have_param']
        if param not in code_full:
            return False
    
    return True


def find_code_line_smart(code_full: str, line_index: int, template: str, validators: Dict) -> str:
    """
    智能查找代码行（处理用户添加额外行导致的偏移）
    
    策略：
    1. 先尝试 line_index
    2. 如果是注释/空行，在附近搜索
    3. 使用 template 中的关键词在 ±5 行范围内搜索
    """
    lines = code_full.split('\n')
    
    # 先从 line_index 开始
    if line_index >= len(lines):
        return ''
    
    target_line = lines[line_index].strip()
    
    # 如果目标行是注释或空行，向下搜索
    if target_line.startswith('#') or not target_line:
        for i in range(line_index + 1, min(line_index + 6, len(lines))):
            line = lines[i].strip()
            if line and not line.startswith('#'):
                return line
    
    # 如果目标行看起来不像代码（没有关键词），在附近搜索
    # 从 template 中提取关键词
    keywords = []
    if 'must_contain' in str(validators):
        import re
        matches = re.findall(r"'([^']+)'", str(validators))
        keywords = [m for m in matches if len(m) > 3 and not m.startswith('__')]
    
    if keywords and not any(kw in target_line for kw in keywords):
        # 在 ±5 行范围内搜索
        for offset in range(-5, 6):
            if offset == 0:
                continue
            idx = line_index + offset
            if 0 <= idx < len(lines):
                line = lines[idx].strip()
                if line and not line.startswith('#'):
                    if any(kw in line for kw in keywords):
                        return line
    
    return target_line


def score_item_v2(item: Dict, practice_nb: Dict, mode: str = 'exam') -> Dict:
    """
    对单个评分点进行评分（v2 版本）
    
    返回: {
        'item_id': 'M1',
        'earned': 1,
        'max': 1,
        'correct': True,
        'details': '...'
    }
    """
    cell_index = item['metadata']['cell_index']
    line_index = item['metadata']['line_index']
    
    # 获取练习代码
    cells = practice_nb.get('cells', [])
    if cell_index >= len(cells):
        return {
            'item_id': item['id'],
            'earned': 0,
            'max': item['score'],
            'correct': False,
            'details': 'Cell 不存在'
        }
    
    cell = cells[cell_index]
    if cell.get('cell_type') != 'code':
        return {
            'item_id': item['id'],
            'earned': 0,
            'max': item['score'],
            'correct': False,
            'details': 'Cell 类型不是代码'
        }
    
    code_full = extract_code_from_cell(cell)
    
    # 获取对应模式的 validators
    validators = item.get('validators', {})
    mode_validators = validators.get(mode, validators.get('exam'))  # 默认使用 exam
    
    if not mode_validators:
        return {
            'item_id': item['id'],
            'earned': 0,
            'max': item['score'],
            'correct': False,
            'details': '未找到验证规则'
        }
    
    # 智能查找代码行
    code_line = find_code_line_smart(code_full, line_index, item['metadata'].get('template', ''), mode_validators)
    
    validator_type = mode_validators.get('type', 'exact')
    rules = mode_validators.get('rules', [])
    
    # 根据类型检查规则
    all_passed = True
    failed_rules = []
    
    for rule in rules:
        if validator_type == 'exact':
            passed = check_exact_rule(code_line, rule)
        elif validator_type == 'semantic':
            passed = check_semantic_rule(code_line, code_full, rule)
        else:
            passed = False
        
        if not passed:
            all_passed = False
            failed_rules.append(str(rule))
    
    return {
        'item_id': item['id'],
        'description': item['description'],
        'earned': item['score'] if all_passed else 0,
        'max': item['score'],
        'correct': all_passed,
        'details': '通过' if all_passed else f'失败规则: {failed_rules}',
        'user_code': code_line,
        'difficulty': item.get('difficulty', 'unknown')
    }


def score_practice_v2(schema: Dict, practice_path: Path, mode: str = 'exam') -> Dict:
    """
    对整个练习进行评分（v2 版本）
    """
    practice_nb = load_notebook(practice_path)
    if not practice_nb:
        return None
    
    results = []
    total_earned = 0
    total_max = 0
    
    for item in schema['items']:
        result = score_item_v2(item, practice_nb, mode)
        results.append(result)
        total_earned += result['earned']
        total_max += result['max']
    
    percentage = (total_earned / total_max * 100) if total_max > 0 else 0
    
    return {
        'chapter': schema['exam']['chapter'],
        'title': schema['exam']['title'],
        'mode': mode,
        'total_score': total_max,
        'earned_score': total_earned,
        'percentage': round(percentage, 1),
        'details': results,
        'graded_at': datetime.now().isoformat()
    }


def print_report(result: Dict):
    """打印评分报告"""
    print(f"\n{'='*70}")
    print(f"📊 {result['title']}")
    print(f"章节: {result['chapter']} | 模式: {result['mode']}")
    print(f"{'='*70}")
    
    print(f"\n🏆 总分: {result['earned_score']} / {result['total_score']} ({result['percentage']}%)")
    
    print(f"\n{'题号':<6} {'难度':<8} {'描述':<30} {'得分':<8} {'状态':<6}")
    print(f"{'-'*6} {'-'*8} {'-'*30} {'-'*8} {'-'*6}")
    
    for detail in result['details']:
        status = '✅' if detail['correct'] else '❌'
        difficulty = detail.get('difficulty', '?')
        desc = detail['description'][:28]
        print(f"{detail['item_id']:<6} {difficulty:<8} {desc:<30} "
              f"{detail['earned']}/{detail['max']:<5} {status}")
    
    # 统计
    correct_count = sum(1 for d in result['details'] if d['correct'])
    total_count = len(result['details'])
    
    print(f"\n📈 统计:")
    print(f"  通过: {correct_count}/{total_count}")
    
    # 按难度统计
    by_difficulty = {}
    for d in result['details']:
        diff = d.get('difficulty', 'unknown')
        if diff not in by_difficulty:
            by_difficulty[diff] = {'correct': 0, 'total': 0}
        by_difficulty[diff]['total'] += 1
        if d['correct']:
            by_difficulty[diff]['correct'] += 1
    
    print(f"\n  难度分布:")
    for diff in ['easy', 'medium', 'hard']:
        if diff in by_difficulty:
            stats = by_difficulty[diff]
            print(f"    {diff}: {stats['correct']}/{stats['total']}")
    
    print(f"\n{'='*70}\n")


def main():
    args = parse_args()
    
    # 加载评分标准
    schema = load_scoring_schema_v2(args.chapter)
    if not schema:
        return
    
    # 确定练习文件路径
    if args.file:
        practice_path = Path(args.file)
    else:
        # 自动查找最新的练习文件
        materials_dir = ROOT / f"{args.chapter}-materials"
        practice_files = list(materials_dir.glob(f"*practice*.ipynb"))
        if not practice_files:
            logger.error(f"未找到练习文件: {materials_dir}")
            return
        practice_path = sorted(practice_files)[-1]  # 取最新的
    
    if not practice_path.exists():
        logger.error(f"练习文件不存在: {practice_path}")
        return
    
    logger.info(f"\n📁 练习文件: {practice_path}")
    logger.info(f"📋 评分模式: {args.mode}")
    
    # 评分
    result = score_practice_v2(schema, practice_path, mode=args.mode)
    if not result:
        return
    
    # 打印报告
    print_report(result)
    
    # 保存结果
    output_path = practice_path.parent / f'scoring_result_v2_{args.mode}.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"💾 结果已保存: {output_path}")


if __name__ == '__main__':
    main()