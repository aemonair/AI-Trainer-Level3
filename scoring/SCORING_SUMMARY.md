# 评分标准汇总

## 生成说明

评分标准由 `scripts/generate_scoring_schema.py` 自动生成。

生成逻辑：
1. 从模板文件（`{chapter}-materials/{chapter}.ipynb`）中提取填空位置
2. 从注释行中提取分值标记（如 `# 读取数据集 1分`）
3. 从答案文件（`answers/1.1.1 - 4.2.5参考答案/{chapter}/{chapter}.ipynb`）中提取标准答案
4. 生成 `scoring/{chapter}.json` 评分标准文件

## 章节列表

| 章节 | 总分 | 评分项数 | 状态 |
|------|------|----------|------|
| 1.1.1 | 22 | 22 | ✅ |
| 1.1.2 | 20 | 20 | ✅ |
| 1.1.3 | 13 | 13 | ✅ |
| 1.1.4 | 24 | 24 | ✅ |
| 1.1.5 | 24 | 24 | ✅ |
| 2.1.1 | 12 | 12 | ✅ |
| 2.1.2 | 11 | 11 | ✅ |
| 2.1.3 | 12 | 12 | ✅ |
| 2.1.4 | 13 | 13 | ✅ |
| 2.1.5 | 12 | 12 | ✅ |
| 2.2.1 | 13 | 13 | ✅ |
| 2.2.2 | 18 | 18 | ✅ |
| 2.2.3 | 20 | 20 | ✅ |
| 2.2.4 | 18 | 18 | ✅ |
| 2.2.5 | 13 | 13 | ✅ |
| 3.2.1 | 16 | 7 | ✅ |
| 3.2.2 | 17 | 12 | ✅ |
| 3.2.3 | 17 | 7 | ✅ |
| 3.2.4 | 15 | 9 | ✅ |
| 3.2.5 | 17 | 10 | ✅ |

**共 20 个章节有模板文件，已生成评分标准**

## 未生成评分标准的章节

以下章节没有 `.ipynb` 模板文件（文档编写题或分析报告题）：

| 章节 | 类型 | 说明 |
|------|------|------|
| 3.1.1 - 3.1.5 | 分析报告题 | 不涉及Python代码编写 |
| 4.1.1 - 4.1.5 | 文档编写题 | 培训大纲编写 |
| 4.2.1 - 4.2.5 | 方案编写题 | 数据采集和处理指导 |

## 评分标准文件结构

```json
{
  "chapter": "1.1.1",
  "total_score": 22,
  "items": [
    {
      "id": "M1",
      "cell_index": 0,
      "blank_index": 0,
      "line_index": 4,
      "type": "api_call",
      "description": "读取数据集",
      "score": 1,
      "answer": "data = pd.read_csv('patient_data.csv')",
      "template_line": "data = _____________"
    }
  ],
  "metadata": {
    "generated_at": "2026-08-06T22:41:00.000000",
    "template_file": "1.1.1-materials/1.1.1.ipynb",
    "answer_file": "answers/1.1.1 - 4.2.5参考答案/1.1.1/1.1.1.ipynb"
  }
}
```

## 使用方法

### 1. 生成评分标准

```bash
# 生成单个章节
uv run python3 scripts/generate_scoring_schema.py 1.1.1

# 生成所有章节
uv run python3 scripts/generate_scoring_schema.py --all

# 预览不生成
uv run python3 scripts/generate_scoring_schema.py 1.1.1 --dry-run
```

### 2. 使用评分标准验证练习

```bash
# 验证单个文件
uv run python3 scripts/scoring_validator.py 1.1.1 --file path/to/practice.ipynb

# 验证Session
uv run python3 scripts/scoring_validator.py --session sessions/2026-08-05-1430-chapter1.1.1

# 生成详细报告
uv run python3 scripts/scoring_validator.py 1.1.1 --file path/to/practice.ipynb --output-report
```

## 注意事项

1. 评分标准只覆盖代码填空部分，不包含输出结果验证
2. 输出结果验证由 `validate_practice.py` 的 `--check-output` 模式处理
3. 同一行有多个填空时，分值平均分配
4. 评分采用严格模式：答案必须完全一致才得分