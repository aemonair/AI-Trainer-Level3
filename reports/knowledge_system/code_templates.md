# 💻 考试代码模板

生成时间: 2026-08-23 19:43:26


## 保存数据 - `data.to_csv()`

**出现次数**: 44 | **正确率**: 86.4%

```python
# 保存为CSV文件
data.to_csv('output.csv', index=False)
```

**要点**: index=False不保存行索引


## 数据读取 - `pd.read_csv`

**出现次数**: 31 | **正确率**: 100.0%

```python
import pandas as pd
import numpy as np

data = pd.read_csv('data.csv')
```

**要点**: 读取CSV文件，返回DataFrame对象


## 计算平均值 - `data.mean()`

**出现次数**: 25 | **正确率**: 88.0%

```python
# 计算列平均值
mean_val = data['col'].mean()
# Z-score标准化分子
normalized = (data['col'] - data['col'].mean()) / data['col'].std()
```

**要点**: mean()计算算术平均值


## 区间判断 - `data.between()`

**出现次数**: 20 | **正确率**: 100.0%

```python
# 检查值是否在区间内
data['col'].between(18, 70)
# 结合布尔索引筛选
data = data[data['Age'].between(18, 70)]
```

**要点**: between(left, right)包含边界值


## 分组聚合 - `data.groupby()`

**出现次数**: 20 | **正确率**: 100.0%

```python
# 单列分组
stats = data.groupby('col')['target'].mean()
# 多列分组
stats = data.groupby(['col1', 'col2'])['target'].mean()
# 使用agg进行多聚合
stats = data.groupby('col').agg({'col1': 'mean', 'col2': 'count'})
```

**要点**: groupby后接聚合函数：mean(), sum(), count(), agg()


## 区间分组 - `pd.cut()`

**出现次数**: 19 | **正确率**: 100.0%

```python
# 定义区间边界
bins = [0, 18.5, 24, 28, np.inf]
labels = ['偏瘦', '正常', '超重', '肥胖']
# 划分区间
data['category'] = pd.cut(data['col'], bins=bins, labels=labels, right=False)
```

**要点**: right=False表示左闭右开区间，np.inf表示正无穷


## 数据类型转换 - `data.astype()`

**出现次数**: 18 | **正确率**: 100.0%

```python
# 转换为整数
data['col'] = data['col'].astype(int)
# 转换为浮点数
data['col'] = data['col'].astype(float)
# 转换为字符串
data['col'] = data['col'].astype(str)
```

**要点**: astype()用于类型转换，注意处理NaN值


## 删除列/行 - `data.drop()`

**出现次数**: 18 | **正确率**: 88.9%

```python
# 删除列
data = data.drop(columns=['col1', 'col2'])
# 删除行
data = data.drop(index=[0, 1, 2])
```

**要点**: columns参数删除列，index参数删除行


## 执行ONNX推理 - `ort_session.run`

**出现次数**: 17 | **正确率**: 100.0%

```python
# 执行模型推理
ort_outs = ort_session.run(None, ort_inputs)
# ort_inputs是字典，格式: {input_name: input_data}
```

**要点**: run(None, inputs)第一个参数为None表示获取所有输出，第二个参数是输入数据字典


## 加载ONNX模型 - `onnxruntime.InferenceSession`

**出现次数**: 16 | **正确率**: 100.0%

```python
import onnxruntime as ort

# 加载ONNX模型，创建推理会话
ort_session = ort.InferenceSession('model.onnx')
```

**要点**: InferenceSession加载ONNX模型，创建推理会话用于后续预测


## 应用自定义函数 - `data.apply()`

**出现次数**: 15 | **正确率**: 100.0%

```python
# 对每组应用自定义函数
result = data.groupby('col')['target'].apply(lambda x: (x > 0).mean())
# 对列应用函数
data['new_col'] = data['col'].apply(lambda x: x * 2)
```

**要点**: apply()灵活应用自定义函数，常用于复杂聚合


## 创建Numpy数组 - `np.array`

**出现次数**: 14 | **正确率**: 100.0%

```python
# 从图像创建numpy数组
image_array = np.array(image, dtype=np.float32)
# 直接创建数组
arr = np.array([1, 2, 3])
```

**要点**: dtype=np.float32指定32位浮点，常用于模型输入


## 求和 - `data.sum()`

**出现次数**: 12 | **正确率**: 100.0%

```python
# 布尔值求和（统计True的数量）
count = data['is_abnormal'].sum()
# 列求和
total = data['col'].sum()
```

**要点**: True被视为1，False为0，sum()可统计True的数量


## 删除缺失值 - `data.dropna()`

**出现次数**: 12 | **正确率**: 100.0%

```python
data = data.dropna()
# 或删除特定列的缺失值
data = data.dropna(subset=['column_name'])
```

**要点**: dropna()删除包含NaN的行，返回新DataFrame


## 32位浮点类型 - `np.float32`

**出现次数**: 12 | **正确率**: 100.0%

```python
# 创建数组时指定类型
image_array = np.array(image, dtype=np.float32)
# 类型转换
arr = arr.astype(np.float32)
```

**要点**: ONNX模型输入通常要求float32类型


## 扩展数组维度 - `np.expand_dims`

**出现次数**: 11 | **正确率**: 90.9%

```python
# 添加batch维度 (H,W) -> (1,H,W)
image_array = np.expand_dims(image_array, axis=0)
# 添加通道维度 (H,W) -> (H,W,1)
image_array = np.expand_dims(image_array, axis=-1)
```

**要点**: axis=0在第0维扩展，axis=-1在最后一维扩展，模型输入通常需要batch维度


## 计数统计 - `data.value_counts()`

**出现次数**: 11 | **正确率**: 100.0%

```python
# 统计各值出现次数
counts = data['col'].value_counts()
# 按索引排序
counts = data['col'].value_counts().sort_index()
```

**要点**: 返回Series，索引为唯一值，值为出现次数


## 打开图像文件 - `Image.open`

**出现次数**: 10 | **正确率**: 100.0%

```python
from PIL import Image

# 打开图像并转为灰度图
image = Image.open('test.png').convert('L')
# 打开图像并转为RGB
image = Image.open('test.png').convert('RGB')
```

**要点**: convert("L")转灰度图，convert("RGB")转彩色图


## 转换图像模式 - `image.convert`

**出现次数**: 10 | **正确率**: 100.0%

```python
# 转为灰度图
image = Image.open('test.png').convert('L')
# 转为RGB
image = Image.open('test.png').convert('RGB')
```

**要点**: "L"=灰度(单通道), "RGB"=彩色(三通道)


## 缺失值检测 - `data.isnull()`

**出现次数**: 9 | **正确率**: 100.0%

```python
missing_values = data.isnull().sum()
print(missing_values)
```

**要点**: isnull()检测缺失值，sum()统计每列缺失数量


## Softmax函数 - `scipy.special.softmax`

**出现次数**: 8 | **正确率**: 100.0%

```python
import scipy.special

# 应用softmax获取概率分布
probabilities = scipy.special.softmax(output, axis=-1)
```

**要点**: softmax将输出转为概率分布，axis=-1表示沿最后一个维度计算


## 获取最大值索引 - `np.argmax`

**出现次数**: 7 | **正确率**: 85.7%

```python
# 获取预测概率最高的类别
predicted_class = np.argmax(ort_outs[0])
# 沿指定轴获取最大值索引
predicted_classes = np.argmax(output, axis=1)
```

**要点**: argmax返回最大值索引，常用于获取预测类别


## 条件选择 - `np.where()`

**出现次数**: 7 | **正确率**: 100.0%

```python
# 根据条件创建新列
data['new_col'] = np.where(
    data['col'] > threshold,
    '满足条件',
    '不满足条件'
)
```

**要点**: np.where(条件, 真值, 假值)，类似Excel的IF函数


## 调整图像大小 - `image.resize`

**出现次数**: 6 | **正确率**: 66.7%

```python
# 调整图像大小
image = image.resize((28, 28))  # MNIST尺寸
image = image.resize((320, 240))  # 自定义尺寸
```

**要点**: resize((width, height))注意参数顺序是(宽, 高)


## 获取数据行数 - `len(data)`

**出现次数**: 6 | **正确率**: 66.7%

```python
# 获取DataFrame行数
total_rows = len(data)
# 计算占比
ratio = count / len(data)
```

**要点**: len(data)获取DataFrame的行数


## 重复值检测 - `data.duplicated()`

**出现次数**: 5 | **正确率**: 80.0%

```python
duplicate_count = data.duplicated().sum()
print(f'重复行数: {duplicate_count}')
```

**要点**: duplicated()检测重复行


## 获取模型输入信息 - `ort_session.get_inputs`

**出现次数**: 5 | **正确率**: 100.0%

```python
# 获取模型输入的名称
input_name = ort_session.get_inputs()[0].name
# 构建输入字典
ort_inputs = {input_name: input_data}
```

**要点**: get_inputs()返回模型输入列表，[0].name获取第一个输入的名称


## 聚合计算 - `data.agg()`

**出现次数**: 5 | **正确率**: 100.0%

```python
# 单列多聚合
stats = data.groupby('col')['target'].agg(['count', 'mean', 'std'])
# 多列不同聚合
stats = data.groupby('col').agg({
    'col1': 'mean',
    'col2': ['count', 'sum']
})
```

**要点**: agg()可同时进行多种聚合计算


## 安全打开文件 - `with open`

**出现次数**: 5 | **正确率**: 100.0%

```python
# 使用with语句安全打开文件
with open('labels.txt') as f:
    labels = f.read().strip().split('\n')
```

**要点**: with语句自动关闭文件，推荐使用


## 填充缺失值 - `data.fillna()`

**出现次数**: 4 | **正确率**: 100.0%

```python
# 前向填充
data['col'].fillna(method='ffill', inplace=True)
# 后向填充
data['col'].fillna(method='bfill', inplace=True)
# 固定值填充
data['col'].fillna(0, inplace=True)
```

**要点**: ffill=前向填充, bfill=后向填充, inplace=True直接修改原数据


## 计算标准差 - `data.std()`

**出现次数**: 4 | **正确率**: 100.0%

```python
# 计算列标准差
std_val = data['col'].std()
# Z-score标准化分母
normalized = (data['col'] - data['col'].mean()) / data['col'].std()
```

**要点**: std()计算样本标准差


## 读取文件所有行 - `open().readlines`

**出现次数**: 3 | **正确率**: 100.0%

```python
# 读取文件所有行
lines = open('labels.txt').readlines()
# 去除空白字符
class_names = [name.strip() for name in open('labels.txt').readlines()]
```

**要点**: readlines()返回包含换行符的列表，常用strip()去除空白


## 去除字符串空白 - `strip()`

**出现次数**: 3 | **正确率**: 100.0%

```python
# 去除首尾空白字符
name = '  hello  '.strip()  # 'hello'
# 列表推导式去除所有行的空白
class_names = [line.strip() for line in open('labels.txt').readlines()]
```

**要点**: strip()去除首尾空白(空格、换行、制表符)


## 创建目录 - `os.makedirs`

**出现次数**: 3 | **正确率**: 100.0%

```python
import os

# 创建目录（如果不存在）
os.makedirs(result_path, exist_ok=True)
```

**要点**: exist_ok=True避免目录已存在时报错


## OpenCV读取图像 - `cv2.imread`

**出现次数**: 2 | **正确率**: 100.0%

```python
import cv2

# 读取图像
orig_image = cv2.imread('image.png')
# 读取灰度图
gray_image = cv2.imread('image.png', cv2.IMREAD_GRAYSCALE)
```

**要点**: cv2.imread返回numpy数组，默认BGR格式


## OpenCV调整图像大小 - `cv2.resize`

**出现次数**: 2 | **正确率**: 100.0%

```python
# 调整图像大小
image = cv2.resize(image, (320, 240))  # (宽, 高)
```

**要点**: cv2.resize(image, (width, height))参数顺序是(宽, 高)


## 行转列 - `data.unstack()`

**出现次数**: 2 | **正确率**: 100.0%

```python
# 将行索引转为列名
result = data.groupby(['col1', 'col2'])['target'].mean().unstack()
```

**要点**: unstack()将最内层行索引转为列名


## 布尔过滤 - `data.isin()`

**出现次数**: 2 | **正确率**: 100.0%

```python
# 筛选包含在列表中的值
mask = data['col'].isin(['value1', 'value2'])
filtered_data = data[mask]
```

**要点**: isin()等价于多个OR条件


## 字典键转列表 - `list().keys`

**出现次数**: 1 | **正确率**: 100.0%

```python
# 将字典键转为列表
emotion_names = list(emotion_table.keys())
# 通过索引获取键名
predicted_emotion = list(emotion_table.keys())[predicted_label]
```

**要点**: list(dict.keys())将字典的键转为列表，可通过索引访问
