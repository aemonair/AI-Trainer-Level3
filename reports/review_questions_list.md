# 📚 复习题目列表 - 基于填空练习

> 根据练习错误记录整理，重点复习得分较低的章节

---

## 📊 需要重点复习的章节

| 章节 | 得分 | 错误数 | 优先级 |
|------|------|--------|--------|
| 1.1.3 | 0分 | 13处 | 🔴 最高 |
| 1.1.4 | 0分 | 24处 | 🔴 最高 |
| 2.2.5 | 0分 | 18处 | 🔴 最高 |
| 2.1.3 | 18分 | 9处 | 🟠 高 |
| 2.1.1 | 28分 | 9处 | 🟠 高 |
| 1.1.5 | 34分 | 7处 | 🟡 中 |
| 2.1.5 | 48分 | 6处 | 🟡 中 |
| 2.2.1 | 68分 | 4处 | 🟢 低 |
| 2.2.4 | 68分 | 4处 | 🟢 低 |

---

## 1.1.3 信用数据清洗 🔴

### 题目1：数据缺失值统计
**题目**：`missing_values = data._________`
**答案**：`isnull().sum()`
**要点**：
- `isnull()` 检测DataFrame中的缺失值，返回布尔值DataFrame
- `.sum()` 计算每列的缺失值数量

### 题目2：数据重复值统计
**题目**：`duplicate_values = data._________`
**答案**：`duplicated().sum()`
**要点**：
- `duplicated()` 检测重复行，返回布尔值Series
- `.sum()` 计算重复行的总数

### 题目3：年龄合理性检查
**题目**：`data['is_age_valid'] = data['Age']._________(18, 70)`
**答案**：`between`
**要点**：
- `between(18, 70)` 检查年龄是否在18-70岁之间
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
- `all(axis=1)` 检查每行是否所有条件都为True
- 即所有字段都合理

### 题目8：筛选不合理数据
**题目**：`invalid_rows = data[___data['is_valid']]`
**答案**：`~`
**要点**：
- `~` 表示逻辑取反
- 筛选出is_valid为False的行

### 题目9：筛选合理数据
**题目**：`cleaned_data = data[data['is_valid']]`
**答案**：直接使用布尔索引
**要点**：
- 筛选出is_valid为True的行

### 题目10：删除标记列
**题目**：`cleaned_data = cleaned_data._________(columns=[...])`
**答案**：`drop`
**要点**：
- `drop(columns=[...])` 删除指定列

### 题目11：保存清洗后的数据
**题目**：`_________._________(_________, index=False)`
**答案**：`cleaned_data.to_csv('cleaned_credit_data.csv', index=False)`
**要点**：
- `to_csv()` 方法将DataFrame保存为CSV文件
- `index=False` 表示不保存行索引

---

## 1.1.4 用户行为数据分析 🔴

### 题目1：导入pandas库
**题目**：`import _________`
**答案**：`pandas`
**要点**：
- 本节没有使用常见的 `pd` 别名
- 后续代码中直接使用 `pandas.cut()` 而不是 `pd.cut()`

### 题目2：读取数据
**题目**：`data = pandas._________('user_behavior_data.csv')`
**答案**：`read_csv`
**要点**：
- `read_csv()` 函数用于读取CSV文件
- 返回DataFrame对象

### 题目3：删除缺失值
**题目**：`data = data._________()`
**答案**：`dropna`
**要点**：
- `dropna()` 方法删除包含缺失值（NaN）的行
- 默认删除任何包含NaN的行

### 题目4：Age数据类型转换
**题目**：`data['Age'] = data['Age']._________(int)`
**答案**：`astype`
**要点**：
- `astype()` 方法用于数据类型转换
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
- `between(18, 70)` 检查年龄是否在18-70之间
- 使用 `&` 连接多个条件

### 题目8：ReviewScore合理性筛选
**题目**：`data['ReviewScore']._________(1, 5)`
**答案**：`between`
**要点**：
- 评分在1-5分之间

### 题目9：PurchaseAmount标准化（分子）
**题目**：`data['PurchaseAmount'] = (data['PurchaseAmount'] - _________) / _________`
**答案**：`data['PurchaseAmount'].mean()`
**要点**：
- Z-score公式：(原始值 - 平均值) / 标准差
- `mean()` 计算平均值

### 题目10：PurchaseAmount标准化（分母）
**题目**：`/ data['PurchaseAmount']._________()`
**答案**：`std`
**要点**：
- `std()` 计算标准差

### 题目11：ReviewScore标准化（分子）
**题目**：`data['ReviewScore'] = (data['ReviewScore'] - _________) / _________`
**答案**：`data['ReviewScore'].mean()`
**要点**：
- 同样的标准化公式应用于ReviewScore

### 题目12：ReviewScore标准化（分母）
**题目**：`/ data['ReviewScore']._________()`
**答案**：`std`
**要点**：
- `std()` 计算标准差

### 题目13：保存清洗数据
**题目**：`_________.to_csv('cleaned_user_behavior_data.csv', index=False)`
**答案**：`data`
**要点**：
- 保存为CSV文件
- `index=False` 不保存行索引

### 题目14：类别统计
**题目**：`purchase_category_counts = data['PurchaseCategory']._________()`
**答案**：`value_counts`
**要点**：
- `value_counts()` 返回各分类的计数

### 题目15：分组聚合 - 平均值
**题目**：`gender_purchase_amount_mean = data._________('Gender')['PurchaseAmount'].mean()`
**答案**：`groupby`
**要点**：
- `groupby()` 按指定列分组
- `mean()` 计算每组的平均值

### 题目16：年龄区间划分函数
**题目**：`data['AgeGroup'] = pandas._________(data['Age'], bins=bins, labels=labels, right=False)`
**答案**：`cut`
**要点**：
- `cut()` 将连续值划分到指定区间
- `bins` 指定区间边界
- `labels` 指定区间标签
- `right=False` 表示左闭右开区间

### 题目17：年龄区间边界
**题目**：`bins = [18, 26, 36, 46, 56, 66, _________]`
**答案**：`np.inf`
**要点**：
- `np.inf` 表示正无穷大
- 用于最后一个区间的上界

### 题目18：年龄组统计并排序
**题目**：`age_group_counts = data['AgeGroup'].value_counts()._________()`
**答案**：`sort_index()`
**要点**：
- `sort_index()` 按索引（年龄组标签）排序
- 使输出按年龄顺序排列

---

## 2.1.3 金融数据清洗 🟠

### 题目1：计算四分位数Q1
**题目**：`Q1 = data[numeric_cols]._________(0.25)`
**答案**：`quantile`
**要点**：
- `quantile()` 计算分位数
- 0.25表示第一四分位数（25%分位）

### 题目2：计算四分位数Q3
**题目**：`Q3 = data[numeric_cols]._________(0.75)`
**答案**：`quantile`
**要点**：
- 0.75表示第三四分位数（75%分位）

### 题目3：计算IQR
**题目**：`IQR = Q3 - Q1`
**答案**：直接相减
**要点**：
- IQR = Q3 - Q1
- 用于识别异常值

### 题目4：IQR异常值处理
**题目**：`data_cleaned = data[~((data[numeric_cols] < (Q1 - 1.5 * IQR)) | (data[numeric_cols] > (Q3 + 1.5 * IQR)))._________(axis=1)]`
**答案**：`any`
**要点**：
- `any(axis=1)` 检查每行是否有任何列满足条件
- `~` 取反，保留正常值

### 题目5：检查重复值
**题目**：`duplicates = data_cleaned._________( )`
**答案**：`duplicated`
**要点**：
- 检测重复行

### 题目6：归一化处理导入
**题目**：`from sklearn.preprocessing import _________`
**答案**：`MinMaxScaler`
**要点**：
- MinMaxScaler用于最小-最大归一化

### 题目7：拟合和转换
**题目**：`data_cleaned[numeric_cols] = scaler.________________(data_cleaned[numeric_cols])`
**答案**：`fit_transform`
**要点**：
- `fit_transform()` 先拟合数据然后转换

### 题目8：定义目标变量
**题目**：`target_variable = '________________'`
**答案**：`SeriousDlqin2yrs`
**要点**：
- 金融数据中的违约目标变量

### 题目9：划分数据集导入
**题目**：`from sklearn.model_selection import _________`
**答案**：`train_test_split`
**要点**：
- 用于将数据划分为训练集和测试集

### 题目10：定义特征
**题目**：`X = data_cleaned.________(columns=[target_variable, 'Unnamed: 0'])`
**答案**：`drop`
**要点**：
- `drop()` 删除指定列

### 题目11：定义目标
**题目**：`y = data_cleaned[_________]`
**答案**：`target_variable`
**要点**：
- 选取目标变量列

### 题目12：划分数据
**题目**：`X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=____, random_state=42)`
**答案**：`0.2`
**要点**：
- test_size=0.2 表示测试集占20%
- random_state确保可重复性

---

## 2.1.1 数据标注基础 🟠

### 题目1：查看数据信息
**题目**：`data._________()`
**答案**：`info`
**要点**：
- 显示DataFrame的基本信息
- 包括列名、非空值数量、数据类型

### 题目2：缺失值统计
**题目**：`data._________.sum()`
**答案**：`isnull()`
**要点**：
- 检测缺失值并统计每列的数量

### 题目3：删除缺失值
**题目**：`data_cleaned = data._________( )`
**答案**：`dropna`
**要点**：
- 删除包含缺失值的行

### 题目4：数据类型转换
**题目**：`pd.to_numeric(data['Your age'], errors='_________')`
**答案**：`coerce`
**要点**：
- `coerce` 将无法转换的值设为NaN

### 题目5：LabelEncoder导入
**题目**：`from sklearn.preprocessing import _________`
**答案**：`LabelEncoder`
**要点**：
- 用于将分类变量编码为数值

### 题目6：拟合和转换
**题目**：`label_encoder.________________(data['fitness'])`
**答案**：`fit_transform`
**要点**：
- 将分类标签转换为数值

### 题目7：去除列名空格
**题目**：`data.columns = data.columns.str._________( )`
**答案**：`strip`
**要点**：
- 去除列名中的空格

### 题目8：统计分布
**题目**：`exercise_frequency_counts = data_cleaned['How often do you exercise?']._________( )`
**答案**：`value_counts`
**要点**：
- 统计各分类的数量

### 题目9：填充缺失值
**题目**：`data_filled = data.apply(lambda x: x.________(x.mode()[0]))`
**答案**：`fillna`
**要点**：
- `fillna()` 用指定值填充缺失值
- `mode()[0]` 取众数

### 题目10：保存处理后的数据
**题目**：`data_filled.________(cleaned_file_path, index=False)`
**答案**：`to_csv`
**要点**：
- 保存为CSV文件

---

## 1.1.5 交通数据分析 🟡

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

### 题目9：保存清洗数据
**题目**：`data._________('cleaned_vehicle_traffic_data.csv', index=False)`
**答案**：`to_csv`
**要点**：
- 保存为CSV文件

### 题目10：交通事件统计
**题目**：`traffic_event_counts = data['TrafficEvent']._________( )`
**答案**：`value_counts`
**要点**：
- 统计各交通事件的发生次数

### 题目11：分组聚合 - 多列平均值
**题目**：`gender_stats = data.groupby('Gender')[['Speed','TravelDistance','TravelTime']]._________( )`
**答案**：`mean`
**要点**：
- 计算多列的平均值

### 题目12：年龄区间划分
**题目**：`data['AgeGroup'] = pd._________(data['Age'], bins=age_bins, labels=age_labels, right=False)`
**答案**：`cut`
**要点**：
- 将年龄划分到指定区间

### 题目13：年龄组统计
**题目**：`age_group_counts = data['AgeGroup']._________( )`
**答案**：`value_counts`
**要点**：
- 统计各年龄组的驾驶员数

---

## 2.1.5 健康咨询数据处理 🟡

### 题目1：填充缺失值
**题目**：`data_filled = data.apply(lambda x: x.________(x.mode()[0]))`
**答案**：`fillna`
**要点**：
- `fillna()` 用指定值填充缺失值
- `mode()[0]` 取众数

### 题目2：划分数据
**题目**：`train_data, test_data = train_test_split(data_filled, random_state=42)`
**答案**：直接使用train_test_split
**要点**：
- 默认test_size=0.25（25%测试集）

### 题目3：保存处理后的数据
**题目**：`data_filled.________(cleaned_file_path, index=False)`
**答案**：`to_csv`
**要点**：
- 保存为CSV文件

---

## 2.2.1 特征工程 🟢

### 题目1：独热编码
**题目**：`data_encoded = pd.________(data, columns=['Category'])`
**答案**：`get_dummies`
**要点**：
- `get_dummies()` 将分类变量转换为独热编码

### 题目2：导入StandardScaler
**题目**：`from sklearn.preprocessing import _________`
**答案**：`StandardScaler`
**要点**：
- StandardScaler用于标准化特征

### 题目3：拟合和转换
**题目**：`scaled_features = scaler.________(features)`
**答案**：`fit_transform`
**要点**：
- `fit_transform()` 先拟合数据然后转换

### 题目4：特征选择
**题目**：`from sklearn.feature_selection import _________`
**答案**：`SelectKBest`
**要点**：
- SelectKBest选择K个最佳特征

### 题目5：保存特征数据
**题目**：`scaled_df.________('scaled_features.csv', index=False)`
**答案**：`to_csv`
**要点**：
- 保存为CSV文件

---

## 2.2.4 模型优化 🟢

### 题目1：导入网格搜索
**题目**：`from sklearn.model_selection import _________`
**答案**：`GridSearchCV`
**要点**：
- 用于超参数调优

### 题目2：定义参数网格
**题目**：`param_grid = {'n_estimators': [10, 50, 100], 'max_depth': [None, 10, 20]}`
**答案**：字典格式
**要点**：
- 键为参数名，值为参数值列表

### 题目3：创建网格搜索对象
**题目**：`grid_search = _________(model, param_grid, cv=5)`
**答案**：`GridSearchCV`

### 题目4：执行网格搜索
**题目**：`grid_search.________(X_train, y_train)`
**答案**：`fit`

### 题目5：获取最佳参数
**题目**：`best_params = grid_search.________`
**答案**：`best_params_`
**要点**：
- 注意有下划线后缀

### 题目6：获取最佳模型
**题目**：`best_model = grid_search.________`
**答案**：`best_estimator_`

---

## 📝 复习建议

### 高频考点
1. **数据读取**：`pd.read_csv()` - 几乎每章都有
2. **缺失值处理**：`isnull().sum()`, `dropna()`, `fillna()`
3. **数据类型转换**：`astype()`
4. **数据筛选**：`between()`, 布尔索引
5. **分组聚合**：`groupby()`, `mean()`, `value_counts()`
6. **数据保存**：`to_csv()`
7. **区间划分**：`pd.cut()`
8. **数据标准化**：Z-score, MinMaxScaler

### 易错点
1. `isnull()` vs `isna()` - 两者功能相同
2. `dropna()` vs `fillna()` - 删除 vs 填充
3. `groupby()` 后的聚合方法
4. `pd.cut()` 的 `right=False` 参数
5. `fit_transform()` vs `fit()` vs `transform()`
6. `best_params_` 和 `best_estimator_` 的下划线

### 复习顺序
1. 先复习 🔴 最高优先级的章节（1.1.3, 1.1.4, 2.2.5）
2. 再复习 🟠 高优先级的章节（2.1.3, 2.1.1）
3. 最后复习 🟡🟢 中低优先级的章节