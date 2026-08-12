#!/usr/bin/env python3
"""
自动验证练习答案是否正确 - 完整版

对比维度：
1. 填空答案对比：提取模板中的 _____ 位置，对比填写的答案是否正确
2. 实现方式对比：对比关键函数、参数使用是否与参考答案一致
3. 执行结果对比：对比 notebook 的输出是否与参考答案一致
4. 多版本进步趋势：对比同一章节的多个版本，看是否有进步
5. IPython历史命令分析：分析答题过程中的命令演化、修正次数、错误类型

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
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import difflib

# 添加项目根目录到 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

SCORING_DIR = ROOT / 'scoring'

from core.session_factory import SessionFactory


def load_scoring_schema(chapter: str) -> Optional[Dict]:
    """
    加载评分标准文件（优先使用 AST 版本）
    
    参数:
        chapter: 章节号（如 '1.1.1'）
    
    返回:
        评分标准字典，如果不存在则返回None
    """
    # 优先使用 AST 版本
    ast_schema_path = SCORING_DIR / f'{chapter}_ast.json'
    if ast_schema_path.exists():
        try:
            with open(ast_schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                logger.info(f"✅ 使用 AST 评分标准: {ast_schema_path.name}")
                return schema
        except Exception as e:
            logger.warning(f"读取 AST 评分标准失败 {ast_schema_path}: {e}")
    
    # Fallback 到普通版本
    schema_path = SCORING_DIR / f'{chapter}.json'
    if not schema_path.exists():
        return None
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            logger.info(f"⚠️  使用普通评分标准: {schema_path.name}")
            return json.load(f)
    except Exception as e:
        logger.warning(f"读取评分标准失败 {schema_path}: {e}")
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='验证练习答案')
    parser.add_argument('--chapter', type=str, help='只验证特定章节（如 1.1.2）')
    parser.add_argument('--latest', action='store_true', help='只验证每个章节最新的练习文件')
    parser.add_argument('--all-versions', action='store_true', help='验证所有章节的所有版本')
    parser.add_argument('--file', type=str, help='验证特定文件路径')
    parser.add_argument('--session', type=str, help='验证特定Session目录')
    parser.add_argument('--compare-mode', choices=['fill', 'implementation', 'result', 'both', 'all'], 
                       default='all',
                       help='[已弃用] 对比模式：fill=填空, implementation=实现, result=结果, both=填空+实现, all=全部。建议使用 --check-fill/--check-output/--check-impl 标志位')
    parser.add_argument('--check-fill', action='store_true', help='对比填空答案')
    parser.add_argument('--check-output', action='store_true', help='对比执行结果')
    parser.add_argument('--check-impl', action='store_true', help='对比实现细节')
    parser.add_argument('--output-report', action='store_true', help='生成详细Markdown报告')
    parser.add_argument('--output-json', action='store_true', help='输出结构化JSON报告（推荐）')
    parser.add_argument('--audit-process', action='store_true', help='启用回溯审计（分析execution_log.json中的中间错误）')
    parser.add_argument('--analyze-history', action='store_true', help='分析IPython历史命令（对比答题过程）')
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
    
    修复：使用正则匹配而非 index() 硬字符匹配，容忍空格/缩进差异
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
            blank_start = match.start()
            blank_end = match.end()
            
            t_line_num = t_source[:blank_start].count('\n')
            t_lines = t_source.split('\n')
            p_lines = p_source.split('\n')
            
            if t_line_num < len(p_lines) and t_line_num < len(t_lines):
                t_line = t_lines[t_line_num]
                p_line = p_lines[t_line_num] if t_line_num < len(p_lines) else ''
                
                t_blank_match = re.search(r'_{3,}', t_line)
                if t_blank_match:
                    t_before = t_line[:t_blank_match.start()].strip()
                    t_after = t_line[t_blank_match.end():].strip()
                    
                    # 使用正则匹配，忽略空格差异
                    answer = None
                    
                    # 策略1：赋值模式提取
                    if '=' in t_before:
                        assign_pattern = r'=\s*(.+?)(?:\s*' + re.escape(t_after) + r'\s*$|$)' if t_after else r'=\s*(.+?)\s*$'
                        match = re.search(assign_pattern, p_line.strip())
                        if match:
                            answer = match.group(1).strip()
                    
                    # 策略2：before/after 锚点匹配（容忍空格）
                    if answer is None and t_before:
                        before_regex = r'\s*'.join(re.escape(c) for c in t_before)
                        after_regex = r'\s*'.join(re.escape(c) for c in t_after) if t_after else ''
                        
                        if after_regex:
                            full_pattern = before_regex + r'\s*(.*?)\s*' + after_regex
                        else:
                            full_pattern = before_regex + r'\s*(.*?)\s*$'
                        
                        match = re.search(full_pattern, p_line.strip())
                        if match:
                            answer = match.group(1).strip()
                    
                    # 策略3：兜底
                    if answer is None:
                        before_no_space = t_before.replace(' ', '')
                        p_line_no_space = p_line.strip().replace(' ', '')
                        if before_no_space in p_line_no_space:
                            idx = p_line_no_space.index(before_no_space)
                            remaining = p_line_no_space[idx + len(before_no_space):]
                            if t_after:
                                after_no_space = t_after.replace(' ', '')
                                if after_no_space in remaining:
                                    remaining = remaining[:remaining.index(after_no_space)]
                            answer = remaining.strip()
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
    
    修复：使用标准化匹配，容忍空格/缩进差异
    
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
    
    # 过滤掉自动注入的日志初始化Cell
    def is_auto_init_cell(cell):
        tags = cell.get('metadata', {}).get('tags', [])
        return 'auto-init-execution-logger' in tags
    
    template_cells = [c for c in template_nb.get('cells', []) if not is_auto_init_cell(c)]
    answer_cells = [c for c in answer_nb.get('cells', []) if not is_auto_init_cell(c)]
    
    # 辅助函数：标准化行（去除所有空格、制表符，统一引号）
    def normalize_line(line: str) -> str:
        no_space = re.sub(r'[\s]', '', line)
        return no_space.replace("'", '"')
    
    blank_answers = []
    
    for i, (t_cell, a_cell) in enumerate(zip(template_cells, answer_cells)):
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
            
            # 标准化答案行（用于匹配）
            norm_a_line = normalize_line(a_line)
            
            # 逐个填空提取
            prev_end = 0
            for b_idx, blank in enumerate(blanks):
                # 获取填空前后的内容
                before_raw = t_line[prev_end:blank.start()]
                after_blank = t_line[blank.end():]
                
                # 查找下一个填空的位置
                if b_idx + 1 < len(blanks):
                    next_blank_start = blanks[b_idx + 1].start()
                    after_raw = t_line[blank.end():next_blank_start]
                else:
                    after_raw = after_blank
                
                # 标准化前后文本
                before_norm = normalize_line(before_raw)
                after_norm = normalize_line(after_raw)
                
                # 在标准化后的答案行中定位
                answer_text = None
                start_idx = -1
                
                if before_norm:
                    start_idx = norm_a_line.find(before_norm)
                    if start_idx != -1:
                        start_idx += len(before_norm)
                    else:
                        start_idx = 0
                else:
                    start_idx = 0
                
                if start_idx != -1 and after_norm:
                    end_idx = norm_a_line.find(after_norm, start_idx)
                    if end_idx != -1:
                        answer_text = norm_a_line[start_idx:end_idx]
                    else:
                        answer_text = norm_a_line[start_idx:]
                elif start_idx != -1:
                    answer_text = norm_a_line[start_idx:]
                
                blank_answers.append({
                    'cell_index': i,
                    'line_index': j,
                    'blank_index': b_idx,
                    'template_line': t_line.strip(),
                    'answer': answer_text.strip() if answer_text else None,
                    'before': before_raw.strip(),
                    'after': after_raw.strip()
                })
                
                prev_end = blank.end()
    
    return blank_answers


def extract_practice_filled_answers(practice_path: Path, template_path: Path) -> List[Dict]:
    """从练习文件中精确提取每个填空处填写的答案（修复空格/缩进容错）"""
    practice_nb = load_notebook(practice_path)
    template_nb = load_notebook(template_path)
    
    if not practice_nb or not template_nb:
        return []
    
    filled_answers = []
    
    # 过滤掉自动注入的日志初始化Cell
    def is_auto_init_cell(cell):
        tags = cell.get('metadata', {}).get('tags', [])
        return 'auto-init-execution-logger' in tags
    
    practice_cells = [c for c in practice_nb.get('cells', []) if not is_auto_init_cell(c)]
    template_cells = [c for c in template_nb.get('cells', []) if not is_auto_init_cell(c)]
    
    # 辅助函数：标准化行（去除所有空格、制表符，统一引号）
    def normalize_line(line: str) -> str:
        # 移除所有空格和制表符
        no_space = re.sub(r'[\s]', '', line)
        # 统一引号为双引号
        return no_space.replace("'", '"')
    
    for i, (p_cell, t_cell) in enumerate(zip(practice_cells, template_cells)):
        if t_cell.get('cell_type') != 'code':
            continue
        
        p_source = ''.join(p_cell.get('source', []))
        t_source = ''.join(t_cell.get('source', []))
        
        p_lines = p_source.split('\n')
        t_lines = t_source.split('\n')
        
        for j, (p_line, t_line) in enumerate(zip(p_lines, t_lines)):
            blanks = list(re.finditer(r'_{3,}', t_line))
            if not blanks:
                continue
            
            # 标准化模板行和练习行（用于定位）
            norm_t_line = normalize_line(t_line)
            norm_p_line = normalize_line(p_line)
            
            prev_end = 0
            for b_idx, blank in enumerate(blanks):
                # 获取填空前后的文本（原始文本）
                before_raw = t_line[prev_end:blank.start()]
                after_raw = t_line[blank.end():]
                
                # 标准化前后文本
                before_norm = normalize_line(before_raw)
                after_norm = normalize_line(after_raw)
                
                filled_text = None
                
                # 1. 尝试在标准化后的练习行中查找
                start_idx = -1
                if before_norm:
                    start_idx = norm_p_line.find(before_norm)
                    if start_idx != -1:
                        start_idx += len(before_norm)
                    else:
                        # 降级：尝试去掉before，直接取开头
                        start_idx = 0
                else:
                    start_idx = 0
                
                if start_idx != -1 and after_norm:
                    end_idx = norm_p_line.find(after_norm, start_idx)
                    if end_idx != -1:
                        filled_text = norm_p_line[start_idx:end_idx]
                    else:
                        filled_text = norm_p_line[start_idx:]
                elif start_idx != -1:
                    filled_text = norm_p_line[start_idx:]
                
                # 如果还是没取到，尝试用正则提取（兜底）
                if not filled_text and norm_p_line:
                    # 尝试匹配 变量 = 值 的模式
                    match = re.search(r'=\s*([^#\n]+)', norm_p_line)
                    if match:
                        filled_text = match.group(1).strip()
                
                filled_answers.append({
                    'cell_index': i,
                    'line_index': j,
                    'blank_index': b_idx,
                    'practice_line': p_line.strip(),
                    'filled_answer': filled_text.strip() if filled_text else None,
                    'before': before_raw.strip(),
                    'after': after_raw.strip()
                })
                
                prev_end = blank.end()
    
    return filled_answers


def normalize_code(code: str) -> str:
    """
    标准化代码：统一引号和空格，用于对比
    
    规则：
    1. 单引号转双引号
    2. 去除所有空格（除了字符串内部的空格）
    3. 去除注释行（#开头的行）
    """
    lines = code.split('\n')
    # 去除注释行和空行
    code_lines = [line for line in lines if not line.strip().startswith('#') and line.strip()]
    
    # 合并所有行
    normalized = '\n'.join(code_lines)
    
    # 统一引号：单引号转双引号
    normalized = normalized.replace("'", '"')
    
    # 去除所有空格（除了字符串内部的空格）
    # 先保护字符串内部的空格
    import re
    # 匹配双引号字符串
    def protect_string_spaces(match):
        s = match.group()
        return s.replace(' ', '\x00')  # 用null字符临时替换空格
    
    normalized = re.sub(r'"[^"]*"', protect_string_spaces, normalized)
    # 去除所有空格
    normalized = normalized.replace(' ', '')
    # 恢复字符串内部的空格
    normalized = normalized.replace('\x00', ' ')
    
    return normalized.strip()


def compare_fill_answers(practice_path: Path, template_path: Path, answer_path: Path) -> List[Dict]:
    """
    对比填空答案是否正确（整单元格精确对比）
    
    规则：
    1. 单双引号差异不算错误
    2. 空格差异不算错误
    3. 注释行（#开头）会被忽略
    4. 其他必须完全一样
    5. 不能增加额外行（除了注释行）
    6. 自动跳过带 auto-init-execution-logger 标签的单元格（日志初始化Cell）
    """
    answer_nb = load_notebook(answer_path)
    practice_nb = load_notebook(practice_path)
    
    if not answer_nb or not practice_nb:
        return []
    
    differences = []
    
    # 过滤掉自动注入的日志初始化Cell
    def is_auto_init_cell(cell):
        tags = cell.get('metadata', {}).get('tags', [])
        return 'auto-init-execution-logger' in tags
    
    answer_cells = [c for c in answer_nb.get('cells', []) if not is_auto_init_cell(c)]
    practice_cells = [c for c in practice_nb.get('cells', []) if not is_auto_init_cell(c)]
    
    for i, (a_cell, p_cell) in enumerate(zip(answer_cells, practice_cells)):
        if a_cell.get('cell_type') != 'code':
            continue
        
        a_source = ''.join(a_cell.get('source', []))
        p_source = ''.join(p_cell.get('source', []))
        
        # 标准化后对比
        a_normalized = normalize_code(a_source)
        p_normalized = normalize_code(p_source)
        
        if a_normalized != p_normalized:
            # 找出具体的差异行
            a_lines = [line for line in a_source.split('\n') if not line.strip().startswith('#') and line.strip()]
            p_lines = [line for line in p_source.split('\n') if not line.strip().startswith('#') and line.strip()]
            
            # 检查行数是否一致
            if len(a_lines) != len(p_lines):
                differences.append({
                    'cell_index': i,
                    'type': 'line_count_mismatch',
                    'answer_lines': len(a_lines),
                    'practice_lines': len(p_lines),
                    'description': f'答案有{len(a_lines)}行代码，你的代码有{len(p_lines)}行（不能增加或删除代码行，注释行除外）'
                })
            else:
                # 逐行对比
                for j, (a_line, p_line) in enumerate(zip(a_lines, p_lines)):
                    if normalize_code(a_line) != normalize_code(p_line):
                        differences.append({
                            'cell_index': i,
                            'line_index': j,
                            'type': 'line_mismatch',
                            'answer_line': a_line.strip(),
                            'practice_line': p_line.strip(),
                            'description': f'第{j+1}行不匹配'
                        })
    
    return differences


def extract_outputs(nb: Dict) -> List[Dict]:
    """
    提取所有输出，跳过自动初始化的日志Cell
    
    修复：支持 text/plain、text/html（DataFrame样式化输出）、image/png（可视化）
    """
    outputs = []
    for cell in nb.get('cells', []):
        # 跳过自动初始化的日志Cell
        if is_auto_init_cell(cell):
            continue
        if cell.get('cell_type') == 'code':
            cell_outputs = []
            for output in cell.get('outputs', []):
                output_data = {}
                if output.get('output_type') == 'stream':
                    output_data['text'] = ''.join(output.get('text', []))
                    output_data['type'] = 'text'
                elif output.get('output_type') == 'execute_result':
                    data = output.get('data', {})
                    # 优先级：text/html > text/plain（DataFrame 优先用 HTML）
                    if 'text/html' in data:
                        # 剥离 HTML 标签，只保留文本内容
                        html_content = ''.join(data['text/html'])
                        output_data['text'] = _strip_html_tags(html_content)
                        output_data['type'] = 'html'
                        output_data['html_raw'] = html_content
                    elif 'text/plain' in data:
                        output_data['text'] = str(data['text/plain'])
                        output_data['type'] = 'text'
                    
                    # 如果有图片（Matplotlib 可视化），计算哈希
                    if 'image/png' in data:
                        import base64
                        import hashlib
                        png_b64 = data['image/png']
                        if isinstance(png_b64, list):
                            png_b64 = ''.join(png_b64)
                        png_bytes = base64.b64decode(png_b64)
                        img_hash = hashlib.md5(png_bytes).hexdigest()
                        output_data['image_hash'] = img_hash
                        output_data['type'] = 'image'
                        # 如果没有文本，使用哈希作为代表
                        if 'text' not in output_data:
                            output_data['text'] = f'[image:{img_hash[:8]}]'
                
                cell_outputs.append(output_data)
            outputs.append(cell_outputs)
    return outputs


def _strip_html_tags(html: str) -> str:
    """剥离 HTML 标签，保留文本内容"""
    import re
    # 移除 <style> 和 <script> 块
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def compare_outputs(practice_outputs: List[Dict], answer_outputs: List[Dict]) -> List[Dict]:
    """
    对比执行结果
    
    修复：支持图片哈希对比、HTML文本对比
    """
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
        
        for j, (p_data, a_data) in enumerate(zip(p_out, a_out)):
            p_text = p_data.get('text', '')
            a_text = a_data.get('text', '')
            
            # 图片类型：优先用哈希对比
            if p_data.get('type') == 'image' and a_data.get('type') == 'image':
                p_hash = p_data.get('image_hash')
                a_hash = a_data.get('image_hash')
                if p_hash and a_hash:
                    if p_hash != a_hash:
                        differences.append({
                            'cell': i,
                            'output_index': j,
                            'type': 'image_mismatch',
                            'practice_hash': p_hash,
                            'answer_hash': a_hash,
                            'description': '图片内容不匹配'
                        })
                    continue
            
            # 文本对比
            if p_text.strip() != a_text.strip():
                similarity = difflib.SequenceMatcher(None, p_text.strip(), a_text.strip()).ratio()
                if similarity < 0.95:
                    differences.append({
                        'cell': i,
                        'output_index': j,
                        'type': 'output_mismatch',
                        'similarity': similarity,
                        'practice': p_text[:200],
                        'answer': a_text[:200]
                    })
    
    return differences


def check_implementation_details(practice_path: Path, answer_path: Path) -> List[Dict]:
    """
    检查实现细节：关键函数、参数使用是否正确
    
    例如：
    - 是否使用了正确的函数（pd.cut vs pd.qcut）
    - 参数是否正确（bins, labels, right等）
    - 变量命名是否一致
    - 关键逻辑错误（如dropna没有赋值）
    """
    answer_nb = load_notebook(answer_path)
    practice_nb = load_notebook(practice_path)
    
    if not answer_nb or not practice_nb:
        return []
    
    issues = []
    
    # 过滤掉自动注入的日志初始化Cell
    def is_auto_init_cell(cell):
        tags = cell.get('metadata', {}).get('tags', [])
        return 'auto-init-execution-logger' in tags
    
    answer_cells = [c for c in answer_nb.get('cells', []) if not is_auto_init_cell(c)]
    practice_cells = [c for c in practice_nb.get('cells', []) if not is_auto_init_cell(c)]
    
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
    
    # 检查关键逻辑错误
    def check_logical_errors(code: str) -> List[Dict]:
        """检查常见的逻辑错误"""
        errors = []
        
        # 检查 dropna() 没有赋值的情况
        if re.search(r"(\w+)\['\w+'\]\.dropna\(\)", code) and not re.search(r"(\w+)\s*=\s*\w+\['\w+'\]\.dropna\(\)", code):
            errors.append({
                'type': 'logical_error',
                'description': 'dropna() 没有赋值回去，不会修改原始DataFrame',
                'code_snippet': re.search(r"\w+\['\w+'\]\.dropna\(\)", code).group()
            })
        
        # 检查 fillna() 没有赋值的情况（排除 inplace=True）
        if re.search(r"(\w+)\['\w+'\]\.fillna\([^)]+\)", code) and not re.search(r"(\w+)\['\w+'\]\s*=\s*\w+\['\w+'\]\.fillna\(", code):
            # 检查是否使用了 inplace=True
            if not re.search(r"fillna\([^)]*inplace\s*=\s*True", code):
                errors.append({
                    'type': 'logical_error',
                    'description': 'fillna() 没有赋值回去，不会修改原始DataFrame',
                    'code_snippet': re.search(r"\w+\['\w+'\]\.fillna\([^)]+\)", code).group()
                })
        
        return errors
    
    for i, (a_cell, p_cell) in enumerate(zip(answer_cells, practice_cells)):
        if a_cell.get('cell_type') != 'code':
            continue
        
        a_source = ''.join(a_cell.get('source', []))
        p_source = ''.join(p_cell.get('source', []))
        
        # 检查逻辑错误
        logical_errors = check_logical_errors(p_source)
        for err in logical_errors:
            issues.append({
                'cell_index': i,
                'type': 'logical_error',
                'description': err['description'],
                'code_snippet': err['code_snippet'],
                'answer_code': a_source[:200],
                'practice_code': p_source[:200]
            })
        
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


def classify_knowledge_point(chapter: str, error_detail: Dict) -> str:
    """
    根据章节和错误详情分类知识点
    
    返回:
        知识点名称，如 'Pandas', 'NumPy', 'Matplotlib', '数据清洗', '数据可视化'
    """
    chapter_to_kp = {
        '1.1': 'Python基础',
        '1.2': 'Python基础',
        '2.1': 'Pandas',
        '2.2': 'Pandas',
        '2.3': '数据清洗',
        '3.1': 'NumPy',
        '3.2': 'NumPy',
        '4.1': '数据可视化',
        '4.2': '数据可视化',
    }
    
    base_chapter = '.'.join(chapter.split('.')[:2])
    knowledge_point = chapter_to_kp.get(base_chapter, '其他')
    
    error_type = error_detail.get('type', '')
    if 'fillna' in str(error_detail) or 'merge' in str(error_detail) or 'groupby' in str(error_detail):
        knowledge_point = 'Pandas'
    elif 'np.where' in str(error_detail) or 'np.array' in str(error_detail):
        knowledge_point = 'NumPy'
    elif 'plot' in str(error_detail) or 'matplotlib' in str(error_detail):
        knowledge_point = '数据可视化'
    
    return knowledge_point


def extract_chapter_from_path(practice_path: Path) -> str:
    """
    从文件路径中提取章节号
    
    支持两种模式：
    1. 旧模式：2.1.1_practice_202608052138.ipynb → 2.1.1
    2. manifest.json：从同目录的manifest.json中读取chapter
    
    参数:
        practice_path: 练习文件路径
    
    返回:
        章节号字符串
    """
    # 尝试从文件名提取（旧模式）
    if '_practice_' in practice_path.name:
        return practice_path.name.split('_practice_')[0]
    
    # 尝试从manifest.json读取
    manifest_path = practice_path.parent / f'{practice_path.stem}_manifest.json'
    if not manifest_path.exists():
        # 尝试查找同目录下所有manifest.json
        for manifest in practice_path.parent.glob('*_manifest.json'):
            with open(manifest, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                if metadata.get('practice_file') == str(practice_path):
                    return metadata.get('chapter', 'unknown')
    
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            if 'chapter' in metadata:
                return metadata['chapter']
    
    # 默认返回未知章节
    return 'unknown'


def load_manifest(practice_path: Path) -> Optional[Dict]:
    """
    加载考试manifest.json
    
    参数:
        practice_path: 练习文件路径
    
    返回:
        manifest数据字典
    """
    # 尝试从文件名提取exam_id
    if '_practice_' in practice_path.name:
        exam_id = practice_path.stem  # 例如：2.1.1_practice_202608052138
        manifest_path = practice_path.parent / f'{exam_id}_manifest.json'
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    # 尝试查找同目录下所有manifest.json
    for manifest in practice_path.parent.glob('*_manifest.json'):
        with open(manifest, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            if metadata.get('practice_file') == str(practice_path):
                return metadata
    
    return None


def find_execution_log(practice_path: Path) -> Optional[Path]:
    """查找与练习文件对应的execution_log.json"""
    practice_name = practice_path.stem  # 不带扩展名的文件名
    
    # 尝试在同目录查找（旧架构）
    log_path = practice_path.parent / f'{practice_name}_execution_log.json'
    if log_path.exists():
        return log_path
    
    # 尝试在Session目录查找（兼容旧架构）
    session_dir = practice_path.parent
    if session_dir.name.startswith('20') and 'chapter' in session_dir.name:
        log_path = session_dir / 'execution_log.json'
        if log_path.exists():
            return log_path
    
    # 支持新架构：logs/execution_log.json
    if session_dir.name.startswith('20') and 'chapter' in session_dir.name:
        log_path = session_dir / 'logs' / 'execution_log.json'
        if log_path.exists():
            return log_path
    
    # 如果 practice_path 在 workspace/ 下，尝试上一级
    if practice_path.parent.name == 'workspace':
        session_dir = practice_path.parent.parent
        log_path = session_dir / 'logs' / 'execution_log.json'
        if log_path.exists():
            return log_path
    
    return None


def match_session_by_timestamp(practice_path: Path, sessions: Dict[int, List[str]]) -> Optional[int]:
    """
    通过时间戳匹配练习文件到IPython session
    
    策略：
    1. 从文件名提取时间戳
    2. 从execution_log.json获取start_time
    3. 找到最接近该时间的session（IPython session是顺序递增的）
    
    返回:
        session_id 或 None
    """
    import re
    import json
    from datetime import datetime
    
    # 策略1：从execution_log.json获取start_time
    practice_name = practice_path.stem
    log_path = practice_path.parent / f'{practice_name}_execution_log.json'
    
    target_time = None
    
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                if 'session_start' in log_data:
                    target_time = datetime.fromisoformat(log_data['session_start'])
        except Exception:
            pass
    
    # 策略2：从文件名提取时间戳
    if not target_time:
        match = re.search(r'practice_(\d{12})', practice_path.name)
        if match:
            timestamp_str = match.group(1)
            try:
                target_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M')
            except Exception:
                pass
    
    if not target_time:
        return None
    
    # IPython的session ID是顺序递增的，找到最接近target_time的session
    # 由于我们无法直接获取session的时间，我们假设最近的session就是目标session
    # 这里我们返回最大的session_id（最新的session）
    if sessions:
        return max(sessions.keys())
    
    return None


def analyze_ipython_history_for_practice(practice_path: Path, chapter: str) -> Optional[Dict]:
    """
    分析IPython历史命令，对比答题过程
    
    参数:
        practice_path: 练习文件路径
        chapter: 章节号
    
    返回:
        历史分析结果字典，如果无法分析则返回None
    """
    import os
    import sqlite3
    from collections import defaultdict
    
    # 加载IPython历史
    history_path = os.path.expanduser('~/.ipython/profile_default/history.sqlite')
    if not os.path.exists(history_path):
        return None
    
    try:
        conn = sqlite3.connect(history_path)
        cur = conn.cursor()
        cur.execute('SELECT session, line, source FROM history ORDER BY session, line')
        history_rows = cur.fetchall()
        conn.close()
    except Exception:
        return None
    
    # 按session分组
    sessions = defaultdict(list)
    for session, line, source in history_rows:
        if source.strip():
            sessions[session].append(source.strip())
    
    # 根据章节关键词匹配session
    chapter_keywords = {
        # 1.1.x 章节
        '1.1.1': ['patient_data', 'RiskLevel', 'BMI', 'AgeGroup', 'DaysInHospital'],
        '1.1.2': ['sensor_data', 'SensorType', 'Temperature', 'Humidity'],
        '1.1.3': ['credit_data', 'CreditScore', 'Income', 'LoanAmount'],
        '1.1.4': ['user_behavior', 'PurchaseAmount', 'Gender', 'Age'],
        '1.1.5': ['vehicle_traffic', 'Speed', 'VehicleType'],
        
        # 2.1.x 章节
        '2.1.1': ['auto-mpg', 'horsepower', 'mpg', 'StandardScaler', 'train_test_split'],
        '2.1.2': ['大学生低碳', '低碳行为积极性', '月生活费', 'pd.read_excel'],
        '2.1.3': ['finance', 'CreditScore', 'Income', 'LoanAmount'],
        '2.1.4': ['medical_data', '就诊日期', '诊断日期', '诊断延迟', '病程', '治疗结果', '疾病类型'],
        '2.1.5': ['健康咨询', '客户数据集', 'CustomerID', 'Purchase', 'Membership'],
        
        # 2.2.x 章节
        '2.2.1': ['finance', 'XGBoost', 'RandomForest', 'train_test_split'],
        '2.2.2': ['auto-mpg', 'RandomForest', 'StandardScaler', 'train_test_split'],
        '2.2.3': ['fitness analysis', 'RandomForest', 'XGBoost', 'Your gender', 'daily_steps'],
        '2.2.4': ['大学生低碳', 'XGBoost', 'train_test_split', '低碳行为积极性'],
        '2.2.5': ['fitness analysis', 'DecisionTree', 'daily_steps', 'Your gender'],
        
        # 3.x 章节
        '3.2.1': ['resnet', 'onnxruntime', 'ort.InferenceSession', 'softmax', 'top5'],
        '3.2.2': ['mnist', 'onnxruntime', 'ort.InferenceSession'],
        '3.2.3': ['emotion-ferplus', 'onnxruntime', 'emotion'],
        '3.2.4': ['flower-detection', 'onnxruntime', 'flower'],
        '3.2.5': ['voc-model-labels', 'version-RFB-320', 'cv2.imread', 'box_utils'],
    }
    
    keywords = chapter_keywords.get(chapter, [])
    matched_session = None
    
    # 策略1：通过关键词匹配
    for session_id, commands in sessions.items():
        full_text = ' '.join(commands)
        if any(kw in full_text for kw in keywords):
            matched_session = session_id
            break
    
    # 策略2：如果关键词匹配失败，尝试通过时间戳匹配
    if not matched_session:
        matched_session = match_session_by_timestamp(practice_path, sessions)
    
    if not matched_session:
        return None
    
    # 分析该session的命令
    commands = sessions[matched_session]
    
    analysis = {
        'session_id': matched_session,
        'total_commands': len(commands),
        'key_commands': [],
        'error_patterns': [],
        'correction_count': 0,
        'suggestions': [],
    }
    
    # 提取关键命令
    key_patterns = [
        (r'groupby', '分组操作'),
        (r'isin\(', '布尔过滤'),
        (r'dropna', '缺失值处理'),
        (r'between\(', '区间判断'),
        (r'value_counts', '计数统计'),
        (r'agg\(', '聚合操作'),
        (r'np\.where', '条件替换'),
        (r'pd\.cut', '区间分组'),
        (r'fillna', '缺失值填充'),
        (r'read_csv', '数据读取'),
    ]
    
    for cmd in commands:
        for pattern, desc in key_patterns:
            if re.search(pattern, cmd):
                analysis['key_commands'].append({
                    'command': cmd[:100],
                    'type': desc,
                })
    
    # 检测错误模式
    error_patterns = [
        (r'pd\.dropna\(\)', '错误：应写为 data = data.dropna()'),
        (r'\.bewteen\(', '拼写错误：应为 .between()'),
        (r'data\.length', '错误：应使用 len(data)'),
        (r'\|\|', '错误：Pandas中应使用 | 而不是 ||'),
        (r"data\['\w+'\]\['\w+','\w+'\]", '错误：应使用 .isin([...])'),
    ]
    
    for cmd in commands:
        for pattern, desc in error_patterns:
            if re.search(pattern, cmd):
                analysis['error_patterns'].append({
                    'command': cmd[:100],
                    'error_type': desc,
                })
    
    # 计算修正次数
    command_groups = defaultdict(int)
    for cmd in commands:
        normalized = re.sub(r'\s+', ' ', cmd).replace("'", '"').strip()[:50]
        command_groups[normalized] += 1
    
    analysis['correction_count'] = sum(1 for count in command_groups.values() if count > 1)
    
    # 生成建议
    if any('pd.dropna()' in cmd for cmd in commands):
        analysis['suggestions'].append('缺失值处理：应写为 data = data.dropna()，不要把 dropna 写成 pd.dropna()')
    
    if any('isin(' in cmd for cmd in commands):
        analysis['suggestions'].append('布尔过滤：先定义 mask = data[col].isin([...])，再用 data[mask] 做筛选')
    
    if any('between(' in cmd for cmd in commands):
        analysis['suggestions'].append('区间判断：检查列名与拼写，常见写法是 data[col].between(18, 70)')
    
    if any('groupby' in cmd and 'agg' in cmd for cmd in commands):
        analysis['suggestions'].append('分组聚合：优先用 groupby(...).agg({...}) 或 groupby(...)[col].agg([...])')
    
    if any('pd.cut' in cmd for cmd in commands):
        analysis['suggestions'].append('区间分组：先定义 bins 和 labels，再用 pd.cut() 分组')
    
    return analysis


def count_blanks_in_template(template_path: Path) -> int:
    """统计模板中填空的总数量"""
    nb = load_notebook(template_path)
    if not nb:
        return 0
    
    count = 0
    for cell in nb.get('cells', []):
        if cell.get('cell_type') != 'code':
            continue
        source = ''.join(cell.get('source', []))
        count += len(re.findall(r'_{3,}', source))
    
    return count


def is_auto_init_cell(cell: Dict) -> bool:
    """判断是否是自动注入的日志初始化Cell"""
    tags = cell.get('metadata', {}).get('tags', [])
    if 'auto-init-execution-logger' in tags:
        return True
    source = ''.join(cell.get('source', []))
    if 'ExecutionLogger' in source and '自动初始化' in source:
        return True
    return False


def align_cells_to_practice(template_nb: Dict, practice_nb: Dict) -> Dict[int, int]:
    """
    对齐模板和练习文件的Cell索引
    
    返回: {template_cell_index: practice_cell_index}
    """
    mapping = {}
    
    template_cells = [c for c in template_nb.get('cells', []) if not is_auto_init_cell(c) and c.get('cell_type') == 'code']
    
    practice_code_cells = []
    for idx, c in enumerate(practice_nb.get('cells', [])):
        if not is_auto_init_cell(c) and c.get('cell_type') == 'code':
            practice_code_cells.append((idx, c))
    
    for t_idx, t_cell in enumerate(template_cells):
        t_id = t_cell.get('id')
        t_source = ''.join(t_cell.get('source', []))[:50]
        
        matched = False
        for p_idx, p_cell in practice_code_cells:
            p_id = p_cell.get('id')
            p_source = ''.join(p_cell.get('source', []))[:50]
            
            if t_id and t_id == p_id:
                mapping[t_idx] = p_idx
                matched = True
                break
            
            if t_source and t_source in p_source:
                mapping[t_idx] = p_idx
                matched = True
                break
        
        if not matched:
            mapping[t_idx] = t_idx
    
    return mapping


def score_with_ast_schema(schema: Dict, practice_path: Path) -> Dict:
    """
    基于 AST 评分标准对练习文件进行验证（混合模式）
    
    验证层次：
    1. AST 检查：是否使用了正确的函数/方法
    2. 关键参数检查：文件名、变量名、关键参数是否正确
    
    参数:
        schema: AST 评分标准字典
        practice_path: 练习文件路径
    
    返回:
        {
            'total_score': 40,
            'earned_score': 38,
            'percentage': 95.0,
            'details': [...],
            'errors': [...],
        }
    """
    practice_nb = load_notebook(practice_path)
    if not practice_nb:
        return {
            'total_score': schema['exam']['total_score'],
            'earned_score': 0,
            'percentage': 0,
            'details': [],
            'errors': [{'type': 'file_load_error', 'message': '无法加载练习文件'}],
        }
    
    details = []
    errors = []
    earned_score = 0
    total_score = schema['exam']['total_score']
    
    for item in schema['items']:
        item_id = item['id']
        score = item['score']
        description = item['description']
        validators = item.get('validators', {})
        practice_rules = validators.get('practice', {}).get('rules', [])
        metadata = item.get('metadata', {})
        
        # 获取对应的 Cell
        cell_index = metadata.get('cell_index', 0)
        
        # 跳过自动初始化的 Cell
        cells = [c for c in practice_nb.get('cells', []) if not is_auto_init_cell(c) and c.get('cell_type') == 'code']
        
        if cell_index >= len(cells):
            errors.append({
                'type': 'cell_not_found',
                'item_id': item_id,
                'description': description,
                'deduction': score,
            })
            continue
        
        cell = cells[cell_index]
        source = ''.join(cell.get('source', []))
        
        # 验证规则
        all_passed = True
        failed_rules = []
        
        for rule in practice_rules:
            if 'must_call' in rule:
                # must_call 格式: "pd.read_csv read_csv vehicle_t"
                keywords = rule['must_call'].split()
                for keyword in keywords:
                    if keyword.lower() not in source.lower():
                        all_passed = False
                        failed_rules.append(f"缺少关键字: {keyword}")
                        break
        
        # 关键参数检查：从模板中提取期望的关键参数
        if all_passed and 'template' in metadata:
            template = metadata['template']
            # 提取模板中的关键参数（如文件名、列名等）
            # 匹配引号中的内容
            import re
            quoted_strings = re.findall(r'["\']([^"\']+)["\']', template)
            # 匹配方括号中的列名
            bracket_contents = re.findall(r"\['([^']+)'\]", template)
            
            # 检查关键参数
            critical_params = quoted_strings + bracket_contents
            for param in critical_params:
                # 跳过占位符
                if '_' in param and all(c == '_' for c in param.replace('_', '')):
                    continue
                # 检查参数是否在代码中
                if param.lower() not in source.lower():
                    all_passed = False
                    failed_rules.append(f"缺少关键参数: {param}")
                    break
        
        if all_passed:
            earned_score += score
        
        detail = {
            'item_id': item_id,
            'description': description,
            'max_score': score,
            'earned_score': score if all_passed else 0,
            'correct': all_passed,
            'type': 'ast_check',
        }
        details.append(detail)
        
        if not all_passed:
            errors.append({
                'type': 'ast_check_failed',
                'item_id': item_id,
                'description': description,
                'deduction': score,
                'failed_rules': failed_rules,
                'knowledge_point': 'api_call',
            })
    
    percentage = (earned_score / total_score * 100) if total_score > 0 else 0
    
    return {
        'total_score': total_score,
        'earned_score': earned_score,
        'percentage': round(percentage, 1),
        'details': details,
        'errors': errors,
    }


def score_with_schema(schema: Dict, practice_path: Path) -> Dict:
    """
    基于评分标准对练习文件进行严格评分
    
    参数:
        schema: 评分标准字典
        practice_path: 练习文件路径
    
    返回:
        {
            'total_score': 22,
            'earned_score': 18,
            'percentage': 81.8,
            'details': [...],
            'errors': [...],
        }
    """
    practice_nb = load_notebook(practice_path)
    if not practice_nb:
        return {
            'total_score': schema['total_score'],
            'earned_score': 0,
            'percentage': 0,
            'details': [],
            'errors': [{'type': 'file_load_error', 'message': '无法加载练习文件'}],
        }
    
    template_path = find_template_file(schema['chapter'])
    template_nb = load_notebook(template_path) if template_path else None
    
    cell_mapping = {}
    if template_nb:
        cell_mapping = align_cells_to_practice(template_nb, practice_nb)
    
    details = []
    errors = []
    earned_score = 0
    
    for item in schema['items']:
        template_cell_idx = item['cell_index']
        line_idx = item['line_index']
        
        practice_cell_idx = cell_mapping.get(template_cell_idx, template_cell_idx)
        
        user_answer = ''
        correct = False
        
        if practice_cell_idx < len(practice_nb.get('cells', [])):
            cell = practice_nb['cells'][practice_cell_idx]
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                lines = source.split('\n')
                if line_idx < len(lines):
                    user_answer = lines[line_idx].strip()
        
        if user_answer:
            correct_answer = item.get('answer', '')
            if correct_answer:
                user_norm = normalize_code(user_answer)
                correct_norm = normalize_code(correct_answer)
                correct = (user_norm == correct_norm)
        
        if correct:
            earned_score += item['score']
        
        detail = {
            'item_id': item['id'],
            'description': item['description'],
            'max_score': item['score'],
            'earned_score': item['score'] if correct else 0,
            'correct': correct,
            'user_answer': user_answer,
            'correct_answer': item.get('answer', ''),
            'type': item.get('type', 'unknown'),
        }
        details.append(detail)
        
        if not correct:
            errors.append({
                'type': 'schema_fill_incorrect',
                'item_id': item['id'],
                'description': item['description'],
                'deduction': item['score'],
                'user_answer': user_answer,
                'correct_answer': item.get('answer', ''),
                'knowledge_point': item.get('type', 'unknown'),
            })
    
    total_score = schema['total_score']
    percentage = (earned_score / total_score * 100) if total_score > 0 else 0
    
    return {
        'total_score': total_score,
        'earned_score': earned_score,
        'percentage': round(percentage, 1),
        'details': details,
        'errors': errors,
    }


def validate_single_practice(practice_path: Path, compare_mode: str = 'all', detailed: bool = True, start_time: Optional[str] = None, chapter: Optional[str] = None, audit_process: bool = False, analyze_history: bool = False, check_fill: bool = True, check_impl: bool = True, check_output: bool = True) -> Dict:
    """
    验证单个练习文件
    
    参数:
        practice_path: 练习文件路径
        compare_mode: 对比模式（已弃用，使用 check_fill/check_impl/check_output）
        detailed: 是否生成详细信息
        start_time: 考试开始时间（ISO格式，可选）
        chapter: 章节号（可选，优先使用此参数）
        audit_process: 是否启用回溯审计（分析中间错误）
        analyze_history: 是否分析IPython历史命令
        check_fill: 是否检查填空（默认开启）
        check_impl: 是否检查实现（默认开启）
        check_output: 是否检查输出（默认开启）
    
    返回:
        验证结果字典
    """
    # 优先使用传入的 chapter 参数，否则从路径提取
    if chapter is None:
        chapter = extract_chapter_from_path(practice_path)
    
    if not start_time:
        manifest = load_manifest(practice_path)
        if manifest and 'start_time' in manifest:
            start_time = manifest['start_time']
    
    template_path = find_template_file(chapter)
    total_blanks = count_blanks_in_template(template_path) if template_path else 0
    
    if total_blanks > 0:
        score_per_blank = 100.0 / total_blanks
    else:
        score_per_blank = 100.0
    
    scoring_schema = load_scoring_schema(chapter)
    use_schema = scoring_schema is not None
    
    # 判断是否使用 AST 验证
    is_ast_schema = use_schema and 'exam' in scoring_schema and 'items' in scoring_schema and 'validators' in scoring_schema['items'][0]
    
    result = {
        'file': str(practice_path),
        'chapter': chapter,
        'errors': [],
        'warnings': [],
        'score': 100,
        'total_score': 100,
        'total_blanks': total_blanks,
        'score_per_blank': round(score_per_blank, 2),
        'fill_comparison': [],
        'implementation_comparison': [],
        'result_comparison': [],
        'knowledge_points': {},
        'start_time': start_time,
        'end_time': datetime.now().isoformat(),
        'process_audit': None,
        'ipython_history': None,
        'scoring_mode': 'ast' if is_ast_schema else ('schema' if use_schema else 'dynamic'),
        'schema_details': [],
    }
    
    if use_schema:
        if is_ast_schema:
            logger.info(f"📋 使用 AST 评分标准: {chapter} (总分: {scoring_schema['exam']['total_score']})")
            schema_result = score_with_ast_schema(scoring_schema, practice_path)
        else:
            logger.info(f"📋 使用普通评分标准: {chapter} (总分: {scoring_schema['total_score']})")
            schema_result = score_with_schema(scoring_schema, practice_path)
        
        result['total_score'] = schema_result['total_score']
        result['score'] = schema_result['earned_score']
        result['schema_details'] = schema_result['details']
        
        for err in schema_result['errors']:
            result['errors'].append(err)
        
        blanks = check_unfilled_blanks(practice_path)
        if blanks:
            error_detail = {
                'type': 'unfilled_blanks',
                'count': len(blanks),
                'details': blanks,
                'deduction': len(blanks),
                'knowledge_point': classify_knowledge_point(chapter, {'type': 'unfilled'}),
                'topic': '未填空',
            }
            result['errors'].append(error_detail)
            result['score'] -= error_detail['deduction']
        
        if check_impl or compare_mode in ['implementation', 'both', 'all']:
            answer_path = find_answer_file(chapter)
            if answer_path:
                impl_issues = check_implementation_details(practice_path, answer_path)
                result['implementation_comparison'] = impl_issues
                if impl_issues:
                    warning_detail = {
                        'type': 'implementation_differs',
                        'count': len(impl_issues),
                        'details': impl_issues,
                        'deduction': len(impl_issues) * 3,
                        'knowledge_point': classify_knowledge_point(chapter, impl_issues[0]),
                        'topic': '实现差异',
                    }
                    result['warnings'].append(warning_detail)
                    result['score'] -= warning_detail['deduction']
        
        if check_output or compare_mode in ['result', 'both', 'all']:
            answer_path = find_answer_file(chapter)
            if answer_path:
                practice_nb = load_notebook(practice_path)
                answer_nb = load_notebook(answer_path)
                if practice_nb and answer_nb:
                    p_outputs = extract_outputs(practice_nb)
                    a_outputs = extract_outputs(answer_nb)
                    output_diffs = compare_outputs(p_outputs, a_outputs)
                    result['result_comparison'] = output_diffs
                    if output_diffs:
                        error_detail = {
                            'type': 'output_mismatch',
                            'count': len(output_diffs),
                            'details': output_diffs,
                            'deduction': len(output_diffs) * 10,
                            'knowledge_point': classify_knowledge_point(chapter, output_diffs[0]),
                            'topic': '输出不匹配',
                        }
                        result['errors'].append(error_detail)
                        result['score'] -= error_detail['deduction']
        
        result['score'] = max(0, result['score'])
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(result['end_time'])
            result['duration_minutes'] = int((end_dt - start_dt).total_seconds() / 60)
        
        return result
    
    blanks = check_unfilled_blanks(practice_path)
    if blanks:
        deduction = len(blanks) * score_per_blank
        error_detail = {
            'type': 'unfilled_blanks',
            'count': len(blanks),
            'details': blanks,
            'deduction': round(deduction, 2),
            'knowledge_point': classify_knowledge_point(chapter, {'type': 'unfilled'}),
            'topic': '未填空',
        }
        result['errors'].append(error_detail)
        result['score'] -= error_detail['deduction']
    
    answer_path = find_answer_file(chapter)
    
    if answer_path and template_path:
        practice_nb = load_notebook(practice_path)
        answer_nb = load_notebook(answer_path)
        
        if practice_nb and answer_nb:
            if check_fill or compare_mode in ['fill', 'both', 'all']:
                fill_diffs = compare_fill_answers(practice_path, template_path, answer_path)
                result['fill_comparison'] = fill_diffs
                if fill_diffs:
                    deduction = len(fill_diffs) * score_per_blank
                    error_detail = {
                        'type': 'fill_incorrect',
                        'count': len(fill_diffs),
                        'details': fill_diffs,
                        'deduction': round(deduction, 2),
                        'knowledge_point': classify_knowledge_point(chapter, fill_diffs[0]),
                        'topic': '填空错误',
                    }
                    result['errors'].append(error_detail)
                    result['score'] -= error_detail['deduction']
            
            if check_impl or compare_mode in ['implementation', 'both', 'all']:
                impl_issues = check_implementation_details(practice_path, answer_path)
                result['implementation_comparison'] = impl_issues
                if impl_issues:
                    warning_detail = {
                        'type': 'implementation_differs',
                        'count': len(impl_issues),
                        'details': impl_issues,
                        'deduction': len(impl_issues) * 3,
                        'knowledge_point': classify_knowledge_point(chapter, impl_issues[0]),
                        'topic': '实现差异',
                    }
                    result['warnings'].append(warning_detail)
                    result['score'] -= warning_detail['deduction']
            
            # 执行结果对比
            if check_output or compare_mode in ['result', 'both', 'all']:
                p_outputs = extract_outputs(practice_nb)
                a_outputs = extract_outputs(answer_nb)
                output_diffs = compare_outputs(p_outputs, a_outputs)
                result['result_comparison'] = output_diffs
                if output_diffs:
                    error_detail = {
                        'type': 'output_mismatch',
                        'count': len(output_diffs),
                        'details': output_diffs,
                        'deduction': len(output_diffs) * 10,
                        'knowledge_point': classify_knowledge_point(chapter, output_diffs[0]),
                        'topic': '输出不匹配',
                    }
                    result['errors'].append(error_detail)
                    result['score'] -= error_detail['deduction']
    
    # 3. 回溯审计（如果启用）
    if audit_process:
        import sys
        sys.path.insert(0, str(ROOT))
        from process_auditor import ProcessAuditor
        
        # 查找execution_log文件
        execution_log_path = find_execution_log(practice_path)
        
        if execution_log_path and execution_log_path.exists():
            logger.info(f"🔍 启用回溯审计: {execution_log_path.name}")
            auditor = ProcessAuditor(execution_log_path, practice_path, answer_path if answer_path else None)
            audit_result = auditor.audit()
            result['process_audit'] = audit_result
            
            # 应用过程罚分
            if audit_result['process_penalty'] > 0:
                result['score'] -= audit_result['process_penalty']
                logger.info(f"   ⚠️ 过程罚分: -{audit_result['process_penalty']}分 (检测到{audit_result['error_attempts']}次错误尝试)")
            else:
                logger.info(f"   ✅ 过程完美，无罚分")
        else:
            logger.info(f"   ⚠️ 未找到execution_log文件，跳过回溯审计")
    
    # 4. IPython历史命令分析（如果启用）
    if analyze_history:
        logger.info(f"📜 分析IPython历史命令...")
        history_analysis = analyze_ipython_history_for_practice(practice_path, chapter)
        result['ipython_history'] = history_analysis
        
        if history_analysis:
            logger.info(f"   匹配到session: {history_analysis['session_id']}")
            logger.info(f"   命令数: {history_analysis['total_commands']}")
            logger.info(f"   修正次数: {history_analysis['correction_count']}")
            if history_analysis['error_patterns']:
                logger.info(f"   错误模式: {len(history_analysis['error_patterns'])}个")
            if history_analysis['suggestions']:
                logger.info(f"   建议: {len(history_analysis['suggestions'])}条")
        else:
            logger.info(f"   ⚠️ 未匹配到IPython session")
    
    # 确保分数不低于0
    result['score'] = max(0, result['score'])
    
    # 计算耗时
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(result['end_time'])
        result['duration_minutes'] = int((end_dt - start_dt).total_seconds() / 60)
    
    return result


def generate_json_report(result: Dict, output_path: Path):
    """生成结构化JSON报告（用于Session）"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"JSON报告已保存: {output_path}")


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
        
        # 添加IPython历史命令分析
        if r.get('ipython_history'):
            hist = r['ipython_history']
            report.append("#### 📜 IPython历史命令分析\n")
            report.append(f"- **Session ID**: {hist['session_id']}\n")
            report.append(f"- **命令数**: {hist['total_commands']}\n")
            report.append(f"- **修正次数**: {hist['correction_count']}\n")
            
            if hist['error_patterns']:
                report.append("**错误模式:**\n")
                for err in hist['error_patterns'][:5]:
                    report.append(f"- {err['error_type']}")
                    report.append(f"  - `{err['command']}`\n")
            
            if hist['suggestions']:
                report.append("**建议:**\n")
                for sug in hist['suggestions']:
                    report.append(f"- {sug}\n")
        
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
        
        # 显示实际总分（AST 总分或 100）
        actual_total = r.get('total_score', 100)
        if actual_total != 100:
            print(f"💯 得分: {r['score']}/{actual_total} (换算: {r['score']/actual_total*100:.0f}%)")
        else:
            print(f"💯 得分: {r['score']}/100")
        
        # 显示每道题的得分详情
        if r.get('schema_details'):
            print(f"\n📋 评分详情:")
            for detail in r['schema_details']:
                status = "✅" if detail.get('correct') else "❌"
                print(f"  {status} {detail['item_id']}: {detail['description']} - {detail['earned_score']}/{detail['max_score']}分")
        
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
        
        # 显示IPython历史命令分析
        if r.get('ipython_history'):
            hist = r['ipython_history']
            print(f"\n📜 IPython历史命令分析:")
            print(f"  Session: {hist['session_id']}")
            print(f"  命令数: {hist['total_commands']}")
            print(f"  修正次数: {hist['correction_count']}")
            
            if hist['error_patterns']:
                print(f"\n  ❌ 错误模式 ({len(hist['error_patterns'])}个):")
                for err in hist['error_patterns'][:5]:
                    print(f"    - {err['error_type']}")
                    print(f"      `{err['command']}`")
            
            if hist['suggestions']:
                print(f"\n  💡 建议:")
                for sug in hist['suggestions']:
                    print(f"    - {sug}")
        
        if not r['errors'] and not r['warnings']:
            print(f"\n✅ 完全正确！")
    
    # 汇总统计
    print(f"\n{'='*80}")
    print(f"📈 汇总统计")
    print(f"{'='*80}")
    total = len(results)
    # 修复：使用百分比判断是否满分，而不是固定 100 分
    perfect = sum(1 for r in results if r['score'] == r.get('total_score', 100))
    avg_score = sum(r['score'] for r in results) / total if total > 0 else 0
    avg_percentage = sum(r['score'] / r.get('total_score', 100) * 100 for r in results) / total if total > 0 else 0
    
    print(f"总练习数: {total}")
    print(f"完全正确: {perfect} ({perfect/total*100:.1f}%)")
    print(f"平均分: {avg_score:.1f} (平均百分比: {avg_percentage:.1f}%)")


def resolve_compare_mode(args: argparse.Namespace) -> str:
    """从新的标志位或旧的compare-mode解析对比模式"""
    # 如果使用了新标志位，优先使用
    if args.check_fill or args.check_output or args.check_impl:
        modes = []
        if args.check_fill:
            modes.append('fill')
        if args.check_impl:
            modes.append('implementation')
        if args.check_output:
            modes.append('result')
        if len(modes) == 3:
            return 'all'
        elif len(modes) == 0:
            return 'all'
        elif len(modes) == 1:
            return modes[0]
        else:
            return 'both'
    # 否则使用旧的compare-mode
    return args.compare_mode


def main():
    args = parse_args()
    
    # 解析对比模式
    compare_mode = resolve_compare_mode(args)
    
    # 检查是否是Session模式（兼容旧的sessions/目录）
    if args.session:
        from pathlib import Path as PathLib
        session_dir = PathLib(args.session)
        if not session_dir.exists():
            logger.error(f"Session目录不存在: {session_dir}")
            return
        
        # 支持新架构（workspace/）和旧架构
        practice_path = session_dir / 'workspace' / 'practice.ipynb'
        if not practice_path.exists():
            practice_path = session_dir / 'practice.ipynb'
        
        if not practice_path.exists():
            logger.error(f"练习文件不存在: {practice_path}")
            return
        
        # Session 对象（来自 --session 分支）
        session_id = session_dir.name  # 从路径提取 session_id
        session = SessionFactory(ROOT).load_session(session_id)
        
        # 通过 Session API 获取章节、路径（替代自拼）
        chapter = session.chapter  # 优先使用 Session.metadata.chapter
        if chapter is None:
            # 回退：从 practice_nb_path 所在 session_dir 读取 metadata
            metadata_path = session.session_dir / 'metadata.json'
            if metadata_path.exists():
                import json as json_module
                metadata = json_module.loads(metadata_path.read_text(encoding='utf-8'))
                chapter = metadata.get('chapter')
        
        start_time = None  # 保持旧行为：metadata 无 start_time，不计算 duration_minutes
        
        result = validate_single_practice(
            practice_path,
            compare_mode=compare_mode,
            start_time=start_time,
            chapter=chapter,
            audit_process=args.audit_process,
            analyze_history=args.analyze_history,
            check_fill=args.check_fill,
            check_impl=args.check_impl,
            check_output=args.check_output
        )
        
        # 通过 Session API 保存 report（而不是直接写入 session_dir 根目录）
        session.save_report(result)  # 写入 reports/report.json
        
        # 更新metadata状态（通过 Session API）
        session.update_status('completed')
        
        print_validation_report([result])
        return
    
    if args.file:
        practice_path = Path(args.file)
        if not practice_path.exists():
            logger.error(f"文件不存在: {practice_path}")
            return
        
        result = validate_single_practice(practice_path, compare_mode=compare_mode, audit_process=args.audit_process, analyze_history=args.analyze_history, check_fill=args.check_fill, check_impl=args.check_impl, check_output=args.check_output)
        results = [result]
        
        # 更新manifest.json（如果存在）
        manifest = load_manifest(practice_path)
        if manifest:
            manifest_path = practice_path.parent / f'{practice_path.stem}_manifest.json'
            manifest['status'] = 'completed'
            manifest['score'] = result['score']
            manifest['end_time'] = result['end_time']
            manifest['duration_minutes'] = result.get('duration_minutes')
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            logger.info(f"已更新manifest: {manifest_path.name}")
        
        # 生成result.json（阅卷结果）
        result_path = practice_path.parent / f'{practice_path.stem}_result.json'
        generate_json_report(result, result_path)
        
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
            result = validate_single_practice(pf, compare_mode=compare_mode, audit_process=args.audit_process, analyze_history=args.analyze_history, check_fill=args.check_fill, check_impl=args.check_impl, check_output=args.check_output)
            results.append(result)
            
            # 更新manifest.json（如果存在）
            manifest = load_manifest(pf)
            if manifest:
                manifest_path = pf.parent / f'{pf.stem}_manifest.json'
                manifest['status'] = 'completed'
                manifest['score'] = result['score']
                manifest['end_time'] = result['end_time']
                manifest['duration_minutes'] = result.get('duration_minutes')
                manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            
            # 生成result.json（阅卷结果）
            result_path = pf.parent / f'{pf.stem}_result.json'
            generate_json_report(result, result_path)
    
    print_validation_report(results)
    
    if args.output_report:
        output_path = ROOT / 'reports' / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generate_markdown_report(results, output_path)
    
    if args.output_json:
        for result in results:
            json_path = ROOT / 'reports' / f"{result['chapter']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            generate_json_report(result, json_path)


if __name__ == '__main__':
    main()