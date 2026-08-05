#!/usr/bin/env python3
"""
执行日志记录器（Execution Logger）

核心功能：
1. 在Jupyter Notebook中记录每次Cell执行的代码和输出
2. 输出到Session专属的execution_log.json文件
3. 支持在validate_practice.py中回溯审计

用法（在Jupyter Notebook中）：
    # 方式1：在第一个Cell中运行
    %run scripts/execution_logger.py --init
    
    # 方式2：手动指定日志路径
    %run scripts/execution_logger.py --init --log-path sessions/2026-08-05-1430-chapter1.1.1/execution_log.json
    
    # 方式3：在代码中导入使用
    from scripts.execution_logger import ExecutionLogger
    logger = ExecutionLogger(log_path="path/to/execution_log.json")
    logger.start()
"""
import json
import time
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import traceback


class ExecutionLogger:
    """执行日志记录器"""
    
    def __init__(self, log_path: Optional[Path] = None, auto_save: bool = True):
        """
        初始化执行日志记录器
        
        参数:
            log_path: 日志文件路径（可选，默认自动查找Session目录）
            auto_save: 是否自动保存（每次执行后保存）
        """
        self.log_path = log_path or self._find_default_log_path()
        self.auto_save = auto_save
        self.entries: List[Dict[str, Any]] = []
        self.session_start = datetime.now().isoformat()
        self.execution_count = 0
        self.session_uuid = None
        
        # 加载已有日志（如果存在）
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entries = data.get('entries', [])
                    self.session_start = data.get('session_start', self.session_start)
                    self.session_uuid = data.get('session_uuid')
                    # 修复：execution_count 基于已有 entries 长度递增，避免重置
                    self.execution_count = len(self.entries)
                    if not self.session_uuid:
                        import uuid
                        self.session_uuid = str(uuid.uuid4())
            except Exception as e:
                print(f"⚠️ 加载已有日志失败: {e}")
                import uuid
                self.session_uuid = str(uuid.uuid4())
        else:
            import uuid
            self.session_uuid = str(uuid.uuid4())
    
    def _find_default_log_path(self) -> Path:
        """自动查找默认日志路径（优先查找当前Notebook同目录下的*_execution_log.json）"""
        cwd = Path.cwd()
        
        # 策略1：查找当前目录下是否有 *_execution_log.json（匹配materials模式）
        log_files = list(cwd.glob('*_execution_log.json'))
        if log_files:
            # 如果有多个，取最新修改的
            return max(log_files, key=lambda p: p.stat().st_mtime)
        
        # 策略2：检查是否在Session目录中（旧模式）
        if 'sessions' in cwd.parts:
            sessions_idx = cwd.parts.index('sessions')
            session_dir = Path(*cwd.parts[:sessions_idx + 2])
            return session_dir / 'execution_log.json'
        
        # 策略3：向上查找sessions目录
        for parent in cwd.parents:
            if 'sessions' in parent.parts:
                sessions_idx = parent.parts.index('sessions')
                session_dir = Path(*parent.parts[:sessions_idx + 2])
                log_path = session_dir / 'execution_log.json'
                if log_path.exists():
                    return log_path
        
        # 策略4：默认返回当前目录下的execution_log.json
        return cwd / 'execution_log.json'
    
    def record_execution(self, cell_index: int, code: str, output: str = "", 
                        error: Optional[str] = None, execution_time: float = 0.0):
        """
        记录一次Cell执行（修复：execution_id基于已有条目递增）
        
        参数:
            cell_index: Cell索引（从0开始）
            code: 执行的代码
            output: 输出内容
            error: 错误信息（如果有）
            execution_time: 执行时间（秒）
        """
        # 使用已有entries长度作为ID基准，而不是自增计数器
        self.execution_count = len(self.entries) + 1
        
        entry = {
            'execution_id': self.execution_count,
            'cell_index': cell_index,
            'code': code.strip(),
            'output': output.strip() if output else "",
            'error': error,
            'execution_time': round(execution_time, 3),
            'timestamp': datetime.now().isoformat(),
        }
        
        self.entries.append(entry)
        
        if self.auto_save:
            self.save()
    
    def save(self):
        """保存日志到文件"""
        data = {
            'session_uuid': self.session_uuid,
            'session_start': self.session_start,
            'last_updated': datetime.now().isoformat(),
            'total_executions': len(self.entries),
            'entries': self.entries,
        }
        
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_errors(self) -> List[Dict]:
        """获取所有执行错误"""
        return [e for e in self.entries if e.get('error')]
    
    def get_cell_history(self, cell_index: int) -> List[Dict]:
        """获取特定Cell的执行历史"""
        return [e for e in self.entries if e['cell_index'] == cell_index]
    
    def start(self):
        """启动日志记录（打印提示信息）"""
        print(f"📝 执行日志记录器已启动")
        print(f"   日志路径: {self.log_path}")
        print(f"   自动保存: {self.auto_save}")


def create_ipython_extension():
    """创建IPython扩展（用于Jupyter Notebook）"""
    try:
        from IPython.core.getipython import get_ipython
        from IPython.core.magic import register_cell_magic
        from IPython.core.magic import register_line_magic
    except ImportError:
        print("⚠️ IPython未安装，无法使用Jupyter集成")
        return None
    
    ip = get_ipython()
    if ip is None:
        print("⚠️ 不在IPython环境中")
        return None
    
    # 创建全局logger实例
    logger = ExecutionLogger()
    logger.start()
    
    @register_cell_magic
    def log_execution(line, cell):
        """
        %%log_execution
        记录Cell执行的magic command
        """
        start_time = time.time()
        
        try:
            # 执行Cell代码
            result = ip.run_cell(cell)
            
            execution_time = time.time() - start_time
            
            # 记录执行
            logger.record_execution(
                cell_index=ip.execution_count,
                code=cell,
                output=str(result.result) if result.result else "",
                error=None,
                execution_time=execution_time
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            logger.record_execution(
                cell_index=ip.execution_count,
                code=cell,
                output="",
                error=error_msg,
                execution_time=execution_time
            )
            
            raise
    
    return logger


def init_logger(log_path: Optional[str] = None):
    """
    初始化执行日志记录器（供Jupyter Notebook调用）
    
    用法:
        %run scripts/execution_logger.py --init
        %run scripts/execution_logger.py --init --log-path path/to/log.json
    """
    if log_path:
        logger = ExecutionLogger(log_path=Path(log_path))
    else:
        logger = ExecutionLogger()
    
    logger.start()
    
    # 尝试注册IPython magic
    ipy_logger = create_ipython_extension()
    if ipy_logger:
        print("✅ IPython magic已注册，可以使用 %%log_execution 记录Cell执行")
    
    return logger


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='执行日志记录器')
    parser.add_argument('--init', action='store_true', help='初始化日志记录器')
    parser.add_argument('--log-path', type=str, help='日志文件路径')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    
    if args.init:
        init_logger(args.log_path)
    else:
        print("用法: python3 execution_logger.py --init [--log-path path/to/log.json]")
        print("或在Jupyter中: %run scripts/execution_logger.py --init")