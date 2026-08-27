"""
3.1.5 智能家居 - 考试简短脚本
"""
import pandas as pd

df = pd.read_excel('template/3.1.5/智能家居环境控制系统数据集.xlsx')

# 任务1：提取小时 + 分时段
df['hour'] = pd.to_datetime(df['时间戳']).dt.hour
def get_period(h):
    if 6 <= h < 12: return '06:00-12:00'
    if 12 <= h < 18: return '13:00-18:00'
    return '19:00-05:00'
df['period'] = df['hour'].apply(get_period)

# 各时段平均温度、湿度、光照
print("各时段平均温度/湿度/光照：")
print(df.groupby('period')[['温度', '湿度', '光照水平']].mean())

# 任务2：平均响应时间
print("\n平均响应时间：", round(df['响应时间'].mean(), 2))

# 任务3：平均能耗
print("平均能源消耗：", round(df['能源消耗'].mean(), 2))