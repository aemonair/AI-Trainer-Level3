import os
import sys
from pathlib import Path

def init_practice_logger():
    try:
        cwd = os.getcwd()
        if "sessions" not in cwd or "chapter" not in cwd:
            print("⚠️ 当前目录不在练习 session 中，跳过日志初始化")
            return None

        p = Path(cwd).resolve()
        while p != p.parent:
            if (p / "core").exists() and (p / "sessions").exists():
                root_dir = p
                break
            p = p.parent
        else:
            print("⚠️ 未找到项目根目录，跳过日志初始化")
            return None

        sys.path.insert(0, str(root_dir))

        from core.session import Session
        from scripts.execution_logger import ExecutionLogger

        session_dir = Path(cwd).resolve()
        while session_dir.parent != session_dir:
            if (session_dir / "metadata.json").exists() and (session_dir / "workspace").is_dir():
                break
            session_dir = session_dir.parent
        else:
            print("⚠️ 未找到 session 目录，跳过日志初始化")
            return None

        with open(session_dir / "metadata.json", "r", encoding="utf-8") as f:
            import json
            meta = json.load(f)
        session_id = meta.get("session_id", "")
        if not session_id:
            print("⚠️ metadata.json 中无 session_id，跳过日志初始化")
            return None

        session = Session(session_id, root_dir)
        logger = ExecutionLogger(session=session, auto_save=True)
        logger.start()

        ip = get_ipython()
        if ip is not None:
            logger.register_ipython_hook(ip)
            logger.save()

        print(f"✅ 练习日志已初始化")
        print(f"   Session: {session_id}")
        print(f"   日志: {logger.log_path}")
        return logger
    except Exception as e:
        print(f"⚠️ 日志初始化失败: {e}")
        return None