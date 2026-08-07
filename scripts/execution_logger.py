#!/usr/bin/env python3
"""
执行日志记录器（Execution Logger）- v2 重构版

核心功能：
1. 在Jupyter Notebook中记录每次Cell执行的代码和输出
2. 输出到Session专属的execution_log.json文件
3. 严格遵循 schemas/execution_log.schema.json v1.0.0
4. 支持在validate_practice.py中回溯审计

用法（在Jupyter Notebook中）：
    # 方式1：在第一个Cell中运行（自动从Session获取路径）
    %run scripts/execution_logger.py --init
    
    # 方式2：在代码中导入使用
    from core.session import Session
    from scripts.execution_logger import ExecutionLogger
    
    session = Session("session_id", ROOT)
    logger = ExecutionLogger(session=session)
    logger.start()

数据协议：
    严格遵循 schemas/execution_log.schema.json v1.0.0
"""
import json
import time
import sys
import hashlib
import argparse
import traceback as tb_module
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class ExecutionLogger:
    """执行日志记录器（基于Session）"""
    
    def __init__(self, session, auto_save: bool = True):
        """
        初始化执行日志记录器
        
        参数:
            session: Session 对象（提供 execution_log_path）
            auto_save: 是否自动保存（每次执行后保存）
        """
        self.session = session
        self.log_path = session.execution_log_path
        self.auto_save = auto_save
        self.events: List[Dict[str, Any]] = []
        self.event_count = 0
        
        # 加载已有日志（如果存在）
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.events = data.get('events', [])
                    self.event_count = len(self.events)
            except Exception as e:
                print(f"⚠️ 加载已有日志失败: {e}")
                self.events = []
                self.event_count = 0
    
    def record_execution(
        self,
        cell_index: int,
        code: str,
        output: str = "",
        error: Optional[Dict[str, str]] = None,
        execution_time: float = 0.0,
        execution_count: Optional[int] = None
    ):
        """
        记录一次Cell执行
        
        参数:
            cell_index: Cell索引（从0开始）
            code: 执行的代码
            output: 输出内容
            error: 错误信息字典（包含 type, message, traceback）
            execution_time: 执行时间（秒）
            execution_count: IPython execution counter（可选）
        """
        self.event_count = len(self.events) + 1
        
        # 计算代码哈希
        source_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        
        # 确定执行状态
        status = 'error' if error else 'success'
        
        # 构建事件（遵循 execution_log.schema.json v1.0.0）
        event = {
            'event_id': self.event_count,
            'cell_index': cell_index,
            'timestamp': datetime.now().isoformat(),
            'source': code.strip(),
            'source_hash': source_hash,
            'output': output.strip() if output else "",
            'status': status,
            'error': error,
            'duration_ms': round(execution_time * 1000, 2),
            'execution_count': execution_count or self.event_count,
        }
        
        self.events.append(event)
        
        if self.auto_save:
            self.save()
    
    def save(self):
        """保存日志到文件（遵循 Schema v1.0.0）"""
        # 加载元数据获取 session_id
        metadata = self.session.load_metadata()
        session_id = metadata.get('session_id', self.session.session_id) if metadata else self.session.session_id
        
        data = {
            'schema_version': '1.0.0',
            'session_id': session_id,
            'logger': {
                'version': '2.0.0'
            },
            'created_at': metadata.get('created_at', datetime.now().isoformat()) if metadata else datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'kernel_info': metadata.get('kernel_info', {}) if metadata else {},
            'events': self.events,
        }
        
        # 目录由 SessionFactory 保证，无需创建
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_errors(self) -> List[Dict]:
        """获取所有执行错误"""
        return [e for e in self.events if e.get('error')]
    
    def get_cell_history(self, cell_index: int) -> List[Dict]:
        """获取特定Cell的执行历史"""
        return [e for e in self.events if e['cell_index'] == cell_index]
    
    def start(self):
        """启动日志记录（注册IPython自动记录钩子）"""
        print(f"📝 执行日志记录器已启动")
        print(f"   日志路径: {self.log_path}")
        print(f"   自动保存: {self.auto_save}")
        
        # 注册IPython post_run_cell事件钩子
        try:
            from IPython.core.getipython import get_ipython
            ip = get_ipython()
            if ip is not None:
                self._register_ipython_hook(ip)
        except ImportError:
            pass  # 不在IPython环境中，忽略
    
    def _register_ipython_hook(self, ip):
        """注册IPython的post_run_cell事件钩子"""
        
        def post_run_cell_hook(result):
            """Cell执行后自动记录日志"""
            try:
                # 获取当前Cell的代码
                cell_code = ip.user_ns.get('_ih', [''])[-1] if hasattr(ip, 'user_ns') else ""
                
                # 获取输出
                output = ""
                if result is not None:
                    output = str(result)
                
                # 获取错误信息（如果有）
                error = None
                if hasattr(result, 'error_in_exec') and result.error_in_exec is not None:
                    error = {
                        'type': type(result.error_in_exec).__name__,
                        'message': str(result.error_in_exec),
                        'traceback': tb_module.format_exc()
                    }
                
                # 记录执行
                self.record_execution(
                    cell_index=ip.execution_count - 1 if ip.execution_count else 0,
                    code=cell_code,
                    output=output,
                    error=error,
                    execution_time=0.0,  # 暂时无法获取执行时间
                    execution_count=ip.execution_count
                )
            except Exception as e:
                # 钩子本身出错，不影响用户
                print(f"⚠️ 日志记录失败（不影响练习）: {e}")
        
        # 注册钩子
        ip.events.register('post_run_cell', post_run_cell_hook)
        print("✅ IPython自动记录钩子已注册")


def create_ipython_extension(session):
    """
    创建IPython扩展（用于Jupyter Notebook）
    
    参数:
        session: Session 对象
    """
    try:
        from IPython.core.getipython import get_ipython
    except ImportError:
        print("⚠️ IPython未安装，无法使用Jupyter集成")
        return None
    
    ip = get_ipython()
    if ip is None:
        print("⚠️ 不在IPython环境中")
        return None
    
    # 创建全局logger实例
    logger = ExecutionLogger(session=session)
    logger.start()
    
    @ip.register_magic_function
    def log_execution(line='', cell=None):
        """
        %%log_execution
        记录Cell执行的magic command
        """
        if cell is None:
            # line magic mode
            return
        
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
                execution_time=execution_time,
                execution_count=ip.execution_count
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 构建错误信息（遵循 Schema）
            error_info = {
                'type': type(e).__name__,
                'message': str(e),
                'traceback': tb_module.format_exc()
            }
            
            logger.record_execution(
                cell_index=ip.execution_count,
                code=cell,
                output="",
                error=error_info,
                execution_time=execution_time,
                execution_count=ip.execution_count
            )
            
            raise
    
    return logger


def init_logger(session):
    """
    初始化执行日志记录器（供Jupyter Notebook调用）
    
    参数:
        session: Session 对象
    """
    logger = ExecutionLogger(session=session)
    logger.start()
    
    # 尝试注册IPython magic
    ipy_logger = create_ipython_extension(session)
    if ipy_logger:
        print("✅ IPython magic已注册，可以使用 %%log_execution 记录Cell执行")
    
    return logger


def load_log(session) -> Optional[Dict]:
    """
    从Session安全读取execution_log
    
    参数:
        session: Session 对象
    
    返回:
        日志数据字典，或None（如果不存在）
    """
    log_path = session.execution_log_path
    if not log_path.exists():
        return None
    
    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='执行日志记录器')
    parser.add_argument('--init', action='store_true', help='初始化日志记录器')
    parser.add_argument('--session-id', type=str, help='Session ID')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    
    if args.init:
        if args.session_id:
            # 从项目根目录导入
            ROOT = Path(__file__).resolve().parent.parent
            sys.path.insert(0, str(ROOT))
            
            from core.session import Session
            session = Session(args.session_id, ROOT)
            init_logger(session)
        else:
            print("用法: python3 execution_logger.py --init --session-id <session_id>")
            print("或在Jupyter中: %run scripts/execution_logger.py --init")
    else:
        print("用法: python3 execution_logger.py --init [--session-id <session_id>]")
        print("或在Jupyter中: %run scripts/execution_logger.py --init")