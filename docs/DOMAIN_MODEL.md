# 领域模型设计文档

> 生成时间：2026-08-07
> Phase：2.2.6
> 状态：设计阶段（待实现）

---

## 1. 核心领域对象

```
                 Assessment
                      |
                      | 1:N
                   Session
                      |
        +-------------+-------------+
        |                           |
 ExecutionLog                    Report
        |
        |
 Learning Analysis
```

---

## 2. 对象定义

### 2.1 Assessment（评估任务）

**定义**：一个完整的考试/练习任务定义，包含题目、答案、评分规则。

**职责**：
- 定义章节、模式、材料
- 提供参考答案路径
- 提供评分标准
- 不依赖具体用户

**属性**：
```python
class Assessment:
    id: str                    # 章节号，如 "1.1.1"
    chapter: str               # 章节号
    mode: str                  # "practice" | "exam"
    materials_dir: Path        # 素材目录路径
    template_nb: Path          # 模板 notebook 路径
    answer_nb: Path            # 参考答案路径
    scoring_schema: Path       # 评分标准路径
    guide_md: Path             # 代码详解路径
    data_files: List[Path]     # 数据文件列表（.csv, .pkl 等）
    total_blanks: int          # 填空总数
    total_score: int           # 总分
```

**方法**：
```python
class Assessment:
    def load_template(self) -> Dict
    def load_answer(self) -> Dict
    def load_scoring_schema(self) -> Dict
    def get_blank_count(self) -> int
    def get_total_score(self) -> int
```

**示例**：
```python
assessment = Assessment(
    id="1.1.1",
    chapter="1.1.1",
    mode="practice",
    materials_dir=Path("1.1.1-materials"),
    template_nb=Path("1.1.1-materials/1.1.1.ipynb"),
    answer_nb=Path("answers/1.1.1 - 4.2.5参考答案/1.1.1/1.1.1.ipynb"),
    scoring_schema=Path("scoring/1.1.1.json"),
    guide_md=Path("1.1.1-materials/1.1.1_guide.md"),
    data_files=[Path("1.1.1-materials/patient_data.csv")],
    total_blanks=10,
    total_score=100
)
```

---

### 2.2 Session（会话实例）

**定义**：用户一次完整的练习/考试过程，包含用户代码、执行日志、评分报告。

**职责**：
- 记录用户练习过程
- 存储执行日志
- 存储评分报告
- 关联到 Assessment

**属性**：
```python
class Session:
    session_id: str            # 唯一标识，如 "20260807_143022_abc123_chapter1.1.1"
    assessment: Assessment     # 关联的评估任务
    root_dir: Path             # 项目根目录
    session_dir: Path          # Session 目录
    workspace_dir: Path        # 工作目录
    logs_dir: Path             # 日志目录
    reports_dir: Path          # 报告目录
    
    # 文件路径
    metadata_path: Path        # metadata.json
    practice_nb_path: Path     # practice.ipynb
    execution_log_path: Path   # execution_log.json
    report_path: Path          # report.json
    summary_path: Path         # summary.md
    
    # 元数据
    created_at: str            # 创建时间
    updated_at: str            # 更新时间
    status: str                # "created" | "in_progress" | "completed" | "reviewed"
    mode: str                  # "practice" | "exam"
    score: Optional[int]       # 得分
```

**方法**：
```python
class Session:
    def exists(self) -> bool
    def create_directories(self)
    def save_metadata(self, metadata: Dict)
    def load_metadata(self) -> Optional[Dict]
    def save_execution_log(self, log_data: Dict)
    def load_execution_log(self) -> Optional[Dict]
    def save_report(self, report: Dict)
    def load_report(self) -> Optional[Dict]
    def save_summary(self, summary: str)
    def load_summary(self) -> Optional[str]
    def update_status(self, status: str)
```

**示例**：
```python
session = Session(
    session_id="20260807_143022_abc123_chapter1.1.1",
    assessment=assessment,
    root_dir=Path("/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai")
)

session.create_directories()
session.save_metadata({
    "schema_version": "1.0.0",
    "session_id": session.session_id,
    "chapter": "1.1.1",
    "mode": "practice",
    "created_at": "2026-08-07T14:30:22",
    "status": "created"
})
```

---

### 2.3 ExecutionLog（执行日志）

**定义**：用户在 Session 中的所有代码执行记录，形成事件流。

**职责**：
- 记录每次 Cell 执行
- 记录代码、输出、错误
- 记录执行时间
- 支持回放分析

**属性**：
```python
class ExecutionLog:
    schema_version: str        # "1.0.0"
    session_id: str            # 关联的 Session ID
    logger: Dict               # 日志器信息
    events: List[Event]        # 事件列表
    kernel_info: Dict          # 内核信息
```

**Event 结构**：
```python
class Event:
    event_id: int              # 事件 ID
    cell_index: int            # Cell 索引
    timestamp: str             # 执行时间
    source: str                # 执行的代码
    source_hash: str           # 代码哈希（SHA256）
    output: str                # 输出内容
    status: str                # "success" | "error"
    error: Optional[Dict]      # 错误信息
    duration_ms: float         # 执行时间（毫秒）
    execution_count: int       # 执行次数
```

**Error 结构**：
```python
class Error:
    type: str                  # 错误类型，如 "NameError"
    message: str               # 错误消息
    traceback: str             # 完整堆栈
```

**示例**：
```python
log = {
    "schema_version": "1.0.0",
    "session_id": "20260807_143022_abc123_chapter1.1.1",
    "logger": {
        "version": "1.0.0"
    },
    "events": [
        {
            "event_id": 0,
            "cell_index": 0,
            "timestamp": "2026-08-07T14:30:25",
            "source": "import pandas as pd",
            "source_hash": "abc123...",
            "output": "",
            "status": "success",
            "error": None,
            "duration_ms": 150.5,
            "execution_count": 0
        }
    ],
    "kernel_info": {
        "python_version": "3.11.0"
    }
}
```

---

### 2.4 Report（评分报告）

**定义**：Session 的评分结果，包含得分、错误、建议。

**职责**：
- 记录总分、得分
- 记录错误详情
- 记录过程罚分
- 记录知识点掌握度

**属性**：
```python
class Report:
    schema_version: str        # "1.0.0"
    session_id: str            # 关联的 Session ID
    chapter: str               # 章节号
    total_score: int           # 总分
    earned_score: int          # 得分
    percentage: float          # 得分率
    process_penalty: int       # 过程罚分
    items: List[Item]          # 评分项详情
    detected_errors: List[Error]  # 检测到的错误
    knowledge_points: Dict     # 知识点掌握度
    suggestions: List[str]     # 学习建议
    created_at: str            # 生成时间
```

**Item 结构**：
```python
class Item:
    id: str                    # 评分项 ID，如 "M1"
    description: str           # 描述
    max_score: int             # 满分
    earned_score: int          # 得分
    correct: bool              # 是否正确
    user_answer: str           # 用户答案
    correct_answer: str        # 正确答案
    type: str                  # 类型，如 "api_call"
```

**示例**：
```python
report = {
    "schema_version": "1.0.0",
    "session_id": "20260807_143022_abc123_chapter1.1.1",
    "chapter": "1.1.1",
    "total_score": 100,
    "earned_score": 85,
    "percentage": 85.0,
    "process_penalty": 5,
    "items": [
        {
            "id": "M1",
            "description": "读取数据集",
            "max_score": 10,
            "earned_score": 10,
            "correct": True,
            "user_answer": "data = pd.read_csv('patient_data.csv')",
            "correct_answer": "data = pd.read_csv('patient_data.csv')",
            "type": "api_call"
        }
    ],
    "detected_errors": [
        {
            "type": "fill_incorrect",
            "item_id": "M3",
            "description": "分组操作",
            "deduction": 10,
            "user_answer": "data.groupby('AgeGroup')",
            "correct_answer": "data.groupby('AgeGroup').size()"
        }
    ],
    "knowledge_points": {
        "Pandas": 80.0,
        "数据清洗": 90.0
    },
    "suggestions": [
        "分组操作后需要调用聚合函数（如 .size()、.sum()）"
    ],
    "created_at": "2026-08-07T14:35:00"
}
```

---

### 2.5 Score（评分）

**定义**：评分计算的中间结果，用于生成 Report。

**职责**：
- 记录评分详情
- 记录扣分原因
- 支持多版本对比

**属性**：
```python
class Score:
    total_score: int           # 总分
    earned_score: int          # 得分
    percentage: float          # 得分率
    fill_score: int            # 填空得分
    impl_score: int            # 实现得分
    output_score: int          # 输出得分
    process_penalty: int       # 过程罚分
    details: List[Detail]      # 评分详情
```

---

## 3. 对象关系

### 3.1 核心关系

```
Assessment 1:N Session
Session 1:1 ExecutionLog
Session 1:1 Report
Session 1:N Score（多版本评分）
```

### 3.2 关系图

```
                 Assessment
                      |
                      | 1:N
                      |
                   Session
                      |
        +-------------+-------------+
        |             |             |
        | 1:1         | 1:1         | 1:N
        |             |             |
 ExecutionLog      Report       Score
        |
        | 1:N
        |
      Event
```

---

## 4. 模块职责边界

### 4.1 核心模块

| 模块 | 职责 | 依赖 |
|------|------|------|
| `core/session.py` | Session 实体 | 无 |
| `core/session_factory.py` | Session 创建 | Session |
| `core/assessment.py` | Assessment 实体 | 无 |
| `core/assessment_factory.py` | Assessment 创建 | Assessment |

### 4.2 验证模块

| 模块 | 职责 | 依赖 |
|------|------|------|
| `validation/validator.py` | 协调所有检查器 | Session, Assessment |
| `validation/notebook_loader.py` | 加载/解析 notebook | 无 |
| `validation/answer_checker.py` | 填空答案对比 | notebook_loader |
| `validation/output_checker.py` | 输出对比 | notebook_loader |
| `validation/implementation_checker.py` | 实现细节检查 | notebook_loader |
| `validation/score_calculator.py` | 评分计算 | 所有检查器 |
| `validation/report_generator.py` | 生成报告 | Report |

### 4.3 分析模块

| 模块 | 职责 | 依赖 |
|------|------|------|
| `analysis/process_auditor.py` | 回溯审计 | ExecutionLog |
| `analysis/ipython_analyzer.py` | IPython 历史分析 | history.sqlite |
| `analysis/error_analyzer.py` | 错误模式分析 | ExecutionLog |
| `analysis/learning_pattern.py` | 学习轨迹分析 | ExecutionLog, Report |

### 4.4 脚本模块

| 模块 | 职责 | 依赖 |
|------|------|------|
| `scripts/create_timestamped_practice.py` | 创建练习 | SessionFactory, AssessmentFactory |
| `scripts/validate_practice.py` | CLI 入口 | Validator |
| `scripts/aggregate_reviews.py` | 聚合统计 | Report |
| `scripts/exam_review.py` | 考试分析 | Report, Analysis |

---

## 5. 数据流

### 5.1 创建流程

```
用户输入章节号
    |
    v
AssessmentFactory.create(chapter)
    |
    +-- 查找素材目录
    +-- 加载模板
    +-- 加载答案
    +-- 加载评分标准
    |
    v
SessionFactory.create(assessment, mode)
    |
    +-- 生成 session_id
    +-- 创建目录结构
    +-- 初始化 metadata
    +-- 初始化 execution_log
    +-- 复制模板文件
    |
    v
Session 实例
```

### 5.2 练习流程

```
用户打开 practice.ipynb
    |
    v
ExecutionLogger 自动启动
    |
    v
用户执行 Cell
    |
    v
ExecutionLogger.record_execution()
    |
    +-- 记录代码
    +-- 记录输出
    +-- 记录错误
    +-- 记录时间
    |
    v
保存到 execution_log.json
```

### 5.3 验证流程

```
用户运行 validate_practice.py
    |
    v
Validator(session, assessment)
    |
    +-- notebook_loader.load_practice()
    +-- notebook_loader.load_answer()
    +-- answer_checker.compare_fills()
    +-- output_checker.compare_outputs()
    +-- implementation_checker.check_details()
    +-- process_auditor.audit()
    +-- score_calculator.calculate()
    |
    v
生成 Report
    |
    v
保存到 report.json
```

### 5.4 分析流程

```
aggregate_reviews.py
    |
    v
读取所有 Session 的 report.json
    |
    v
统计分析
    |
    +-- 成绩趋势
    +-- 知识点掌握度
    +-- 通过率统计
    +-- 错误模式分析
    |
    v
生成 reviews_summary.md
```

---

## 6. Session Ownership Rule

**原则**：所有功能必须属于某个 Session。

**错误示例**：
```python
# ❌ 错误：不依赖 Session
validate_practice(
    notebook_path,
    answer_path
)
```

**正确示例**：
```python
# ✅ 正确：依赖 Session
validator = PracticeValidator(
    session=session,
    assessment=assessment
)
validator.run()
```

**原因**：
- Session 是核心资产，不是 notebook
- Notebook 只是 Session 的一个输入
- 所有数据（日志、报告、评分）都归属于 Session

---

## 7. 未来扩展

### 7.1 AI 分析能力

```
ExecutionLog
    |
    v
analysis/error_analyzer.py
    |
    +-- 错误模式识别
    +-- 知识薄弱点分析
    +-- 学习轨迹分析
    |
    v
analysis/learning_pattern.py
    |
    +-- 能力画像
    +-- 学习建议
    +-- 进步趋势
    |
    v
AI Coach
```

### 7.2 Dashboard

```
Session + Report + Analysis
    |
    v
dashboard/
├── session_viewer.py      # Session 查看器
├── score_chart.py         # 成绩趋势图
├── knowledge_map.py       # 知识点掌握图
└── error_heatmap.py       # 错误热力图
```

---

## 8. 实施计划

### Phase 2.2.6：设计（当前）

- ✅ 定义 Assessment 实体
- ✅ 定义 Session 实体
- ✅ 定义 ExecutionLog 实体
- ✅ 定义 Report 实体
- ✅ 定义对象关系
- ✅ 定义模块职责边界

### Phase 2.3：实现 Assessment

- 创建 `core/assessment.py`
- 创建 `core/assessment_factory.py`
- 更新 `SessionFactory` 接收 Assessment
- 更新 `create_timestamped_practice.py`

### Phase 2.3.1：拆分 Validator

- 创建 `validation/` 目录
- 拆分 `validate_practice.py`
- 更新 `Validator` 接口
- 添加单元测试

### Phase 2.3.2：迁移分析模块

- 创建 `analysis/` 目录
- 迁移 `process_auditor.py`
- 创建 `ipython_analyzer.py`
- 添加单元测试

### Phase 2.4：重构报告层

- 重构 `exam_review.py`
- 重构 `aggregate_reviews.py`
- 统一 Report schema

### Phase 2.5：清理遗留

- 标记 `session_manager.py` 为废弃
- 移动旧版文件到 `deprecated/`
- 删除临时测试文件

---

## 9. 约束条件

### 9.1 Schema 约束

- 所有数据文件必须遵循 schema 定义
- schema_version 必须明确
- 不允许随意添加字段

### 9.2 路径约束

- 不允许自己拼 sessions 路径
- 统一使用 `session.xxx_path`
- 所有路径由 Session 提供

### 9.3 依赖约束

- 验证模块不依赖文件系统查找
- 所有输入由 Session/Assessment 提供
- CLI 层负责参数解析和文件查找

---

## 10. 术语表

| 术语 | 定义 |
|------|------|
| Assessment | 评估任务定义（题目、答案、评分规则） |
| Session | 用户一次完整的练习/考试过程 |
| ExecutionLog | 用户代码执行记录事件流 |
| Report | 评分结果（得分、错误、建议） |
| Score | 评分计算的中间结果 |
| Event | 单次 Cell 执行记录 |
| Schema | 数据协议定义 |
| Validator | 验证器（协调所有检查器） |