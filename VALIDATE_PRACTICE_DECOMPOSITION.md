# validate_practice.py 职责拆分报告

> 分析时间：2026-08-07
> 文件：scripts/validate_practice.py
> 总行数：1992 行
> 目的：为 Phase 2.3 拆分提供设计依据

---

## 1. 职责分布统计

| 职责 | 行数 | 占比 | 函数数量 | 关键函数 |
|------|------|------|----------|----------|
| **Notebook 读取/加载** | ~150 | 7.5% | 3 | `load_notebook`, `extract_outputs` |
| **文件查找/路径管理** | ~200 | 10% | 6 | `find_answer_file`, `find_template_file`, `find_guide_file`, `find_practice_files`, `find_execution_log`, `extract_chapter_from_path` |
| **填空答案提取** | ~350 | 17.5% | 5 | `extract_blanks_from_template`, `extract_filled_answers`, `extract_blank_answers_from_template_and_answer`, `extract_practice_filled_answers`, `count_blanks_in_template` |
| **填空答案对比** | ~200 | 10% | 2 | `compare_fill_answers`, `normalize_code` |
| **输出对比** | ~150 | 7.5% | 3 | `extract_outputs`, `compare_outputs`, `_strip_html_tags` |
| **实现细节检查** | ~150 | 7.5% | 3 | `check_implementation_details`, `extract_key_functions`, `check_logical_errors` |
| **评分计算** | ~250 | 12.5% | 3 | `score_with_schema`, `validate_single_practice`, `load_scoring_schema` |
| **Cell 对齐** | ~100 | 5% | 2 | `align_cells_to_practice`, `is_auto_init_cell` |
| **回溯审计** | ~50 | 2.5% | 1 | 调用 `ProcessAuditor` |
| **IPython 历史分析** | ~200 | 10% | 3 | `analyze_ipython_history_for_practice`, `match_session_by_timestamp`, `classify_knowledge_point` |
| **报告生成** | ~200 | 10% | 3 | `generate_json_report`, `generate_markdown_report`, `print_validation_report` |
| **CLI/入口** | ~100 | 5% | 3 | `parse_args`, `resolve_compare_mode`, `main` |
| **辅助函数** | ~92 | 4.5% | 2 | `check_unfilled_blanks`, `analyze_progress` |

---

## 2. 详细职责分析

### 2.1 Notebook 读取/加载（7.5%）

**函数**：
- `load_notebook(nb_path)` - 加载 notebook JSON
- `extract_outputs(nb)` - 提取所有 Cell 输出（支持 text/html/image）
- `_strip_html_tags(html)` - 剥离 HTML 标签

**依赖**：
- 无外部依赖

**问题**：
- 无

**拆分建议**：
```
validation/notebook_loader.py
├── load_notebook()
├── extract_outputs()
└── _strip_html_tags()
```

---

### 2.2 文件查找/路径管理（10%）

**函数**：
- `find_answer_file(chapter)` - 查找参考答案
- `find_template_file(chapter)` - 查找模板文件
- `find_guide_file(chapter)` - 查找详解文件
- `find_practice_files(chapter, latest)` - 查找练习文件
- `find_execution_log(practice_path)` - 查找执行日志
- `extract_chapter_from_path(practice_path)` - 从路径提取章节号
- `load_manifest(practice_path)` - 加载 manifest.json

**依赖**：
- `ROOT` 全局变量
- 文件系统

**问题**：
- 硬编码路径查找逻辑
- 与 Session 无关

**拆分建议**：
```
# 这部分逻辑应该由 Session + Assessment 提供
# 不再需要独立的文件查找函数
```

---

### 2.3 填空答案提取（17.5%）

**函数**：
- `extract_blanks_from_template(template_path)` - 从模板提取填空位置
- `extract_filled_answers(practice_path, template_path)` - 提取练习填写的答案
- `extract_blank_answers_from_template_and_answer(template_path, answer_path)` - 提取标准答案
- `extract_practice_filled_answers(practice_path, template_path)` - 精确提取填空答案
- `count_blanks_in_template(template_path)` - 统计填空数量

**依赖**：
- `load_notebook`
- 正则表达式

**问题**：
- 逻辑复杂，多种提取策略
- 空格/缩进容错处理

**拆分建议**：
```
validation/answer_checker.py
├── extract_blanks_from_template()
├── extract_filled_answers()
├── extract_blank_answers_from_template_and_answer()
├── extract_practice_filled_answers()
└── count_blanks_in_template()
```

---

### 2.4 填空答案对比（10%）

**函数**：
- `compare_fill_answers(practice_path, template_path, answer_path)` - 对比填空答案
- `normalize_code(code)` - 标准化代码（统一引号、空格）

**依赖**：
- `load_notebook`
- `normalize_code`

**问题**：
- 无

**拆分建议**：
```
validation/answer_checker.py
├── compare_fill_answers()
└── normalize_code()
```

---

### 2.5 输出对比（7.5%）

**函数**：
- `extract_outputs(nb)` - 提取输出（与 2.1 重叠）
- `compare_outputs(practice_outputs, answer_outputs)` - 对比输出
- `_strip_html_tags(html)` - 剥离 HTML（与 2.1 重叠）

**依赖**：
- `difflib`

**问题**：
- `extract_outputs` 被多处调用

**拆分建议**：
```
validation/output_checker.py
├── extract_outputs()
├── compare_outputs()
└── _strip_html_tags()
```

---

### 2.6 实现细节检查（7.5%）

**函数**：
- `check_implementation_details(practice_path, answer_path)` - 检查实现细节
- `extract_key_functions(code)` - 提取关键函数调用
- `check_logical_errors(code)` - 检查逻辑错误（dropna/fillna 未赋值）

**依赖**：
- `load_notebook`
- 正则表达式

**问题**：
- 无

**拆分建议**：
```
validation/implementation_checker.py
├── check_implementation_details()
├── extract_key_functions()
└── check_logical_errors()
```

---

### 2.7 评分计算（12.5%）

**函数**：
- `score_with_schema(schema, practice_path)` - 基于评分标准严格评分
- `validate_single_practice(practice_path, ...)` - 验证单个练习（核心函数）
- `load_scoring_schema(chapter)` - 加载评分标准

**依赖**：
- 几乎所有其他模块
- `ProcessAuditor`
- `analyze_ipython_history_for_practice`

**问题**：
- `validate_single_practice` 是核心函数，但职责过重
- 混合了填空检查、实现检查、输出检查、审计、历史分析

**拆分建议**：
```
validation/validator.py
├── validate_single_practice()  # 作为协调器
└── load_scoring_schema()

validation/score_calculator.py
├── score_with_schema()
└── classify_knowledge_point()
```

---

### 2.8 Cell 对齐（5%）

**函数**：
- `align_cells_to_practice(template_nb, practice_nb)` - 对齐 Cell 索引
- `is_auto_init_cell(cell)` - 判断是否是自动注入的日志 Cell

**依赖**：
- 无

**问题**：
- 无

**拆分建议**：
```
validation/notebook_loader.py
├── align_cells_to_practice()
└── is_auto_init_cell()
```

---

### 2.9 回溯审计（2.5%）

**函数**：
- 调用 `ProcessAuditor`（外部模块）

**依赖**：
- `scripts/process_auditor.ProcessAuditor`

**问题**：
- 无

**拆分建议**：
```
# 迁移到 analysis/process_auditor.py
# 由 validator 调用
```

---

### 2.10 IPython 历史分析（10%）

**函数**：
- `analyze_ipython_history_for_practice(practice_path, chapter)` - 分析历史命令
- `match_session_by_timestamp(practice_path, sessions)` - 通过时间戳匹配 Session
- `classify_knowledge_point(chapter, error_detail)` - 分类知识点

**依赖**：
- `~/.ipython/profile_default/history.sqlite`
- 正则表达式

**问题**：
- 与验证逻辑无关，属于分析能力
- 应该独立为分析模块

**拆分建议**：
```
analysis/ipython_analyzer.py
├── analyze_ipython_history_for_practice()
└── match_session_by_timestamp()

validation/score_calculator.py
└── classify_knowledge_point()  # 或者放在 analysis/
```

---

### 2.11 报告生成（10%）

**函数**：
- `generate_json_report(result, output_path)` - 生成 JSON 报告
- `generate_markdown_report(results, output_path)` - 生成 Markdown 报告
- `print_validation_report(results)` - 打印控制台报告

**依赖**：
- 验证结果字典

**问题**：
- 无

**拆分建议**：
```
validation/report_generator.py
├── generate_json_report()
├── generate_markdown_report()
└── print_validation_report()
```

---

### 2.12 CLI/入口（5%）

**函数**：
- `parse_args()` - 解析命令行参数
- `resolve_compare_mode(args)` - 解析对比模式
- `main()` - 主入口

**依赖**：
- `argparse`
- 所有验证函数

**问题**：
- 无

**拆分建议**：
```
scripts/validate_practice.py  # 仅保留 CLI 入口
└── main()
```

---

## 3. 依赖关系图

```
validate_practice.py (1992行)
    |
    +-- notebook_loader.py (150行)
    |   ├── load_notebook()
    |   ├── extract_outputs()
    |   ├── _strip_html_tags()
    |   ├── align_cells_to_practice()
    |   └── is_auto_init_cell()
    |
    +-- answer_checker.py (350行)
    |   ├── extract_blanks_from_template()
    |   ├── extract_filled_answers()
    |   ├── extract_blank_answers_from_template_and_answer()
    |   ├── extract_practice_filled_answers()
    |   ├── count_blanks_in_template()
    |   ├── compare_fill_answers()
    |   └── normalize_code()
    |
    +-- output_checker.py (150行)
    |   ├── compare_outputs()
    |   └── extract_outputs()  # 可能与 notebook_loader 合并
    |
    +-- implementation_checker.py (150行)
    |   ├── check_implementation_details()
    |   ├── extract_key_functions()
    |   └── check_logical_errors()
    |
    +-- score_calculator.py (250行)
    |   ├── score_with_schema()
    |   ├── load_scoring_schema()
    |   └── classify_knowledge_point()
    |
    +-- validator.py (协调器)
    |   └── validate_single_practice()  # 调用以上所有模块
    |
    +-- report_generator.py (200行)
    |   ├── generate_json_report()
    |   ├── generate_markdown_report()
    |   └── print_validation_report()
    |
    +-- analysis/
    |   ├── process_auditor.py (待迁移)
    |   └── ipython_analyzer.py (100行)
    |       ├── analyze_ipython_history_for_practice()
    |       └── match_session_by_timestamp()
    |
    └── scripts/validate_practice.py (100行)
        └── main()  # CLI 入口
```

---

## 4. 拆分优先级

### Phase 2.3.1：核心模块拆分（高优先）

1. `validation/notebook_loader.py` - 150行
2. `validation/answer_checker.py` - 350行
3. `validation/score_calculator.py` - 250行
4. `validation/validator.py` - 协调器

### Phase 2.3.2：辅助模块拆分（中优先）

5. `validation/output_checker.py` - 150行
6. `validation/implementation_checker.py` - 150行
7. `validation/report_generator.py` - 200行

### Phase 2.3.3：分析模块迁移（低优先）

8. `analysis/process_auditor.py` - 待迁移
9. `analysis/ipython_analyzer.py` - 100行

---

## 5. 关键设计决策

### 5.1 Validator 接口设计

```python
class Validator:
    def validate(
        self,
        session: Session,
        assessment: Assessment
    ) -> Report:
        pass
```

### 5.2 模块职责边界

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| `notebook_loader` | 加载/解析 notebook | Path | Dict |
| `answer_checker` | 填空答案对比 | practice, template, answer | List[Diff] |
| `output_checker` | 输出对比 | practice_outputs, answer_outputs | List[Diff] |
| `implementation_checker` | 实现细节检查 | practice, answer | List[Issue] |
| `score_calculator` | 评分计算 | schema, diffs | Score |
| `validator` | 协调所有检查器 | Session, Assessment | Report |
| `report_generator` | 生成报告 | Report | File/Console |

---

## 6. 风险点

### 高风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `validate_single_practice` 职责过重 | 拆分困难 | 先提取子函数，再拆分模块 |
| 填空提取逻辑复杂 | 容易出错 | 保留原有测试用例 |
| `ProcessAuditor` 依赖旧格式 | 数据不兼容 | 提供格式转换 |

### 中风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 文件查找逻辑硬编码 | 迁移困难 | 由 Session/Assessment 提供 |
| IPython 历史分析独立 | 无影响 | 保持独立 |

### 低风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| CLI 参数复杂 | 无影响 | 保持不变 |

---

## 7. 总结

**validate_practice.py** 实际上已经不是一个简单的 validator，而是：

```
Notebook 加载
    +
文件查找
    +
答案提取
    +
答案对比
    +
输出对比
    +
实现检查
    +
评分计算
    +
回溯审计
    +
历史分析
    +
报告生成
    +
CLI 入口
```

**拆分目标**：

```
validation/
├── notebook_loader.py      # 150行
├── answer_checker.py       # 350行
├── output_checker.py       # 150行
├── implementation_checker.py  # 150行
├── score_calculator.py     # 250行
├── validator.py            # 协调器
└── report_generator.py     # 200行

analysis/
├── process_auditor.py      # 待迁移
└── ipython_analyzer.py     # 100行

scripts/validate_practice.py  # 100行（CLI 入口）
```

**总行数**：1992行 → 1350行（拆分后）+ 642行（协调器/CLI）