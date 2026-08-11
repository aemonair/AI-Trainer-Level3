# 脚本清单与目录结构梳理

**生成时间**: 2026-08-08

---

## 📁 当前目录结构

```
人工智能训练师_3级_sucai/
├── backup/                          # 备份目录（原 *-materials）
│   ├── 1.1.1-materials/            # 练习文件、模板、数据等
│   ├── 1.1.2-materials/
│   └── ... (共40个)
├── questions/                       # 题目文件（40个Markdown）
│   ├── 1.1.1_智能医疗系统....md
│   └── ...
├── scoring/                         # 评分标准JSON
│   ├── 1.1.1.json
│   └── ...
├── sessions/                        # 考试会话记录
│   └── 20260808_*/
├── reports/                         # 报告文件
│   ├── reviews_summary.md
│   └── ...
├── scripts/                         # 脚本目录
│   └── (见下方详细清单)
├── core/                            # 核心模块
│   ├── session.py
│   └── session_factory.py
└── schemas/                         # JSON Schema定义
```

---

## 🔍 依赖 materials 目录的脚本

### ⚠️ 需要更新路径的脚本（14个）

| 脚本 | 依赖内容 | 影响程度 | 建议 |
|------|---------|---------|------|
| `validate_practice.py` | 模板文件、详解文件、练习文件 | 🔴 高 | 更新为 `backup/*-materials/` |
| `batch_scoring_report.py` | 练习文件查找 | 🔴 高 | 更新为 `backup/*-materials/` |
| `scoring_validator.py` | 模板文件 | 🔴 高 | 更新为 `backup/*-materials/` |
| `generate_scoring_schema.py` | 模板文件、目录扫描 | 🔴 高 | 更新为 `backup/*-materials/` |
| `extract_answers_from_ipynb.py` | materials目录扫描 | 🟡 中 | 更新为 `backup/*-materials/` |
| `check_practice_errors.py` | guide.md文件 | 🟡 中 | 更新为 `backup/*-materials/` |
| `test_v2_scoring.py` | 练习文件 | 🟡 中 | 更新为 `backup/*-materials/` |
| `analyze_ipython_history.py` | 练习文件路径示例 | 🟢 低 | 仅文档示例 |
| `test_extract.py` | 硬编码路径 | 🟢 低 | 测试脚本，可删除 |
| `test_extract2.py` | 硬编码路径 | 🟢 低 | 测试脚本，可删除 |
| `EXECUTION_LOG_GUIDE.md` | 路径示例 | 🟢 低 | 仅文档示例 |
| `rename_materials.sh` | 重命名脚本 | 🟢 低 | 已完成任务，可删除 |
| `regenerate_questions_from_materials.py` | 题目文件提取 | 🟢 低 | 已完成任务，可归档 |
| `compare_questions.py` | 对比题目 | 🟢 低 | 已完成任务，可归档 |

---

## 📋 脚本详细清单

### 🎯 核心工作流脚本

#### 1. `create_timestamped_practice.py`
- **作用**: 创建考试会话（Exam Session）
- **功能**: 
  - 使用 SessionFactory 创建 Session
  - 自动生成 session_id
  - 创建标准目录结构（workspace/logs/reports）
  - 注入执行日志初始化Cell到notebook
- **用法**: `python3 scripts/create_timestamped_practice.py 1.1.1`
- **依赖**: `core/session_factory.py`
- **状态**: ✅ 正常

#### 2. `validate_practice.py`
- **作用**: 自动验证练习答案是否正确（完整版）
- **功能**:
  - 填空答案对比
  - 实现方式对比
  - 执行结果对比
  - 多版本进步趋势分析
  - IPython历史命令分析
- **用法**: `python3 scripts/validate_practice.py --chapter 1.1.1`
- **依赖**: ⚠️ `backup/*-materials/`（需更新）
- **状态**: ⚠️ 需更新路径

#### 3. `scoring_validator.py`
- **作用**: 基于评分标准的验证器
- **功能**:
  - 读取 scoring/{chapter}.json 评分标准
  - 对比练习文件中的答案与标准答案
  - 支持考试模式（严格）和练习模式（宽松）
  - 生成详细的评分报告
- **用法**: `python3 scripts/scoring_validator.py 1.1.1 --file path/to/practice.ipynb`
- **依赖**: ⚠️ `backup/*-materials/`（需更新）
- **状态**: ⚠️ 需更新路径

#### 4. `batch_scoring_report.py`
- **作用**: 批量生成评分报告
- **功能**:
  - 查找所有章节的练习文件
  - 使用 AST 评分标准进行评分
  - 生成汇总报告（Markdown + CSV）
- **用法**: `python3 scripts/batch_scoring_report.py`
- **依赖**: ⚠️ `backup/*-materials/`（需更新）
- **状态**: ⚠️ 需更新路径

---

### 📊 评分与报告脚本

#### 5. `generate_scoring_schema.py`
- **作用**: 生成评分标准结构化文件
- **功能**:
  - 从代码题目汇总.md中提取评分标准
  - 从模板.ipynb中提取填空位置和分值对应关系
  - 生成 scoring/{chapter}.json 评分标准文件
- **用法**: `python3 scripts/generate_scoring_schema.py --all`
- **依赖**: ⚠️ `backup/*-materials/`（需更新）
- **状态**: ⚠️ 需更新路径

#### 6. `aggregate_reviews.py`
- **作用**: 成绩中心（Score Center）
- **功能**:
  - 读取所有Session的report.json
  - 统计分析：成绩趋势、知识点掌握度、通过率、错题本
  - 生成综合性成绩报告
- **用法**: `python3 scripts/aggregate_reviews.py`
- **依赖**: `sessions/`, `reports/`
- **状态**: ✅ 正常

#### 7. `extract_answers_from_ipynb.py`
- **作用**: 从练习文件和答案文件中提取填空题答案
- **功能**:
  - 提取填空题答案
  - 生成复习题目列表
- **用法**: `python3 scripts/extract_answers_from_ipynb.py --all`
- **依赖**: ⚠️ `backup/*-materials/`（需更新）
- **状态**: ⚠️ 需更新路径

#### 8. `check_practice_errors.py`
- **作用**: 自动检查所有 practice 文件中的错误
- **功能**:
  - 检查练习文件中的错误
  - 生成 review 文件
- **用法**: `python3 scripts/check_practice_errors.py`
- **依赖**: ⚠️ `backup/*-materials/`（需更新）
- **状态**: ⚠️ 需更新路径

---

### 🔧 辅助工具脚本

#### 9. `execution_logger.py`
- **作用**: 执行日志记录器
- **功能**:
  - 在Jupyter Notebook中记录每次Cell执行的代码和输出
  - 输出到Session专属的execution_log.json文件
  - 支持在validate_practice.py中回溯审计
- **用法**: 在Jupyter中运行 `%run scripts/execution_logger.py --init`
- **依赖**: `core/session.py`
- **状态**: ✅ 正常

#### 10. `session_manager.py`
- **作用**: 考试会话管理模块
- **功能**:
  - 创建考试会话目录结构
  - 管理会话生命周期
  - 提供会话查询和统计功能
- **依赖**: 无
- **状态**: ✅ 正常

#### 11. `process_auditor.py`
- **作用**: 回溯审计模块
- **功能**:
  - 读取execution_log.json，分析考试过程中的错误尝试
  - 对比最终代码和历史尝试，识别"中间犯过错"的题目
  - 生成process_penalty（过程罚分）和detected_errors列表
- **依赖**: 无
- **状态**: ✅ 正常

#### 12. `analyze_ipython_history.py`
- **作用**: IPython历史命令分析器
- **功能**:
  - 从 ~/.ipython/profile_default/history.sqlite 读取命令历史
  - 根据时间戳匹配练习文件的session
  - 分析答题过程中的命令演化、修正次数、错误类型
- **用法**: `python3 scripts/analyze_ipython_history.py --all`
- **依赖**: ⚠️ 路径示例需更新
- **状态**: 🟢 低影响

---

### 📝 题目处理脚本

#### 13. `create_questions_batch.py`
- **作用**: 批量生成题目文件（旧版）
- **状态**: 🟢 已被 `regenerate_questions_from_materials.py` 替代

#### 14. `regenerate_questions_from_materials.py`
- **作用**: 从 materials 目录重新生成 questions 目录
- **状态**: ✅ 已完成任务，可归档

#### 15. `compare_questions.py`
- **作用**: 对比 materials 和 questions 目录中的题目文件
- **状态**: ✅ 已完成任务，可归档

#### 16. `parse_questions.py`
- **作用**: 解析题目数据（早期版本）
- **状态**: 🟢 已被替代

#### 17. `extract_questions_from_doc.py`
- **作用**: 从DOC文件提取题目
- **状态**: 🟢 已完成任务

---

### 🧪 测试脚本

#### 18. `test_extract.py`
- **作用**: 测试提取功能
- **状态**: 🟢 可删除

#### 19. `test_extract2.py`
- **作用**: 测试提取功能（第二版）
- **状态**: 🟢 可删除

#### 20. `test_v2_scoring.py`
- **作用**: 测试v2评分系统
- **依赖**: ⚠️ `backup/*-materials/`（需更新）
- **状态**: ⚠️ 需更新路径

#### 21. `test_ast_checker.py`
- **作用**: 测试AST检查器
- **状态**: ✅ 正常

---

### 🔄 转换脚本

#### 22. `convert_v1_to_v2.py`
- **作用**: 将v1评分标准转换为v2格式
- **状态**: ✅ 已完成任务

#### 23. `convert_v2_to_ast.py`
- **作用**: 将v2评分标准转换为AST格式
- **状态**: ✅ 已完成任务

#### 24. `merge_template.py`
- **作用**: 合并模板文件
- **状态**: ✅ 正常

---

### 📚 文档脚本

#### 25. `EXECUTION_LOG_GUIDE.md`
- **作用**: 执行日志使用指南
- **状态**: 🟢 路径示例需更新

#### 26. `validate_practice_workflow.md`
- **作用**: 验证练习工作流程文档
- **状态**: ✅ 正常

#### 27. `REFACTORING_SUMMARY.md`
- **作用**: 重构总结文档
- **状态**: ✅ 正常

---

### 🗂️ 其他脚本

#### 28. `rename_materials.sh`
- **作用**: 批量重命名目录和文件
- **状态**: 🟢 已完成任务，可删除

#### 29. `exam_review.py`
- **作用**: 考试review生成
- **状态**: ✅ 正常

#### 30. `generate_history_summary.py`
- **作用**: 生成历史总结
- **状态**: ✅ 正常

#### 31. `generate_scoring_index.py`
- **作用**: 生成评分索引
- **状态**: ✅ 正常

#### 32. `compare_docx.py`
- **作用**: 比较DOCX文件
- **状态**: ✅ 正常

---

## 🔧 需要更新路径的脚本清单

### 高优先级（🔴 核心工作流）

1. **validate_practice.py** - 第117行、127行
2. **batch_scoring_report.py** - 第39行
3. **scoring_validator.py** - 第819行
4. **generate_scoring_schema.py** - 第72行、208行、238-239行

### 中优先级（🟡 常用工具）

5. **extract_answers_from_ipynb.py** - 第53行、57行
6. **check_practice_errors.py** - 第143行
7. **test_v2_scoring.py** - 第401行

### 低优先级（🟢 文档/测试）

8. **analyze_ipython_history.py** - 第13行（仅示例）
9. **EXECUTION_LOG_GUIDE.md** - 路径示例
10. **test_extract.py** - 可删除
11. **test_extract2.py** - 可删除
12. **rename_materials.sh** - 可删除

---

## 💡 建议操作

### 方案A：全局替换路径（推荐）
```bash
# 将所有脚本中的 *-materials 替换为 backup/*-materials
sed -i '' 's|ROOT / f'\''{chapter}-materials'\''|ROOT / "backup" / f"{chapter}-materials"|g' scripts/*.py
```

### 方案B：创建符号链接（快速）
```bash
# 为每个 materials 目录创建符号链接
for dir in backup/*-materials; do
    ln -s ../$dir .
done
```

### 方案C：修改脚本配置（最安全）
在每个脚本开头添加配置变量，统一修改路径前缀。

---

**下一步**: 请告诉我您希望使用哪种方案更新路径，我将帮您完成修改！