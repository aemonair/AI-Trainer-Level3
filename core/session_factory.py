"""
Session 工厂类

职责：
- 创建 Session
- 生成 session_id
- 创建目录结构
- 初始化 metadata
- 初始化 execution_log
- 复制模板文件
"""
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from .session import Session


class SessionFactory:
    """Session 创建工厂"""
    
    def __init__(self, root_dir: Path):
        """
        初始化 SessionFactory
        
        参数:
            root_dir: 项目根目录
        """
        self.root_dir = root_dir
        self.sessions_dir = root_dir / 'sessions'
        self.sessions_dir.mkdir(exist_ok=True)
    
    def generate_session_id(self, chapter: str) -> str:
        """
        生成 session_id
        
        格式：YYYYMMDD_HHMMSS_{random6}_chapter{chapter}
        
        参数:
            chapter: 章节编号，如 1.1.1
        
        返回:
            session_id 字符串
        """
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        random_str = uuid.uuid4().hex[:6]
        return f"{timestamp}_{random_str}_chapter{chapter}"
    
    def find_chapter_notebooks(self, chapter: str) -> List[Path]:
        """
        查找章节目录下的所有 .ipynb 文件
        
        优先级：
        1. template/{chapter}/ 目录（标准模板）
        2. {chapter}-materials/ 目录（兼容旧版）
        
        参数:
            chapter: 章节编号
        
        返回:
            notebook 文件列表
        """
        # 优先使用 template/ 目录
        template_dir = self.root_dir / 'template' / chapter
        if template_dir.exists():
            notebooks = list(template_dir.glob('*.ipynb'))
            if notebooks:
                return sorted(notebooks)
        
        # Fallback 到 materials/ 目录（兼容旧版）
        materials_dir = self.root_dir / f'{chapter}-materials'
        if not materials_dir.exists():
            return []
        
        notebooks = list(materials_dir.glob('*.ipynb'))
        # 排除 practice 文件和 review 文件
        notebooks = [
            nb for nb in notebooks
            if '_practice_' not in nb.name and '_review' not in nb.name
        ]
        return sorted(notebooks)
    
    def _copy_template(self, src: Path, dest: Path, strategy: str = 'auto'):
        """
        复制模板文件到 workspace
        
        策略：
        - 小文件（.ipynb, .csv, .txt）：copy
        - 大文件（.onnx, .pkl, .mp4）：hard link -> symlink -> copy
        """
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # 获取文件扩展名
        suffix = src.suffix.lower()
        
        # 小文件策略
        small_file_suffixes = {'.ipynb', '.csv', '.txt', '.md', '.json'}
        
        if strategy == 'copy' or suffix in small_file_suffixes:
            shutil.copy2(src, dest)
        elif strategy == 'auto':
            # 自动判断
            if suffix in small_file_suffixes:
                shutil.copy2(src, dest)
            else:
                # 大文件尝试 hard link
                try:
                    src.link_to(dest)
                except OSError:
                    # 失败则尝试 symlink
                    try:
                        dest.symlink_to(src)
                    except OSError:
                        # 最后 fallback 到 copy
                        shutil.copy2(src, dest)
        else:
            shutil.copy2(src, dest)
    
    def _copy_chapter_data(self, chapter: str, workspace_dir: Path, strategy: str = 'auto'):
        """
        复制章节相关数据文件到 workspace
        
        注意：只从 template/ 目录复制文件，不再从 materials/ 复制额外文件
        template/ 目录应该包含所有必要的素材文件
        
        参数:
            chapter: 章节编号
            workspace_dir: workspace 目录
            strategy: 复制策略
        """
        # 只从 template/ 目录复制文件
        template_dir = self.root_dir / 'template' / chapter
        if not template_dir.exists():
            return
        
        # 复制 template 目录中的所有文件（排除 .ipynb，因为已经在 create() 中处理）
        for file_path in template_dir.iterdir():
            if not file_path.is_file():
                continue
            
            # 跳过 .ipynb 文件（已在 create() 中作为模板处理）
            if file_path.suffix.lower() == '.ipynb':
                continue
            
            dest = workspace_dir / file_path.name
            self._copy_template(file_path, dest, strategy=strategy)
    
    def create(
        self,
        chapter: str,
        mode: str = 'practice',
        notebook_name: Optional[str] = None,
        copy_strategy: str = 'auto'
    ) -> Session:
        """
        创建新 Session
        
        参数:
            chapter: 章节编号
            mode: Session模式（practice/exam）
            notebook_name: 指定要使用的 notebook 文件名（可选）
            copy_strategy: 文件复制策略（auto/copy/link）
        
        返回:
            Session 实例
        
        异常:
            FileNotFoundError: 章节目录不存在
            ValueError: 找不到模板 notebook 或有多个 notebook 但未指定
        """
        # 查找章节 notebook
        notebooks = self.find_chapter_notebooks(chapter)
        
        if len(notebooks) == 0:
            raise FileNotFoundError(
                f"章节 {chapter} 目录下找不到模板 notebook\n"
                f"请确保 {chapter}-materials/ 目录下有 .ipynb 文件"
            )
        
        if len(notebooks) > 1 and notebook_name is None:
            notebook_list = '\n'.join(f'  - {nb.name}' for nb in notebooks)
            raise ValueError(
                f"章节 {chapter} 目录下有多个 notebook 文件，请指定一个：\n{notebook_list}\n"
                f"使用 notebook_name 参数指定"
            )
        
        # 确定要使用的模板 notebook
        if notebook_name:
            template_nb = self.root_dir / f'{chapter}-materials' / notebook_name
            if not template_nb.exists():
                raise FileNotFoundError(f"指定的 notebook 不存在: {template_nb}")
        else:
            template_nb = notebooks[0]
        
        # 生成 session_id 并创建 Session
        session_id = self.generate_session_id(chapter)
        session = Session(session_id, self.root_dir)
        
        # 创建目录结构
        session.create_directories()
        
        # 初始化 metadata
        # template_file 使用相对路径（相对项目根目录），避免绝对路径硬编码导致跨机器/跨目录失败
        try:
            template_rel = template_nb.relative_to(self.root_dir)
        except ValueError:
            # 模板不在项目根目录下时，退化为文件名
            template_rel = Path(template_nb.name)
        metadata = {
            'schema_version': '1.0.0',
            'session_id': session_id,
            'chapter': chapter,
            'mode': mode,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'created',
            'template_file': str(template_rel),
            'practice_file': 'practice.ipynb',
        }
        session.save_metadata(metadata)
        
        # 初始化 execution_log
        execution_log = {
            'schema_version': '1.0.0',
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'kernel_info': {},
            'events': []
        }
        session.save_execution_log(execution_log)
        
        # 复制模板 notebook
        self._copy_template(template_nb, session.practice_nb_path, strategy=copy_strategy)
        
        # 复制章节数据文件
        self._copy_chapter_data(chapter, session.workspace_dir, strategy=copy_strategy)
        
        # 更新状态
        metadata['status'] = 'in_progress'
        metadata['updated_at'] = datetime.now().isoformat()
        session.save_metadata(metadata)
        
        return session
    
    def load_session(self, session_id: str) -> Session:
        """
        加载已存在的 Session
        
        参数:
            session_id: Session ID
        
        返回:
            Session 实例
        
        异常:
            FileNotFoundError: Session 不存在
        """
        session = Session(session_id, self.root_dir)
        if not session.exists():
            raise FileNotFoundError(f"Session 不存在: {session_id}")
        return session
    
    def get_latest_session(self, chapter: Optional[str] = None) -> Optional[Session]:
        """
        获取最新的 Session
        
        参数:
            chapter: 章节过滤（可选）
        
        返回:
            最新的 Session 实例，或 None
        """
        if not self.sessions_dir.exists():
            return None
        
        sessions = []
        for session_dir in sorted(self.sessions_dir.iterdir()):
            if not session_dir.is_dir():
                continue
            
            session_id = session_dir.name
            if chapter and chapter not in session_id:
                continue
            
            metadata_path = session_dir / 'metadata.json'
            if metadata_path.exists():
                sessions.append(session_id)
        
        if not sessions:
            return None
        
        return self.load_session(sessions[-1])