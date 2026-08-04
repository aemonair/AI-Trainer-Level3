#!/usr/bin/env python3
"""
聚合仓库中所有 `*_review.md` 文件为 CSV 和 Markdown 报告。

改进点：
- 统一解析策略，新老格式归一化
- 增强异常处理和日志记录
- 保留时间信息，支持更精确的排序
- 分离任务完成度和评分字段
- 支持命令行参数
- 优化正则表达式可读性

用法:
  python3 scripts/aggregate_reviews.py
  python3 scripts/aggregate_reviews.py --scan-dir . --output-dir reports
  python3 scripts/aggregate_reviews.py --pattern '*_review.md'
"""
from pathlib import Path
import csv
import re
import argparse
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# 字段常量
CSV_FIELDNAMES = [
    'datetime', 'notebook', 'path',
    'tasks_completed', 'tasks_total',
    'score', 'total_score', 'percentage',
    'errors_count', 'errors_summary'
]


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='聚合所有 *_review.md 文件为 CSV 和 Markdown 报告'
    )
    parser.add_argument(
        '--scan-dir',
        type=Path,
        default=Path('.').resolve(),
        help='扫描目录（默认：当前目录）'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='输出目录（默认：扫描目录下的 reports/）'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*_review.md',
        help='文件匹配模式（默认：*_review.md）'
    )
    return parser.parse_args()


def extract_datetime(text: str) -> Tuple[Optional[datetime], str]:
    """
    从Review文件标题中提取日期时间
    
    支持格式：
    - YYYY-MM-DD HH:MM
    - YYYYMMDDHHMM
    - YYYY-MM-DD
    
    返回: (datetime对象, 格式化字符串)
    """
    patterns = [
        (r'# .+ Review - (\d{4}-\d{2}-\d{2} \d{2}:\d{2})', '%Y-%m-%d %H:%M'),
        (r'# .+ Review - (\d{12})', '%Y%m%d%H%M'),
        (r'# .+ review \((\d{12})\)', '%Y%m%d%H%M'),
        (r'# .+ Review - (\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
    ]
    
    for pattern, fmt in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                dt = datetime.strptime(match.group(1), fmt)
                return dt, dt.strftime('%Y-%m-%d %H:%M')
            except ValueError as e:
                logger.warning(f"日期解析失败: {match.group(1)}, 错误: {e}")
    
    return None, ''


def extract_errors_new_format(text: str) -> List[Dict[str, str]]:
    """
    提取新格式错误（### 错误1：...）
    
    返回结构化的错误列表，每个错误包含：
    - name: 错误名称
    - wrong_code: 错误代码
    - correct_code: 正确代码
    - reason: 错误原因
    """
    errors = []
    
    # 匹配错误块（包含所有子项）
    # 注意：不使用 re.VERBOSE，因为需要保留 \n 的语义
    error_pattern = re.compile(
        r'### (错误\d+：[^\n]+)\n'
        r'(.*?)(?=### 错误\d+：|$)',
        re.DOTALL
    )
    
    # 提取代码块的正则
    code_pattern = re.compile(
        r'\*\*错误代码\*\*[:：]\s*`(.*?)`',
        re.DOTALL
    )
    correct_pattern = re.compile(
        r'\*\*正确写法\*\*[:：]\s*`(.*?)`',
        re.DOTALL
    )
    reason_pattern = re.compile(
        r'\*\*原因\*\*[:：]\s*(.*?)(?=\n\*|$)',
        re.DOTALL
    )
    
    for match in error_pattern.finditer(text):
        error_name = match.group(1).strip()
        error_content = match.group(2)
        
        wrong_match = code_pattern.search(error_content)
        correct_match = correct_pattern.search(error_content)
        reason_match = reason_pattern.search(error_content)
        
        errors.append({
            'name': error_name,
            'wrong_code': wrong_match.group(1).strip() if wrong_match else '',
            'correct_code': correct_match.group(1).strip() if correct_match else '',
            'reason': reason_match.group(1).strip() if reason_match else ''
        })
    
    return errors


def extract_errors_old_format(text: str) -> List[Dict[str, str]]:
    """
    提取旧格式错误（#### 错误1：... + 代码块）
    
    返回与新格式相同的结构化数据
    """
    errors = []
    
    pattern = re.compile(
        r'#### (错误\d+：.+?)\n'
        r'```python\n(.*?)```\n'
        r'.*?正确写法.*?```python\n(.*?)```',
        re.DOTALL
    )
    
    for match in pattern.finditer(text):
        errors.append({
            'name': match.group(1).strip(),
            'wrong_code': match.group(2).strip(),
            'correct_code': match.group(3).strip(),
            'reason': ''
        })
    
    return errors


def extract_errors(text: str) -> List[Dict[str, str]]:
    """
    统一错误提取入口
    
    优先尝试新格式，失败则尝试旧格式
    返回归一化的错误列表
    """
    # 先尝试新格式
    new_errors = extract_errors_new_format(text)
    if new_errors:
        return new_errors
    
    # 回退到旧格式
    old_errors = extract_errors_old_format(text)
    if old_errors:
        return old_errors
    
    return []


def extract_score(text: str) -> Dict[str, Optional[float]]:
    """
    从评分表格中提取分数
    
    返回: {score, total, percentage}
    """
    pattern = re.compile(
        r'\|\s*\*\*总计\*\*\s*\|'
        r'\s*\*{0,2}(\d+(?:\.\d+)?)\*{0,2}\s*\|'
        r'\s*\*{0,2}(\d+(?:\.\d+)?)\*{0,2}\s*\|'
        r'\s*\*{0,2}([\d.]+)%.*?\|',
        re.VERBOSE
    )
    
    match = pattern.search(text)
    if match:
        try:
            score = float(match.group(1))
            total = float(match.group(2))
            percentage = float(match.group(3))
            
            # 验证数值有效性
            if total > 0 and 0 <= percentage <= 100:
                return {
                    'score': score,
                    'total': total,
                    'percentage': percentage
                }
        except ValueError as e:
            logger.warning(f"评分数值解析失败: {e}")
    
    return {'score': None, 'total': None, 'percentage': None}


def extract_tasks(text: str) -> Tuple[int, int]:
    """
    提取任务完成情况
    
    返回: (completed_count, total_count)
    """
    total_pattern = re.compile(r'### 任务\d+：')
    completed_pattern = re.compile(r'### 任务\d+：.+? ✅')
    
    total_tasks = len(total_pattern.findall(text))
    completed_tasks = len(completed_pattern.findall(text))
    
    return completed_tasks, total_tasks


def format_errors_summary(errors: List[Dict[str, str]], max_length: int = 150) -> str:
    """
    格式化错误摘要，用于Markdown表格显示
    
    - 统一格式：错误名: 错误代码 → 正确代码
    - 安全截断，添加省略号
    - 避免破坏HTML标签
    """
    if not errors:
        return '无错误'
    
    parts = []
    for err in errors:
        if err.get('wrong_code') and err.get('correct_code'):
            part = f"{err['name']}: `{err['wrong_code']}` → `{err['correct_code']}`"
        else:
            part = err['name']
        parts.append(part)
    
    full_text = '<br>'.join(parts)
    
    # 安全截断
    if len(full_text) > max_length:
        # 找到最后一个完整的<br>标签
        truncated = full_text[:max_length]
        last_br = truncated.rfind('<br>')
        if last_br > 0:
            truncated = truncated[:last_br]
        return truncated + '…'
    
    return full_text


def parse_review_file(md_path: Path) -> Optional[Dict]:
    """
    解析单个Review文件
    
    返回结构化的数据字典，失败时返回None
    """
    try:
        text = md_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"读取文件失败 {md_path}: {e}")
        return None
    
    if not text.strip():
        logger.warning(f"文件为空: {md_path}")
        return None
    
    rel = md_path.relative_to(ROOT)
    notebook = md_path.stem
    
    # 提取所有字段
    dt, datetime_str = extract_datetime(text)
    errors = extract_errors(text)
    score_data = extract_score(text)
    completed_tasks, total_tasks = extract_tasks(text)
    
    # 构建数据行
    return {
        'datetime': datetime_str,
        'notebook': notebook,
        'path': str(rel),
        'tasks_completed': completed_tasks if total_tasks > 0 else '',
        'tasks_total': total_tasks if total_tasks > 0 else '',
        'score': score_data['score'] if score_data['score'] is not None else '',
        'total_score': score_data['total'] if score_data['total'] is not None else '',
        'percentage': f"{score_data['percentage']}%" if score_data['percentage'] is not None else '',
        'errors_count': len(errors),
        'errors_summary': format_errors_summary(errors)
    }


def write_csv(rows: List[Dict], filepath: Path):
    """写入CSV文件"""
    with filepath.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in CSV_FIELDNAMES})


def write_markdown(rows: List[Dict], filepath: Path):
    """写入Markdown报告"""
    with filepath.open('w', encoding='utf-8') as f:
        f.write('# 复盘聚合报告\n\n')
        f.write(f'- 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
        f.write(f'- 文件总数: {len(rows)}\n\n')
        
        # 表头与CSV字段顺序一致
        f.write('| 日期时间 | Notebook | 任务完成 | 得分 | 错误数 | 错误详情 | Path |\n')
        f.write('|---|---|---|---|---|---|---|\n')
        
        for r in rows:
            # 构建任务完成字符串
            if r['tasks_total']:
                tasks_str = f"{r['tasks_completed']}/{r['tasks_total']}"
            else:
                tasks_str = '-'
            
            # 构建得分字符串
            if r['score'] != '':
                score_str = f"{r['score']}/{r['total_score']} ({r['percentage']})"
            else:
                score_str = '-'
            
            f.write(
                f"| {r['datetime']} | {r['notebook']} | {tasks_str} "
                f"| {score_str} | {r['errors_count']} "
                f"| {r['errors_summary']} | {r['path']} |\n"
            )


def main():
    args = parse_args()
    
    global ROOT
    ROOT = args.scan_dir.resolve()
    
    if not ROOT.exists():
        logger.error(f"扫描目录不存在: {ROOT}")
        return
    
    # 确定输出目录
    outdir = args.output_dir if args.output_dir else ROOT / 'reports'
    
    # 确保输出目录是目录而不是文件
    if outdir.exists() and not outdir.is_dir():
        logger.error(f"输出路径已存在且不是目录: {outdir}")
        return
    
    outdir.mkdir(parents=True, exist_ok=True)
    
    # 扫描所有Review文件
    logger.info(f"扫描目录: {ROOT}")
    logger.info(f"文件模式: {args.pattern}")
    
    rows = []
    failed_files = []
    
    for md in sorted(ROOT.rglob(args.pattern)):
        if md.is_file():
            row = parse_review_file(md)
            if row:
                rows.append(row)
            else:
                failed_files.append(md)
    
    # 按日期时间排序
    rows.sort(key=lambda x: x.get('datetime', ''), reverse=True)
    
    # 写入输出文件
    csvfile = outdir / 'reviews_summary.csv'
    mdfile = outdir / 'reviews_summary.md'
    
    write_csv(rows, csvfile)
    write_markdown(rows, mdfile)
    
    # 输出统计信息
    logger.info(f"成功解析: {len(rows)} 个文件")
    if failed_files:
        logger.warning(f"失败文件: {len(failed_files)} 个")
        for f in failed_files:
            logger.warning(f"  - {f}")
    
    logger.info(f"CSV报告: {csvfile}")
    logger.info(f"Markdown报告: {mdfile}")


if __name__ == '__main__':
    main()