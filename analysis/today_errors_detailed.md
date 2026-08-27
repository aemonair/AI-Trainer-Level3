# 📝 今日(2026-08-23)做题错误详细分析

生成时间: 2026-08-23 20:15:00

## 📊 总体统计

- 今日做题session数: 30个
- 有错误的session: 3个
- 总错误数: 9个（全部为评分错误，无执行错误）

---

## ❌ 错误详细分析

### 章节 2.1.5（7个错误）

#### 错误1：M2 - 完成代码填空
- **你的代码**: `print(data.head())`
- **正确答案**: `print(data.info())`
- **错误类型**: 概念错误
- **原因**: 题目要求查看表结构基本信息（列名、数据类型、非空数量），应该用 `info()` 而不是 `head()`
- **记忆要点**: `info()` = 表结构信息，`head()` = 前几行数据

#### 错误2：M11 - 完成代码填空（饼图绘制）
- **你的代码**: `exercise_frequency_counts.plt.pie(autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)`
- **正确答案**: `exercise_frequency_counts.plot.pie(autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)`
- **错误类型**: API记忆错误
- **原因**: 混淆了 `.plot.pie()` 和 `.plt.pie()`，Series对象应该用 `.plot.pie()`
- **记忆要点**: Series/ DataFrame绘图用 `.plot.xxx()`，plt.xxx()是matplotlib.pyplot的函数

#### 错误3 & 4：M12/M13 - 划分训练集和测试集
- **你的代码**: `train_data, test_data = train_test_split(data_filled, random_state=42)`
- **正确答案**: `train_data, test_data = train_test_split(data_filled, test_size=0.2, random_state=42)`
- **错误类型**: 参数错误
- **原因**: 缺少 `test_size=0.2` 参数，题目明确要求测试集占比20%
- **记忆要点**: train_test_split必须指定test_size或train_size

#### 错误5：M11 - 完成代码填空（第二次尝试）
- **你的代码**: `plt.pie(autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)`
- **正确答案**: `exercise_frequency_counts.plot.pie(autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)`
- **错误类型**: 流程错误
- **原因**: 直接用plt.pie()缺少数据源，应该用Series的plot.pie()方法
- **记忆要点**: 饼图数据来自Series时，用 `series.plot.pie()`

#### 错误6 & 7：M15/M16 - 保存结果到文件
- **你的代码**: `data_cleaned.to_csv(cleaned_file_path, index=False)`
- **正确答案**: `data_filled.to_csv(cleaned_file_path, index=False)`
- **错误类型**: 变量名错误
- **原因**: 题目中填充缺失值后的变量名是 `data_filled`，不是 `data_cleaned`
- **记忆要点**: 填空题变量名必须与上下文中定义的变量名一致

---

### 章节 3.2.4（2个错误）

#### 错误8：M7 - 模型预测
- **你的代码**: `predicted_idx = list(labels)`
- **正确答案**: `predicted_idx = np.argmax(accuracy[0])`
- **错误类型**: 概念错误
- **原因**: 不理解如何从概率数组中获取预测类别索引，应该用argmax找最大概率的位置
- **记忆要点**: `np.argmax(probs)` 返回最大值的索引位置

#### 错误9：M8 - 获取预测准确值（百分比）
- **你的代码**: `prob_percentage = accuracy[0]`
- **正确答案**: `prob_percentage = accuracy[0, predicted_idx] * 100`
- **错误类型**: 流程错误
- **原因**: 
  1. 没有用predicted_idx索引到具体类别的概率值
  2. 没有乘以100转换为百分比
- **记忆要点**: `accuracy[0, predicted_idx] * 100` 才是百分比概率

---

## 📋 错误分类汇总

| 错误类型 | 数量 | 涉及题目 |
|---------|------|---------|
| 概念错误 | 2 | M2(info vs head), M7(argmax) |
| API记忆错误 | 2 | M11(plot.pie vs plt.pie) |
| 参数错误 | 2 | M12/M13(缺少test_size) |
| 变量名错误 | 2 | M15/M16(data_cleaned vs data_filled) |
| 流程错误 | 1 | M8(概率计算) |

---

## 🎯 改进建议

### 立即复习（P0）
1. **info() vs head()** - 明确两者区别
2. **plot.pie()** - Series绘图方法
3. **train_test_split参数** - 必须指定test_size
4. **np.argmax()** - 找最大值索引

### 需要建立记忆（P1）
1. **变量名一致性** - 填空题必须用题目中的变量名
2. **概率百分比计算** - `accuracy[0, idx] * 100`

### 已经掌握
- 其他27个session全部正确，说明大部分知识点已经掌握