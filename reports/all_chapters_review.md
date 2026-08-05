# 📚 所有章节复习题目列表

> 包含所有章节的完整复习题目，无论对错都列出，帮助你全面复习

---

## 📊 所有章节概览

| 章节 | 主题 | 题目数 | 核心考点 |
|------|------|--------|----------|
| 1.1.1 | 患者数据分析 | 12 | np.where, pd.cut, groupby, value_counts |
| 1.1.2 | 传感器数据处理 | 10 | groupby.agg, isin, unstack, fillna |
| 1.1.3 | 信用数据清洗 | 11 | isnull, duplicated, between, all, drop |
| 1.1.4 | 用户行为数据分析 | 18 | dropna, astype, Z-score, pd.cut |
| 1.1.5 | 交通数据分析 | 13 | dropna, astype, between, groupby.agg, pd.cut |

---

## 1.1.1 患者数据分析

### 题目1：导入pandas库
**题目**：`import pandas _________`
**答案**：`as pd`
**要点**：
- 导入pandas库并简写为pd
- 用于数据处理和分析

### 题目2：导入numpy库
**题目**：`import numpy _________`
**答案**：`as np`
**要点**：
- 导入numpy库并简写为np
- 用于数值计算

### 题目3：读取CSV数据
**题目**：`data = pd._________('patient_data.csv')`
**答案**：`read_csv`
**要点**：
- read_csv函数用于读取CSV文件
- 返回DataFrame对象

### 题目4：使用np.where创建风险等级
**题目**：`data['RiskLevel'] = np._________(data['DaysInHospital'] > 7, '高风险患者', '低风险患者')`
**答案**：`where`
**要点**：
- np.where(条件, 真值, 假值)
- 根据条件创建新列

### 题目5：统计风险等级数量
**题目**：`risk_counts = data['RiskLevel']._________( )`
**答案**：`value_counts`
**要点**：
- value_counts()返回各分类的计数

### 题目6：计算高风险患者占比
**题目**：`high_risk_ratio = risk_counts['高风险患者'] / _________(data)`
**答案**：`len`
**要点**：
- len(data)获取数据总行数
- 占比 = 高风险数量 / 总数

### 题目7：定义BMI区间边界
**题目**：`bmi_bins = [0, 18.5, 24, 28, _________]`
**答案**：`np.inf`
**要点**：
- np.inf表示正无穷大
- 用于最后一个区间的上界

### 题目8：定义BMI区间标签
**题目**：`bmi_labels = ['偏瘦', '正常', '超重', _________]`
**答案**：`'肥胖'`
**要点**：
- 标签数量必须与区间数量一致
- 0-18.5偏瘦, 18.5-24正常, 24-28超重, 28+肥胖

### 题目9：使用pd.cut划分BMI区间
**题目**：`data['BMIRange'] = pd._________(data['BMI'], bins=bmi_bins, labels=bmi_labels, right=False)`
**答案**：`cut`
**要点**：
- cut()将连续值划分到指定区间
- right=False表示左闭右开区间

### 题目10：计算各BMI区间高风险比例
**题目**：`bmi_risk_rate = data.groupby('BMIRange')['RiskLevel']._________(lambda x: (x == '高风险患者').mean())`
**答案**：`apply`
**要点**：
- apply()应用自定义函数
- lambda函数计算每组中高风险患者的比例

### 题目11：统计各BMI区间患者数量
**题目**：`bmi_patient_count = data['BMIRange']._________( )`
**答案**：`value_counts`
**要点**：
- value_counts()统计各区间数量

### 题目12：定义年龄区间边界
**题目**：`age_bins = [0, 26, 36, 46, 56, 66, _________]`
**答案**：`np.inf`
**要点**：
- 年龄区间：0-25, 26-35, 36-45, 46-55, 56-65, 65+
- np.inf作为最后一个区间的上界

---

## 1.1.2 传感器数据处理

### 题目1：导入matplotlib库
**题目**：`import matplotlib.pyplot _________`
**答案**：`as plt`
**要点**：
- matplotlib.pyplot用于数据可视化
- 简写为plt

### 题目2：按传感器类型分组统计
**题目**：`sensor_stats = data.groupby('SensorType')['Value']._________(['count', 'mean'])`
**答案**：`agg`
**要点**：
- agg()用于聚合计算
- ['count', 'mean']计算数量和平均值

### 题目3：筛选特定传感器类型
**题目**：`data[data['SensorType']._________(['Temperature', 'Humidity'])]`
**答案**：`isin`
**要点**：
- isin()筛选包含在指定列表中的值
- 等价于多个|条件

### 题目4：按位置和传感器类型双重分组
**题目**：`.groupby([_________, _________])['Value'].mean()`
**答案**：`'Location', 'SensorType'`
**要点**：
- 可以按多列分组
- 计算每组的平均值

### 题目5：将分组结果转为表格形式
**题目**：`._________( )`
**答案**：`unstack`
**要点**：
- unstack()将行索引转为列名
- 使结果更易读

### 题目6：使用np.where标记异常值
**题目**：`data['is_abnormal'] = np.where(条件, _________, _________)`
**答案**：`True, False`
**要点**：
- 满足条件标记为True（异常）
- 否则标记为False（正常）

### 题目7：统计异常值数量
**题目**：`data['is_abnormal']._________( )`
**答案**：`sum`
**要点**：
- True被视为1，False为0
- sum()可以计算异常值数量

### 题目8：前向填充缺失值
**题目**：`data['Value'].fillna(method='_________', inplace=True)`
**答案**：`ffill`
**要点**：
- ffill用前一个有效值填充
- inplace=True直接修改原DataFrame

### 题目9：后向填充缺失值
**题目**：`data['Value'].fillna(method='_________', inplace=True)`
**答案**：`bfill`
**要点**：
- bfill用后一个有效值填充
- 确保开头缺失值也被填补

### 题目10：保存清洗后的数据
**题目**：`cleaned_data.to_csv('cleaned_sensor_data.csv', index=_________)`
**答案**：`False`
**要点**：
- index=False不保存行索引

---

## 1.1.3 信用数据清洗

### 题目1：数据缺失值统计
**题目**：`missing_values = data._________`
**答案**：`isnull().sum()`
**要点**：
- isnull()检测DataFrame中的缺失值，返回布尔值DataFrame
- .sum()计算每列的缺失值数量

### 题目2：数据重复值统计
**题目**：`duplicate_values = data._________`
**答案**：`duplicated().sum()`
**要点**：
- duplicated()检测重复行，返回布尔值Series
- .sum()计算重复行的总数

### 题目3：年龄合理性检查
**题目**：`data['is_age_valid'] = data['Age']._________(18, 70)`
**答案**：`between`
**要点**：
- between(18, 70)检查年龄是否在18-70岁之间
- 合理返回True，否则返回False

### 题目4：收入合理性检查
**题目**：`data['is_income_valid'] = data['Income'] _________ 2000`
**答案**：`>`
**要点**：
- 检查收入是否大于2000（最低合理收入）

### 题目5：贷款金额合理性检查
**题目**：`data['is_loan_amount_valid'] = data['LoanAmount'] < (data['Income'] _________ 5)`
**答案**：`*`
**要点**：
- 贷款金额应小于收入的5倍（合理负债比例）

### 题目6：信用评分合理性检查
**题目**：`data['is_credit_score_valid'] = data['CreditScore']._________(300, 850)`
**答案**：`between`
**要点**：
- FICO信用评分标准范围：300-850

### 题目7：综合有效性检查
**题目**：`validity_checks = data[[...]]._________(axis=1)`
**答案**：`all`
**要点**：
- all(axis=1)检查每行是否所有条件都为True
- 即所有字段都合理

### 题目8：标记整行数据是否合理
**题目**：`data['is_valid'] = _________`
**答案**：`validity_checks`
**要点**：
- 将综合检查结果赋值给新列

### 题目9：筛选不合理数据
**题目**：`invalid_rows = data[___data['is_valid']]`
**答案**：`~`
**要点**：
- ~表示逻辑取反
- 筛选出is_valid为False的行

### 题目10：筛选合理数据
**题目**：`cleaned_data = data[data['is_valid']]`
**答案**：直接使用布尔索引
**要点**：
- 筛选出is_valid为True的行

### 题目11：删除标记列
**题目**：`cleaned_data = cleaned_data._________(columns=[...])`
**答案**：`drop`
**要点**：
- drop(columns=[...])删除指定列

### 题目12：保存清洗后的数据
**题目**：`_________._________(_________, index=False)`
**答案**：`cleaned_data.to_csv('cleaned_credit_data.csv', index=False)`
**要点**：
- to_csv()方法将DataFrame保存为CSV文件
- index=False表示不保存行索引

---

## 1.1.4 用户行为数据分析

### 题目1：导入pandas库
**题目**：`import _________`
**答案**：`pandas`
**要点**：
- 本节没有使用常见的pd别名
- 后续代码中直接使用pandas.cut()而不是pd.cut()

### 题目2：读取数据
**题目**：`data = pandas._________('user_behavior_data.csv')`
**答案**：`read_csv`
**要点**：
- read_csv()函数用于读取CSV文件
- 返回DataFrame对象

### 题目3：删除缺失值
**题目**：`data = data._________( )`
**答案**：`dropna`
**要点**：
- dropna()方法删除包含缺失值（NaN）的行
- 默认删除任何包含NaN的行

### 题目4：Age数据类型转换
**题目**：`data['Age'] = data['Age']._________(int)`
**答案**：`astype`
**要点**：
- astype()方法用于数据类型转换
- Age列转换为整数型（int）

### 题目5：PurchaseAmount数据类型转换
**题目**：`data['PurchaseAmount'] = data['PurchaseAmount']._________(float)`
**答案**：`astype`
**要点**：
- 购买金额可以有小数，所以用float类型

### 题目6：ReviewScore数据类型转换
**题目**：`data['ReviewScore'] = data['ReviewScore']._________(int)`
**答案**：`astype`
**要点**：
- 评分数据为整数

### 题目7：Age合理性筛选
**题目**：`data = data[(data['Age']._________(18, 70)) & ...]`
**答案**：`between`
**要点**：
- between(18, 70)检查年龄是否在18-70之间
- 使用&连接多个条件

### 题目8：PurchaseAmount合理性筛选
**题目**：`data['PurchaseAmount'] _________ 0`
**答案**：`>`
**要点**：
- 购买金额必须大于0

### 题目9：ReviewScore合理性筛选
**题目**：`data['ReviewScore']._________(1, 5)`
**答案**：`between`
**要点**：
- 评分在1-5分之间

### 题目10：PurchaseAmount标准化（分子）
**题目**：`data['PurchaseAmount'] = (data['PurchaseAmount'] - _________) / _________`
**答案**：`data['PurchaseAmount'].mean()`
**要点**：
- Z-score公式：(原始值 - 平均值) / 标准差
- mean()计算平均值

### 题目11：PurchaseAmount标准化（分母）
**题目**：`/ data['PurchaseAmount']._________( )`
**答案**：`std`
**要点**：
- std()计算标准差

### 题目12：ReviewScore标准化（分子）
**题目**：`data['ReviewScore'] = (data['ReviewScore'] - _________) / _________`
**答案**：`data['ReviewScore'].mean()`
**要点**：
- 同样的标准化公式应用于ReviewScore

### 题目13：ReviewScore标准化（分母）
**题目**：`/ data['ReviewScore']._________( )`
**答案**：`std`
**要点**：
- std()计算标准差

### 题目14：保存清洗数据
**题目**：`_________.to_csv('cleaned_user_behavior_data.csv', index=False)`
**答案**：`data`
**要点**：
- 保存为CSV文件
- index=False不保存行索引

### 题目15：类别统计
**题目**：`purchase_category_counts = data['PurchaseCategory']._________( )`
**答案**：`value_counts`
**要点**：
- value_counts()返回各分类的计数

### 题目16：分组聚合 - 平均值
**题目**：`gender_purchase_amount_mean = data._________('Gender')['PurchaseAmount'].mean()`
**答案**：`groupby`
**要点**：
- groupby()按指定列分组
- mean()计算每组的平均值

### 题目17：年龄区间划分函数
**题目**：`data['AgeGroup'] = pandas._________(data['Age'], bins=bins, labels=labels, right=False)`
**答案**：`cut`
**要点**：
- cut()将连续值划分到指定区间
- bins指定区间边界
- labels指定区间标签
- right=False表示左闭右开区间

### 题目18：年龄区间边界
**题目**：`bins = [18, 26, 36, 46, 56, 66, _________]`
**答案**：`np.inf`
**要点**：
- np.inf表示正无穷大
- 用于最后一个区间的上界

### 题目19：年龄组统计并排序
**题目**：`age_group_counts = data['AgeGroup'].value_counts()._________( )`
**答案**：`sort_index()`
**要点**：
- sort_index()按索引（年龄组标签）排序
- 使输出按年龄顺序排列

---

## 1.1.5 交通数据分析

### 题目1：读取数据
**题目**：`data = pd._________('vehicle_traffic_data.csv')`
**答案**：`read_csv`
**要点**：
- 读取CSV文件到DataFrame

### 题目2：删除缺失值
**题目**：`data = data._________( )`
**答案**：`dropna`
**要点**：
- 删除包含缺失值的行

### 题目3：Age数据类型转换
**题目**：`data['Age'] = data['Age']._________(int)`
**答案**：`astype`
**要点**：
- Age列转换为整数型

### 题目4：Speed数据类型转换
**题目**：`data['Speed'] = data['Speed']._________(float)`
**答案**：`astype`
**要点**：
- Speed列转换为浮点型

### 题目5：TravelDistance数据类型转换
**题目**：`data['TravelDistance'] = data['TravelDistance']._________(float)`
**答案**：`astype`
**要点**：
- TravelDistance列转换为浮点型

### 题目6：TravelTime数据类型转换
**题目**：`data['TravelTime'] = data['TravelTime']._________(float)`
**答案**：`astype`
**要点**：
- TravelTime列转换为浮点型

### 题目7：Age合理性筛选
**题目**：`data['Age']._________(18, 70)`
**答案**：`between`
**要点**：
- 年龄在18-70之间

### 题目8：Speed合理性筛选
**题目**：`data['Speed']._________(0, 200)`
**答案**：`between`
**要点**：
- 速度在0-200之间

### 题目9：TravelDistance合理性筛选
**题目**：`data['TravelDistance']._________(1, 1000)`
**答案**：`between`
**要点**：
- 行驶距离在1-1000公里之间

### 题目10：TravelTime合理性筛选
**题目**：`data['TravelTime']._________(1, 1440)`
**答案**：`between`
**要点**：
- 行驶时间在1-1440分钟（24小时）之间

### 题目11：保存清洗数据
**题目**：`data._________('cleaned_vehicle_traffic_data.csv', index=False)`
**答案**：`to_csv`
**要点**：
- 保存为CSV文件

### 题目12：交通事件统计
**题目**：`traffic_event_counts = data['TrafficEvent']._________( )`
**答案**：`value_counts`
**要点**：
- 统计各交通事件的发生次数

### 题目13：分组聚合 - 多列平均值
**题目**：`gender_stats = data.groupby('Gender')._________({'Speed':'mean', 'TravelDistance':'mean', 'TravelTime':'mean'})`
**答案**：`agg`
**要点**：
- agg()方法指定要计算的统计量
- 可以同时计算多列的平均值

### 题目14：年龄区间划分
**题目**：`data['AgeGroup'] = pd._________(data['Age'], bins=age_bins, labels=age_labels, right=False)`
**答案**：`cut`
**要点**：
- 将年龄划分到指定区间

### 题目15：年龄组统计
**题目**：`age_group_counts = data['AgeGroup']._________( )`
**答案**：`value_counts`
**要点**：
- 统计各年龄组的驾驶员数

---

## 📝 复习建议

### 高频考点
1. **数据读取**：`pd.read_csv()` - 几乎每章都有
2. **缺失值处理**：`isnull().sum()`, `dropna()`, `fillna()`
3. **数据类型转换**：`astype()`
4. **数据筛选**：`between()`, 布尔索引
5. **分组聚合**：`groupby()`, `mean()`, `value_counts()`, `agg()`
6. **数据保存**：`to_csv()`
7. **区间划分**：`pd.cut()`
8. **数据标准化**：Z-score, MinMaxScaler

### 易错点
1. `isnull()` vs `isna()` - 两者功能相同
2. `dropna()` vs `fillna()` - 删除 vs 填充
3. `groupby()`后的聚合方法
4. `pd.cut()`的`right=False`参数
5. `fit_transform()` vs `fit()` vs `transform()`
6. `best_params_`和`best_estimator_`的下划线

### 复习顺序
1. 先复习1.1.1和1.1.2（基础数据分析）
2. 再复习1.1.3和1.1.4（数据清洗和标准化）
3. 最后复习1.1.5（综合应用）