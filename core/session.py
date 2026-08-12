"""
Session 实体类

职责：
- Session 实体
- 提供 workspace/logs/reports 路径访问
- metadata 读取保存

不负责创建逻辑。
"""
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class Session:
    """Session 实体类"""
    
    def __init__(self, session_id: str, root_dir: Path):
        """
        初始化 Session
        
        参数:
            session_id: Session 唯一标识
            root_dir: 项目根目录
        """
        self.session_id = session_id
        self.root_dir = root_dir
        self.session_dir = root_dir / 'sessions' / session_id
        
        # 便捷属性（从 metadata 惰性读取，metadata 不存在时返回 None）
        self._metadata_cache = None
        self._metadata_loaded = False
        
        # 子目录
        self.workspace_dir = self.session_dir / 'workspace'
        self.logs_dir = self.session_dir / 'logs'
        self.reports_dir = self.session_dir / 'reports'
        
        # 文件路径
        self.metadata_path = self.session_dir / 'metadata.json'
        self.execution_log_path = self.logs_dir / 'execution_log.json'
        self.report_path = self.reports_dir / 'report.json'
        self.summary_path = self.reports_dir / 'summary.md'
        self.practice_nb_path = self.workspace_dir / 'practice.ipynb'
    
    def exists(self) -> bool:
        """检查 Session 是否存在"""
        return self.session_dir.exists()
    
    def create_directories(self):
        """创建 Session 目录结构"""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def save_metadata(self, metadata: Dict):
        """保存 metadata"""
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def load_metadata(self) -> Optional[Dict]:
        """加载 metadata"""
        if not self.metadata_path.exists():
            return None
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._metadata_cache = data
        self._metadata_loaded = True
        return data
    
    @property
    def id(self) -> str:
        """Session 唯一标识（等价于 session_id）"""
        return self.session_id
    
    @property
    def chapter(self) -> Optional[str]:
        """章节编号（从 metadata 读取）"""
        if not self._metadata_loaded:
            self.load_metadata()
        if self._metadata_cache:
            return self._metadata_cache.get('chapter')
        return None
    
    @property
    def created_at(self) -> Optional[str]:
        """创建时间（从 metadata 读取）"""
        if not self._metadata_loaded:
            self.load_metadata()
        if self._metadata_cache:
            return self._metadata_cache.get('created_at')
        return None
    
    def save_execution_log(self, log_data: Dict):
        """保存 execution_log"""
        self.execution_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.execution_log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    def load_execution_log(self) -> Optional[Dict]:
        """加载 execution_log"""
        if not self.execution_log_path.exists():
            return None
        with open(self.execution_log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_report(self, report: Dict):
        """保存 report"""
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def load_report(self) -> Optional[Dict]:
        """加载 report"""
        if not self.report_path.exists():
            return None
        with open(self.report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_summary(self, summary: str):
        """保存 summary.md"""
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.summary_path.write_text(summary, encoding='utf-8')
    
    def load_summary(self) -> Optional[str]:
        """加载 summary.md"""
        if not self.summary_path.exists():
            return None
        return self.summary_path.read_text(encoding='utf-8')
    
    def update_status(self, status: str):
        """更新 Session 状态"""
        metadata = self.load_metadata()
        if metadata:
            metadata['status'] = status
            metadata['updated_at'] = datetime.now().isoformat()
            self.save_metadata(metadata)
    
    def __repr__(self):
        return f"Session(id='{self.session_id}', dir='{self.session_dir}')"
    
    def __str__(self):
        return f"Session {self.session_id} [{self.session_dir}]"