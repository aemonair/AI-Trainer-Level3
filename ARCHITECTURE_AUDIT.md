# Architecture Audit Report — READ ONLY

> 审计日期：2026-08-12
> 审计方式：静态代码审查（未修改任何代码）
> 审计范围：`core/` + `scripts/` 全部 Python 文件 + `sessions/` 实际目录

---

## 一、核心结论

**项目状态确认：`Phase 2.x — Architecture Migration In Progress`**

新架构（`core.Session` / `SessionFactory`）已经出现，但**只有一半业务流程真正接入**。
旧架构（`session_manager.py`、validator 自拼路径、session 根目录 report.json）仍然在多处存活。

**最关键的三个实证（不是推测）：**

1. **`core.Session` 定义了 `reports/report.json`，但 validate 实际写到 session 根目录**
   - `core/session.py:40` → `report_path = session_dir / 'reports' / 'report.json'`
   - `scripts/validate_practice.py:2083` → `report_path = session_dir / 'report.json'`
   - 实锤：`sessions/20260808_112503_efb060_chapter1.1.1/reports/` 是**空目录**，根目录却有 `report.json`

2. **`1.1.1-materials/` 已清空，内容迁到 `template/1.1.1/`，但 validator 仍只从 materials 找模板**
   - `core/session_factory.py:68` 自动选择 → `template/1.1.1/` ✅
   - `scripts/validate_practice.py:117` 找模板 → `{chapter}-materials/{chapter}.ipynb` ❌（当前是空目录）
   - 指定 `--notebook` 时 `core/session_factory.py:193` 仍指向 `{chapter}-materials/` ❌

3. **`session_manager.py` 无任何代码调用者（dead code），文档已标记废弃**
   - 全仓搜索：业务代码 0 处引用
   - `ARCHITECTURE_MAP.md` / `ARCHITECTURE_FREEZE.md` / `PROJECT_HEALTH_REPORT.md` 均标注"待废弃"
   - 它在磁盘上留存的意义仅是占位

---

## 二、真实依赖图（代码实证）

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         新架构（已接通）                               │
├──────────────────────────────────────────────────────────────────────┤
│  scripts/create_timestamped_practice.py                              │
│       │                                                              │
│       ▼                                                              │
│  core/session_factory.py ──────► core/session.py                     │
│                                          ▲                           │
│                                          │ (运行时注入 cell 内)       │
│  scripts/execution_logger.py ────────────┘                           │
│       │  (通过 Session.execution_log_path 绑定)                       │
│       └── 被 notebook 首个 auto-init cell 运行时加载                   │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    旧路径逻辑（仍存活）                                │
├──────────────────────────────────────────────────────────────────────┤
│  scripts/validate_practice.py                                        │
│       │                                                              │
│       ├── 自拼 {chapter}-materials/（模板）     ← 目录已清空 ❌         │
│       ├── 自拼 answers/（答案）                ← 正常 ✅               │
│       ├── 自拼 scoring/{chapter}_ast.json     ← 正常 ✅               │
│       ├── ROOT.rglob('*_practice_*.ipynb')    ← 不匹配新 Session ❌   │
│       ├── --session 分支：手动拼 workspace/practice.ipynb ✅           │
│       │       但报告写到 session 根目录 → reports/ 空 ❌              │
│       └── 运行时 from process_auditor import ... ← 脆弱导入 🟡        │
│                                                                      │
│  scripts/aggregate_reviews.py ──► sessions/*/report.json（根目录）🟡  │
│  scripts/exam_review.py ─────────► sessions/*/report.json（根目录）🟡  │
│       └── 写 summary.md 到 session 根目录（非 reports/）🟡            │
│                                                                      │
│  scripts/session_manager.py ──► 无调用者（dead code）❌               │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                        独立领域模块                                    │
├──────────────────────────────────────────────────────────────────────┤
│  scripts/process_auditor.py                                          │
│       └── 构造函数接收 3 个路径参数，不依赖 core，不依赖 Session       │
│       └── 被 validate_practice.py 运行时导入（同目录，脆弱）           │
│                                                                      │
│  scripts/scoring_validator.py                                        │
│       └── 被 scripts/test_ast_checker.py 引用（from scoring_validator）│
│       ├── 被 convert_v2_to_ast.py 间接关联（AST 规则来源）            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 三、每个 scripts 文件的真实分类（代码实证）

| 文件 | 分类 | 依据 |
|---|---|---|
| `create_timestamped_practice.py` | **生产 CLI（新架构）** | import SessionFactory；职责为 CLI + 后处理 |
| `execution_logger.py` | **运行时领域库（已绑定新架构）** | 构造签名 `ExecutionLogger(session)`；通过 session.execution_log_path |
| `process_auditor.py` | **独立领域模块（能力可用）** | 纯路径参数输入，零 core 依赖 |
| `validate_practice.py` | **生产 CLI（巨石，旧路径逻辑）** | 2167 行；36 个函数；自拼全部路径 |
| `aggregate_reviews.py` | **生产 CLI（旧模型）** | 直接 `sessions/<id>/report.json`（根目录） |
| `exam_review.py` | **生产 CLI（旧模型）** | 同上；写 `sessions/<id>/summary.md`（根目录） |
| `batch_scoring_report.py` | **生产 CLI（scoring 报告）** | 独立读取 sessions |
| `extract_answers_from_ipynb.py` | **生产工具** | 答案提取 |
| `check_practice_errors.py` | **生产检查工具** | 独立运行 |
| `analyze_ipython_history.py` | **分析工具** | IPython history 分析 |
| `generate_history_summary.py` | **分析工具** | 历史汇总 |
| `compare_docx.py` | **临时对比工具** | docx 对比 |
| `compare_questions.py` | **临时对比工具** | 题目对比 |
| `merge_template.py` | **迁移工具** | materials → template 合并 |
| `convert_v1_to_v2.py` | **迁移工具** | 评分 schema v1→v2 |
| `convert_v2_to_ast.py` | **迁移工具** | v2→AST 转换 |
| `create_questions_batch.py` | **问题生成** | 批量生成 |
| `extract_questions_from_doc.py` | **问题生成** | doc 提取 |
| `parse_questions.py` | **问题生成** | 解析 |
| `regenerate_questions_from_materials.py` | **问题生成** | 从材料重新生成 |
| `generate_scoring_index.py` | **scoring 基础设施** | 索引生成 |
| `generate_scoring_schema.py` | **scoring 基础设施** | schema 生成 |
| `scoring_validator.py` | **scoring 基础设施（库）** | 被 test_ast_checker 引用 |
| `test_ast_checker.py` | **测试** | 单测风格 |
| `test_extract.py` | **临时测试** | 提取测试 |
| `test_extract2.py` | **临时测试** | 提取测试 |
| `test_v2_scoring.py` | **测试** | v2 评分测试 |
| `session_manager.py` | **LEGACY（dead code）** | 0 调用者；文档已标记待废弃 |

---

## 四、数据模型不一致清单（同一领域对象存在两种模型）

### 4.1 Session 目录布局（两套并存）

```text
新模型（core/session.py）                    旧模型（session_manager.py + 旧 sessions/）
────────────────────────                    ────────────────────────────────
sessions/<id>/                               sessions/<id>/
├── metadata.json                            ├── metadata.json
├── workspace/practice.ipynb                 ├── practice.ipynb        ← 根目录
├── logs/execution_log.json                  ├── report.json           ← 根目录
└── reports/report.json                      └── summary.md            ← 根目录
    reports/summary.md
```

磁盘实证：`sessions/` 下两种命名格式并存：
- 旧：`2026-08-05-2144-chapter1.1.1/`（根目录 metadata.json + practice.ipynb）
- 新：`20260808_112503_efb060_chapter1.1.1/`（workspace/ + logs/ + reports/）

且新格式 session 的根目录**仍有 report.json 残留**（validate 写入），reports/ 为空的畸形状态。

### 4.2 notebook 发现协议（两套不一致）

```text
SessionFactory.find_chapter_notebooks()
  ① template/{chapter}/*.ipynb        ← 新（已迁移）
  ② {chapter}-materials/*.ipynb       ← fallback（已清空，实际不再命中）

validate_practice.find_practice_files()
  ROOT.rglob('*_practice_*.ipynb')    ← 旧命名（{chapter}_practice_时间戳.ipynb）
  无法匹配 workspace/practice.ipynb   ← 新命名 ❌
```

### 4.3 模板定位协议（两套不一致）

```text
SessionFactory（创建时）  → template/{chapter}/1.1.1.ipynb        ✅
validate_practice（验证时）→ {chapter}-materials/{chapter}.ipynb   ❌（空目录）
```

### 4.4 执行日志 Schema 字段（同一字段双重语义）

```text
execution_logger.py:212   cell_index = execution_count - 1   ← 实际是执行序号
process_auditor.py:195    _get_final_code_for_cell(cell_index) ← 当 Notebook cell 位置用

真实场景：
  Cell 8 第一次执行  → count=1 → cell_index=0 → 但 notebook 里是第 8 个 cell
  Cell 3 再执行      → count=2 → cell_index=1 → 但 notebook 里是第 3 个 cell
                                                                    → 分组/对比错位
```

### 4.5 报告保存位置（模型 vs 实际行为）

```text
模型定义：session.report_path = sessions/<id>/reports/report.json
实际行为：validate_practice.py → sessions/<id>/report.json（根目录）
消费方：  aggregate_reviews / exam_review → 都读根目录 report.json
```

---

## 五、SessionFactory 路径不一致（用户指出的 Bug，代码实证）

`core/session_factory.py:192-197`：

```python
if notebook_name:
    template_nb = self.root_dir / f'{chapter}-materials' / notebook_name
```

而 `find_chapter_notebooks()` 已优先 `template/{chapter}/`。

**影响：**
- 用户执行 `--notebook 1.1.1.ipynb` 时，若模板已迁到 `template/1.1.1/`，而 `{chapter}-materials/` 为空 → 必然报 `FileNotFoundError`
- 实测 `1.1.1-materials/` 为空目录，`template/1.1.1/` 有 `1.1.1.ipynb` 和 `patient_data.csv` → **此 Bug 当前实际会触发**

---

## 六、validate_practice.py God Object 实测

### 6.1 规模
- 总行数：**2167 行**（open 的 tab 显示 3736 行是不同版本/或包含展开，当前工作区实际文件 2167 行）
- 顶层函数：**36 个**
- 覆盖职责：notebook 读取、答案提取、HTML 清洗、图片处理、输出比较、实现细节检查、评分（动态/schema/AST 三套）、过程审计、IPython 历史分析、报告生成（JSON/Markdown/控制台）

### 6.2 关键领域函数清单（职责编号）

| 函数 | 行号 | 职责域 |
|---|---|---|
| `load_scoring_schema` | 44 | scoring |
| `find_answer_file` | 99 | 路径查找 |
| `find_template_file` | 115 | 路径查找 |
| `find_guide_file` | 125 | 路径查找 |
| `find_practice_files` | 135 | 路径查找 |
| `load_notebook` | 158 | notebook |
| `extract_blanks_from_template` | 168 | notebook |
| `extract_filled_answers` | 216 | notebook |
| `extract_blank_answers_from_template_and_answer` | 310 | notebook |
| `extract_practice_filled_answers` | 422 | notebook |
| `normalize_code` | 521 | 对比 |
| `compare_fill_answers` | 557 | 对比 |
| `extract_outputs` | 626 | 输出 |
| `_strip_html_tags` | 677 | 清洗 |
| `compare_outputs` | 690 | 对比 |
| `check_implementation_details` | 751 | 实现检查 |
| `check_unfilled_blanks` | 854 | 检查 |
| `analyze_progress` | 873 | 分析 |
| `classify_knowledge_point` | 918 | scoring |
| `extract_chapter_from_path` | 951 | 路径解析 |
| `load_manifest` | 989 | 元数据 |
| `find_execution_log` | 1017 | 路径查找 |
| `match_session_by_timestamp` | 1049 | 会话匹配 |
| `analyze_ipython_history_for_practice` | 1102 | 历史分析 |
| `count_blanks_in_template` | 1263 | 检查 |
| `is_auto_init_cell` | 1279 | notebook |
| `align_cells_to_practice` | 1290 | notebook |
| `score_with_ast_schema` | 1330 | scoring |
| `score_with_schema` | 1462 | scoring |
| `validate_single_practice` | 1562 | 总控 |
| `generate_json_report` | 1824 | 报告 |
| `generate_markdown_report` | 1832 | 报告 |
| `print_validation_report` | 1912 | 报告 |
| `resolve_compare_mode` | 2014 | CLI |
| `main` | 2037 | CLI |

**结论：`validate_practice.py` 同时充当了 Notebook 解析器 + 输出比较器 + 评分引擎 + 过程审计接线 + 报告生成器 + CLI。是当前第二大的架构风险（第一是 Session 双模型）。**

### 6.3 脆弱导入实证

```python
# validate_practice.py:1773-1775（运行时导入，非顶部）
import sys
sys.path.insert(0, str(ROOT))
from process_auditor import ProcessAuditor
```

- `process_auditor.py` 位于 `scripts/`，ROOT 是项目根
- 只有 cwd 在 `scripts/` 或 `scripts/` 已在 sys.path 时才能成功
- 这是"为什么不写在顶部 import"的原因——它知道自己目录不匹配

---

## 七、Process Audit 规则脆弱性实证

`scripts/process_auditor.py:119-125`：

```python
def _is_error_different_from_final(self, error_code: str, final_code: str) -> bool:
    if not final_code:
        return True
    similarity = self._calculate_similarity(error_code, final_code)
    return similarity < 0.85  # 相似度低于85%视为不同尝试
```

`scripts/process_auditor.py:127-144`（严重程度分类）：

```python
# 语法错误 → high
# 类型/值/键/属性 error → medium
# 断言/mismatch → medium
# 其他 → low
```

罚分规则：`high=-3, medium=-2, low=-1`，上限 20 分（`_calculate_penalty`）。

**评价（与用户判断一致）：**
- 文本相似度 ≠ 语义相似度（`df.dropna()` vs `df = df.dropna()` 文本近语义远）
- 错误类型分类不覆盖所有情况（如 `ModuleNotFoundError`、`IndexError` 落到 low）
- 建议定位为"过程分析辅助指标"，不直接作为唯一扣分依据

---

## 八、Execution Log Schema 的价值（确认成立）

`execution_logger.py` 完整实现：

```
pre_run_cell → 记录 start_time + 启动 stdout/stderr 捕获
post_run_cell → 获取 _ih 代码 + 输出 + error → record_execution()
```

事件结构（遵循 `schemas/execution_log.schema.json` v1.0.0）：
```json
{
  "event_id": 1,
  "cell_index": 0,
  "timestamp": "...",
  "source": "代码",
  "source_hash": "sha256",
  "output": "...",
  "status": "success|error",
  "error": {"type": "...", "message": "...", "traceback": "..."},
  "duration_ms": 123,
  "execution_count": 1
}
```

**价值确认：practice.ipynb（答案状态）+ execution_log.json（行为轨迹）= 完整的考试证据链。方向正确。**

**但 `cell_index` = `execution_count - 1` 是明确的模型缺陷**（见 4.4）。

---

## 九、项目健康度总评

| 方面 | 状态 | 证据 |
|---|---|---|
| Session 概念已建立 | 🟢 | core/session.py 117 行，职责收敛 |
| Session 目录结构 | 🟡 | 定义合理，但实际报告写到根目录 |
| Template → Session | 🟢 | SessionFactory + create_timestamped_practice 已接通 |
| Core/Scripts 分层 | 🟡 | core 只有 2 个文件，尚未形成完整领域层 |
| Legacy 清理 | 🔴 | session_manager.py dead code 未删 |
| Session 单一模型 | 🔴 | 新模型 + session_manager + validator 自拼路径三套 |
| Notebook 数据模型 | 🟡 | 文件名两套协议（_practice_* vs workspace/practice.ipynb） |
| Execution Log | 🟢 | 实现完整，schema v1.0.0 有 spec |
| Process Audit | 🟡 | 可用但规则偏脆（文本相似度） |
| Scoring | 🟡 | 三套评分（dynamic/schema/AST）共存，功能多耦合重 |
| validate_practice | 🔴 | 2167 行 / 36 函数 / God Object |
| 测试体系 | 🟡 | tests/ 有 test_execution_logger.py；scripts 下有 test_*.py |
| Schema/versioning | 🟡 | schemas/ 有 3 个 schema，scoring/ 有 v1/v2/ast 并存 |

---

## 十、给下一步的建议（冻结优先级排序）

### P0 — 先回答两个问题（确定删除边界）

1. **Session 是否最终唯一数据模型？**
   - 若是 → 所有消费方（validate/aggregate/exam_review）必须只走 `Session` 的 `report_path` / `summary_path`
   - 若不是 → 先定模型，再改代码

2. **session_manager.py 是否可以删除？**
   - 已确认 0 代码调用者，文档全标"待废弃"
   - 建议：移动到 `legacy/` 或直接删除（当前没有任何运行路径引用它）

### P1 — 修复 4 个实际会触发的 Bug

| # | Bug | 位置 | 影响 |
|---|---|---|---|
| 1 | `--notebook` 指定时路径指向空 materials 目录 | `core/session_factory.py:193` | 指定 notebook 必然失败 |
| 2 | validate 找模板只查 materials（已清空） | `validate_practice.py:117` | 验证时模板缺失，填空对比失效 |
| 3 | validate 默认模式 rglob 不匹配新 Session | `validate_practice.py:140` | 批量验证永远扫不到新 Session |
| 4 | validate 写入根目录 report.json（非 reports/） | `validate_practice.py:2083` | 目录结构畸形，违背模型 |

### P2 — 冻结 4 个东西（不新增功能）

```text
① Session Model          （Session + SessionFactory 为唯一入口）
② Session Directory Layout（workspace/ logs/ reports/ 为唯一布局）
③ Notebook/ExecutionLog Schema（固定字段语义，cell_index 与 execution_count 分离）
④ Scoring/Validation Boundary（validate_practice 只接 session + 输出结果）
```

### P3 — 领域文件拆分（架构冻结**之后**再做）

```text
core/
├── session.py            ← 不动
├── session_factory.py    ← 修路径 Bug
├── notebook.py           ← 从 validate 迁出：load/extract/align
├── execution.py          ← 从 validate 迁出：output compare + 清洗
├── scoring.py            ← 从 validate 迁出：三套评分统一入口
└── report.py             ← 从 validate 迁出：json/md 生成
```

**注意：拆分的前提是先把上面 P1 的 4 个路径 Bug 修掉 + 确认 Session 唯一模型。否则拆出来的新模块仍会带着旧路径逻辑。**

---

## 十一、最终判断

用户的判断完全正确：

> **"设计方向已经对了，但架构迁移没有完成。"**

补充一个更精确的表述：

> 这个项目目前处于 **Session 新模型已定义、创建流程已迁移、但消费流程（验证/聚合/复盘）仍在走旧路径** 的非对称迁移状态。
>
> 最危险的不是代码量，而是 **同一文件在不同流程下指向不同路径**（template 找得到但 validate 找不到、reports/ 定义了但没人写、practice.ipynb 定义了但批量扫描扫不到）。

这正是必须**先做架构冻结，再进入下一阶段**的最硬理由。