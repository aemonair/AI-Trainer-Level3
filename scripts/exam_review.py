#!/usr/bin/env python3
"""
考试化错题统计与分析脚本

核心功能：
1. 读取 exam_db.csv，计算加权风险分
2. 输出高危题目清单（按危险系数排序）
3. 生成考试前24小时急救清单
4. 支持 --weak 模式只看重点复习题目

加权风险分 = 错误次数*2 + 连续错误*3 - 最近正确*1

用法:
  python3 scripts/exam_review.py              # 显示全部
  python3 scripts/exam_review.py --weak       # 只看高危题目
  python3 scripts/exam_review.py --rescue     # 考试前24小时急救清单
  python3 scripts/exam_review.py --update     # 从 review.md 自动更新 exam_db.csv
"""
from pathlib import Path
import csv
import re
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'exam_db.csv'


def load_db() -> List[Dict]:
    """加载考试数据库"""
    if not DB_PATH.exists():
        logger.error(f"数据库文件不存在: {DB_PATH}")
        return []
    
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def calc_risk_score(row: Dict) -> float:
    """
    计算加权风险分
    
    公式：错误次数*2 + 连续错误*3 - 最近正确*1
    """
    errors = int(row.get('累计错误次数', 0))
    consecutive = int(row.get('连续错误次数', 0))
    recent_correct = 1 if row.get('最近一次结果') == '正确' else 0
    
    return errors * 2 + consecutive * 3 - recent_correct * 1


def classify_status(row: Dict) -> str:
    """自动判断掌握状态"""
    risk = calc_risk_score(row)
    recent = row.get('最近一次结果', '')
    
    if risk <= 1 and recent == '正确':
        return '✅ 已掌握'
    elif risk >= 5:
        return '🚨 高危'
    elif risk >= 3:
        return '⚠️ 注意'
    else:
        return '🟡 一般'


def show_all(db: List[Dict]):
    """显示全部题目状态"""
    print("\n📊 考试风险矩阵\n")
    print(f"{'题目ID':<10} {'练习次数':<8} {'最近结果':<8} {'累计错误':<8} {'连续错误':<8} {'风险分':<8} {'状态'}")
    print("-" * 80)
    
    for row in sorted(db, key=lambda x: calc_risk_score(x), reverse=True):
        risk = calc_risk_score(row)
        status = classify_status(row)
        print(
            f"{row['题目ID']:<10} "
            f"{row['总练习次数']:<8} "
            f"{row['最近一次结果']:<8} "
            f"{row['累计错误次数']:<8} "
            f"{row['连续错误次数']:<8} "
            f"{risk:<8} "
            f"{status}"
        )


def show_weak(db: List[Dict]):
    """显示高危题目（重点复习）"""
    weak = []
    mastered = []
    
    for row in db:
        risk = calc_risk_score(row)
        if risk >= 3:
            weak.append((risk, row))
        else:
            mastered.append(row)
    
    # 按风险分降序排列
    weak.sort(key=lambda x: x[0], reverse=True)
    
    print("\n🚨 重点复习（按危险系数排序）：")
    if not weak:
        print("  暂无高危题目，继续保持！")
    else:
        for i, (risk, row) in enumerate(weak, 1):
            trap = row.get('最大陷阱', '未知')
            print(f"{i}. {row['题目ID']} {row.get('核心考点', '')}  |  "
                  f"错误{row['累计错误次数']}次，最近连续错{row['连续错误次数']}次  |  "
                  f"陷阱：{trap}")
    
    print(f"\n✅ 已掌握（可跳过）：")
    if not mastered:
        print("  暂无已掌握题目")
    else:
        for i, row in enumerate(mastered, 1):
            print(f"{i}. {row['题目ID']} {row.get('核心考点', '')}  |  "
                  f"最近{row['总练习次数']}次全对")


def show_rescue(db: List[Dict]):
    """考试前24小时急救清单"""
    print("\n🆘 考试前24小时急救清单\n")
    print("筛选条件：最近3次平均分 < 60% 或 连续错误 >= 2\n")
    
    rescue = []
    for row in db:
        consecutive = int(row.get('连续错误次数', 0))
        errors = int(row.get('累计错误次数', 0))
        total = int(row.get('总练习次数', 1))
        
        # 简单判断：连续错误 >= 2 或 错误率 > 50%
        error_rate = errors / total if total > 0 else 0
        if consecutive >= 2 or error_rate > 0.5:
            rescue.append(row)
    
    if not rescue:
        print("✅ 无高危题目，可以直接上考场！")
        return
    
    rescue.sort(key=lambda x: int(x['连续错误次数']), reverse=True)
    
    print("⚠️ 必须复习的题目：")
    for i, row in enumerate(rescue, 1):
        print(f"\n{i}. {row['题目ID']}")
        print(f"   核心考点：{row.get('核心考点', '未知')}")
        print(f"   最大陷阱：{row.get('最大陷阱', '未知')}")
        print(f"   关键代码：{row.get('关键代码骨架', '未知')}")


def extract_score_from_review(content: str) -> Optional[float]:
    """
    从 review 文件中提取评分百分比
    
    支持格式：
    - | **总计** | **18** | **18** | **100%** |
    - | 总计 | 18 | 18 | 100% |
    """
    pattern = re.compile(
        r'\|\s*\*?总计\*?\s*\|'
        r'\s*\*?[\d.]+\*?\s*\|'
        r'\s*\*?([\d.]+)\*?\s*\|'
        r'\s*\*?([\d.]+)%\*?\s*\|',
        re.IGNORECASE
    )
    match = pattern.search(content)
    if match:
        try:
            return float(match.group(2))
        except ValueError:
            return None
    return None


def is_review_correct(content: str) -> bool:
    """
    判断一次练习是否正确
    
    优先级：
    1. 评分 >= 90% → 正确
    2. 有 ❌ 错误记录 → 错误
    3. 默认正确
    """
    score = extract_score_from_review(content)
    if score is not None:
        return score >= 90
    
    # 回退：检查是否有明确的错误标记
    # 注意：要排除"历史错误分析"等章节
    error_section = re.search(r'## ❌ 错误记录\n(.*?)(?=##|$)', content, re.DOTALL)
    if error_section:
        return '错误1' not in error_section.group(1)
    
    return True


def update_db_from_reviews():
    """从 review.md 文件自动更新 exam_db.csv"""
    logger.info("正在扫描所有 review.md 文件...")
    
    reviews = list(ROOT.rglob('*_review.md'))
    logger.info(f"找到 {len(reviews)} 个 review 文件")
    
    # 按题目ID分组
    topic_reviews: Dict[str, List[Path]] = {}
    for r in reviews:
        match = re.match(r'^(\d+\.\d+\.\d+)', r.stem)
        if match:
            topic_id = match.group(1)
            topic_reviews.setdefault(topic_id, []).append(r)
    
    logger.info(f"涉及 {len(topic_reviews)} 个题目")
    
    # 加载现有数据库（保留手动录入的考点/陷阱/代码）
    existing_db = {}
    if DB_PATH.exists():
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_db[row['题目ID']] = row
    
    # 构建新数据库
    new_rows = []
    for topic_id in sorted(topic_reviews.keys()):
        files = sorted(topic_reviews[topic_id])
        total = len(files)
        
        # 分析最后一次练习的结果
        last_file = files[-1]
        content = last_file.read_text(encoding='utf-8')
        recent_correct = is_review_correct(content)
        recent_result = '正确' if recent_correct else '错误'
        
        # 统计每次练习的错误情况
        results_sequence = []
        total_errors = 0
        for f in files:
            c = f.read_text(encoding='utf-8')
            is_correct = is_review_correct(c)
            results_sequence.append(is_correct)
            
            # 统计错误数（排除历史回顾章节）
            # 移除"历史错误分析"等章节，只保留当前练习的错误
            c_cleaned = re.sub(r'## .*历史.*?(?=## |\Z)', '', c, flags=re.DOTALL)
            # 匹配 ### 错误N 或 #### 错误N
            total_errors += len(re.findall(r'#{3,4} 错误\d+', c_cleaned))
        
        # 连续错误次数（从后往前数）
        consecutive_errors = 0
        for is_correct in reversed(results_sequence):
            if not is_correct:
                consecutive_errors += 1
            else:
                break
        
        # 从现有数据库保留手动录入的信息
        existing = existing_db.get(topic_id, {})
        core_point = existing.get('核心考点', '')
        trap = existing.get('最大陷阱', '')
        code_skeleton = existing.get('关键代码骨架', '')
        
        new_rows.append({
            '题目ID': topic_id,
            '总练习次数': total,
            '最近一次结果': recent_result,
            '累计错误次数': total_errors,
            '连续错误次数': consecutive_errors,
            '掌握状态': '',
            '核心考点': core_point,
            '最大陷阱': trap,
            '关键代码骨架': code_skeleton
        })
    
    # 写入新数据库
    fieldnames = ['题目ID', '总练习次数', '最近一次结果', '累计错误次数', 
                  '连续错误次数', '掌握状态', '核心考点', '最大陷阱', '关键代码骨架']
    
    with open(DB_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in new_rows:
            risk = row['累计错误次数'] * 2 + row['连续错误次数'] * 3 - (1 if row['最近一次结果'] == '正确' else 0)
            if risk <= 1 and row['最近一次结果'] == '正确':
                row['掌握状态'] = '已掌握'
            elif risk >= 5:
                row['掌握状态'] = '高危'
            elif risk >= 3:
                row['掌握状态'] = '注意'
            else:
                row['掌握状态'] = '一般'
            writer.writerow(row)
    
    logger.info(f"已更新 {DB_PATH}，共 {len(new_rows)} 条记录")


def main():
    parser = argparse.ArgumentParser(description='考试化错题统计与分析')
    parser.add_argument('--weak', action='store_true', help='只看高危题目')
    parser.add_argument('--rescue', action='store_true', help='考试前24小时急救清单')
    parser.add_argument('--update', action='store_true', help='从 review.md 自动更新数据库')
    args = parser.parse_args()
    
    if args.update:
        update_db_from_reviews()
        return
    
    db = load_db()
    if not db:
        return
    
    if args.weak:
        show_weak(db)
    elif args.rescue:
        show_rescue(db)
    else:
        show_all(db)


if __name__ == '__main__':
    main()