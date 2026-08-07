# AI训练师三级考试练习平台 - 当前架构地图

> 生成时间：2026-08-07
> Phase：2.2 完成
> 状态：数据基础设施阶段完成

---

## 1. 目录结构总览

```
人工智能训练师_3级_sucai/
├── core/                          # 核心模块（Phase 2.1 新增）
│   ├── __init__.py
│   ├── session.py                 # Session 实体类
│   └── session_factory.py         # Session 创建工厂
│
├── schemas/                       # 数据协议定义（Phase 2.1 新增）
│   ├── metadata.schema.json       # Session 元数据协议 v1.0.0
│   ├── execution_log.schema.json  # 执行日志协议 v1.0.0
│   └── report.schema.json         # 评分报告协议 v1.0.0
│
├── scripts/                       # 脚本集合
│   ├── create_timestamped_practice.py  # 创建练习（Phase 2.1 重构）
│   ├── execution_logger.py             # 执行日志（Phase 2.2 重构）
│   ├── validate_practice.py            # 验证练习答案（1992行，待迁移）
│   ├── process_auditor.py              # 回溯审计工具（待迁移）
│   ├── exam_review.py                  # 考试分析报告（待迁移）
│   ├── aggregate_reviews.py            # 成绩中心（聚合统计）（待迁移）
│   ├── scoring_validator.py            # 评分标准验证器（待迁移）
│   ├── generate_scoring_schema.py      # 生成评分标准
│   ├── analyze_ipython_history.py      # IPython历史分析（独立）
│   ├── check_practice_errors.py        # 自动错误检查（独立）
│   ├── batch_scoring_report.py         # 批量评分报告（待迁移）
│   ├── extract_answers_from_ipynb.py   # 提取答案
│   ├── generate_history_summary.py     # 历史摘要生成
│   ├── convert_v1_to_v2.py             # 格式转换工具
│   ├── convert_v2_to_ast.py            # AST转换工具
│   ├── session_manager.py              # Session管理器（旧版，待废弃）
│   └── test_*.py                       # 测试脚本
│
├── tests/                         # 测试模块
│   ├── __init__.py
│   ├── test_session.py            # Session 测试（12个用例）
│   └── test_execution_logger.py   # Execution Logger 测试（13个用例）
│
├── sessions/                      # Session 数据目录
│   └── {session_id}/
│       ├── metadata.json
│       ├── workspace/
│       │   └── practice.ipynb
│       ├── logs/
│       │   └── execution_log.json
│       └── reports/
│           ├── report.json
│           └── summary.md
│
├── scoring/                       # 评分标准目录
│   └── {chapter}.json
│
├── reports/                       # 聚合报告目录
│   ├── reviews_summary.md
│   └── reviews_summary.csv
│
├── {chapter}-materials/           # 章节素材目录
│   ├── {chapter}.ipynb            # 模板 notebook
│   ├── {chapter}_guide.md         # 代码详解
│   └── *.csv/*.pkl                # 数据文件
│
└── answers/                       # 参考答案目录
    └── 1.1.1 - 4.2.5参考答案/
        └── {chapter}/
            └── {chapter}.ipynb
```

---

## 2. 模块关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                │
│                                                                 │
│   Jupyter Notebook  ←→  practice.ipynb                         │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Session 生命周期层                          │
│                                                                 │
│   create_timestamped_practice.py                                │
│         │                                                       │
│         ▼                                                       │
│   SessionFactory.create()                                       │
│         │                                                       │
│         ├── 生成 session_id                                     │
│         ├── 创建目录结构                                        │
│         ├── 初始化 metadata.json                                │
│         ├── 初始化 execution_log.json                           │
│         └── 复制模板文件                                        │
│                                                                 │
│   Session 实体                                                  │
│         │                                                       │
│         ├── metadata_path                                       │
│         ├── workspace_dir                                       │
│         ├── logs_dir                                            │
│         └── reports_dir                                         │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       日志记录层                                 │
│                                                                 │
│   execution_logger.py (Phase 2.2 重构)                          │
│         │                                                       │
│         ├── ExecutionLogger(session=session)                    │
│         ├── record_execution()                                  │
│         ├── save() → execution_log.json                         │
│         └── load_log(session)                                   │
│                                                                 │
│   数据协议：schemas/execution_log.schema.json v1.0.0            │
│         │                                                       │
│         ├── schema_version                                      │
│         ├── session_id                                          │
│         ├── logger.version                                      │
│         ├── events[]                                            │
│         │   ├── event_id                                        │
│         │   ├── cell_index                                      │
│         │   ├── source                                          │
│         │   ├── source_hash                                     │
│         │   ├── status                                          │
│         │   └── error {type, message, traceback}                │
│         └── kernel_info                                         │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       验证评分层                                 │
│                                                                 │
│   validate_practice.py                                          │
│         │                                                       │
│         ├── 填空答案对比                                        │
│         ├── 实现方式对比                                        │
│         ├── 执行结果对比                                        │
│         ├── 多版本进步趋势                                      │
│         └── IPython历史命令分析                                 │
│                                                                 │
│   process_auditor.py                                            │
│         │                                                       │
│         ├── 读取 execution_log.json                             │
│         ├── 分析错误模式                                        │
│         ├── 计算过程罚分                                        │
│         └── 稳定性得分                                          │
│                                                                 │
│   scoring_validator.py                                          │
│         │                                                       │
│         ├── 读取 scoring/{chapter}.json                         │
│         ├── v1/v2 格式支持                                      │
│         ├── 考试模式（严格）                                    │
│         └── 练习模式（语义宽松）                                │
│                                                                 │
│   generate_scoring_schema.py                                    │
│         │                                                       │
│         └── 从代码题目汇总.md生成评分标准                        │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       报告分析层                                 │
│                                                                 │
│   exam_review.py                                                │
│         │                                                       │
│         ├── 读取 Session report.json                            │
│         ├── 生成考试分析报告                                    │
│         └── 学习建议                                            │
│                                                                 │
│   aggregate_reviews.py                                          │
│         │                                                       │
│         ├── 读取所有 Session report.json                        │
│         ├── 成绩趋势分析                                        │
│         ├── 知识点掌握度                                        │
│         ├── 通过率统计                                          │
│         └── 生成 reviews_summary.md/csv                         │
│                                                                 │
│   batch_scoring_report.py                                       │
│         │                                                       │
│         └── 批量评分报告                                        │
│                                                                 │
│   analyze_ipython_history.py                                    │
│         │                                                       │
│         ├── 读取 ~/.ipython/history.sqlite                      │
│         ├── 匹配练习文件                                        │
│         └── 命令演化分析                                        │
│                                                                 │
│   check_practice_errors.py                                      │
│         │                                                       │
│         ├── 自动检查 practice 文件错误                          │
│         └── 生成 review 文件                                    │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       数据协议层                                 │
│                                                                 │
│   schemas/metadata.schema.json                                  │
│         │                                                       │
│         ├── session_id                                          │
│         ├── chapter                                             │
│         ├── mode (practice/exam)                                │
│         ├── status                                              │
│         └── kernel_info                                         │
│                                                                 │
│   schemas/execution_log.schema.json                             │
│         │                                                       │
│         ├── events[]                                            │
│         ├── source_hash                                         │
│         └── error {type, message, traceback}                    │
│                                                                 │
│   schemas/report.schema.json                                    │
│         │                                                       │
│         ├── total_score                                         │
│         ├── earned_score                                        │
│         ├── process_penalty                                     │
│         ├── items[]                                             │
│         └── detected_errors[]                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Session 生命周期

```
创建阶段
  │
  ├─ SessionFactory.create(chapter, mode)
  ├─ 生成 session_id: YYYYMMDD_HHMMSS_{random6}_chapter{chapter}
  ├─ 创建目录结构: workspace/, logs/, reports/
  ├─ 初始化 metadata.json
  ├─ 初始化 execution_log.json
  └─ 复制模板文件 → practice.ipynb
  │
  ▼
练习阶段
  │
  ├─ 用户在 Jupyter 中打开 practice.ipynb
  ├─ 执行日志初始化Cell自动运行
  ├─ ExecutionLogger 记录每次 Cell 执行
  │   ├── event_id
  │   ├── cell_index
  │   ├── source (代码)
  │   ├── source_hash
  │   ├── status (success/error)
  │   ├── error {type, message, traceback}
  │   └── duration_ms
  └─ 保存到 logs/execution_log.json
  │
  ▼
验证阶段
  │
  ├─ validate_practice.py 运行
  ├─ 对比填空答案
  ├─ 对比实现方式
  ├─ 对比执行结果
  ├─ process_auditor.py 分析 execution_log
  │   ├── 错误模式识别
  │   ├── 过程罚分计算
  │   └── 稳定性得分
  └─ 生成 reports/report.json
  │
  ▼
分析阶段
  │
  ├─ exam_review.py 生成考试分析报告
  ├─ aggregate_reviews.py 聚合所有 Session
  │   ├── 成绩趋势
  │   ├── 知识点掌握度
  │   └── 通过率统计
  └─ 生成 reports/reviews_summary.md
  │
  ▼
完成阶段
  │
  └─ Session 状态更新为 "completed"
```

---

## 4. 数据流图

```
用户输入
  │
  ▼
create_timestamped_practice.py
  │
  ├── 调用 SessionFactory.create()
  │   ├── 生成 session_id
  │   ├── 创建目录
  │   ├── 初始化 metadata.json
  │   └── 初始化 execution_log.json
  │
  └── 注入日志初始化Cell到 practice.ipynb
      │
      ▼
Jupyter Notebook (用户练习)
  │
  ├── ExecutionLogger 记录每次执行
  │   └── 保存到 logs/execution_log.json
  │
  ▼
validate_practice.py
  │
  ├── 读取 practice.ipynb
  ├── 读取 answers/{chapter}.ipynb
  ├── 读取 logs/execution_log.json
  ├── 调用 process_auditor.py
  │   ├── 分析错误模式
  │   └── 计算过程罚分
  │
  └── 生成 reports/report.json
      │
      ▼
exam_review.py
  │
  └── 读取 report.json
      └── 生成考试分析报告
      │
      ▼
aggregate_reviews.py
  │
  ├── 读取所有 sessions/*/reports/report.json
  ├── 统计分析
  └── 生成 reports/reviews_summary.md
```

---

## 5. 脚本职责矩阵

| 脚本 | 职责 | 依赖 | 状态 |
|------|------|------|------|
| `create_timestamped_practice.py` | 创建 Session | SessionFactory | ✅ 已重构 |
| `execution_logger.py` | 记录执行日志 | Session | ✅ 已重构 |
| `validate_practice.py` | 验证练习答案 | answers/, execution_log | ⏸ 待迁移 |
| `process_auditor.py` | 回溯审计 | execution_log | ⏸ 待迁移 |
| `exam_review.py` | 考试分析报告 | report.json | ⏸ 待迁移 |
| `aggregate_reviews.py` | 成绩中心 | report.json | ⏸ 待迁移 |
| `scoring_validator.py` | 评分验证 | scoring/*.json | ⏸ 待迁移 |
| `generate_scoring_schema.py` | 生成评分标准 | 代码题目汇总.md | ✅ 稳定 |
| `analyze_ipython_history.py` | IPython历史分析 | history.sqlite | ⏸ 独立 |
| `check_practice_errors.py` | 自动错误检查 | practice.ipynb | ⏸ 独立 |
| `batch_scoring_report.py` | 批量评分报告 | report.json | ⏸ 待迁移 |
| `extract_answers_from_ipynb.py` | 提取答案 | practice.ipynb | ✅ 稳定 |
| `session_manager.py` | Session管理器（旧版） | - | ❌ 待废弃 |

---

## 6. 下一步重构风险

### 高风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `validate_practice.py` 路径查找逻辑复杂（1992行） | 迁移困难 | 逐步重构，先保留旧逻辑 |
| `process_auditor.py` 依赖旧 execution_log 格式 | 数据不兼容 | 提供格式转换逻辑 |
| 旧 Session 数据不兼容新 schema | 历史数据丢失 | 提供迁移脚本 |

### 中风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `aggregate_reviews.py` 使用 rglob 搜索 | 性能问题 | 改为从 sessions/ 目录遍历 |
| `exam_review.py` 依赖固定目录结构 | 路径断裂 | 改为从 Session 获取路径 |
| `scoring_validator.py` 支持 v1/v2 格式 | 逻辑复杂 | 统一为 v2 格式 |

### 低风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `analyze_ipython_history.py` 独立运行 | 无影响 | 保持独立 |
| `check_practice_errors.py` 独立运行 | 无影响 | 保持独立 |
| `session_manager.py` 旧版存在 | 混淆 | 标记废弃 |

---

## 7. 重构建议优先级

### Phase 2.3: 验证系统迁移（高优先）

1. 重构 `validate_practice.py`
   - 改为从 Session 获取路径
   - 统一 report.json schema
   - 集成 process_auditor

2. 重构 `process_auditor.py`
   - 接收 Session 对象
   - 使用新 execution_log schema
   - 更新错误指纹逻辑

### Phase 2.4: 报告系统迁移（中优先）

1. 重构 `exam_review.py`
   - 接收 Session 对象
   - 使用新 report schema

2. 重构 `aggregate_reviews.py`
   - 从 sessions/ 目录遍历
   - 统一数据格式

### Phase 3: AI 分析能力（低优先）

1. 知识薄弱点分析
2. 学习建议生成
3. 错误模式识别

### Phase 4: Dashboard（等待）

1. HTML 可视化
2. 成绩趋势图
3. 知识点掌握度图

---

## 8. 隐藏问题

### 8.1 Notebook 路径绑定

**问题**：
```python
# 注入的Cell代码中硬编码了 ROOT_DIR
session = Session('{SESSION_ID}', '/Users/air/xxx')
```

**影响**：
- git clone 到另一台机器会失败
- session 目录移动会失败
- 用户复制 notebook 会失败

**建议**（Phase 3）：
```python
# 只保存 session_id
session = SessionManager.find('{SESSION_ID}')
```

### 8.2 旧 Session 数据迁移

**问题**：
- 现有 sessions/ 目录使用旧格式
- execution_log.json 格式不兼容

**建议**：
```bash
python scripts/migrate_sessions.py
```

### 8.3 session_manager.py 旧版

**问题**：
- `scripts/session_manager.py` 与 `core/session.py` 功能重叠
- 可能导致混淆

**建议**：
- 标记 `scripts/session_manager.py` 为废弃
- 迁移完成后删除

---

## 9. 测试覆盖

| 模块 | 测试文件 | 用例数 | 状态 |
|------|----------|--------|------|
| Session | tests/test_session.py | 12 | ✅ 通过 |
| ExecutionLogger | tests/test_execution_logger.py | 13 | ✅ 通过 |
| SessionFactory | tests/test_session.py | 包含 | ✅ 通过 |
| validate_practice.py | - | 0 | ❌ 无测试 |
| process_auditor.py | - | 0 | ❌ 无测试 |
| exam_review.py | - | 0 | ❌ 无测试 |
| aggregate_reviews.py | - | 0 | ❌ 无测试 |

---

## 10. 总结

### 已完成

- ✅ Session 模型稳定
- ✅ execution_log v1.0 统一
- ✅ 数据关联建立
- ✅ 自动分析基础完成

### 待完成

- ⏸ 验证系统迁移
- ⏸ 报告系统迁移
- ⏸ 历史数据迁移
- ⏸ AI 分析能力
- ⏸ Dashboard

### 当前状态

> **数据基础设施阶段完成**
> 
> 现在可以安全地进行上层功能开发，但建议先完成 Phase 2.3/2.4 迁移，再进入 Phase 3/4。

---

## 11. 下一步行动

1. **立即**：确认此架构地图
2. **Phase 2.3**：重构 `validate_practice.py` + `process_auditor.py`
3. **Phase 2.4**：重构 `exam_review.py` + `aggregate_reviews.py`
4. **Phase 3**：AI 分析能力
5. **Phase 4**：Dashboard