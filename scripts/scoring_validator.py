#!/usr/bin/env python3
"""
基于评分标准的验证器（Scoring Schema Validator）

核心功能：
1. 读取 scoring/{chapter}.json 评分标准（支持 v1 和 v2 格式）
2. 对比练习文件中的答案与标准答案
3. 支持考试模式（严格）和练习模式（语义宽松）
4. 生成详细的评分报告

用法:
  # v1 格式（旧版）
  python3 scripts/scoring_validator.py 1.1.1 --file path/to/practice.ipynb
  python3 scripts/scoring_validator.py 1.1.1 --file path/to/practice.ipynb --strict
  
  # v2 格式（新版）
  python3 scripts/scoring_validator.py 2.2.2 --file path/to/practice.ipynb --mode exam
  python3 scripts/scoring_validator.py 2.2.2 --file path/to/practice.ipynb --mode practice
  
  # Session 模式
  python3 scripts/scoring_validator.py --session sessions/2026-08-05-1430-chapter1.1.1
"""
from pathlib import Path
import json
import re
import ast
import argparse
import logging
import traceback
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SCORING_DIR = ROOT / 'scoring'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='基于评分标准的验证器')
    parser.add_argument('chapter', type=str, nargs='?', help='章节号（如 1.1.1）')
    parser.add_argument('--file', type=str, help='练习文件路径')
    parser.add_argument('--session', type=str, help='Session目录路径')
    parser.add_argument('--mode', type=str, choices=['exam', 'practice'], default=None,
                       help='评分模式：exam（严格）或 practice（宽松）。v2 格式专用')
    parser.add_argument('--strict', action='store_true', help='严格模式（v1 格式兼容）')
    parser.add_argument('--output-report', action='store_true', help='生成详细报告')
    return parser.parse_args()


def detect_schema_version(schema: Dict) -> str:
    """
    检测评分标准版本
    
    v1: 扁平结构，有 'chapter' 和 'items'，item 有 'answer' 字段
    v2: 分层结构，有 'exam' 和 'items'，item 有 'validators' 字段
    """
    if 'exam' in schema and 'items' in schema:
        if 'validators' in schema['items'][0]:
            return 'v2'
    return 'v1'


def load_scoring_schema(chapter: str) -> Optional[Dict]:
    """加载评分标准（优先级：_ast > _v2 > 默认）"""
    # 优先级 1: AST 版本
    schema_path = SCORING_DIR / f'{chapter}_ast.json'
    version_hint = 'ast'
    
    # 优先级 2: v2 版本
    if not schema_path.exists():
        schema_path = SCORING_DIR / f'{chapter}_v2.json'
        version_hint = 'v2'
    
    # 优先级 3: 默认版本（v1）
    if not schema_path.exists():
        schema_path = SCORING_DIR / f'{chapter}.json'
        version_hint = 'v1'
    
    if not schema_path.exists():
        logger.error(f"评分标准不存在: {chapter}")
        return None
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    version = detect_schema_version(schema)
    logger.info(f"📋 评分标准版本: {version} ({schema_path.name})")
    
    return schema


def load_notebook(nb_path: Path) -> Optional[Dict]:
    """加载 notebook 文件"""
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取文件失败 {nb_path}: {e}")
        return None


def normalize_code(code: str) -> str:
    """标准化代码（去除多余空格、统一引号等）"""
    code = code.strip()
    code = re.sub(r'\s+', ' ', code)
    code = code.replace("'", '"')
    return code


def normalize_quotes(text: str) -> str:
    """统一引号为双引号（方便比较）"""
    return text.replace("'", '"')


def check_answer_match(user_answer: str, correct_answer: str, strict: bool = False) -> bool:
    """
    检查答案是否匹配（v1 格式）
    
    严格模式：完全一致
    宽松模式：标准化后一致（忽略空格、引号差异）
    """
    if not user_answer or not correct_answer:
        return False
    
    if strict:
        return user_answer.strip() == correct_answer.strip()
    
    return normalize_code(user_answer) == normalize_code(correct_answer)


def is_auto_init_cell(cell: Dict) -> bool:
    """判断是否是自动注入的日志初始化Cell"""
    tags = cell.get('metadata', {}).get('tags', [])
    if 'auto-init' in tags or 'execution-logger' in tags:
        return True
    
    source = ''.join(cell.get('source', []))
    if 'ExecutionLogger' in source and '自动初始化' in source:
        return True
    
    return False


def align_cells(template_nb: Dict, practice_nb: Dict) -> Dict[int, int]:
    """
    对齐模板和练习文件的Cell索引
    
    返回: {template_cell_index: practice_cell_index}
    """
    mapping = {}
    
    template_cells = [c for c in template_nb.get('cells', []) if c.get('cell_type') == 'code']
    practice_cells = practice_nb.get('cells', [])
    
    practice_code_cells = [c for c in practice_cells if c.get('cell_type') == 'code']
    
    for t_idx, t_cell in enumerate(template_cells):
        t_id = t_cell.get('id')
        t_source = ''.join(t_cell.get('source', []))
        
        matched = False
        for p_idx, p_cell in enumerate(practice_cells):
            if p_cell.get('cell_type') != 'code':
                continue
            if is_auto_init_cell(p_cell):
                continue
            
            p_id = p_cell.get('id')
            p_source = ''.join(p_cell.get('source', []))
            
            if t_id and t_id == p_id:
                mapping[t_idx] = p_idx
                matched = True
                break
            
            if t_source[:50] and t_source[:50] in p_source:
                mapping[t_idx] = p_idx
                matched = True
                break
        
        if not matched:
            mapping[t_idx] = t_idx
    
    return mapping


def extract_code_from_cell(cell: Dict) -> str:
    """从 cell 中提取代码"""
    source = cell.get('source', [])
    if isinstance(source, list):
        return ''.join(source)
    return source


def find_code_line_smart(code_full: str, line_index: int, validators: Dict, search_window: int = 5) -> str:
    """
    智能查找代码行（v2 格式专用）
    
    策略：
    1. 先尝试 line_index
    2. 如果是注释/空行，向下搜索
    3. 使用 validators 中的关键词在 ±search_window 范围内搜索
    """
    lines = code_full.split('\n')
    
    if line_index >= len(lines):
        return ''
    
    target_line = lines[line_index].strip()
    
    # 如果目标行是注释或空行，向下搜索
    if target_line.startswith('#') or not target_line:
        for i in range(line_index + 1, min(line_index + search_window + 1, len(lines))):
            line = lines[i].strip()
            if line and not line.startswith('#'):
                return line
    
    # 从 validators 中提取关键词
    keywords = []
    validators_str = str(validators)
    matches = re.findall(r"'([^']+)'", validators_str)
    keywords = [m for m in matches if len(m) > 3 and not m.startswith('__')]
    
    # 如果目标行不包含关键词，在附近搜索
    if keywords and not any(kw in target_line for kw in keywords):
        for offset in range(-search_window, search_window + 1):
            if offset == 0:
                continue
            idx = line_index + offset
            if 0 <= idx < len(lines):
                line = lines[idx].strip()
                if line and not line.startswith('#'):
                    if any(kw in line for kw in keywords):
                        return line
    
    return target_line


def check_exact_rule(code_line: str, rule: Dict) -> bool:
    """
    检查 exact 类型的规则（v2 格式）
    
    规则类型：
    - must_contain: 必须包含某些字符串
    - must_contain_any: 必须包含任意一个
    - must_assign_to: 必须赋值给某个变量
    - must_have_arg: 必须包含某个参数
    - must_call_method: 必须调用某个方法
    """
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
    检查 semantic 类型的规则（v2 格式，宽松匹配）
    
    规则类型：
    - must_contain_any: 包含任意一个关键词
    - must_call_method: 必须调用某个方法
    - must_have_param: 必须包含某个参数
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


# ============================================================================
# AST 检查功能
# ============================================================================

class ASTChecker:
    """基于 AST 的代码结构检查器"""
    
    def __init__(self, code: str):
        self.code = code
        self.tree = None
        self.parse_error = False
        
        try:
            self.tree = ast.parse(code)
        except SyntaxError:
            self.parse_error = True
    
    def has_function_call(self, func_name: str, module: Optional[str] = None) -> bool:
        """
        检查是否调用了指定函数
        
        Args:
            func_name: 函数名（如 'read_csv', 'groupby'）
            module: 模块名（如 'pd', 'df'），可选
        """
        if not self.tree:
            return False
        
        # 如果 func_name 包含 '.'，拆分 module 和 function
        if '.' in func_name and module is None:
            parts = func_name.split('.', 1)
            module = parts[0]
            func_name = parts[1]
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                # 简单函数调用：func()
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    if module is None:
                        return True
                
                # 属性调用：module.func()
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == func_name:
                        if module is None:
                            return True
                        # 检查模块名
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == module:
                            return True
        
        return False
    
    def has_assignment(self, target_name: str) -> bool:
        """检查是否赋值给指定变量"""
        if not self.tree:
            return False
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == target_name:
                        return True
                    # 检查属性赋值：df['col'] = ...
                    elif isinstance(target, ast.Subscript):
                        if isinstance(target.value, ast.Name) and target.value.id == target_name:
                            return True
        
        return False
    
    def get_call_args(self, func_name: str, module: Optional[str] = None) -> List[Dict]:
        """
        获取函数调用的参数信息
        
        Returns:
            列表，每个元素包含 {'positional': [...], 'keyword': {...}}
        """
        if not self.tree:
            return []
        
        results = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                is_match = False
                
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    is_match = True
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == func_name:
                        if module is None:
                            is_match = True
                        elif isinstance(node.func.value, ast.Name) and node.func.value.id == module:
                            is_match = True
                
                if is_match:
                    args_info = {
                        'positional': [],
                        'keyword': {}
                    }
                    
                    # 位置参数
                    for arg in node.args:
                        args_info['positional'].append(self._ast_node_to_str(arg))
                    
                    # 关键字参数
                    for kw in node.keywords:
                        args_info['keyword'][kw.arg] = self._ast_node_to_str(kw.value)
                    
                    results.append(args_info)
        
        return results
    
    def has_method_chain(self, methods: List[str], base: Optional[str] = None) -> bool:
        """
        检查是否有方法链式调用
        
        Args:
            methods: 方法链（如 ['groupby', 'agg']）
            base: 基础对象名（如 'data'），可选
        """
        if not self.tree or not methods:
            return False
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                # 提取完整的调用链
                chain = self._extract_call_chain(node.func)
                
                # 过滤掉 None（如 Subscript）
                chain_filtered = [m for m in chain if m is not None]
                
                # 检查链是否匹配
                if len(chain_filtered) >= len(methods):
                    # 检查最后几个方法是否匹配
                    if chain_filtered[-len(methods):] == methods:
                        if base is None:
                            return True
                        # 检查基础对象
                        base_idx = len(chain_filtered) - len(methods) - 1
                        if base_idx >= 0 and chain_filtered[base_idx] == base:
                            return True
        
        return False
    
    def _extract_call_chain(self, node) -> List[Optional[str]]:
        """提取方法调用链（支持 Attribute、Call、Subscript）"""
        chain = []
        current = node
        
        while current is not None:
            if isinstance(current, ast.Attribute):
                chain.append(current.attr)
                current = current.value
            elif isinstance(current, ast.Call):
                # 如果是 Call，提取 func
                current = current.func
            elif isinstance(current, ast.Subscript):
                # Subscript 不影响方法链，跳过
                current = current.value
            elif isinstance(current, ast.Name):
                chain.append(current.id)
                current = None
            else:
                break
        
        chain.reverse()
        return chain
    
    def _ast_node_to_str(self, node: ast.AST) -> str:
        """将 AST 节点转换为字符串表示"""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return f"[{', '.join(self._ast_node_to_str(e) for e in node.elts)}]"
        elif isinstance(node, ast.Tuple):
            return f"({', '.join(self._ast_node_to_str(e) for e in node.elts)})"
        elif isinstance(node, ast.Dict):
            keys = [self._ast_node_to_str(k) for k in node.keys]
            values = [self._ast_node_to_str(v) for v in node.values]
            return f"{{{', '.join(f'{k}: {v}' for k, v in zip(keys, values))}}}"
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_node_to_str(node.value)}.{node.attr}"
        else:
            return ast.dump(node)
    
    def has_import(self, module: str, alias: Optional[str] = None) -> bool:
        """检查是否导入了指定模块"""
        if not self.tree:
            return False
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias_node in node.names:
                    if alias_node.name == module or alias_node.name.startswith(module + '.'):
                        if alias is None or (alias_node.asname and alias_node.asname == alias):
                            return True
            elif isinstance(node, ast.ImportFrom):
                if node.module and (node.module == module or node.module.startswith(module + '.')):
                    return True
        
        return False
    
    def get_all_function_calls(self) -> List[Dict]:
        """获取所有函数调用信息"""
        if not self.tree:
            return []
        
        calls = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                call_info = {
                    'function': '',
                    'module': None,
                    'args': []
                }
                
                if isinstance(node.func, ast.Name):
                    call_info['function'] = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    call_info['function'] = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        call_info['module'] = node.func.value.id
                
                calls.append(call_info)
        
        return calls


def check_ast_rule(code_full: str, rule: Dict) -> bool:
    """
    检查 ast_check 类型的规则
    
    规则类型：
    - must_call: 必须调用某个函数
    - must_assign: 必须赋值给某个变量
    - must_have_arg: 函数必须包含某个参数
    - must_chain: 必须有方法链式调用
    - must_import: 必须导入某个模块
    """
    checker = ASTChecker(code_full)
    
    if checker.parse_error:
        return False
    
    # must_call: 必须调用某个函数
    if 'must_call' in rule:
        call_spec = rule['must_call']
        if isinstance(call_spec, str):
            # 简单形式：'read_csv'
            if not checker.has_function_call(call_spec):
                return False
        elif isinstance(call_spec, dict):
            # 复杂形式：{'function': 'read_csv', 'module': 'pd'}
            func_name = call_spec.get('function', '')
            module = call_spec.get('module')
            if not checker.has_function_call(func_name, module):
                return False
    
    # must_assign: 必须赋值给某个变量
    if 'must_assign' in rule:
        target = rule['must_assign']
        if not checker.has_assignment(target):
            return False
    
    # must_have_arg: 函数必须包含某个参数
    if 'must_have_arg' in rule:
        arg_spec = rule['must_have_arg']
        func_name = arg_spec.get('function', '')
        module = arg_spec.get('module')
        param_name = arg_spec.get('param')
        param_value = arg_spec.get('value')
        
        calls = checker.get_call_args(func_name, module)
        if not calls:
            return False
        
        # 检查参数
        found = False
        for call_info in calls:
            if param_name:
                if param_name in call_info['keyword']:
                    if param_value is None or param_value in call_info['keyword'][param_name]:
                        found = True
                        break
                # 也检查位置参数
                if param_value:
                    for pos_arg in call_info['positional']:
                        if param_value in pos_arg:
                            found = True
                            break
            if found:
                break
        
        if not found:
            return False
    
    # must_chain: 必须有方法链式调用
    if 'must_chain' in rule:
        chain_spec = rule['must_chain']
        methods = chain_spec.get('methods', [])
        base = chain_spec.get('base')
        if not checker.has_method_chain(methods, base):
            return False
    
    # must_import: 必须导入某个模块
    if 'must_import' in rule:
        import_spec = rule['must_import']
        if isinstance(import_spec, str):
            if not checker.has_import(import_spec):
                return False
        elif isinstance(import_spec, dict):
            module = import_spec.get('module', '')
            alias = import_spec.get('alias')
            if not checker.has_import(module, alias):
                return False
    
    return True


# ============================================================================
# 执行结果验证功能
# ============================================================================

class ExecutionValidator:
    """基于执行结果的代码验证器（仅用于练习模式）"""
    
    def __init__(self, code: str, timeout: int = 10):
        self.code = code
        self.timeout = timeout
        self.variables = {}
        self.exec_error = None
    
    def execute(self) -> bool:
        """执行代码并捕获变量"""
        try:
            exec_globals = {'__builtins__': __builtins__}
            exec(self.code, exec_globals)
            self.variables = {
                k: v for k, v in exec_globals.items()
                if not k.startswith('__') and k != '__builtins__'
            }
            return True
        except Exception as e:
            self.exec_error = str(e)
            return False
    
    def check_variable_type(self, var_name: str, expected_type: str) -> bool:
        """检查变量类型"""
        if var_name not in self.variables:
            return False
        
        var = self.variables[var_name]
        type_map = {
            'DataFrame': 'pandas.core.frame.DataFrame',
            'Series': 'pandas.core.series.Series',
            'ndarray': 'numpy.ndarray',
            'list': 'list',
            'dict': 'dict',
            'Pipeline': 'sklearn.pipeline.Pipeline',
            'LinearRegression': 'sklearn.linear_model',
            'RandomForestRegressor': 'sklearn.ensemble',
        }
        
        expected_full = type_map.get(expected_type, expected_type)
        actual_type = type(var).__module__ + '.' + type(var).__name__
        return expected_type in actual_type or expected_full in actual_type
    
    def check_variable_shape(self, var_name: str, expected_shape: tuple) -> bool:
        """检查变量形状"""
        if var_name not in self.variables:
            return False
        var = self.variables[var_name]
        return hasattr(var, 'shape') and var.shape == expected_shape
    
    def check_variable_value(self, var_name: str, expected_value: Any, tolerance: float = 0.01) -> bool:
        """检查变量值"""
        if var_name not in self.variables:
            return False
        var = self.variables[var_name]
        if isinstance(expected_value, (int, float)):
            try:
                return abs(float(var) - expected_value) < tolerance
            except (ValueError, TypeError):
                return False
        return var == expected_value
    
    def check_variable_exists(self, var_name: str) -> bool:
        """检查变量是否存在"""
        return var_name in self.variables
    
    def check_variable_length(self, var_name: str, expected_length: int) -> bool:
        """检查变量长度"""
        if var_name not in self.variables:
            return False
        var = self.variables[var_name]
        return hasattr(var, '__len__') and len(var) == expected_length


def check_execution_rule(code_full: str, rule: Dict, notebook_dir: Optional[Path] = None) -> Dict:
    """
    检查 execution 类型的规则
    
    规则类型：
    - variable_exists: 变量是否存在
    - variable_type: 变量类型
    - variable_shape: 变量形状
    - variable_value: 变量值
    - variable_length: 变量长度
    """
    import os
    original_cwd = os.getcwd()
    if notebook_dir:
        os.chdir(notebook_dir)
    
    try:
        validator = ExecutionValidator(code_full)
        success = validator.execute()
        
        if not success:
            return {'passed': False, 'details': f'执行失败: {validator.exec_error}', 'error': validator.exec_error}
        
        checks_passed = []
        checks_failed = []
        
        if 'variable_exists' in rule:
            var_name = rule['variable_exists']
            if validator.check_variable_exists(var_name):
                checks_passed.append(f'变量 {var_name} 存在')
            else:
                checks_failed.append(f'变量 {var_name} 不存在')
        
        if 'variable_type' in rule:
            spec = rule['variable_type']
            if isinstance(spec, dict):
                var_name = spec.get('name', '')
                expected = spec.get('type', '')
                if validator.check_variable_type(var_name, expected):
                    checks_passed.append(f'{var_name} 类型是 {expected}')
                else:
                    checks_failed.append(f'{var_name} 类型不是 {expected}')
        
        if 'variable_shape' in rule:
            spec = rule['variable_shape']
            if isinstance(spec, dict):
                var_name = spec.get('name', '')
                expected = tuple(spec.get('shape', []))
                if validator.check_variable_shape(var_name, expected):
                    checks_passed.append(f'{var_name} 形状是 {expected}')
                else:
                    actual = getattr(validator.variables.get(var_name), 'shape', 'N/A')
                    checks_failed.append(f'{var_name} 形状不是 {expected} (实际: {actual})')
        
        if 'variable_value' in rule:
            spec = rule['variable_value']
            if isinstance(spec, dict):
                var_name = spec.get('name', '')
                expected = spec.get('value')
                tolerance = spec.get('tolerance', 0.01)
                if validator.check_variable_value(var_name, expected, tolerance):
                    checks_passed.append(f'{var_name} 值正确')
                else:
                    actual = validator.variables.get(var_name, 'N/A')
                    checks_failed.append(f'{var_name} 值不正确 (期望: {expected}, 实际: {actual})')
        
        if 'variable_length' in rule:
            spec = rule['variable_length']
            if isinstance(spec, dict):
                var_name = spec.get('name', '')
                expected = spec.get('length', 0)
                if validator.check_variable_length(var_name, expected):
                    checks_passed.append(f'{var_name} 长度是 {expected}')
                else:
                    actual = len(validator.variables.get(var_name, []))
                    checks_failed.append(f'{var_name} 长度不是 {expected} (实际: {actual})')
        
        return {
            'passed': len(checks_failed) == 0,
            'details': '; '.join(checks_passed) if checks_passed else '; '.join(checks_failed),
            'error': None
        }
    except Exception as e:
        return {'passed': False, 'details': f'验证异常: {str(e)}', 'error': str(e)}
    finally:
        os.chdir(original_cwd)


def extract_user_answers(practice_path: Path, schema: Dict) -> List[Dict]:
    """
    从练习文件中提取用户填写的答案（v1 格式）
    
    基于评分标准中的 cell_index 和 line_index 定位
    支持Cell索引自动对齐（处理自动注入的日志初始化Cell）
    """
    practice_nb = load_notebook(practice_path)
    if not practice_nb:
        return []
    
    template_path = ROOT / f"{schema['chapter']}-materials" / f"{schema['chapter']}.ipynb"
    template_nb = load_notebook(template_path) if template_path.exists() else None
    
    cell_mapping = {}
    if template_nb:
        cell_mapping = align_cells(template_nb, practice_nb)
    
    answers = []
    
    for item in schema['items']:
        template_cell_idx = item['cell_index']
        line_idx = item['line_index']
        
        practice_cell_idx = cell_mapping.get(template_cell_idx, template_cell_idx)
        
        if practice_cell_idx >= len(practice_nb.get('cells', [])):
            answers.append({'item_id': item['id'], 'answer': '', 'found': False})
            continue
        
        cell = practice_nb['cells'][practice_cell_idx]
        if cell.get('cell_type') != 'code':
            answers.append({'item_id': item['id'], 'answer': '', 'found': False})
            continue
        
        source = ''.join(cell.get('source', []))
        lines = source.split('\n')
        
        if line_idx < len(lines):
            answers.append({
                'item_id': item['id'],
                'answer': lines[line_idx].strip(),
                'found': True,
                'line': lines[line_idx]
            })
        else:
            answers.append({'item_id': item['id'], 'answer': '', 'found': False})
    
    return answers


def score_item_v2(item: Dict, practice_nb: Dict, mode: str = 'exam') -> Dict:
    """
    对单个评分点进行评分（v2 格式）
    """
    cell_index = item['metadata']['cell_index']
    line_index = item['metadata']['line_index']
    
    cells = practice_nb.get('cells', [])
    if cell_index >= len(cells):
        return {
            'item_id': item['id'],
            'description': item.get('description', ''),
            'earned': 0,
            'max': item['score'],
            'correct': False,
            'details': 'Cell 不存在',
            'difficulty': item.get('difficulty', '?')
        }
    
    cell = cells[cell_index]
    if cell.get('cell_type') != 'code':
        return {
            'item_id': item['id'],
            'description': item.get('description', ''),
            'earned': 0,
            'max': item['score'],
            'correct': False,
            'details': 'Cell 类型不是代码',
            'difficulty': item.get('difficulty', '?')
        }
    
    code_full = extract_code_from_cell(cell)
    
    validators = item.get('validators', {})
    mode_validators = validators.get(mode, validators.get('exam'))
    
    if not mode_validators:
        return {
            'item_id': item['id'],
            'description': item.get('description', ''),
            'earned': 0,
            'max': item['score'],
            'correct': False,
            'details': '未找到验证规则',
            'difficulty': item.get('difficulty', '?')
        }
    
    code_line = find_code_line_smart(code_full, line_index, mode_validators)
    
    validator_type = mode_validators.get('type', 'exact')
    rules = mode_validators.get('rules', [])
    
    all_passed = True
    failed_rules = []
    
    for rule in rules:
        if validator_type == 'exact':
            passed = check_exact_rule(code_line, rule)
        elif validator_type == 'semantic':
            passed = check_semantic_rule(code_line, code_full, rule)
        elif validator_type == 'ast_check':
            passed = check_ast_rule(code_full, rule)
        elif validator_type == 'execution':
            notebook_dir = Path(args.file).parent if hasattr(args, 'file') and args.file else None
            result = check_execution_rule(code_full, rule, notebook_dir)
            passed = result['passed']
            if not passed:
                failed_rules.append(result.get('details', str(rule)))
                continue
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


def score_practice_v1(schema: Dict, user_answers: List[Dict], strict: bool = False) -> Dict:
    """
    对练习进行评分（v1 格式）
    """
    details = []
    earned_score = 0
    
    for item, user_ans in zip(schema['items'], user_answers):
        correct = False
        
        if user_ans['found'] and user_ans['answer']:
            correct = check_answer_match(user_ans['answer'], item['answer'], strict)
        
        if correct:
            earned_score += item['score']
        
        details.append({
            'item_id': item['id'],
            'description': item['description'],
            'max_score': item['score'],
            'earned_score': item['score'] if correct else 0,
            'correct': correct,
            'user_answer': user_ans.get('answer', ''),
            'correct_answer': item['answer'],
        })
    
    total_score = schema['total_score']
    percentage = (earned_score / total_score * 100) if total_score > 0 else 0
    
    return {
        'chapter': schema['chapter'],
        'total_score': total_score,
        'earned_score': earned_score,
        'percentage': round(percentage, 1),
        'details': details,
        'graded_at': datetime.now().isoformat(),
    }


def score_practice_v2(schema: Dict, practice_path: Path, mode: str = 'exam') -> Dict:
    """
    对整个练习进行评分（v2 格式）
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
        'title': schema['exam'].get('title', ''),
        'mode': mode,
        'total_score': total_max,
        'earned_score': total_earned,
        'percentage': round(percentage, 1),
        'details': results,
        'graded_at': datetime.now().isoformat()
    }


def print_report_v1(result: Dict):
    """打印 v1 格式评分报告"""
    logger.info(f"\n{'='*60}")
    logger.info(f"评分验证: {result['chapter']}")
    logger.info(f"{'='*60}")
    
    logger.info(f"\n总分: {result['earned_score']} / {result['total_score']} ({result['percentage']}%)")
    logger.info(f"\n详细评分:")
    
    for detail in result['details']:
        status = '✅' if detail['correct'] else '❌'
        logger.info(
            f"  {detail['item_id']}: {detail['description']} - "
            f"{detail['earned_score']}/{detail['max_score']} {status}"
        )


def print_report_v2(result: Dict):
    """打印 v2 格式评分报告"""
    title = result.get('title', result['chapter'])
    mode = result.get('mode', 'unknown')
    
    print(f"\n{'='*70}")
    print(f"📊 {title}")
    print(f"章节: {result['chapter']} | 模式: {mode}")
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
    
    correct_count = sum(1 for d in result['details'] if d['correct'])
    total_count = len(result['details'])
    
    print(f"\n📈 统计:")
    print(f"  通过: {correct_count}/{total_count}")
    
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


def generate_report(result: Dict, output_path: Optional[Path] = None) -> str:
    """生成评分报告（v1 格式兼容）"""
    lines = []
    lines.append(f"# {result['chapter']} 评分报告")
    lines.append(f"\n生成时间: {result['graded_at']}")
    lines.append(f"\n## 总分")
    lines.append(f"\n**{result['earned_score']} / {result['total_score']}** ({result['percentage']}%)")
    lines.append(f"\n## 详细评分")
    lines.append(f"\n| 题号 | 描述 | 得分 | 满分 | 状态 |")
    lines.append(f"|------|------|------|------|------|")
    
    for detail in result['details']:
        status = '✅' if detail['correct'] else '❌'
        earned = detail.get('earned_score', detail.get('earned', 0))
        max_score = detail.get('max_score', detail.get('max', 0))
        lines.append(
            f"| {detail['item_id']} | {detail['description']} | "
            f"{earned} | {max_score} | {status} |"
        )
    
    report = '\n'.join(lines)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"\n报告已保存: {output_path}")
    
    return report


def main():
    args = parse_args()
    
    if not args.chapter and not args.session:
        logger.error("请指定章节或Session")
        return
    
    chapter = args.chapter
    practice_file = None
    
    if args.session:
        session_path = Path(args.session)
        if not session_path.is_absolute():
            session_path = ROOT / 'sessions' / session_path
        
        practice_file = session_path / 'practice.ipynb'
        if not practice_file.exists():
            logger.error(f"练习文件不存在: {practice_file}")
            return
        
        chapter_match = re.search(r'chapter(\d+\.\d+\.\d+)', session_path.name)
        if chapter_match:
            chapter = chapter_match.group(1)
    
    elif args.file:
        practice_file = Path(args.file)
        if not practice_file.exists():
            logger.error(f"练习文件不存在: {practice_file}")
            return
        
        chapter_match = re.search(r'(\d+\.\d+\.\d+)', practice_file.name)
        if chapter_match:
            chapter = chapter_match.group(1)
    
    if not chapter:
        logger.error("无法确定章节号")
        return
    
    schema = load_scoring_schema(chapter)
    if not schema:
        return
    
    if not practice_file:
        logger.error("请指定练习文件路径")
        return
    
    version = detect_schema_version(schema)
    
    if version == 'v2':
        mode = args.mode if args.mode else 'exam'
        logger.info(f"\n📁 练习文件: {practice_file}")
        logger.info(f"📋 评分模式: {mode}")
        
        result = score_practice_v2(schema, practice_file, mode=mode)
        if not result:
            return
        
        print_report_v2(result)
        
        if args.output_report:
            output_path = practice_file.parent / 'scoring_report.md'
            generate_report(result, output_path)
        
        result_json_path = practice_file.parent / f'scoring_result_v2_{mode}.json'
        with open(result_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 JSON结果已保存: {result_json_path}")
    
    else:
        logger.info(f"\n📁 练习文件: {practice_file}")
        
        user_answers = extract_user_answers(practice_file, schema)
        result = score_practice_v1(schema, user_answers, strict=args.strict)
        
        print_report_v1(result)
        
        if args.output_report:
            output_path = practice_file.parent / 'scoring_report.md'
            generate_report(result, output_path)
        
        result_json_path = practice_file.parent / 'scoring_result.json'
        with open(result_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"\n💾 JSON结果已保存: {result_json_path}")


if __name__ == '__main__':
    main()