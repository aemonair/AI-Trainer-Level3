# 项目现状诊断报告（痛点与优化建议）

> 生成时间：2026-08-11
> 分析范围：core/、scripts/、schemas/、tests/、sessions/、scoring/、questions/
> 目的：梳理当前实现痛点，为后续优化提供依据

---

## 1. 项目概况

本项目是一个"人工智能训练师三级考试"练习平台，核心功能：

- 创建练习 Session（`SessionFactory`）
- 在 Jupyter 中记录执行日志（`ExecutionLogger`）
- 自动阅卷评分（`validate_practice.py` + `scoring_validator.py`）
- 成绩聚合分析（`aggregate_reviews.py`）

当前阶段：**数据基础设施已完成（Phase 2.2），验证/报告系统迁移未完成（Phase 2.3/2.4）**

---

## 2. 架构层面痛点

### 2.1 新旧 Session 格式并存

`sessions/` 目录存在三种格式：

| 格式 | 示例 | 结构 | 数量 |
|------|------|------|------|
| 旧格式 | `2026-08-05-2144-chapter1.1.1/` | 仅 `metadata.json` + `practice.ipynb` | 2 |
| 新格式 | `20260808_112503_efb060_chapter1.1.1/` | `workspace/` + `logs/` + `reports/` | ~35 |
| 拼写错误 | `20260809_145955_chaper2.2.5/` | "chaper" 应为 "chapter" | 1 |

**影响**：`aggregate_reviews.py`、`validate_practice.py` 被迫做新旧格式兼容，逻辑复杂；拼写错误的目录会被 `get_latest_session` 误检出。

### 2.2 文档标注的"待迁移"脚本仍未迁移

`ARCHITECTURE_MAP.md` 明确标注以下脚本待迁移，实际未完成：

- `validate_practice.py`（2167 行，架构文档标注 1992 行，文件已增长）
- `process_auditor.py`
- `exam_review.py`
- `aggregate_reviews.py`
- `scoring_validator.py`
- `batch_scoring_report.py`

### 2.3 旧版 `session_manager.py` 与 `core/session.py` 功能重叠

文档已标注"待废弃"，但文件仍存在于 `scripts/`，容易造成混淆。

---

## 3. 代码层面痛点

### 3.1 绝对路径硬编码（严重）

**位置一**：`metadata.json` 中 `template_file` 字段

```json
"template_file": "/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/template/1.1.1/1.1.1.ipynb"
```

来源：`core/session_factory.py` 第 215 行 `'template_file': str(template_nb)` 直接存储了绝对路径。

**位置二**：`scripts/create_timestamped_practice.py` 的 `inject_logger_init_cell` 函数将 `ROOT_DIR` 绝对路径写死进 notebook 代码：

```python
root_dir = Path('{ROOT_DIR}')  # 绝对路径
```

**影响**：
- git clone 到另一台机器失败
- session 目录移动失败
- 用户复制 notebook 失败

### 3.2 `validate_practice.py` 巨型脚本问题

**规模**：2167 行，14 个顶层函数 + 大量嵌套内部函数。

**重复代码**：
- `is_auto_init_cell` 在以下函数中重复定义（至少 4 处）：
  - `extract_blank_answers_from_template_and_answer`
  - `extract_practice_filled_answers`
  - `compare_fill_answers`
  - `check_implementation_details`
- `normalize_line` 同样多处重复

**性能问题**：`find_practice_files` 使用 `ROOT.rglob(pattern)` 递归搜索整个项目目录树。

### 3.3 评分逻辑"双轨制"

- `validate_practice.py` 内部有 `score_with_schema`（普通）和 `score_with_ast_schema`（AST）两套
- `scoring_validator.py` 又独立实现了 v1/v2 检测和评分逻辑
- 两部分 `load_scoring_schema` 各自实现了加载优先级，逻辑重复可能不一致

### 3.4 `scoring_validator.py` 代码质量问题

- 第 24、29 行 `import json` 重复导入
- 第 1198 行规模，与 `validate_practice.py` 功能大量重叠

### 3.5 测试脆弱

`tests/test_execution_logger.py` 中：

```python
def test_no_mkdir_in_logger(session_with_template):
    source = inspect.getsource(ExecutionLogger.save)
    assert 'mkdir' not in source
```

使用 `inspect.getsource` 检查源码字符串，**测试与实现耦合过紧**——任何重构或格式化都会导致测试失败。

---

## 4. 数据层面痛点

### 4.1 Schema 漂移（协议不一致）

**`metadata.json`**：
- 实际含 `score` 字段，但 `metadata.schema.json` 未定义
- `template_file` 存绝对路径

**`report.json`**：
- `report.schema.json` 定义：`total_score` / `earned_score` / `percentage` / `process_penalty` / `items[]` / `detected_errors[]`
- 实际输出：`score` / `total_score` / `total_blanks` / `score_per_blank` / `fill_comparison` / `implementation_comparison` / `result_comparison` / `schema_details`
- **两者完全不一致**，schema 是"理想设计"，实际从未遵循

### 4.2 执行日志质量差

`sessions/20260808_112503_efb060_chapter1.1.1/logs/execution_log.json` 实测：

| 字段 | 实际值 | 期望值 |
|------|--------|--------|
| `output` | `<ExecutionResult object at 0x10506f6d0...>` | 真实输出内容 |
| `error.traceback` | `"NoneType: None\n"` | 完整堆栈 |
| `cell_index` | 从 1 开始（日志注入 Cell 占位） | 从 0 开始（schema 定义） |
| `duration_ms` | `0.0` | 真实执行耗时 |

**根因**：`execution_logger.py` 的 `post_run_cell_hook` 中：
- `cell_index=ip.execution_count - 1` 计算错误（execution_count 是全局计数器，不是 cell 索引）
- `execution_time=0.0` 硬编码
- `output = str(result)` 取到的是 ExecutionResult 对象字符串

### 4.3 评分标准文件版本冗余

`scoring/` 目录下每个章节有 3 个版本：

```
1.1.1.json       # v1 旧版
1.1.1_v2.json    # v2 新版
1.1.1_ast.json   # AST 最新
```

共 60+ 文件（19 章节 × 3 版本 + 2 额外文件），版本冗余且易混淆。

### 4.4 `questions/` 目录重复文件

| 章节 | 重复文件 |
|------|---------|
| 2.1.2 | `2.1.2.md` + `2.1.2_低碳生活行为影响因素数据清洗和标注流程设计.md` |
| 2.2.1 | `2.2.1_智能信用评分Logistic 回归模型开发与测试.md` + `2.2.1_智能信用评分 Logistic 回归模型开发与测试.md` |
| 3.2.5 | `3.2.5_人脸AI 智能检测系统交互流程设计.md` + `3.2.5_人脸 AI 智能检测系统交互流程设计.md` |

---

## 5. 配置层面痛点

### 5.1 `pyproject.toml` 平台版本硬编码

```toml
requires-python = "==3.9.7"
# 以下按平台重复 4 次
"pandas==1.3.4; sys_platform == 'win32'",
"pandas==1.4.4; sys_platform == 'darwin' and platform_machine == 'arm64'",
"pandas==1.3.4; sys_platform == 'darwin' and platform_machine == 'x86_64'",
"pandas==1.3.4; sys_platform == 'linux'",
```

维护成本高，且无法覆盖未来的平台组合。

### 5.2 垃圾文件与目录混杂

- `sessions/` 下有 `.DS_Store`、`.ipynb_checkpoints/`
- `daily_practice_log.csv`、`exam_db.csv` 等数据文件与代码混放在根目录
- `backup/`、`docx_version2_backup/` 等备份目录占用空间
- `answers/` 目录存在多套参考答案（PDF、docx、ipynb 混杂）

---

## 6. 测试覆盖

| 模块 | 测试文件 | 用例数 | 状态 |
|------|----------|--------|------|
| Session | `tests/test_session.py` | 12 | ✅ 通过 |
| ExecutionLogger | `tests/test_execution_logger.py` | 13 | ✅ 通过 |
| `validate_practice.py` | - | 0 | ❌ 无测试 |
| `process_auditor.py` | - | 0 | ❌ 无测试 |
| `exam_review.py` | - | 0 | ❌ 无测试 |
| `aggregate_reviews.py` | - | 0 | ❌ 无测试 |
| `scoring_validator.py` | - | 0 | ❌ 无测试 |

核心评分/审计/聚合逻辑均无自动化测试保护。

---

## 7. 优化建议（按优先级）

### 🔴 第一批：数据一致性与可移植性（影响所有功能）

| # | 优化项 | 具体做法 | 风险 | 状态 |
|---|--------|---------|------|------|
| 1 | 消除绝对路径硬编码 | `metadata.json` 的 `template_file` 改为相对路径；`inject_logger_init_cell` 改为运行时通过 `Path(__file__)` 推导 | 低 | ✅ 已完成（2026-08-11） |
| 2 | 统一 Session 格式 | 编写 `migrate_sessions.py` 将旧格式转换为新格式；重命名拼写错误目录 | 中（涉及真实数据，需谨慎） | ⏳ 待实施 |
| 3 | 修复执行日志质量 | `output` 捕获真实 stdout；`execution_time` 用 `time.perf_counter()`；`cell_index` 用真实 cell 序号 | 中 | ✅ 已完成（2026-08-11） |

### 🟡 第二批：代码可维护性

| # | 优化项 | 具体做法 | 风险 |
|---|--------|---------|------|
| 4 | 拆分 `validate_practice.py` | 提取公共函数（`is_auto_init_cell`、`normalize_line`）；按职责拆分为 `scoring/`、`comparison/`、`report/` 模块 | 高（需配套测试） |
| 5 | 统一评分标准 | 合并 `{chapter}.json`/`_v2.json`/`_ast.json` 为单一版本；统一 `load_scoring_schema` | 中 |
| 6 | 统一 report schema | 让实际输出遵循 `report.schema.json`，或更新 schema 匹配实际 | 中 |

### 🟢 第三批：整洁性

| # | 优化项 | 具体做法 | 风险 | 状态 |
|---|--------|---------|------|------|
| 7 | 清理重复文件 | 删除 `questions/` 重复 md 文件 | 低 | ⏳ 待实施（MD5 不同，需人工确认） |
| 8 | 清理垃圾文件 | 移除 `.DS_Store`、`.ipynb_checkpoints` | 低 | ✅ 已完成（2026-08-11） |
| 9 | 删除旧版 `session_manager.py` | 确认无引用后删除 | 低 | ⏳ 待实施 |
| 10 | 修复 tester 脆弱断言 | 改用行为断言替代 `inspect.getsource` | 低 | ✅ 已完成（2026-08-11） |

> **⚠️ 清理说明（2026-08-11）**：已删除全部 `.DS_Store`（8 个）和 `.ipynb_checkpoints`（50+ 目录）。这些文件从未被 git 跟踪（`.gitignore` 已忽略），无法从 git 恢复。经核实，"错误改正确"检测逻辑依赖 `~/.ipython/profile_default/history.sqlite`（`analyze_ipython_history.py`）和 `execution_log.json`（`process_auditor.py`），**不依赖 checkpoint 文件**，因此清理不影响该功能。若需手动回溯某章节答题中间版本，可从对应 `execution_log.json` 的 `source` 字段重建。

---

## 8. 参考文件索引

| 文件 | 说明 |
|------|------|
| `ARCHITECTURE_MAP.md` | 架构地图（2026-08-07，Phase 2.2 状态） |
| `REFACTOR_SUMMARY.md` | Phase 2.1 基础设施重构报告 |
| `IMPLEMENTATION_SUMMARY.md` | 执行日志与回溯审计实施总结 |
| `core/session.py` | Session 实体类 |
| `core/session_factory.py` | Session 创建工厂 |
| `scripts/execution_logger.py` | 执行日志记录器 |
| `scripts/process_auditor.py` | 回溯审计模块 |
| `scripts/validate_practice.py` | 自动阅卷（2167 行） |
| `scripts/scoring_validator.py` | 评分标准验证器 |
| `scripts/aggregate_reviews.py` | 成绩聚合 |
| `schemas/execution_log.schema.json` | 执行日志协议 |
| `schemas/report.schema.json` | 评分报告协议 |
| `schemas/metadata.schema.json` | Session 元数据协议 |

---

## 9. 结论

**当前项目处于"数据基础设施完成、上层功能待迁移"的中间状态**。核心痛点集中在：

1. **可移植性**：绝对路径硬编码导致项目无法跨机器/跨目录使用
2. **数据一致性**：Session 格式多样、schema 漂移、日志质量差
3. **可维护性**：巨型脚本、重复代码、双轨评分逻辑
4. **可靠性**：核心逻辑无测试覆盖

建议按第一批 → 第二批 → 第三批顺序逐步推进，每次改动配套测试验证。