import os
import sys
from pathlib import Path

def _auto_init_practice_logger():
    try:
        cwd = os.getcwd()
        if 'sessions' not in cwd or 'chapter' not in cwd:
            return

        p = Path(cwd).resolve()
        while p != p.parent:
            if (p / 'core').exists() and (p / 'sessions').exists():
                root_dir = p
                break
            p = p.parent
        else:
            return

        sys.path.insert(0, str(root_dir))

        from core.session import Session
        from scripts.execution_logger import ExecutionLogger

        session_dir = Path(cwd).resolve()
        while session_dir.parent != session_dir:
            if (session_dir / 'metadata.json').exists() and (session_dir / 'workspace').is_dir():
                break
            session_dir = session_dir.parent
        else:
            return

        with open(session_dir / 'metadata.json', 'r', encoding='utf-8') as f:
            import json
            meta = json.load(f)
        session_id = meta.get('session_id', '')
        if not session_id:
            return

        session = Session(session_id, root_dir)
        logger = ExecutionLogger(session=session, auto_save=True)
        logger.start()

        ip = get_ipython()
        if ip is not None:
            logger.register_ipython_hook(ip)
            logger.save()

        print(f'✅ 练习日志自动初始化（IPython startup）')
        print(f'   Session: {session_id}')
        print(f'   日志: {logger.log_path}')
    except Exception:
        pass

_auto_init_practice_logger()