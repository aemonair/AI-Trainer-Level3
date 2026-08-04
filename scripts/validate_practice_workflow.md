# 练习验证系统 - 完整说明

## 📊 当前脚本功能清单

### ✅ 已实现的功能

| 功能 | 说明 | 状态 |
|------|------|------|
| **填空对比** | 对比练习文件与参考答案的代码相似度（95%阈值） | ✅ |
| **实现细节对比** | 检查关键函数使用（pd.cut, np.where, groupby等） | ✅ |
| **执行结果对比** | 对比notebook输出结果（95%相似度） | ✅ |
| **未填空检查** | 检测是否还有 `_____` 未填写 | ✅ |
| **多版本验证** | 支持 `--all-versions` 查看同一章节所有版本 | ✅ |
| **最新版本验证** | 默认 `--latest` 只验证每个章节最新版 | ✅ |
| **特定文件验证** | `--file` 验证单个文件 | ✅ |
| **分模式验证** | fill/implementation/result/both/all 五种模式 | ✅ |
| **Markdown报告** | `--output-report` 生成详细报告 | ✅ |

### ❌ 缺少的功能

| 功能 | 说明 | 优先级 |
|------|------|--------|
| **进步趋势分析** | 对比多版本分数变化，生成进步曲线 | 中 |
| **填空精确提取** | 精确提取每个 `_____` 处填写的内容（当前是整行对比） | 高 |
| **关键参数验证** | 验证参数是否正确（如 bins, labels, right=False） | 中 |
| **错误分类统计** | 按错误类型统计（拼写/语法/逻辑） | 低 |
| **历史对比** | 与之前的练习对比，看是否重复犯同样的错误 | 低 |

---

## 🔄 完整练习流程

### 阶段1：创建练习

```bash
# 1. 创建带时间戳的练习文件
uv run python3 scripts/create_timestamped_practice.py 1.1.1

# 生成文件：1.1.1-materials/1.1.1_practice_202608041234.ipynb
```

### 阶段2：完成练习

在 Jupyter 中打开练习文件，填写所有 `_____` 空白处：

```python
# 模板文件（1.1.1.ipynb）
data = _____________

# 你填写后（1.1.1_practice_202608041234.ipynb）
data = pd.read_csv('patient_data.csv')
```

### 阶段3：验证答案

```bash
# 方式1：快速验证（只看结果）
uv run python3 scripts/validate_practice.py --file 1.1.1-materials/1.1.1_practice_202608041234.ipynb --compare-mode result

# 方式2：完整验证（填空+实现+结果）
uv run python3 scripts/validate_practice.py --file 1.1.1-materials/1.1.1_practice_202608041234.ipynb --compare-mode all

# 方式3：生成详细报告
uv run python3 scripts/validate_practice.py --file 1.1.1-materials/1.1.1_practice_202608041234.ipynb --output-report
```

### 阶段4：查看验证结果

#### 示例输出：
```
📁 章节: 1.1.1
📄 文件: 1.1.1_practice_202608041234.ipynb
💯 得分: 85/100

📝 填空对比:
  单元格 1: 相似度 81%  ← 填空有误

🔧 实现对比:
  单元格 2: 缺少 ['pd.cut']  ← 没用对函数

📤 结果对比:
  单元格 2: 相似度 92%  ← 结果接近但不完全一致

❌ 错误 (2个):
  - 填空错误: 1处
  - 输出不匹配: 1处
```

### 阶段5：修正错误

根据验证结果，回到 Jupyter 修改错误的填空。

### 阶段6：生成Review（仅当有错误时）

```bash
# 手动创建 Review 文件
# 文件名：1.1.1_practice_review.md
```

### 阶段7：多版本进步分析

```bash
# 查看某个章节的所有版本
uv run python3 scripts/validate_practice.py --chapter 1.1.1 --all-versions

# 输出示例：
# 版本1 (20260729): 70分 - 4处未填空
# 版本2 (20260801): 85分 - 1处填空错误
# 版本3 (20260802): 100分 - ✅ 完全正确
# 进步：+30分 📈
```

---

## 📈 验证维度详解

### 1. 填空对比（Fill Comparison）

**对比对象**：练习文件 vs 参考答案

**方法**：
- 逐单元格对比代码
- 计算相似度（SequenceMatcher）
- 相似度 < 95% 标记为错误

**示例**：
```python
# 参考答案
data['RiskLevel'] = np.where(data['DaysInHospital'] > 7, '高风险患者', '低风险患者')

# 你的答案（正确）
data['RiskLevel'] = np.where(data['DaysInHospital'] > 7, '高风险患者', '低风险患者')
# 相似度: 100% ✅

# 你的答案（错误）
data['RiskLevel'] = np.where(data['DaysInHospital'] > 7, '高风险', '低风险')
# 相似度: 85% ❌
```

### 2. 实现对比（Implementation Comparison）

**对比对象**：关键函数使用

**检查项**：
- `pd.read_csv` - 数据读取
- `np.where` - 条件判断
- `pd.cut` - 区间划分
- `.groupby()` - 分组
- `.value_counts()` - 计数
- `.apply()` - 应用函数

**示例**：
```python
# 参考答案使用了 pd.cut
data['BMIRange'] = pd.cut(data['BMI'], bins=bmi_bins, labels=bmi_labels, right=False)

# 如果你用了其他方法（如 pd.qcut）
data['BMIRange'] = pd.qcut(data['BMI'], q=4)
# 警告：缺少 pd.cut ⚠️
```

### 3. 结果对比（Result Comparison）

**对比对象**：notebook 执行输出

**方法**：
- 提取所有 cell 的输出
- 逐一对比文本
- 相似度 < 95% 标记为不匹配

**示例**：
```
# 参考答案输出
高风险患者数量: 413
低风险患者数量: 587

# 你的输出（正确）
高风险患者数量: 413
低风险患者数量: 587
# 相似度: 100% ✅

# 你的输出（错误）
高风险患者数量: 400
低风险患者数量: 600
# 相似度: 85% ❌
```

---

## 🎯 使用建议

### 日常练习流程

```bash
# 1. 创建练习
uv run python3 scripts/create_timestamped_practice.py 1.1.2

# 2. 在 Jupyter 中完成

# 3. 快速验证（只看结果）
uv run python3 scripts/validate_practice.py --file 1.1.2-materials/1.1.2_practice_*.ipynb --compare-mode result

# 4. 如果有错误，详细验证
uv run python3 scripts/validate_practice.py --file 1.1.2-materials/1.1.2_practice_*.ipynb --compare-mode all

# 5. 修正后再次验证

# 6. 如果还有错误，生成 Review
# （手动创建 *_review.md 文件）
```

### 阶段性复习

```bash
# 查看所有章节的最新版本
uv run python3 scripts/validate_practice.py --latest

# 查看特定章节的所有版本（看进步）
uv run python3 scripts/validate_practice.py --chapter 1.1.1 --all-versions

# 生成完整报告
uv run python3 scripts/validate_practice.py --latest --output-report
```

---

## 📊 评分标准

| 项目 | 扣分 | 说明 |
|------|------|------|
| 未填空 | -5分/处 | 还有 `_____` 未填写 |
| 填空错误 | -8分/处 | 填写的答案与参考答案不匹配 |
| 输出不匹配 | -10分/处 | 执行结果与参考答案不一致 |
| 实现差异 | -3分/处 | 使用的函数/方法与参考答案不同 |

**分数区间**：
- 100分：完全正确 ✅
- 90-99分：基本正确，有小问题
- 80-89分：有明显错误
- <80分：需要重点改进

---

## 🔧 脚本位置

- **验证脚本**：`scripts/validate_practice.py`
- **创建练习**：`scripts/create_timestamped_practice.py`
- **聚合Review**：`scripts/aggregate_reviews.py`
- **检查错误**：`scripts/check_practice_errors.py`