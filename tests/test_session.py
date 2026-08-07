"""
Session 创建测试

验证：
- 创建Session成功
- 目录存在
- metadata存在
- execution_log存在
- notebook复制成功
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

from core.session import Session
from core.session_factory import SessionFactory


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


def test_create_session_success(factory, sample_template):
    """测试：创建Session成功"""
    session = factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )
    
    # 验证 session_id 格式
    assert 'chapter1.1.1' in session.session_id
    assert len(session.session_id.split('_')) >= 4
    
    # 验证目录存在
    assert session.session_dir.exists()
    assert session.workspace_dir.exists()
    assert session.logs_dir.exists()
    assert session.reports_dir.exists()


def test_metadata_created(factory, sample_template):
    """测试：metadata存在"""
    session = factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )
    
    assert session.metadata_path.exists()
    
    metadata = session.load_metadata()
    assert metadata is not None
    assert metadata['schema_version'] == '1.0.0'
    assert metadata['chapter'] == '1.1.1'
    assert metadata['mode'] == 'practice'
    assert metadata['status'] == 'in_progress'


def test_execution_log_created(factory, sample_template):
    """测试：execution_log存在"""
    session = factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )
    
    assert session.execution_log_path.exists()
    
    log = session.load_execution_log()
    assert log is not None
    assert log['schema_version'] == '1.0.0'
    assert log['session_id'] == session.session_id
    assert log['events'] == []


def test_notebook_copied(factory, sample_template):
    """测试：notebook复制成功"""
    session = factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )
    
    assert session.practice_nb_path.exists()
    
    # 验证内容
    original = json.loads(sample_template.read_text())
    copied = json.loads(session.practice_nb_path.read_text())
    assert original['cells'] == copied['cells']


def test_load_existing_session(factory, sample_template):
    """测试：加载已存在的Session"""
    # 先创建
    session1 = factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )
    
    # 再加载
    session2 = factory.load_session(session1.session_id)
    
    assert session2.session_id == session1.session_id
    assert session2.exists()


def test_session_id_format(factory):
    """测试：session_id格式正确"""
    session_id = factory.generate_session_id('1.1.1')
    
    parts = session_id.split('_')
    assert len(parts) >= 4
    assert len(parts[0]) == 8  # YYYYMMDD
    assert len(parts[1]) == 6  # HHMMSS
    assert len(parts[2]) == 6  # random
    assert parts[3].startswith('chapter')


def test_get_latest_session(factory, sample_template):
    """测试：获取最新Session"""
    factory.create(chapter='1.1.1', notebook_name='1.1.1.ipynb')
    factory.create(chapter='1.1.1', notebook_name='1.1.1.ipynb')
    
    latest = factory.get_latest_session(chapter='1.1.1')
    assert latest is not None
    assert 'chapter1.1.1' in latest.session_id


def test_no_notebook_raises_error(factory, temp_project):
    """测试：没有notebook时抛出错误"""
    chapter = '2.2.2'
    materials_dir = temp_project / f'{chapter}-materials'
    materials_dir.mkdir()
    
    with pytest.raises(FileNotFoundError):
        factory.create(chapter=chapter)


def test_multiple_notebooks_requires_specification(factory, temp_project):
    """测试：多个notebook时需要指定"""
    chapter = '3.3.3'
    materials_dir = temp_project / f'{chapter}-materials'
    materials_dir.mkdir()
    
    # 创建多个 notebook
    (materials_dir / '3.3.3.ipynb').write_text('{}')
    (materials_dir / '3.3.3_extra.ipynb').write_text('{}')
    
    with pytest.raises(ValueError):
        factory.create(chapter=chapter)


def test_session_update_status(factory, sample_template):
    """测试：更新Session状态"""
    session = factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )
    
    session.update_status('completed')
    
    metadata = session.load_metadata()
    assert metadata['status'] == 'completed'


def test_session_save_load_report(factory, sample_template):
    """测试：保存和加载report"""
    session = factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )
    
    report = {
        'schema_version': '1.0.0',
        'session_id': session.session_id,
        'chapter': '1.1.1',
        'scored_at': '2026-08-07T16:30:00',
        'total_score': 100,
        'earned_score': 85,
        'percentage': 85.0,
        'items': []
    }
    
    session.save_report(report)
    loaded_report = session.load_report()
    
    assert loaded_report is not None
    assert loaded_report['earned_score'] == 85


def test_session_save_load_summary(factory, sample_template):
    """测试：保存和加载summary"""
    session = factory.create(
        chapter='1.1.1',
        mode='practice',
        notebook_name='1.1.1.ipynb'
    )
    
    summary = "# 测试总结\n\n这是一个测试。"
    session.save_summary(summary)
    
    loaded_summary = session.load_summary()
    assert loaded_summary == summary