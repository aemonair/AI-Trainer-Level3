# Phase 2.1 基础设施重构完成报告

> 生成时间：2026-08-07
> 状态：✅ 完成
> 测试：12/12 通过

---

## 1. 修改文件列表

### 新增文件

| 文件 | 职责 |
|------|------|
| `core/__init__.py` | 核心模块初始化 |
| `core/session.py` | Session 实体类（路径访问、metadata 读写） |
| `core/session_factory.py` | Session 工厂类（创建、目录结构、文件复制） |
| `schemas/metadata.schema.json` | Session 元数据协议定义 |
| `schemas/execution_log.schema.json` | 执行日志协议定义 |
| `schemas/report.schema.json` | 评分报告协议定义 |
| `tests/__init__.py` | 测试模块初始化 |
| `tests/test_session.py` | Session 创建测试（12个测试用例） |

### 重构文件

| 文件 | 变化 |
|------|------|
| `scripts/create_timestamped_practice.py` | 从"自己处理一切"改为"调用 SessionFactory" |

---

## 2. 架构变化说明

### 之前

```
create_timestamped_practice.py
  ├─ 自己 mkdir
  ├─ 自己 copy 文件
  ├─ 自己创建 metadata
  ├─ 自己创建 execution_log
  └─ 路径散落在各处
```

### 现在

```
create_timestamped_practice.py
  └─ 调用 SessionFactory.create()
       └─ SessionFactory
            ├─ 生成 session_id
            ├─ 创建目录结构
            ├─ 初始化 metadata
            ├─ 初始化 execution_log
            └─ 复制模板文件
                 └─ Session
                      ├─ workspace/
                      ├─ logs/
                      └─ reports/
```

### 新目录结构

```
sessions/
└── {session_id}/
    ├── metadata.json          # Session 元数据
    ├── workspace/
    │   ├── practice.ipynb     # 练习 notebook
    │   └── *.csv/*.pkl        # 数据文件
    ├── logs/
    │   └── execution_log.json # 执行日志
    └── reports/
        ├── report.json        # 评分报告
        └── summary.md         # 总结报告
```

### session_id 格式升级

**之前**：`1.1.1_202608071630`

**现在**：`20260807_163000_a83f91_chapter1.1.1`

格式：`YYYYMMDD_HHMMSS_{random6}_chapter{chapter}`

---

## 3. 测试结果

```
============ test session starts ============
platform darwin -- Python 3.9.7, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai
collected 12 items

tests/test_session.py::test_create_session_success PASSED [  8%]
tests/test_session.py::test_metadata_created PASSED [ 16%]
tests/test_session.py::test_execution_log_created PASSED [ 25%]
tests/test_session.py::test_notebook_copied PASSED [ 33%]
tests/test_session.py::test_load_existing_session PASSED [ 41%]
tests/test_session.py::test_session_id_format PASSED [ 50%]
tests/test_session.py::test_get_latest_session PASSED [ 58%]
tests/test_session.py::test_no_notebook_raises_error PASSED [ 66%]
tests/test_session.py::test_multiple_notebooks_requires_specification PASSED [ 75%]
tests/test_session.py::test_session_update_status PASSED [ 83%]
tests/test_session.py::test_session_save_load_report PASSED [ 91%]
tests/test_session.py::test_session_save_load_summary PASSED [100%]

============ 12 passed in 0.16s =============
```

**所有测试通过 ✅**

---

## 4. 数据协议定义

### metadata.schema.json

定义 Session 元数据结构：
- `schema_version`: "1.0.0"
- `session_id`: 唯一标识
- `chapter`: 章节编号
- `mode`: practice/exam
- `status`: created/in_progress/completed/abandoned
- `kernel_info`: Jupyter Kernel 信息

### execution_log.schema.json

定义执行日志结构：
- `events[]`: 执行事件列表
  - `event_id`: 事件 ID
  - `cell_index`: Cell 索引
  - `source`: 代码内容
  - `source_hash`: 代码哈希
  - `status`: success/error/warning
  - `error`: 错误信息（含 fingerprint）
  - `duration_ms`: 执行耗时

### report.schema.json

定义评分报告结构：
- `total_score`: 总分
- `earned_score`: 得分
- `percentage`: 正确率
- `process_penalty`: 过程罚分
- `items[]`: 评分项列表
- `detected_errors[]`: 检测到的错误

---

## 5. 后续迁移建议

### Phase 2.2: 日志系统迁移

1. 更新 `execution_logger.py` 路径查找逻辑
2. 改为从 Session 获取日志路径
3. 更新 execution_log schema 到 v1

### Phase 2.3: 验证系统迁移

1. 重构 `validate_practice.py`
2. 统一 report.json schema
3. 集成 process_auditor

### Phase 2.4: 报告系统迁移

1. 更新 `exam_review.py`
2. 更新 `aggregate_reviews.py`
3. 清理旧数据

### 暂时不修改的文件

- `process_auditor.py` - 依赖新 schema
- `aggregate_reviews.py` - 依赖新 schema
- `exam_review.py` - 依赖新 schema
- `validate_practice.py` - 逻辑复杂，需要更多测试

---

## 6. 向后兼容

新架构保持向后兼容：

1. **旧 Session 仍然可用**：通过 `session_id` 查找
2. **旧脚本仍可运行**：`create_timestamped_practice.py` 保留原有功能
3. **数据迁移**：可提供迁移脚本将旧数据转换为新格式

---

## 7. 使用示例

### 创建新 Session

```bash
# 基本用法
uv run python3 scripts/create_timestamped_practice.py 1.1.1

# 指定 notebook
uv run python3 scripts/create_timestamped_practice.py 1.1.1 --notebook 1.1.1.ipynb

# 考试模式
uv run python3 scripts/create_timestamped_practice.py 1.1.1 --mode exam

# 跳过 git 操作
uv run python3 scripts/create_timestamped_practice.py 1.1.1 --no-git
```

### 在代码中使用

```python
from pathlib import Path
from core.session_factory import SessionFactory

ROOT = Path('.').resolve()
factory = SessionFactory(ROOT)

# 创建 Session
session = factory.create(
    chapter='1.1.1',
    mode='practice'
)

print(f"Session ID: {session.session_id}")
print(f"练习文件: {session.practice_nb_path}")
print(f"执行日志: {session.execution_log_path}")

# 加载已有 Session
session = factory.load_session('20260807_163000_a83f91_chapter1.1.1')

# 获取最新 Session
latest = factory.get_latest_session(chapter='1.1.1')
```

---

## 8. 总结

✅ **Phase 2.1 基础设施重构完成**

- 新增 8 个文件
- 重构 1 个脚本
- 12 个测试全部通过
- 定义了 3 个核心数据协议
- 建立了 Session 生命周期管理基础

**下一步**：Phase 2.2 日志系统迁移