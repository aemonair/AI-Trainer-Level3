# 练习验证报告

生成时间: 2026-08-05 23:11:09

## 📊 汇总统计

| 指标 | 数值 |
|------|------|
| 总练习数 | 1 |
| 完全正确 | 0 (0.0%) |
| 平均分 | 0.0 |

## 📝 详细结果

### 1.1.1 - 1.1.1_practice_202608052255.ipynb

**得分**: 0/100

#### ❌ 错误

- 未填空: 4处
- 填空错误: 19处
  - 单元格 0: 相似度 0%
    - 参考答案: ``
    - 你的答案: ``
  - 单元格 1: 相似度 0%
    - 参考答案: ``
    - 你的答案: ``
  - 单元格 2: 相似度 0%
    - 参考答案: ``
    - 你的答案: ``
#### ⚠️ 警告

- 实现差异: 4处
  - 单元格 0: 缺少函数 ['pd.read_csv']
  - 单元格 1: 缺少函数 ['.value_counts(', 'np.where']
  - 单元格 2: 缺少函数 ['.apply(', '.value_counts(', 'pd.cut', 'np.inf', '.groupby(']
#### 📜 IPython历史命令分析

- **Session ID**: 1

- **命令数**: 47

- **修正次数**: 6

**错误模式:**

- 错误：应使用 len(data)
  - `# 1. 统计住院天数超过7天的患者数量及其占比
# 创建新列'RiskLevel'，根据住院天数判断风险等级 3分
data['RiskLevel'] = np.where(data['DaysIn`

- 错误：应使用 len(data)
  - `# 1. 统计住院天数超过7天的患者数量及其占比
# 创建新列'RiskLevel'，根据住院天数判断风险等级 3分
data['RiskLevel'] = np.where(data['DaysIn`

- 错误：应使用 len(data)
  - `# 1. 统计住院天数超过7天的患者数量及其占比
# 创建新列'RiskLevel'，根据住院天数判断风险等级 3分
data['RiskLevel'] = np.where(data['DaysIn`

- 错误：应使用 len(data)
  - `print (help(data.length))
# 1. 统计住院天数超过7天的患者数量及其占比
# 创建新列'RiskLevel'，根据住院天数判断风险等级 3分
data['RiskLevel`

- 错误：应使用 len(data)
  - `print (help(data.length))
# 1. 统计住院天数超过7天的患者数量及其占比
# 创建新列'RiskLevel'，根据住院天数判断风险等级 3分
data['RiskLevel`

**建议:**

- 区间分组：先定义 bins 和 labels，再用 pd.cut() 分组

