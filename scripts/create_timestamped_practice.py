#!/usr/bin/env python3
"""
创建考试会话（Exam Session）- v2 重构版

核心功能：
1. 使用 SessionFactory 创建 Session
2. 自动生成 session_id（格式：YYYYMMDD_HHMMSS_{random6}_chapter{chapter}）
3. 创建标准目录结构（workspace/logs/reports）
4. 注入执行日志初始化Cell到notebook
5. 支持旧模式兼容（可选）

用法:
  python3 scripts/create_timestamped_practice.py 1.1.1
  python3 scripts/create_timestamped_practice.py 1.1.1 --notebook 1.1.1.ipynb
  python3 scripts/create_timestamped_practice.py 1.1.1 --review
  python3 scripts/create_timestamped_practice.py 1.1.1 --mode exam
"""
import argparse
import csv
import datetime
import json
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.session_factory import SessionFactory


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='创建考试会话（Exam Session）')
    parser.add_argument(
        'chapter',
        nargs='?',
        default='1.1.1',
        help='章节编号，如 1.1.1'
    )
    parser.add_argument(
        '--notebook',
        type=str,
        default=None,
        help='指定模板 notebook 文件名（可选）'
    )
    parser.add_argument(
        '--mode',
        type=str,
        default='practice',
        choices=['practice', 'exam'],
        help='Session模式（默认：practice）'
    )
    parser.add_argument(
        '--review',
        action='store_true',
        help='同时创建 review 复盘文件（仅在有错误需要记录时使用）'
    )
    parser.add_argument(
        '--no-git',
        action='store_true',
        help='跳过 git 操作'
    )
    return parser.parse_args()


def inject_logger_init_cell(nb: dict, session) -> dict:
    """
    注入执行日志初始化Cell到notebook
    
    参数:
        nb: notebook 字典
        session: Session 对象
    
    返回:
        修改后的 notebook 字典
    """
    session_id = session.session_id
    root_dir = str(session.root_dir)
    
    # 使用字符串模板避免f-string中的逗号问题
    code_template = """# 自动初始化执行日志记录器（请勿删除）
import sys
from pathlib import Path
try:
    # 添加项目根目录到路径
    root_dir = Path('{ROOT_DIR}')
    sys.path.insert(0, str(root_dir))
    
    from core.session import Session
    from scripts.execution_logger import ExecutionLogger
    
    session = Session('{SESSION_ID}', root_dir)
    logger = ExecutionLogger(session=session, auto_save=True)
    logger.start()
    print('✅ 执行日志记录器已自动启动')
except Exception as e:
    print(f'⚠️ 日志记录器初始化失败（不影响练习）: {{e}}')
"""
    
    log_init_code = code_template.format(ROOT_DIR=root_dir, SESSION_ID=session_id)
    log_init_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {
            "tags": ["auto-init-execution-logger"],
            "description": "自动初始化执行日志记录器（无需手动运行）"
        },
        "outputs": [],
        "source": [line + '\n' for line in log_init_code.strip().split('\n')]
    }
    
    # 插入到第一个Cell之前
    nb['cells'].insert(0, log_init_cell)
    return nb


def create_review_file(session, chapter: str, now_str: str) -> Path:
    """
    创建 review 复盘文件
    
    参数:
        session: Session 实例
        chapter: 章节编号
        now_str: 时间戳字符串
    
    返回:
        review 文件路径
    """
    review_path = session.workspace_dir / f'{chapter}_practice_{now_str}_review.md'
    review_content = f'''# {chapter} 练习 review ({now_str})

- Session ID：`{session.session_id}`
- 练习 notebook：`practice.ipynb`
- 模板 notebook：`{Path(session.load_metadata()['template_file']).name}`（保持填空原样）

## 练习目标
- 在 `practice.ipynb` 中完成所有下划线填空
- 运行 notebook，确认计算结果没有异常
- 和 `_guide.md` 对照，记录差异与错误点

## 练习步骤
1. 打开 `practice.ipynb`，完成所有下划线填空
2. 运行 notebook，确认计算结果没有异常
3. 与 `_guide.md` 对照，补充差异记录

## 练习结果记录
- 问题点：
  - 
- 与标准答案不同之处：
  - 
- 发现的错误：
  - 
- 改进建议：
  - 

## review 结论
- 做得对的地方：
  - 
- 需要改进的地方：
  - 
'''
    review_path.write_text(review_content, encoding='utf-8')
    return review_path


def main():
    """主函数"""
    args = parse_args()
    chapter = args.chapter
    do_review = args.review
    no_git = args.no_git
    
    # 创建 SessionFactory
    factory = SessionFactory(ROOT)
    
    try:
        # 创建 Session
        session = factory.create(
            chapter=chapter,
            mode=args.mode,
            notebook_name=args.notebook
        )
        
        # 注入日志初始化Cell
        nb = json.loads(session.practice_nb_path.read_text(encoding='utf-8'))
        nb = inject_logger_init_cell(nb, session)
        session.practice_nb_path.write_text(
            json.dumps(nb, ensure_ascii=False, indent=1) + '\n',
            encoding='utf-8'
        )
        
        # 输出 Session 信息
        print(f'✅ Session 创建成功')
        print(f'   Session ID: {session.session_id}')
        print(f'   章节: {chapter}')
        print(f'   模式: {args.mode}')
        print(f'   目录: {session.session_dir}')
        print(f'   练习文件: {session.practice_nb_path}')
        print(f'   执行日志: {session.execution_log_path}')
        
        # 生成时间戳（用于兼容旧模式）
        now = datetime.datetime.now()
        now_str = now.strftime('%Y%m%d%H%M')
        
        # 如果需要创建 review 文件
        if do_review:
            review_path = create_review_file(session, chapter, now_str)
            print(f'   Review 文件: {review_path}')
            
            # 更新 daily_practice_log.csv
            log_csv = ROOT / 'daily_practice_log.csv'
            if not log_csv.exists():
                with log_csv.open('w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'date', 'notebook', 'summary', 'completed_steps',
                        'errors_found', 'error_rate', 'error_points',
                        'improvement_actions', 'fixed', 'notes'
                    ])
            
            row = [
                datetime.date.today().isoformat(),
                session.session_id,
                f'创建 {chapter} 考试会话并生成 review 记录',
                '创建练习 notebook->生成复盘 md',
                '0',
                '0%',
                '待练习后补充',
                '完成基本练习版本创建',
                'no',
                str(review_path)
            ]
            with log_csv.open('a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            
            # 运行聚合脚本
            subprocess.run(['python3', 'scripts/aggregate_reviews.py'], check=True)
        
        # Git 操作（可选）
        if not no_git:
            files_to_add = [
                str(session.session_dir),
            ]
            if do_review:
                files_to_add.append(str(log_csv))
                files_to_add.append('reports/reviews_summary.csv')
                files_to_add.append('reports/reviews_summary.md')
            
            subprocess.run(['git', 'add'] + files_to_add, check=True)
            commit_msg = f'Create exam session for {chapter} ({session.session_id})'
            if do_review:
                commit_msg += ' with review'
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        print(f'\n🎉 完成！请在 Jupyter 中打开: {session.practice_nb_path}')
        
    except FileNotFoundError as e:
        print(f'❌ 错误: {e}', file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f'❌ 错误: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()