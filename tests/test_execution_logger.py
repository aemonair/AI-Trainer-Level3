"""
Execution Logger 测试

验证：
- 传入 Session 对象能正确写入日志
- 日志文件落在 sessions/{id}/logs/execution_log.json
- 写入的内容能通过 JSON Schema 验证
"""
import json
import pytest
from pathlib import Path
import tempfile
import shutil
import sys

# 添加项目根目录到 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.session_factory import SessionFactory
from scripts.execution_logger import ExecutionLogger, load_log


@pytest.fixture
def temp_project():
    """创建临时项目目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def factory(temp_project):
    """创建 SessionFactory"""
    return SessionFactory(temp_project)


@pytest.fixture
def sample_template(temp_project):
    """创建示例模板文件"""
    chapter = '1.1.1'
    materials_dir = temp_project / f'{chapter}-materials'
    materials_dir.mkdir()
    
    template_nb = materials_dir / f'{chapter}.ipynb'
    template_content = {
        'cells': [
            {
                'cell_type': 'code',
                'execution_count': None,
                'metadata': {},
                'outputs': [],
                'source': ['# 示例代码']
            }
        ],
        'metadata': {},
        'nbformat': 4,
        'nbformat_minor': 5
    }
    template_nb.write_text(json.dumps(template_content), encoding='utf-8')
    return template_nb


@pytest.fixture
def session_with_template(factory, sample_template):
    """创建带有模板的 Session"""
    return factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )


def test_logger_creates_log_file(session_with_template):
    """测试：传入 Session 对象能正确写入日志"""
    logger = ExecutionLogger(session=session_with_template, auto_save=True)
    
    # 记录一次执行
    logger.record_execution(
        cell_index=0,
        code="print('hello')",
        output="hello",
        execution_time=0.5
    )
    
    # 验证日志文件存在
    assert session_with_template.execution_log_path.exists()
    
    # 验证日志内容
    log_data = json.loads(session_with_template.execution_log_path.read_text())
    assert len(log_data['events']) == 1
    assert log_data['events'][0]['source'] == "print('hello')"
    assert log_data['events'][0]['status'] == 'success'


def test_log_path_correct(session_with_template):
    """测试：日志文件落在 sessions/{id}/logs/execution_log.json"""
    logger = ExecutionLogger(session=session_with_template, auto_save=False)
    
    expected_path = session_with_template.session_dir / 'logs' / 'execution_log.json'
    assert logger.log_path == expected_path


def test_log_follows_schema(session_with_template):
    """测试：写入的内容能通过 JSON Schema 验证"""
    logger = ExecutionLogger(session=session_with_template, auto_save=True)
    
    # 记录成功执行
    logger.record_execution(
        cell_index=0,
        code="x = 1 + 1",
        output="2",
        execution_time=0.1
    )
    
    # 记录错误执行
    logger.record_execution(
        cell_index=1,
        code="print(undefined_var)",
        output="",
        error={
            'type': 'NameError',
            'message': "name 'undefined_var' is not defined",
            'traceback': 'Traceback (most recent call last):...'
        },
        execution_time=0.2
    )
    
    # 加载日志
    log_data = json.loads(session_with_template.execution_log_path.read_text())
    
    # 验证 Schema 必需字段
    assert log_data['schema_version'] == '1.0.0'
    assert log_data['session_id'] == session_with_template.session_id
    assert 'logger' in log_data
    assert 'version' in log_data['logger']
    assert 'created_at' in log_data
    assert 'updated_at' in log_data
    assert 'events' in log_data
    
    # 验证事件字段
    assert len(log_data['events']) == 2
    
    # 验证第一个事件（成功）
    event1 = log_data['events'][0]
    assert event1['event_id'] == 1
    assert event1['cell_index'] == 0
    assert event1['source'] == "x = 1 + 1"
    assert event1['source_hash']  # 应该有哈希
    assert event1['status'] == 'success'
    assert event1['duration_ms'] == 100.0  # 0.1秒 = 100毫秒
    
    # 验证第二个事件（错误）
    event2 = log_data['events'][1]
    assert event2['event_id'] == 2
    assert event2['status'] == 'error'
    assert event2['error']['type'] == 'NameError'
    assert event2['error']['message'] == "name 'undefined_var' is not defined"


def test_load_log_function(session_with_template):
    """测试：load_log 函数能正确读取日志"""
    logger = ExecutionLogger(session=session_with_template, auto_save=True)
    
    logger.record_execution(
        cell_index=0,
        code="test",
        output="output"
    )
    
    # 使用 load_log 读取
    log_data = load_log(session_with_template)
    
    assert log_data is not None
    assert len(log_data['events']) == 1


def test_load_log_nonexistent(temp_project):
    """测试：load_log 在日志不存在时返回 None"""
    from core.session import Session
    
    session = Session("nonexistent_session", temp_project)
    result = load_log(session)
    
    assert result is None


def test_logger_auto_save(session_with_template):
    """测试：auto_save=True 时自动保存"""
    logger = ExecutionLogger(session=session_with_template, auto_save=True)
    
    logger.record_execution(
        cell_index=0,
        code="test"
    )
    
    # 应该已经保存
    assert session_with_template.execution_log_path.exists()


def test_logger_manual_save(session_with_template):
    """测试：auto_save=False 时需要手动保存"""
    logger = ExecutionLogger(session=session_with_template, auto_save=False)
    
    # 记录前检查 events 为空
    assert len(logger.events) == 0
    
    logger.record_execution(
        cell_index=0,
        code="test"
    )
    
    # events 应该有数据
    assert len(logger.events) == 1
    
    # 手动保存
    logger.save()
    
    # 现在应该保存到文件了
    log_data = json.loads(session_with_template.execution_log_path.read_text())
    assert len(log_data['events']) == 1


def test_get_errors(session_with_template):
    """测试：get_errors 返回所有错误"""
    logger = ExecutionLogger(session=session_with_template, auto_save=False)
    
    # 记录成功
    logger.record_execution(
        cell_index=0,
        code="x = 1",
        error=None
    )
    
    # 记录错误
    logger.record_execution(
        cell_index=1,
        code="y = undefined",
        error={'type': 'NameError', 'message': 'undefined'}
    )
    
    # 记录另一个错误
    logger.record_execution(
        cell_index=2,
        code="z = 1/0",
        error={'type': 'ZeroDivisionError', 'message': 'division by zero'}
    )
    
    errors = logger.get_errors()
    assert len(errors) == 2
    assert errors[0]['error']['type'] == 'NameError'
    assert errors[1]['error']['type'] == 'ZeroDivisionError'


def test_get_cell_history(session_with_template):
    """测试：get_cell_history 返回特定Cell的历史"""
    logger = ExecutionLogger(session=session_with_template, auto_save=False)
    
    # 记录 Cell 0 的多次执行
    logger.record_execution(cell_index=0, code="x = 1")
    logger.record_execution(cell_index=1, code="y = 2")
    logger.record_execution(cell_index=0, code="x = 2")
    
    history = logger.get_cell_history(0)
    assert len(history) == 2
    assert history[0]['source'] == "x = 1"
    assert history[1]['source'] == "x = 2"


def test_source_hash_generation(session_with_template):
    """测试：source_hash 正确生成"""
    import hashlib
    
    logger = ExecutionLogger(session=session_with_template, auto_save=False)
    
    code = "print('test')"
    logger.record_execution(
        cell_index=0,
        code=code
    )
    
    expected_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
    
    # 检查最后一个事件
    last_event = logger.events[-1]
    assert last_event['source_hash'] == expected_hash


def test_duration_ms_conversion(session_with_template):
    """测试：execution_time（秒）正确转换为 duration_ms（毫秒）"""
    logger = ExecutionLogger(session=session_with_template, auto_save=False)
    
    logger.record_execution(
        cell_index=0,
        code="test",
        execution_time=1.5  # 1.5秒
    )
    
    last_event = logger.events[-1]
    assert last_event['duration_ms'] == 1500.0


def test_no_mkdir_in_logger(session_with_template):
    """测试：ExecutionLogger 不负责创建目录（目录由 SessionFactory 保证）"""
    # 删除日志目录，模拟目录不存在的情况
    import shutil
    logs_dir = session_with_template.logs_dir
    if logs_dir.exists():
        shutil.rmtree(logs_dir)
    
    logger = ExecutionLogger(session=session_with_template, auto_save=False)
    logger.record_execution(cell_index=0, code="test")
    
    # save() 不应自动创建目录，目录不存在时应抛出异常
    with pytest.raises(FileNotFoundError):
        logger.save()


def test_no_path_discovery_in_logger(session_with_template):
    """测试：ExecutionLogger 使用 Session 提供的路径，不自行发现路径"""
    logger = ExecutionLogger(session=session_with_template, auto_save=False)
    
    # 日志路径应直接来自 Session，而非自行搜索
    assert logger.log_path == session_with_template.execution_log_path
    assert logger.log_path == session_with_template.session_dir / 'logs' / 'execution_log.json'
