#!/usr/bin/env python3
"""
考试会话（Exam Session）管理模块

核心功能：
1. 创建考试会话目录结构
2. 管理会话生命周期
3. 提供会话查询和统计功能

目录结构：
sessions/
└── 2026-08-05-1430-chapter1.1.1/
    ├── practice.ipynb      # 考生的答卷
    ├── report.json         # validate_practice.py 生成的评分报告
    └── summary.md          # exam_review.py 生成的考试分析
"""
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'


def create_session(chapter: str, practice_nb_path: Optional[Path] = None) -> Path:
    """
    创建考试会话目录
    
    参数:
        chapter: 章节编号，如 '1.1.1'
        practice_nb_path: 练习文件路径（可选）
    
    返回:
        会话目录路径
    """
    now = datetime.now()
    session_id = f"{now.strftime('%Y-%m-%d-%H%M')}-chapter{chapter}"
    session_dir = SESSIONS_DIR / session_id
    
    session_dir.mkdir(parents=True, exist_ok=True)
    
    if practice_nb_path and practice_nb_path.exists():
        import shutil
        dest_nb = session_dir / 'practice.ipynb'
        shutil.copy2(practice_nb_path, dest_nb)
        logger.info(f"已复制练习文件到: {dest_nb}")
    
    logger.info(f"已创建考试会话: {session_dir}")
    return session_dir


def save_report(session_dir: Path, report_data: Dict) -> Path:
    """
    保存评分报告到会话目录
    
    参数:
        session_dir: 会话目录路径
        report_data: 评分报告数据（字典）
    
    返回:
        报告文件路径
    """
    report_path = session_dir / 'report.json'
    
    report_data['session_id'] = session_dir.name
    report_data['generated_at'] = datetime.now().isoformat()
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"评分报告已保存: {report_path}")
    return report_path


def save_summary(session_dir: Path, summary_text: str) -> Path:
    """
    保存考试分析摘要到会话目录
    
    参数:
        session_dir: 会话目录路径
        summary_text: 摘要文本（Markdown格式）
    
    返回:
        摘要文件路径
    """
    summary_path = session_dir / 'summary.md'
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)
    
    logger.info(f"考试分析摘要已保存: {summary_path}")
    return summary_path


def get_session(session_id: str) -> Optional[Dict]:
    """
    获取单个会话信息
    
    参数:
        session_id: 会话ID（目录名）
    
    返回:
        会话信息字典，失败时返回None
    """
    session_dir = SESSIONS_DIR / session_id
    
    if not session_dir.exists():
        logger.warning(f"会话不存在: {session_dir}")
        return None
    
    report_path = session_dir / 'report.json'
    
    session_info = {
        'session_id': session_id,
        'session_dir': str(session_dir),
        'has_report': report_path.exists(),
        'has_practice': (session_dir / 'practice.ipynb').exists(),
        'has_summary': (session_dir / 'summary.md').exists(),
    }
    
    if report_path.exists():
        with open(report_path, 'r', encoding='utf-8') as f:
            session_info['report'] = json.load(f)
    
    return session_info


def list_sessions(chapter: Optional[str] = None, limit: int = None) -> List[Dict]:
    """
    列出所有考试会话
    
    参数:
        chapter: 章节过滤（可选）
        limit: 返回数量限制（可选）
    
    返回:
        会话信息列表
    """
    if not SESSIONS_DIR.exists():
        return []
    
    sessions = []
    
    for session_dir in sorted(SESSIONS_DIR.iterdir()):
        if not session_dir.is_dir():
            continue
        
        session_id = session_dir.name
        
        if chapter and chapter not in session_id:
            continue
        
        report_path = session_dir / 'report.json'
        
        session_info = {
            'session_id': session_id,
            'session_dir': str(session_dir),
            'has_report': report_path.exists(),
            'has_practice': (session_dir / 'practice.ipynb').exists(),
        }
        
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                session_info['score'] = report.get('score')
                session_info['total_score'] = report.get('total_score')
                session_info['chapter'] = report.get('chapter')
                session_info['duration_minutes'] = report.get('duration_minutes')
        
        sessions.append(session_info)
    
    if limit:
        sessions = sessions[:limit]
    
    return sessions


def parse_session_id(session_id: str) -> Dict:
    """
    解析会话ID，提取时间、章节等信息
    
    参数:
        session_id: 会话ID，如 '2026-08-05-1430-chapter1.1.1'
    
    返回:
        解析后的信息字典
    """
    pattern = r'(\d{4}-\d{2}-\d{2})-(\d{4})-chapter(.+)'
    match = re.match(pattern, session_id)
    
    if not match:
        return {}
    
    return {
        'date': match.group(1),
        'time': match.group(2),
        'chapter': match.group(3),
        'datetime': f"{match.group(1)} {match.group(2)[:2]}:{match.group(2)[2:]}"
    }


def get_session_stats() -> Dict:
    """
    获取所有会话的统计信息
    
    返回:
        统计信息字典
    """
    sessions = list_sessions()
    
    if not sessions:
        return {
            'total_sessions': 0,
            'avg_score': 0,
            'max_score': 0,
            'min_score': 0,
            'pass_rate': 0,
        }
    
    scores = [s['score'] for s in sessions if s.get('score') is not None]
    
    if not scores:
        return {
            'total_sessions': len(sessions),
            'avg_score': 0,
            'max_score': 0,
            'min_score': 0,
            'pass_rate': 0,
        }
    
    pass_threshold = 60
    passed = sum(1 for s in scores if s >= pass_threshold)
    
    return {
        'total_sessions': len(sessions),
        'avg_score': sum(scores) / len(scores),
        'max_score': max(scores),
        'min_score': min(scores),
        'pass_rate': passed / len(scores) * 100,
    }