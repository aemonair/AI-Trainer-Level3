# Session Consumer Migration Map

> 生成时间：2026-08-12
> 修订：2026-08-12（整合评审校正）
> 目的：Phase 2.2.5 Architecture Freeze 最终交付物
> 方法：代码 + 磁盘状态实证（非架构推断）
> 状态：**只读审计，未修改任何代码**

---

## 0. 冻结结论（本表的前提）

以下结论已由代码 + 磁盘实证确认，不再讨论：

| # | 冻结项 | 实证依据 |
|---|--------|----------|
| F1 | `core.Session` 是唯一 Session 模型 | `core/session.py` 117 行定义全部 canonical paths；`session_manager.py` 0 调用者 |
| F2 | `sessions/<id>/{workspace,logs,reports}/` 是唯一布局 | `core/session.py:33-42`；磁盘实证见 §7 |
| F3 | 只有 `SessionFactory` 可以创建 Session | `core/session_factory.py` 是唯一 `mkdir sessions/` 的代码 |
| F4 | 只有 `Session` 定义 canonical paths | 其他脚本不得自拼 `workspace/`、`logs/`、`reports/` |
| F5 | `session_manager.py` 是 confirmed dead code | 全仓 0 个 Python 调用者；所有文档标记废弃 |
| **F6** | **`Session` owns identity** | 任何业务代码不得从路径猜 `session_id` / `chapter` / `created_at` |

### F6 详解：Session owns identity

```text
Session
 ├── id
 ├── chapter
 ├── created_at
 ├── metadata
 └── paths
```

**禁止出现**（旧架构遗留，代码实证存在）：

```python
extract_chapter_from_path(...)    # validate_practice.py:951
match_session_by_timestamp(...)   # validate_practice.py:1049
```

**原则**：Validator 收到 `Session` 对象后，天然知道 `session.id` / `session.chapter`，不需要从 `/path/to/20260808_xxx_chapter1.1.1/practice.ipynb` 猜回来。

---

## 1. 架构 Contract 总览

```text
              SessionFactory
                    │
                 create
                    ↓
                 Session
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
    workspace/    logs/      reports/
        │           │           │
        ↓           ↓           ↓
 practice.ipynb execution_log  report/summary
                    │
                    ↓
               Validation
                    │
                    ↓
                Scoring
```

**核心原则**：所有业务代码只能**消费 Session 对象**，不能重新理解 Session 的文件结构。

---

## 2. 消费方总览

| 消费方 | 当前状态 | 是否 Session consumer | 迁移优先级 |
|--------|----------|----------------------|-----------|
| `validate_practice.py` | 旧路径逻辑（God Object） | 部分（--session 分支） | **P0** |
| `aggregate_reviews.py` | 旧模型（读根目录 report.json） | 否 | **P0** |
| `exam_review.py` | 旧模型（读根目录 report.json / 写根目录 summary.md） | 否 | **P0** |
| `batch_scoring_report.py` | 独立（直接读 materials） | 否（见 §6 讨论） | P1 |
| `session_manager.py` | dead code | — | 删除 |

---

## 3. validate_practice.py — 当前读什么 / 写什么

### 3.1 当前读取路径（代码实证）

| 数据 | 当前路径逻辑 | 行号 | 是否 legacy |
|------|-------------|------|-------------|
| 模板 notebook | `ROOT / f'{chapter}-materials' / f'{chapter}.ipynb'` | 117 | ❌ **LEGACY**（materials 已清空，实际找不到） |
| 详解文件 | `ROOT / f'{chapter}-materials' / f'{chapter}_guide.md'` | 125 | ❌ **LEGACY**（同上） |
| 练习文件（默认模式） | `ROOT.rglob('*_practice_*.ipynb')` | 140 | ❌ **LEGACY**（不匹配 `workspace/practice.ipynb`） |
| 练习文件（--session 模式） | `session_dir / 'workspace' / 'practice.ipynb'`（fallback 根目录） | 2083 | ✅ 新（但 fallback 是 legacy） |
| 答案 | `ROOT / 'answers' / ...` | 99 | ✅ 正常 |
| scoring schema | `ROOT / 'scoring' / f'{chapter}_ast.json'` | 44 | ✅ 正常 |
| execution_log | `find_execution_log()` 4 种探测（见 §3.3） | 1017 | ❌ **LEGACY**（自拼路径） |
| metadata | `session_dir / 'metadata.json'` | 2083 | ✅ 新 |
| chapter 身份 | `extract_chapter_from_path()` | 951 | ❌ **LEGACY**（违反 F6） |
| session 身份 | `match_session_by_timestamp()` | 1049 | ❌ **LEGACY**（违反 F6） |

### 3.2 当前写入路径（代码实证）

| 数据 | 当前路径 | 行号 | 是否 legacy |
|------|---------|------|-------------|
| report.json | `session_dir / 'report.json'`（**根目录**） | 2083 | ❌ **LEGACY**（应为 `reports/report.json`） |
| 批量报告 | `ROOT / 'reports' / f'validation_report_*.md'` | 2083 | ✅ 独立输出，可保留 |

### 3.3 find_execution_log() 的 4 种 legacy 探测（行 1017-1047）

```python
def find_execution_log(practice_path):
    # ① 同目录 {practice_name}_execution_log.json   ← 旧架构
    # ② session 根目录 execution_log.json           ← 旧架构
    # ③ session 根目录 logs/execution_log.json      ← 新（但自拼路径）
    # ④ workspace 上一级 logs/execution_log.json    ← 新（但自拼路径）
```

**问题**：这 4 种探测全部是"自拼路径"，违反 F4。应改为 `Session.execution_log_path`。

### 3.4 迁移方案

```python
# 迁移前（自拼路径）
materials_dir = ROOT / f'{chapter}-materials'
template_path = materials_dir / f'{chapter}.ipynb'

# 迁移后（Session API）
session = SessionFactory(ROOT).load_session(session_id)
template_path = session.metadata['template_file']   # 见 §3.5 唯一来源
```

**关键迁移点**：

| 函数 | 迁移动作 |
|------|---------|
| `find_template_file` | 改为 `Session.metadata['template_file']`（单一来源，见 §3.5） |
| `find_guide_file` | 改为由 `SessionFactory` 在创建时写入 metadata，或从 `template/{chapter}/` 查找 |
| `find_practice_files` | 改为遍历 `sessions/` 下所有 `Session.practice_nb_path` |
| `find_execution_log` | 删除 4 种探测，改为 `Session.execution_log_path` |
| `extract_chapter_from_path` | 删除，改为 `session.chapter` |
| `match_session_by_timestamp` | 删除，改为 `session.id` / `session.created_at` |
| `main` 的 report 写入 | 改为 `Session.save_report()` |

### 3.5 模板选择：单一来源（冻结）

**禁止**再出现两套协议。模板选择是 **Session 创建时决定的事实，不是 Validator 再猜一次**。

```text
template/1.1.1/1.1.1.ipynb
        ↓
SessionFactory
        ↓
metadata.json
```

创建 Session 时记录：

```json
{
  "template_file": "template/1.1.1/1.1.1.ipynb"
}
```

验证时：

```text
Session
  ↓
metadata
  ↓
template_file
```

**迁移后 `find_template_file()` 只允许一个来源：`Session.metadata['template_file']`。**

---

## 4. aggregate_reviews.py — 当前读什么

### 4.1 当前读取路径（代码实证）

| 数据 | 当前路径 | 行号 | 是否 legacy |
|------|---------|------|-------------|
| 所有 session 的 report | `session_dir / 'report.json'`（**根目录**） | 行内 | ❌ **LEGACY**（应为 `reports/report.json`） |

### 4.2 迁移方案

```python
# 迁移前
for session_dir in sorted(SESSIONS_DIR.iterdir()):
    report_path = session_dir / 'report.json'

# 迁移后
factory = SessionFactory(ROOT)
for session_dir in sorted(SESSIONS_DIR.iterdir()):
    session = factory.load_session(session_dir.name)
    report = session.load_report()  # 读 reports/report.json
```

**注意**：`aggregate_reviews.py` 还读取 `report['session_id']`、`report['session_dir']` 等字段，迁移后应改为 `session.id` / `session.session_dir`。

---

## 5. exam_review.py — 当前读什么 / 写什么

### 5.1 当前读取路径（代码实证）

| 数据 | 当前路径 | 行号 | 是否 legacy |
|------|---------|------|-------------|
| 指定 session 的 report | `session_dir / 'report.json'`（**根目录**） | 行内 | ❌ **LEGACY** |
| 同章节历史 session 的 report | `session_dir / 'report.json'`（**根目录**） | 行内 | ❌ **LEGACY** |

### 5.2 当前写入路径（代码实证）

| 数据 | 当前路径 | 行号 | 是否 legacy |
|------|---------|------|-------------|
| summary.md | `session_dir / 'summary.md'`（**根目录**） | 行内 | ❌ **LEGACY**（应为 `reports/summary.md`） |

### 5.3 迁移方案

```python
# 迁移前
report_path = session_dir / 'report.json'
output_path = session_dir / 'summary.md'

# 迁移后
session = SessionFactory(ROOT).load_session(session_id)
report = session.load_report()
session.save_summary(summary_text)  # 写 reports/summary.md
```

---

## 6. batch_scoring_report.py — 当前读什么 / 是否 Session consumer

### 6.1 当前读取路径（代码实证）

| 数据 | 当前路径 | 行号 | 是否 legacy |
|------|---------|------|-------------|
| 练习文件 | `ROOT / f'{chapter}-materials' / '*practice*.ipynb'` | 39 | ❌ **LEGACY**（materials 已清空） |
| scoring schema | `ROOT / 'scoring' / f'{chapter}_ast.json'` | 63 | ✅ 正常 |

### 6.2 迁移语义（重要校正）

**不要写死 "latest session"。**

"批量评分" 与 "最新一个 Session" 是两个不同概念。未来可能存在：

```text
sessions/
├── 20260811_xxx_chapter1.1.1
├── 20260812_xxx_chapter1.1.1
├── 20260812_xxx_chapter1.1.1
└── ...
```

那么"批量评分"究竟是：
- 评分最新一个？
- 评分所有未评分 Session？
- 评分指定 Session 集合？

**这个语义不要在迁移过程中偷偷决定。**

### 6.3 冻结的边界

```text
batch_scoring_report
        ↓
Session collection          ← 业务层负责"选择哪些 Session"
        ↓
逐个 Session
        ↓
scoring
        ↓
aggregate report
```

**原则**：`Session API` 负责"找到 Session"（提供 `find` / `load` / `get_latest` 等能力），**业务层**负责"选择哪些 Session"。

```python
# Session API 提供（core/session_factory.py 已有）：
factory.load_session(session_id)
factory.get_latest_session(chapter)

# 业务层决定（batch_scoring_report.py）：
sessions_to_score = [...]   # 业务逻辑决定
for session in sessions_to_score:
    result = score(session)
```

**注意**：`batch_scoring_report.py` 的**输出**（`reports/batch_scoring_*.md/csv`）是独立汇总报告，不属于某个 Session，保留在 `ROOT/reports/`。

---

## 7. 磁盘实证（sessions/ 实际状态）

### 7.1 新格式 session（`20260808_112503_efb060_chapter1.1.1`）

```text
sessions/20260808_112503_efb060_chapter1.1.1/
├── metadata.json          ✅
├── report.json            ❌ 畸形（validate 写入根目录，应为 reports/）
├── logs/
│   └── execution_log.json ✅
├── reports/               ❌ 空目录（模型定义但没人写）
└── workspace/
    ├── practice.ipynb     ✅
    ├── 1.1.1_guide.md     ✅
    ├── patient_data.csv   ✅
    └── scoring_report.md  ⚠️ 额外文件（非模型定义）
```

### 7.2 新格式 session（`20260811_225122_84b2fb_chapter2.2.1`）

```text
sessions/20260811_225122_84b2fb_chapter2.2.1/
├── metadata.json          ✅
├── logs/
│   └── execution_log.json ✅
├── reports/               ❌ 空目录（未运行 validate）
└── workspace/
    ├── practice.ipynb     ✅
    ├── 2.2.1.docx         ✅
    └── finance数据集.csv   ✅
```

### 7.3 旧格式 session（`2026-08-05-2144-chapter1.1.1`）

```text
sessions/2026-08-05-2144-chapter1.1.1/
├── metadata.json          ✅
└── practice.ipynb         ❌ 根目录（旧布局）
```

**结论**：磁盘上三种状态并存，验证了"非对称迁移"判断。

### 7.4 旧 Session 迁移策略（冻结）

**不要让 Session API 永久兼容两套 layout。**

否则会变成：

```python
if new: ...
elif old: ...
elif legacy: ...
```

这正是要摆脱的东西。当前约 40 个 session，旧数据可迁移。

```text
一次性 migration
       ↓
所有 Session → canonical layout
       ↓
Session API 只支持 canonical layout
```

---

## 8. cell_index / execution_count Schema 冻结

### 8.1 当前语义冲突（代码实证）

```python
# execution_logger.py:212  ← 写入方
cell_index = count - 1 if count else 0  # 实际是执行序号

# process_auditor.py:195  ← 读取方
def _get_final_code_for_cell(self, cell_index):
    cells = self.practice_nb.get('cells', [])
    if cell_index >= len(cells):  # 当 Notebook cell 位置用
```

**真实场景**：
```text
Cell 8 第一次执行  → count=1 → cell_index=0 → 但 notebook 里是第 8 个 cell
Cell 3 再执行      → count=2 → cell_index=1 → 但 notebook 里是第 3 个 cell
                                                    → 分组/对比错位
```

### 8.2 冻结 Schema（v2）

```json
{
  "schema_version": "2.0.0",
  "cell_index": 8,
  "execution_count": 17
}
```

| 字段 | 语义 |
|------|------|
| `cell_index` | Notebook 中的物理 Cell 位置（从 0 开始） |
| `execution_count` | Jupyter 实际执行序号（从 1 开始） |

### 8.3 关键约束（实证发现）

**IPython post_run_cell 钩子无法直接获取物理 cell 位置。**

`execution_logger.py:193` 的代码来源是：
```python
cell_code = ip.user_ns.get('_ih', [''])[-1]  # 只拿到代码，拿不到 cell 位置
```

**解决方案**：需要从 `practice.ipynb` 的 cells 中按代码内容反查 cell_index，或在 `pre_run_cell` 钩子中通过 `ip` 的 cell 栈获取。

### 8.4 迁移策略

- 旧 sessions 不兼容，做一次性 migration。
- `execution_log.json` 的 `schema_version` 从 `1.0.0` 升到 `2.0.0`。

---

## 9. Scoring / Validation Boundary 冻结

### 9.1 目标边界

```text
Session
  │
  ├── input
  │    └── practice.ipynb
  │
  ├── evidence
  │    └── execution_log.json
  │
  └── output
       ├── report.json
       └── summary.md
```

```text
Validator
    │
    └── Session
         ↓
    ValidationResult
```

### 9.2 当前违反（代码实证）

`validate_practice.py` 当前是 God Object，自己完成：
- 找 notebook（自拼路径）
- 找 answer（自拼路径）
- 找 template（自拼路径）
- 找 scoring（自拼路径）
- 找 execution log（4 种探测）
- 找 session（自拼路径）
- 自己判断 session
- 自己决定 report 放哪里

### 9.3 迁移后

```python
# validate_practice.py 只做：
session = SessionFactory(ROOT).load_session(session_id)
result = validate(session)          # 内部通过 Session API 读 input/evidence
session.save_report(result)         # 写 reports/report.json
```

---

## 10. Session 生命周期所有权

### 10.1 冻结规则

```text
只有 SessionFactory 可以创建 Session。
其他脚本不得 mkdir sessions/xxx 或自己生成 session_id。
```

### 10.2 当前违反（代码实证）

| 文件 | 违反行为 |
|------|---------|
| `session_manager.py` | `create_session()` 自己 `mkdir` + 生成 session_id（dead code，待删） |
| `validate_practice.py` | 无创建，但自拼路径读取（违反 F4） |

### 10.3 迁移后

```text
SessionFactory
    ↓
创建 Session

Session
    ↓
定义 Session 数据与路径

validate
    ↓
消费 Session + 产生 ValidationResult

aggregate
    ↓
消费 report

exam_review
    ↓
消费 report
```

---

## 11. Phase 2.2.6 迁移原则：零行为变化

### 11.1 核心原则

**Phase 2.2.6 不允许改变评分算法。**

只允许改变：

```text
路径
Session 获取
输入输出
生命周期
```

**不允许同时改**：

```text
AST scoring
schema scoring
dynamic scoring
output comparison
process audit
penalty
```

否则出了问题无法判断：

```text
是 Session migration bug？
还是 scoring regression？
```

### 11.2 目标

不是"让代码更漂亮"，而是：

> **同一个 Session，迁移前后评分结果应该一致。**

```text
旧 validator
     │
     ▼
report_old.json
     │
     │ compare
     ▼
新 validator
     │
     ▼
report_new.json
```

验证以下全部一致：

```text
score
question scores
knowledge points
errors
process audit
```

唯一允许变化的是：

```text
文件位置
↓
sessions/<id>/reports/report.json
```

---

## 12. Phase 2.2.6 验收标准

### Contract

```text
[ ] 不再出现 session_dir/"report.json"
[ ] 不再出现 session_dir/"summary.md"
[ ] 不再出现 session_dir/"practice.ipynb"
[ ] 不再出现 session_dir/"execution_log.json"
[ ] 不再由 consumer 创建 Session
[ ] 不再由 consumer 生成 session_id
```

### Consumer

```text
[ ] validate_practice → Session
[ ] aggregate_reviews → Session
[ ] exam_review → Session
[ ] batch_scoring_report → Session collection
```

### Legacy

```text
[ ] session_manager.py 删除/归档
[ ] materials 路径从生产流程移除
[ ] *_practice_*.ipynb discovery 移除
[ ] execution_log 四路 fallback 移除
```

### Behavior

```text
[ ] 评分结果不变
[ ] report 内容不变
[ ] process audit 结果不变
[ ] summary 内容不变
```

### Storage

最终所有新 Session 都必须满足：

```text
sessions/<id>/
├── metadata.json
├── workspace/
│   └── practice.ipynb
├── logs/
│   └── execution_log.json
└── reports/
    ├── report.json
    └── summary.md
```

---

## 13. 迁移步骤（Phase 2.2.6 执行顺序）

```text
Step 1
SessionFactory + dead code
        ↓
Step 2
validate consumer migration
        ↓
Step 3
aggregate
        ↓
Step 4
exam_review
        ↓
Step 5
batch scoring
        ↓
Step 6
旧 Session migration
        ↓
Phase 2.2.6 complete
        ↓
Phase 2.3
拆 validate God Object
```

### Step 1 详细（受控的第一步）

> **只修 `SessionFactory` 的 `--notebook` 路径 + 建立 Session Consumer API contract + 删除/归档 `session_manager.py`，不碰 validator。**

然后运行完整测试，确认 Session 基础设施稳定之后再进入 Step 2。

---

## 14. 最终判断

> 这个项目目前处于 **Session 新模型已定义、创建流程已迁移、但消费流程（验证/聚合/复盘）仍在走旧路径** 的非对称迁移状态。
>
> 最危险的不是代码量，而是 **同一文件在不同流程下指向不同路径**（template 找得到但 validate 找不到、reports/ 定义了但没人写、practice.ipynb 定义了但批量扫描扫不到）。

**本表完成 Phase 2.2.5 Architecture Freeze，可以放心进入 Phase 2.2.6。**

---

## 15. Phase 2.2.5 状态

```text
Phase 2.2.5 Architecture Freeze
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: COMPLETE
```

冻结的核心不是"代码已经重构完"，而是：

```text
                ┌──────────────┐
                │    Session   │
                │ 唯一领域模型  │
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    workspace/       logs/         reports/
        │              │              │
        ↓              ↓              ↓
   practice.ipynb execution_log   report/summary
                       │
                       ↓
                  Validation
                       │
                       ↓
                    Scoring
```

**这个模型现在已经足够明确，不需要继续讨论。**