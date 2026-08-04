#!/usr/bin/env python3
"""
自动验证练习答案是否正确 - 完整版

对比维度：
1. 填空答案对比：提取模板中的 _____ 位置，对比填写的答案是否正确
2. 实现方式对比：对比关键函数、参数使用是否与参考答案一致
3. 执行结果对比：对比 notebook 的输出是否与参考答案一致
4. 多版本进步趋势：对比同一章节的多个版本，看是否有进步

对比标准：
- 参考答案：answers/1.1.1 - 4.2.5参考答案/{chapter}/{chapter}.ipynb
- 模板文件：{chapter}-materials/{chapter}.ipynb（含下划线填空）
- 详解文件：{chapter}-materials/{chapter}_guide.md
- 练习文件：{chapter}-materials/{chapter}_practice_*.ipynb

用法:
  python3 scripts/validate_practice.py                              # 验证所有最新练习
  python3 scripts/validate_practice.py --chapter 1.1.1              # 验证特定章节所有版本
  python3 scripts/validate_practice.py --file <path>                # 验证特定文件
  python3 scripts/validate_practice.py --compare-mode fill          # 只对比填空
  python3 scripts/validate_practice.py --compare-mode implementation # 只对比实现
  python3 scripts/validate_practice.py --compare-mode result        # 只对比结果
  python3 scripts/validate_practice.py --compare-mode both          # 对比填空+实现+结果
  python3 scripts/validate_practice.py --output-report              # 生成详细Markdown报告
"""
from pathlib import Path
import json
import re
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import difflib

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='验证练习答案')
    parser.add_argument('--chapter', type=str, help='只验证特定章节（如 1.1.2）')
    parser.add_argument('--latest', action='store_true', help='只验证每个章节最新的练习文件')
    parser.add_argument('--all-versions', action='store_true', help='验证所有章节的所有版本')
    parser.add_argument('--file', type=str, help='验证特定文件路径')
    parser.add_argument('--compare-mode', choices=['fill', 'implementation', 'result', 'both', 'all'], 
                       default='all',
                       help='对比模式：fill=填空, implementation=实现, result=结果, both=填空+实现, all=全部')
    parser.add_argument('--output-report', action='store_true', help='生成详细Markdown报告')
    return parser.parse_args()


def find_answer_file(chapter: str) -> Optional[Path]:
    """查找参考答案文件"""
    answer_dirs = [
        ROOT / 'answers' / '1.1.1 - 4.2.5参考答案' / chapter,
        ROOT / 'answers' / '1.1.1 -2.2.5 参考答案' / chapter,
    ]
    
    for ans_dir in answer_dirs:
        if ans_dir.exists():
            nb_path = ans_dir / f'{chapter}.ipynb'
            if nb_path.exists():
                return nb_path
    
    return None


def find_template_file(chapter: str) -> Optional[Path]:
    """查找模板文件（含下划线填空）"""
    materials_dir = ROOT / f'{chapter}-materials'
    if materials_dir.exists():
        template_path = materials_dir / f'{chapter}.ipynb'
        if template_path.exists():
            return template_path
    return None


def find_guide_file(chapter: str) -> Optional[Path]:
    """查找详解文件"""
    materials_dir = ROOT / f'{chapter}-materials'
    if materials_dir.exists():
        guide_path = materials_dir / f'{chapter}_guide.md'
        if guide_path.exists():
            return guide_path
    return None


def find_practice_files(chapter: Optional[str] = None, latest: bool = False) -> List[Path]:
    """查找练习文件"""
    pattern = '*_practice_*.ipynb'
    files = []
    
    for md in ROOT.rglob(pattern):
        if md.is_file() and '_review.md' not in md.name:
            if chapter and not md.name.startswith(chapter):
                continue
            files.append(md)
    
    if latest:
        # 按章节分组，只保留最新的
        by_chapter = {}
        for f in files:
            ch = f.name.split('_practice_')[0]
            if ch not in by_chapter or f > by_chapter[ch]:
                by_chapter[ch] = f
        files = sorted(by_chapter.values())
    
    return sorted(files)


def load_notebook(nb_path: Path) -> Optional[Dict]:
    """加载 notebook 文件"""
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取文件失败 {nb_path}: {e}")
        return None


def extract_blanks_from_template(template_path: Path) -> List[Dict]:
    """
    从模板文件中提取所有填空位置和标准答案
    
    返回: [
        {
            'cell_index': 0,
            'blank_index': 0,
            'blank_context': 'data = _____',
            'answer': 'pd.read_csv("patient_data.csv")',
        },
        ...
    ]
    """
    nb = load_notebook(template_path)
    if not nb:
        return []
    
    blanks = []
    
    for i, cell in enumerate(nb.get('cells', [])):
        if cell.get('cell_type') != 'code':
            continue
        
        source = ''.join(cell.get('source', []))
        
        # 查找所有下划线填空
        # 匹配 _____ 或 _____________ 等
        blank_pattern = r'_{3,}'
        matches = list(re.finditer(blank_pattern, source))
        
        for j, match in enumerate(matches):
            # 提取填空周围的上下文
            start = max(0, match.start() - 30)
            end = min(len(source), match.end() + 30)
            context = source[start:end].strip()
            
            blanks.append({
                'cell_index': i,
                'blank_index': j,
                'position': match.start(),
                'context': context,
                'full_line': source.split('\n')[source[:match.start()].count('\n')]
            })
    
    return blanks


def extract_filled_answers(practice_path: Path, template_path: Path) -> List[Dict]:
    """
    提取练习文件中填写的答案
    
    通过对比模板和练习文件，提取每个填空处的实际填写内容
    """
    template_nb = load_notebook(template_path)
    practice_nb = load_notebook(practice_path)
    
    if not template_nb or not practice_nb:
        return []
    
    filled = []
    
    for i, (t_cell, p_cell) in enumerate(zip(
        template_nb.get('cells', []), 
        practice_nb.get('cells', [])
    )):
        if t_cell.get('cell_type') != 'code':
            continue
        
        t_source = ''.join(t_cell.get('source', []))
        p_source = ''.join(p_cell.get('source', []))
        
        # 查找模板中的填空位置
        blank_pattern = r'_{3,}'
        t_matches = list(re.finditer(blank_pattern, t_source))
        
        for j, match in enumerate(t_matches):
            # 提取填空的答案
            blank_start = match.start()
            blank_end = match.end()
            
            # 在练习文件中对应位置的内容
            # 由于可能长度不同，使用行号定位
            t_line_num = t_source[:blank_start].count('\n')
            t_lines = t_source.split('\n')
            p_lines = p_source.split('\n')
            
            if t_line_num < len(p_lines) and t_line_num < len(t_lines):
                t_line = t_lines[t_line_num]
                p_line = p_lines[t_line_num] if t_line_num < len(p_lines) else ''
                
                # 提取填空处的答案
                # 在模板行中找到 _____ 的位置
                t_blank_match = re.search(r'_{3,}', t_line)
                if t_blank_match:
                    # 在练习行中提取对应位置的内容
                    t_before = t_line[:t_blank_match.start()]
                    t_after = t_line[t_blank_match.end():]
                    
                    # 在练习行中查找对应内容
                    if t_before.strip() in p_line:
                        start_idx = p_line.index(t_before.strip()) + len(t_before.strip())
                        if t_after.strip() and t_after.strip() in p_line[start_idx:]:
                            end_idx = p_line.index(t_after.strip(), start_idx)
                            answer = p_line[start_idx:end_idx].strip()
                        else:
                            answer = p_line[start_idx:].strip()
                    else:
                        answer = p_line.strip()
                    
                    filled.append({
                        'cell_index': i,
                        'blank_index': j,
                        'answer': answer,
                        'full_line': p_line
                    })
    
    return filled


def extract_blank_answers_from_template_and_answer(template_path: Path, answer_path: Path) -> List[Dict]:
    """
    精确提取模板中每个填空处的标准答案
    
    返回: [
        {
            'cell_index': 0,
            'line_index': 4,
            'blank_index': 0,
            'template_line': 'data = _____',
            'answer': 'pd.read_csv("patient_data.csv")',
        },
        ...
    ]
    """
    template_nb = load_notebook(template_path)
    answer_nb = load_notebook(answer_path)
    
    if not template_nb or not answer_nb:
        return []
    
    blank_answers = []
    
    for i, (t_cell, a_cell) in enumerate(zip(
        template_nb.get('cells', []),
        answer_nb.get('cells', [])
    )):
        if t_cell.get('cell_type') != 'code':
            continue
        
        t_source = ''.join(t_cell.get('source', []))
        a_source = ''.join(a_cell.get('source', []))
        
        t_lines = t_source.split('\n')
        a_lines = a_source.split('\n')
        
        # 查找模板中的填空
        for j, (t_line, a_line) in enumerate(zip(t_lines, a_lines)):
            blanks = list(re.finditer(r'_{3,}', t_line))
            if not blanks:
                continue
            
            # 逐个填空提取
            prev_end = 0
            for b_idx, blank in enumerate(blanks):
                # 获取填空前后的内容
                before = t_line[prev_end:blank.start()]
                after_blank = t_line[blank.end():]
                
                # 查找下一个填空的位置
                if b_idx + 1 < len(blanks):
                    next_blank_start = blanks[b_idx + 1].start()
                    after = t_line[blank.end():next_blank_start]
                else:
                    after = after_blank
                
                # 在答案行中定位
                answer_text = None
                if before.strip() in a_line:
                    start_idx = a_line.index(before.strip()) + len(before.strip())
                    
                    if after.strip() and after.strip() in a_line[start_idx:]:
                        end_idx = a_line.index(after.strip(), start_idx)
                        answer_text = a_line[start_idx:end_idx].strip()
                    else:
                        # 最后一个填空，取到行尾
                        answer_text = a_line[start_idx:].strip()
                
                blank_answers.append({
                    'cell_index': i,
                    'line_index': j,
                    'blank_index': b_idx,
                    'template_line': t_line.strip(),
                    'answer': answer_text,
                    'before': before.strip(),
                    'after': after.strip()
                })
                
                prev_end = blank.end()
    
    return blank_answers


def extract_practice_filled_answers(practice_path: Path, template_path: Path) -> List[Dict]:
    """
    从练习文件中精确提取每个填空处填写的答案
    
    返回: [
        {
            'cell_index': 0,
            'line_index': 4,
            'blank_index': 0,
            'practice_line': 'data = pd.read_csv("patient_data.csv")',
            'filled_answer': 'pd.read_csv("patient_data.csv")',
        },
        ...
    ]
    """
    practice_nb = load_notebook(practice_path)
    template_nb = load_notebook(template_path)
    
    if not practice_nb or not template_nb:
        return []
    
    filled_answers = []
    
    for i, (p_cell, t_cell) in enumerate(zip(
        practice_nb.get('cells', []),
        template_nb.get('cells', [])
    )):
        if t_cell.get('cell_type') != 'code':
            continue
        
        p_source = ''.join(p_cell.get('source', []))
        t_source = ''.join(t_cell.get('source', []))
        
        p_lines = p_source.split('\n')
        t_lines = t_source.split('\n')
        
        # 查找模板中的填空
        for j, (p_line, t_line) in enumerate(zip(p_lines, t_lines)):
            blanks = list(re.finditer(r'_{3,}', t_line))
            if not blanks:
                continue
            
            # 逐个填空提取
            prev_end = 0
            for b_idx, blank in enumerate(blanks):
                # 获取填空前后的内容
                before = t_line[prev_end:blank.start()]
                after_blank = t_line[blank.end():]
                
                # 查找下一个填空的位置
                if b_idx + 1 < len(blanks):
                    next_blank_start = blanks[b_idx + 1].start()
                    after = t_line[blank.end():next_blank_start]
                else:
                    after = after_blank
                
                # 在练习行中定位
                filled_text = None
                if before.strip() in p_line:
                    start_idx = p_line.index(before.strip()) + len(before.strip())
                    
                    if after.strip() and after.strip() in p_line[start_idx:]:
                        end_idx = p_line.index(after.strip(), start_idx)
                        filled_text = p_line[start_idx:end_idx].strip()
                    else:
                        # 最后一个填空，取到行尾
                        filled_text = p_line[start_idx:].strip()
                
                filled_answers.append({
                    'cell_index': i,
                    'line_index': j,
                    'blank_index': b_idx,
                    'practice_line': p_line.strip(),
                    'filled_answer': filled_text,
                    'before': before.strip(),
                    'after': after.strip()
                })
                
                prev_end = blank.end()
    
    return filled_answers


def compare_fill_answers(practice_path: Path, template_path: Path, answer_path: Path) -> List[Dict]:
    """
    对比填空答案是否正确（精确到每个填空）
    """
    # 提取标准答案
    blank_answers = extract_blank_answers_from_template_and_answer(template_path, answer_path)
    
    # 提取练习填写的答案
    filled_answers = extract_practice_filled_answers(practice_path, template_path)
    
    if not blank_answers or not filled_answers:
        # 回退到整行对比
        answer_nb = load_notebook(answer_path)
        practice_nb = load_notebook(practice_path)
        
        if not answer_nb or not practice_nb:
            return []
        
        differences = []
        for i, (a_cell, p_cell) in enumerate(zip(
            answer_nb.get('cells', []),
            practice_nb.get('cells', [])
        )):
            if a_cell.get('cell_type') != 'code':
                continue
            
            a_source = ''.join(a_cell.get('source', []))
            p_source = ''.join(p_cell.get('source', []))
            
            if a_source.strip() == p_source.strip():
                continue
            
            similarity = difflib.SequenceMatcher(None, a_source.strip(), p_source.strip()).ratio()
            
            if similarity < 0.95:
                differences.append({
                    'cell_index': i,
                    'similarity': similarity,
                    'answer_code': a_source[:300],
                    'practice_code': p_source[:300],
                })
        return differences
    
    # 精确对比每个填空
    differences = []
    
    # 创建查找字典
    filled_dict = {}
    for fa in filled_answers:
        key = (fa['cell_index'], fa['line_index'], fa['blank_index'])
        filled_dict[key] = fa
    
    for ba in blank_answers:
        key = (ba['cell_index'], ba['line_index'], ba['blank_index'])
        fa = filled_dict.get(key)
        
        if not fa:
            differences.append({
                'cell_index': ba['cell_index'],
                'line_index': ba['line_index'],
                'blank_index': ba['blank_index'],
                'type': 'missing_fill',
                'template_line': ba['template_line'],
                'expected_answer': ba['answer'],
                'filled_answer': None,
                'similarity': 0.0
            })
            continue
        
        # 对比答案（统一引号后再对比）
        expected = ba['answer'].replace("'", '"').strip()
        filled = fa['filled_answer'].replace("'", '"').strip()
        
        if expected and filled:
            similarity = difflib.SequenceMatcher(None, expected, filled).ratio()
            if similarity < 0.95:
                differences.append({
                    'cell_index': ba['cell_index'],
                    'line_index': ba['line_index'],
                    'blank_index': ba['blank_index'],
                    'type': 'incorrect_fill',
                    'template_line': ba['template_line'],
                    'expected_answer': expected,
                    'filled_answer': filled,
                    'similarity': similarity
                })
        elif expected and not filled:
            differences.append({
                'cell_index': ba['cell_index'],
                'line_index': ba['line_index'],
                'blank_index': ba['blank_index'],
                'type': 'empty_fill',
                'template_line': ba['template_line'],
                'expected_answer': expected,
                'filled_answer': None,
                'similarity': 0.0
            })
    
    return differences


def extract_outputs(nb: Dict) -> List[Dict]:
    """提取所有输出"""
    outputs = []
    for cell in nb.get('cells', []):
        if cell.get('cell_type') == 'code':
            cell_outputs = []
            for output in cell.get('outputs', []):
                if output.get('output_type') == 'stream':
                    cell_outputs.append(''.join(output.get('text', [])))
                elif output.get('output_type') == 'execute_result':
                    cell_outputs.append(str(output.get('data', {}).get('text/plain', '')))
            outputs.append(cell_outputs)
    return outputs


def compare_outputs(practice_outputs: List[Dict], answer_outputs: List[Dict]) -> List[Dict]:
    """对比执行结果"""
    differences = []
    
    max_len = max(len(practice_outputs), len(answer_outputs))
    
    for i in range(max_len):
        if i >= len(practice_outputs):
            differences.append({
                'cell': i,
                'type': 'missing_output',
                'message': '练习文件缺少输出'
            })
            continue
        
        if i >= len(answer_outputs):
            continue
        
        p_out = practice_outputs[i]
        a_out = answer_outputs[i]
        
        for j, (p, a) in enumerate(zip(p_out, a_out)):
            if p.strip() != a.strip():
                similarity = difflib.SequenceMatcher(None, p.strip(), a.strip()).ratio()
                if similarity < 0.95:
                    differences.append({
                        'cell': i,
                        'output_index': j,
                        'type': 'output_mismatch',
                        'similarity': similarity,
                        'practice': p[:200],
                        'answer': a[:200]
                    })
    
    return differences


def check_implementation_details(practice_path: Path, answer_path: Path) -> List[Dict]:
    """
    检查实现细节：关键函数、参数使用是否正确
    
    例如：
    - 是否使用了正确的函数（pd.cut vs pd.qcut）
    - 参数是否正确（bins, labels, right等）
    - 变量命名是否一致
    """
    answer_nb = load_notebook(answer_path)
    practice_nb = load_notebook(practice_path)
    
    if not answer_nb or not practice_nb:
        return []
    
    issues = []
    
    # 提取关键函数调用
    def extract_key_functions(code: str) -> List[str]:
        """提取关键函数调用"""
        # 匹配 pandas/numpy 函数调用
        patterns = [
            r'pd\.\w+',
            r'np\.\w+',
            r'\.groupby\(',
            r'\.apply\(',
            r'\.value_counts\(',
        ]
        functions = []
        for pattern in patterns:
            functions.extend(re.findall(pattern, code))
        return functions
    
    for i, (a_cell, p_cell) in enumerate(zip(
        answer_nb.get('cells', []),
        practice_nb.get('cells', [])
    )):
        if a_cell.get('cell_type') != 'code':
            continue
        
        a_source = ''.join(a_cell.get('source', []))
        p_source = ''.join(p_cell.get('source', []))
        
        a_funcs = set(extract_key_functions(a_source))
        p_funcs = set(extract_key_functions(p_source))
        
        # 检查是否缺少关键函数
        missing_funcs = a_funcs - p_funcs
        if missing_funcs:
            issues.append({
                'cell_index': i,
                'type': 'missing_function',
                'missing': list(missing_funcs),
                'answer_code': a_source[:200],
                'practice_code': p_source[:200]
            })
    
    return issues


def check_unfilled_blanks(practice_path: Path) -> List[Dict]:
    """检查是否还有未填的空"""
    nb = load_notebook(practice_path)
    if not nb:
        return []
    
    blanks = []
    for i, cell in enumerate(nb.get('cells', [])):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            if re.search(r'_{3,}', source):
                blanks.append({
                    'cell': i,
                    'code': source[:200]
                })
    
    return blanks


def analyze_progress(chapter: str, practice_files: List[Path]) -> Dict:
    """
    分析多版本练习的进步趋势
    
    返回: {
        'versions': [...],
        'score_trend': [...],
        'improved': bool,
        'first_score': int,
        'latest_score': int,
    }
    """
    versions = []
    
    for pf in practice_files:
        result = validate_single_practice(pf, compare_mode='all', detailed=False)
        versions.append({
            'file': pf.name,
            'score': result['score'],
            'errors': len(result['errors']),
            'warnings': len(result['warnings']),
        })
    
    if len(versions) < 2:
        return {
            'versions': versions,
            'has_progress': False,
        }
    
    # 按文件名排序（时间戳）
    versions.sort(key=lambda x: x['file'])
    
    first_score = versions[0]['score']
    latest_score = versions[-1]['score']
    
    return {
        'versions': versions,
        'has_progress': True,
        'first_score': first_score,
        'latest_score': latest_score,
        'improved': latest_score > first_score,
        'score_change': latest_score - first_score,
    }


def validate_single_practice(practice_path: Path, compare_mode: str = 'all', detailed: bool = True) -> Dict:
    """验证单个练习文件"""
    chapter = practice_path.name.split('_practice_')[0]
    
    result = {
        'file': str(practice_path),
        'chapter': chapter,
        'errors': [],
        'warnings': [],
        'score': 100,
        'fill_comparison': [],
        'implementation_comparison': [],
        'result_comparison': [],
    }
    
    # 1. 检查是否还有空白未填
    blanks = check_unfilled_blanks(practice_path)
    if blanks:
        result['errors'].append({
            'type': 'unfilled_blanks',
            'count': len(blanks),
            'details': blanks
        })
        result['score'] -= len(blanks) * 5
    
    # 2. 查找参考答案和模板
    answer_path = find_answer_file(chapter)
    template_path = find_template_file(chapter)
    
    if answer_path and template_path:
        practice_nb = load_notebook(practice_path)
        answer_nb = load_notebook(answer_path)
        
        if practice_nb and answer_nb:
            # 填空对比
            if compare_mode in ['fill', 'both', 'all']:
                fill_diffs = compare_fill_answers(practice_path, template_path, answer_path)
                result['fill_comparison'] = fill_diffs
                if fill_diffs:
                    result['errors'].append({
                        'type': 'fill_incorrect',
                        'count': len(fill_diffs),
                        'details': fill_diffs
                    })
                    result['score'] -= len(fill_diffs) * 8
            
            # 实现细节对比
            if compare_mode in ['implementation', 'both', 'all']:
                impl_issues = check_implementation_details(practice_path, answer_path)
                result['implementation_comparison'] = impl_issues
                if impl_issues:
                    result['warnings'].append({
                        'type': 'implementation_differs',
                        'count': len(impl_issues),
                        'details': impl_issues
                    })
                    result['score'] -= len(impl_issues) * 3
            
            # 执行结果对比
            if compare_mode in ['result', 'both', 'all']:
                p_outputs = extract_outputs(practice_nb)
                a_outputs = extract_outputs(answer_nb)
                output_diffs = compare_outputs(p_outputs, a_outputs)
                result['result_comparison'] = output_diffs
                if output_diffs:
                    result['errors'].append({
                        'type': 'output_mismatch',
                        'count': len(output_diffs),
                        'details': output_diffs
                    })
                    result['score'] -= len(output_diffs) * 10
    
    # 确保分数不低于0
    result['score'] = max(0, result['score'])
    
    return result


def generate_markdown_report(results: List[Dict], output_path: Path):
    """生成详细的Markdown报告"""
    report = []
    report.append("# 练习验证报告\n")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 汇总统计
    total = len(results)
    perfect = sum(1 for r in results if r['score'] == 100)
    avg_score = sum(r['score'] for r in results) / total if total > 0 else 0
    
    report.append("## 📊 汇总统计\n")
    report.append(f"| 指标 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| 总练习数 | {total} |")
    report.append(f"| 完全正确 | {perfect} ({perfect/total*100:.1f}%) |")
    report.append(f"| 平均分 | {avg_score:.1f} |")
    report.append("")
    
    # 详细结果
    report.append("## 📝 详细结果\n")
    
    for r in results:
        report.append(f"### {r['chapter']} - {Path(r['file']).name}\n")
        report.append(f"**得分**: {r['score']}/100\n")
        
        if r['errors']:
            report.append("#### ❌ 错误\n")
            for err in r['errors']:
                if err['type'] == 'unfilled_blanks':
                    report.append(f"- 未填空: {err['count']}处")
                elif err['type'] == 'fill_incorrect':
                    report.append(f"- 填空错误: {err['count']}处")
                    for d in err.get('details', [])[:3]:
                        report.append(f"  - 单元格 {d['cell_index']}: 相似度 {d.get('similarity', 0):.0%}")
                        report.append(f"    - 参考答案: `{d.get('answer_code', '')[:100]}`")
                        report.append(f"    - 你的答案: `{d.get('practice_code', '')[:100]}`")
                elif err['type'] == 'output_mismatch':
                    report.append(f"- 输出不匹配: {err['count']}处")
                    for d in err.get('details', [])[:3]:
                        report.append(f"  - 单元格 {d['cell']}: 相似度 {d.get('similarity', 0):.0%}")
        
        if r['warnings']:
            report.append("#### ⚠️ 警告\n")
            for warn in r['warnings']:
                if warn['type'] == 'implementation_differs':
                    report.append(f"- 实现差异: {warn['count']}处")
                    for d in warn.get('details', [])[:3]:
                        report.append(f"  - 单元格 {d['cell_index']}: 缺少函数 {d.get('missing', [])}")
        
        if not r['errors'] and not r['warnings']:
            report.append("✅ 完全正确！\n")
        
        report.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    logger.info(f"\n报告已生成: {output_path}")


def print_validation_report(results: List[Dict]):
    """打印验证报告"""
    print("\n" + "="*80)
    print("📊 练习验证报告")
    print("="*80)
    
    for r in results:
        print(f"\n{'─'*80}")
        print(f"📁 章节: {r['chapter']}")
        print(f"📄 文件: {Path(r['file']).name}")
        print(f"💯 得分: {r['score']}/100")
        
        if r['fill_comparison']:
            print(f"\n📝 填空对比:")
            for d in r['fill_comparison'][:5]:
                if d.get('type') == 'incorrect_fill':
                    print(f"  单元格 {d['cell_index']}, 行 {d['line_index']}, 填空 {d['blank_index']}: 相似度 {d.get('similarity', 0):.0%}")
                    print(f"    模板: {d.get('template_line', '')[:80]}")
                    print(f"    期望: {d.get('expected_answer', '')[:80]}")
                    print(f"    你的: {d.get('filled_answer', '')[:80]}")
                elif d.get('type') == 'missing_fill':
                    print(f"  单元格 {d['cell_index']}, 行 {d['line_index']}, 填空 {d['blank_index']}: 未填写")
                    print(f"    期望: {d.get('expected_answer', '')[:80]}")
                else:
                    print(f"  单元格 {d['cell_index']}: 相似度 {d.get('similarity', 0):.0%}")
        
        if r['implementation_comparison']:
            print(f"\n🔧 实现对比:")
            for d in r['implementation_comparison'][:3]:
                print(f"  单元格 {d['cell_index']}: 缺少 {d.get('missing', [])}")
        
        if r['result_comparison']:
            print(f"\n📤 结果对比:")
            for d in r['result_comparison'][:3]:
                print(f"  单元格 {d['cell']}: 相似度 {d.get('similarity', 0):.0%}")
        
        if r['errors']:
            print(f"\n❌ 错误 ({len(r['errors'])}个):")
            for err in r['errors']:
                if err['type'] == 'unfilled_blanks':
                    print(f"  - 未填空: {err['count']}处")
                elif err['type'] == 'fill_incorrect':
                    print(f"  - 填空错误: {err['count']}处")
                elif err['type'] == 'output_mismatch':
                    print(f"  - 输出不匹配: {err['count']}处")
        
        if r['warnings']:
            print(f"\n⚠️  警告 ({len(r['warnings'])}个):")
            for warn in r['warnings']:
                if warn['type'] == 'implementation_differs':
                    print(f"  - 实现差异: {warn['count']}处")
        
        if not r['errors'] and not r['warnings']:
            print(f"\n✅ 完全正确！")
    
    # 汇总统计
    print(f"\n{'='*80}")
    print(f"📈 汇总统计")
    print(f"{'='*80}")
    total = len(results)
    perfect = sum(1 for r in results if r['score'] == 100)
    avg_score = sum(r['score'] for r in results) / total if total > 0 else 0
    
    print(f"总练习数: {total}")
    print(f"完全正确: {perfect} ({perfect/total*100:.1f}%)")
    print(f"平均分: {avg_score:.1f}")


def main():
    args = parse_args()
    
    if args.file:
        practice_path = Path(args.file)
        if not practice_path.exists():
            logger.error(f"文件不存在: {practice_path}")
            return
        results = [validate_single_practice(practice_path, compare_mode=args.compare_mode)]
    else:
        practice_files = find_practice_files(
            chapter=args.chapter,
            latest=not args.all_versions
        )
        
        if not practice_files:
            logger.info("未找到练习文件")
            return
        
        logger.info(f"找到 {len(practice_files)} 个练习文件")
        
        results = []
        for pf in practice_files:
            logger.info(f"\n验证: {pf.name}")
            result = validate_single_practice(pf, compare_mode=args.compare_mode)
            results.append(result)
    
    print_validation_report(results)
    
    if args.output_report:
        output_path = ROOT / 'reports' / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generate_markdown_report(results, output_path)


if __name__ == '__main__':
    main()