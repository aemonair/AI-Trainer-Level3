"""
3.1.2 智能照明 - 考试简短脚本
"""
import pandas as pd

df = pd.read_excel('template/3.1.2/智能照明系统数据集.xlsx')

# 任务1：提取小时 + 分时段
df['hour'] = pd.to_datetime(df['数据记录的时间戳']).dt.hour
def get_period(h):
    if 6 <= h < 12: return '06:00-12:00'
    if 12 <= h < 18: return '12:00-18:00'
    return '18:00-24:00'
df['period'] = df['hour'].apply(get_period)

# 各时段平均亮度和色温
print("各时段平均亮度/色温：")
print(df.groupby('period')[['光线亮度值（0-100）', '色温值（1000K-6500K）']].mean())

# 任务2：场景使用频率
print("\n场景使用频率：")
print(df['使用的场景'].value_counts())

# 任务3：平均响应时间
print("\n平均响应时间：", round(df['响应时间（秒）'].mean(), 2))