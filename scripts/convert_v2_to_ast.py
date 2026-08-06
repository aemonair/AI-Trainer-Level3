#!/usr/bin/env python3
"""
批量将 v2 评分标准转换为 AST 版本
"""
from pathlib import Path
import json
import re
import argparse
import logging
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SCORING_DIR = ROOT / 'scoring'

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='批量转换 v2 评分标准为 AST 格式')
    parser.add_argument('--chapters', type=str, help='指定章节号，逗号分隔')
    parser.add_argument('--dry-run', action='store_true', help='只预览，不生成文件')
    return parser.parse_args()

def extract_ast_rules_from_answer(answer: str) -> List[Dict]:
    """从答案中提取 AST 规则"""
    rules = []
    
    func_calls = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\(', answer)
    module_calls = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\(', answer)
    assign_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=', answer)
    
    if module_calls:
        module, func = module_calls[0]
        rule = {"must_call": {"function": func, "module": module}}
        if assign_match:
            rule["must_assign"] = assign_match.group(1)
        rules.append(rule)
    elif func_calls:
        rule = {"must_call": func_calls[0]}
        if assign_match:
            rule["must_assign"] = assign_match.group(1)
        rules.append(rule)
    
    str_params = re.findall(r"['\"]([^'\"]{3,})['\"]", answer)
    kw_params = re.findall(r'(\w+)=([^\s,)]+)', answer)
    
    if func_calls and (str_params or kw_params):
        arg_rule = {"must_have_arg": {"function": func_calls[0]}}
        
        if module_calls:
            arg_rule["must_have_arg"]["module"] = module_calls[0][0]
        
        if kw_params:
            arg_rule["must_have_arg"]["param"] = kw_params[0][0]
            arg_rule["must_have_arg"]["value"] = kw_params[0][1]
        elif str_params:
            arg_rule["must_have_arg"]["param"] = None
            arg_rule["must_have_arg"]["value"] = f"'{str_params[0]}'"
        
        if arg_rule["must_have_arg"].get("param") or arg_rule["must_have_arg"].get("value"):
            rules.append(arg_rule)
    
    return rules if rules else [{"must_call": answer[:30]}]

def convert_item_v2_to_ast(item: Dict) -> Dict:
    """转换单个评分点 v2 -> AST"""
    validators = item.get('validators', {})
    exam_rules = validators.get('exam', {}).get('rules', [])
    
    answer = ''
    for rule in exam_rules:
        if 'must_contain' in rule:
            answer = ' '.join(rule['must_contain'])
            break
        if 'must_have_arg' in rule:
            answer = rule['must_have_arg']
            break
    
    if not answer:
        answer = item.get('metadata', {}).get('template', '')
    
    ast_rules = extract_ast_rules_from_answer(answer)
    
    ast_item = item.copy()
    ast_item['validators'] = {
        "exam": {
            "type": "ast_check",
            "rules": ast_rules
        },
        "practice": {
            "type": "ast_check",
            "rules": [{"must_call": r.get("must_call", "")} if isinstance(r.get("must_call"), str) else r for r in ast_rules]
        }
    }
    
    return ast_item

def convert_schema_v2_to_ast(v2_schema: Dict) -> Dict:
    """转换整个评分标准 v2 -> AST"""
    chapter = v2_schema['exam']['chapter']
    
    ast_schema = v2_schema.copy()
    ast_schema['exam']['title'] = v2_schema['exam'].get('title', '') + '（AST 版本）'
    ast_schema['items'] = [convert_item_v2_to_ast(item) for item in v2_schema['items']]
    ast_schema['metadata'] = v2_schema.get('metadata', {}).copy()
    ast_schema['metadata']['version'] = 'ast'
    ast_schema['metadata']['generated_at'] = datetime.now().isoformat()
    ast_schema['metadata']['converted_from'] = f"{chapter}_v2.json"
    
    return ast_schema

def main():
    args = parse_args()
    
    if args.chapters:
        chapters = [c.strip() for c in args.chapters.split(',')]
    else:
        v2_files = list(SCORING_DIR.glob('*_v2.json'))
        chapters = [f.stem.replace('_v2', '') for f in sorted(v2_files)]
    
    logger.info(f"\n{'='*70}")
    logger.info(f"批量转换 v2 -> AST 评分标准")
    logger.info(f"{'='*70}")
    logger.info(f"待转换章节: {len(chapters)}")
    logger.info(f"章节列表: {', '.join(chapters)}\n")
    
    converted_count = 0
    skipped_count = 0
    
    for chapter in chapters:
        v2_path = SCORING_DIR / f'{chapter}_v2.json'
        ast_path = SCORING_DIR / f'{chapter}_ast.json'
        
        if not v2_path.exists():
            logger.warning(f"⚠️  跳过: {chapter}_v2.json 不存在")
            skipped_count += 1
            continue
        
        if ast_path.exists():
            logger.warning(f"⚠️  跳过: {chapter}_ast.json 已存在")
            skipped_count += 1
            continue
        
        with open(v2_path, 'r', encoding='utf-8') as f:
            v2_schema = json.load(f)
        
        ast_schema = convert_schema_v2_to_ast(v2_schema)
        
        if args.dry_run:
            logger.info(f"👁️  预览: {chapter} ({v2_schema['exam']['total_score']}分, {len(v2_schema['items'])}题)")
        else:
            with open(ast_path, 'w', encoding='utf-8') as f:
                json.dump(ast_schema, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 转换: {chapter} ({v2_schema['exam']['total_score']}分, {len(v2_schema['items'])}题)")
            logger.info(f"   输出: {ast_path.name}")
        
        converted_count += 1
    
    logger.info(f"\n{'='*70}")
    if args.dry_run:
        logger.info(f"预览完成: {converted_count} 个章节待转换, {skipped_count} 个跳过")
    else:
        logger.info(f"转换完成: {converted_count} 个章节已转换, {skipped_count} 个跳过")
    logger.info(f"{'='*70}\n")

if __name__ == '__main__':
    main()
