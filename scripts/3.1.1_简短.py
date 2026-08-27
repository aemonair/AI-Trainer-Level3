"""
3.1.1 智能音箱 - 考试简短脚本
"""
import pandas as pd

df = pd.read_excel('template/3.1.1/智能音箱数据集.xlsx')

# 任务1：最常被使用的功能（前3个）
print("功能使用频率：")
print(df['功能调用类型'].value_counts())

# 任务2：最受欢迎和较少使用的功能
print("\n最受欢迎：", df['功能调用类型'].value_counts().index[0])
print("较少使用：", df['功能调用类型'].value_counts().index[-2:].tolist())

# 任务3：平均响应时间
print("\n各功能平均响应时间：")
print(df.groupby('功能调用类型')['响应时间'].mean().sort_values(ascending=False))