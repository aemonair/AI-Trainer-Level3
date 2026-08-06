#!/usr/bin/env python3
"""
批量转换 v1 评分标准为 v2 格式

功能：
1. 读取 scoring/*.json (v1)
2. 自动推断 validators 规则
3. 生成 scoring/*_v2.json (v2)
4. 保留原始文件，不覆盖

用法:
  python3 scripts/convert_v1_to_v2.py
  python3 scripts/convert_v1_to_v2.py --chapters 1.1.1,1.1.2,2.2.2
  python3 scripts/convert_v1_to_v2.py --dry-run  # 只预览，不生成文件
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
    parser = argparse.ArgumentParser(description='批量转换 v1 评分标准为 v2 格式')
    parser.add_argument('--chapters', type=str, help='指定章节号，逗号分隔（如 1.1.1,1.1.2）')
    parser.add_argument('--dry-run', action='store_true', help='只预览，不生成文件')
    return parser.parse_args()


def extract_keywords_from_answer(answer: str) -> List[str]:
    """从答案中提取关键词"""
    keywords = []
    
    # 提取 API 调用（如 pd.read_csv, df.head, train_test_split）
    api_pattern = r'([a-zA-Z_][a-zA-Z0-9_.]+\.[a-zA-Z_][a-zA-Z0-9_]*)'
    apis = re.findall(api_pattern, answer)
    keywords.extend(apis)
    
    # 提取函数调用（如 read_csv, dropna, fit）
    func_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\('
    funcs = re.findall(func_pattern, answer)
    keywords.extend(funcs)
    
    # 提取字符串参数（如 'auto-mpg.csv', 'mpg'）
    str_pattern = r"['\"]([^'\"]{3,})['\"]"
    strings = re.findall(str_pattern, answer)
    keywords.extend(strings)
    
    # 去重
    return list(set(keywords))


def infer_difficulty(answer: str, template: str) -> str:
    """推断题目难度"""
    # 简单：单行赋值、简单 API 调用
    # 中等：包含参数、链式调用
    # 困难：多步骤、复杂表达式
    
    complexity_score = 0
    
    # 链式调用（如 df.groupby().agg()）
    chain_count = answer.count('.')
    if chain_count >= 2:
        complexity_score += 2
    elif chain_count == 1:
        complexity_score += 1
    
    # 嵌套括号
    paren_depth = answer.count('(')
    if paren_depth >= 2:
        complexity_score += 2
    elif paren_depth == 1:
        complexity_score += 1
    
    # 填空题数量（template 中下划线组数）
    blank_count = len(re.findall(r'_{3,}', template))
    if blank_count >= 3:
        complexity_score += 2
    elif blank_count == 2:
        complexity_score += 1
    
    if complexity_score >= 4:
        return 'hard'
    elif complexity_score >= 2:
        return 'medium'
    else:
        return 'easy'


def infer_knowledge_points(answer: str) -> List[str]:
    """推断知识点"""
    points = []
    
    # pandas 相关
    if 'pd.' in answer or 'DataFrame' in answer:
        points.append('pandas')
    if 'read_csv' in answer or 'read_excel' in answer:
        points.append('数据加载')
    if 'groupby' in answer:
        points.append('数据分组')
    if 'merge' in answer or 'join' in answer:
        points.append('数据合并')
    if 'dropna' in answer or 'fillna' in answer:
        points.append('缺失值处理')
    if 'to_numeric' in answer:
        points.append('类型转换')
    if 'value_counts' in answer:
        points.append('数据统计')
    if 'cut' in answer or 'qcut' in answer:
        points.append('数据分箱')
    if 'where' in answer or 'mask' in answer:
        points.append('条件筛选')
    
    # sklearn 相关
    if 'sklearn' in answer or 'train_test_split' in answer:
        points.append('sklearn')
    if 'train_test_split' in answer:
        points.append('数据集划分')
    if 'fit' in answer:
        points.append('模型训练')
    if 'predict' in answer:
        points.append('模型预测')
    if 'score' in answer:
        points.append('模型评估')
    if 'Pipeline' in answer:
        points.append('Pipeline')
    if 'StandardScaler' in answer or 'MinMaxScaler' in answer:
        points.append('数据标准化')
    if 'LinearRegression' in answer:
        points.append('线性回归')
    if 'RandomForest' in answer:
        points.append('随机森林')
    if 'LogisticRegression' in answer:
        points.append('逻辑回归')
    if 'SVC' in answer or 'SVR' in answer:
        points.append('支持向量机')
    
    # 其他
    if 'pickle' in answer:
        points.append('pickle')
    if 'np.' in answer or 'numpy' in answer:
        points.append('numpy')
    if 'plt.' in answer or 'matplotlib' in answer:
        points.append('matplotlib')
    if 'to_csv' in answer:
        points.append('数据导出')
    
    return points if points else ['基础语法']


def extract_common_errors(answer: str, template: str) -> List[str]:
    """提取常见错误提示"""
    errors = []
    
    # 基于 API 类型推断常见错误
    if 'read_csv' in answer:
        errors.append("文件名拼写错误")
        errors.append("忘记加引号")
    
    if 'groupby' in answer:
        errors.append("列名拼写错误")
        errors.append("忘记指定聚合函数")
    
    if 'train_test_split' in answer:
        errors.append("忘记 random_state 参数")
        errors.append("test_size 比例错误")
    
    if 'fit' in answer:
        errors.append("参数顺序错误（应该是 X_train, y_train）")
    
    if 'predict' in answer:
        errors.append("使用 X_train 而非 X_test")
    
    if 'to_csv' in answer:
        errors.append("忘记 index=False")
        errors.append("文件名错误")
    
    if 'dropna' in answer or 'fillna' in answer:
        errors.append("忘记赋值回原变量")
    
    if 'Pipeline' in answer:
        errors.append("步骤名称错误")
        errors.append("忘记括号或引号")
    
    return errors if errors else ["语法错误"]


def build_exam_rules(answer: str) -> List[Dict]:
    """构建 exam 模式的规则（严格匹配）"""
    rules = []
    
    # 提取必须包含的关键词
    keywords = extract_keywords_from_answer(answer)
    important_keywords = [kw for kw in keywords if len(kw) > 3]
    
    rule = {}
    if important_keywords:
        rule["must_contain"] = important_keywords[:3]
    
    # 提取赋值变量
    assign_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=', answer)
    if assign_match:
        rule['must_assign_to'] = assign_match.group(1)
    
    if rule:
        rules.append(rule)
    
    # 提取关键参数
    str_params = re.findall(r"['\"]([^'\"]{3,})['\"]", answer)
    for param in str_params[:2]:
        rules.append({
            "must_have_arg": f"'{param}'"
        })
    
    return rules if rules else [{"must_contain": [answer[:30]]}]


def build_practice_rules(answer: str) -> List[Dict]:
    """构建 practice 模式的规则（语义匹配）"""
    rules = []
    
    # 提取核心 API
    api_calls = re.findall(r'([a-zA-Z_][a-zA-Z0-9_.]+\.[a-zA-Z_][a-zA-Z0-9_]*)', answer)
    func_calls = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\(', answer)
    
    all_calls = api_calls + func_calls
    unique_calls = list(set(all_calls))
    
    if unique_calls:
        rules.append({
            "must_contain_any": unique_calls[:3],
            "allow_variable_rename": True
        })
    
    return rules if rules else [{"must_contain_any": [answer[:20]]}]


def convert_item_v1_to_v2(item: Dict) -> Dict:
    """转换单个评分点 v1 -> v2"""
    answer = item.get('answer', '')
    template = item.get('template_line', '')
    description = item.get('description', '未知')
    
    # 如果描述是"未知"，尝试从 template 推断
    if description == '未知':
        # 从 answer 中提取操作描述
        if 'read_csv' in answer:
            description = '加载数据集'
        elif 'head' in answer:
            description = '显示数据前几行'
        elif 'dropna' in answer:
            description = '删除缺失值'
        elif 'fillna' in answer:
            description = '填充缺失值'
        elif 'groupby' in answer:
            description = '数据分组统计'
        elif 'train_test_split' in answer:
            description = '划分训练集和测试集'
        elif 'fit' in answer:
            description = '训练模型'
        elif 'predict' in answer:
            description = '模型预测'
        elif 'to_csv' in answer:
            description = '保存结果到文件'
        elif 'pickle.dump' in answer:
            description = '保存模型'
        else:
            description = '完成代码填空'
    
    v2_item = {
        "id": item['id'],
        "score": item['score'],
        "description": description,
        "difficulty": infer_difficulty(answer, template),
        "knowledge_points": infer_knowledge_points(answer),
        
        "validators": {
            "exam": {
                "type": "exact",
                "rules": build_exam_rules(answer)
            },
            "practice": {
                "type": "semantic",
                "rules": build_practice_rules(answer)
            }
        },
        
        "metadata": {
            "cell_index": item['cell_index'],
            "line_index": item['line_index'],
            "template": template,
            "common_errors": extract_common_errors(answer, template)
        }
    }
    
    return v2_item


def convert_schema_v1_to_v2(v1_schema: Dict) -> Dict:
    """转换整个评分标准 v1 -> v2"""
    chapter = v1_schema['chapter']
    
    # 推断标题
    title = f"第{chapter}章操作题"
    first_desc = v1_schema['items'][0].get('description', '')
    if first_desc and first_desc != '未知':
        title = first_desc[:30]
    
    v2_schema = {
        "exam": {
            "chapter": chapter,
            "title": title,
            "total_score": v1_schema['total_score'],
            "passing_score": int(v1_schema['total_score'] * 0.6),
            "time_limit_minutes": 30
        },
        
        "items": [convert_item_v1_to_v2(item) for item in v1_schema['items']],
        
        "grading_rules": {
            "exam_mode": {
                "strict_matching": True,
                "allow_partial_credit": False,
                "deduction_for_syntax_error": 0.5,
                "deduction_for_typo": 0
            },
            "practice_mode": {
                "strict_matching": False,
                "allow_partial_credit": True,
                "semantic_matching": True,
                "provide_hints": True
            }
        },
        
        "metadata": {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "converted_from": f"{chapter}.json",
            "difficulty_distribution": {},
            "knowledge_point_coverage": {}
        }
    }
    
    # 统计难度分布
    difficulty_dist = {'easy': 0, 'medium': 0, 'hard': 0}
    for item in v2_schema['items']:
        diff = item['difficulty']
        difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
    v2_schema['metadata']['difficulty_distribution'] = difficulty_dist
    
    # 统计知识点覆盖
    kp_coverage = {}
    for item in v2_schema['items']:
        for kp in item['knowledge_points']:
            kp_coverage[kp] = kp_coverage.get(kp, 0) + 1
    v2_schema['metadata']['knowledge_point_coverage'] = kp_coverage
    
    return v2_schema


def main():
    args = parse_args()
    
    # 确定要转换的章节
    if args.chapters:
        chapters = [c.strip() for c in args.chapters.split(',')]
    else:
        # 自动查找所有 v1 JSON 文件
        v1_files = list(SCORING_DIR.glob('*.json'))
        v1_files = [f for f in v1_files if not f.name.endswith('_v2.json') and f.name != 'scoring_index.json']
        chapters = [f.stem for f in sorted(v1_files)]
    
    logger.info(f"\n{'='*70}")
    logger.info(f"批量转换 v1 -> v2 评分标准")
    logger.info(f"{'='*70}")
    logger.info(f"待转换章节: {len(chapters)}")
    logger.info(f"章节列表: {', '.join(chapters)}\n")
    
    converted_count = 0
    skipped_count = 0
    
    for chapter in chapters:
        v1_path = SCORING_DIR / f'{chapter}.json'
        v2_path = SCORING_DIR / f'{chapter}_v2.json'
        
        if not v1_path.exists():
            logger.warning(f"⚠️  跳过: {chapter}.json 不存在")
            skipped_count += 1
            continue
        
        if v2_path.exists():
            logger.warning(f"⚠️  跳过: {chapter}_v2.json 已存在")
            skipped_count += 1
            continue
        
        # 读取 v1
        with open(v1_path, 'r', encoding='utf-8') as f:
            v1_schema = json.load(f)
        
        # 转换
        v2_schema = convert_schema_v1_to_v2(v1_schema)
        
        if args.dry_run:
            logger.info(f"👁️  预览: {chapter} ({v1_schema['total_score']}分, {len(v1_schema['items'])}题)")
            logger.info(f"   难度分布: {v2_schema['metadata']['difficulty_distribution']}")
            logger.info(f"   知识点: {list(v2_schema['metadata']['knowledge_point_coverage'].keys())[:5]}...")
        else:
            # 保存 v2
            with open(v2_path, 'w', encoding='utf-8') as f:
                json.dump(v2_schema, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 转换: {chapter} ({v1_schema['total_score']}分, {len(v1_schema['items'])}题)")
            logger.info(f"   难度分布: {v2_schema['metadata']['difficulty_distribution']}")
            logger.info(f"   知识点: {list(v2_schema['metadata']['knowledge_point_coverage'].keys())[:5]}...")
            logger.info(f"   输出: {v2_path.name}")
        
        converted_count += 1
    
    logger.info(f"\n{'='*70}")
    if args.dry_run:
        logger.info(f"预览完成: {converted_count} 个章节待转换, {skipped_count} 个跳过")
    else:
        logger.info(f"转换完成: {converted_count} 个章节已转换, {skipped_count} 个跳过")
    logger.info(f"{'='*70}\n")


if __name__ == '__main__':
    main()