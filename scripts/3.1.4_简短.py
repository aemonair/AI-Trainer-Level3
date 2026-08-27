"""
3.1.4 智能健康监测系统 - 考试简短脚本
"""
import pandas as pd

df = pd.read_excel('template/3.1.4/智能健康监测系统数据集.xlsx')

# 任务1：提取小时
df['hour'] = pd.to_datetime(df['时间戳']).dt.hour

# 血压趋势（早晨vs凌晨）
morning_bp = df[(df['hour'] >= 6) & (df['hour'] <= 8)]['收缩压'].mean()
night_bp = df[(df['hour'] >= 0) & (df['hour'] <= 5)]['收缩压'].mean()
print(f"早晨血压: {morning_bp:.2f}, 凌晨血压: {night_bp:.2f}")

# 血糖趋势（进餐后）
for start, end, name in [(7,9,'早餐后'), (12,14,'午餐后'), (18,20,'晚餐后')]:
    glucose = df[(df['hour'] >= start) & (df['hour'] <= end)]['血糖'].mean()
    print(f"{name}血糖: {glucose:.2f}")

# 任务2：健康指标偏好度
print("\n各指标数据量：")
print(f"  血压: {df['收缩压'].notna().sum() + df['舒张压'].notna().sum()}条")
print(f"  血糖: {df['血糖'].notna().sum()}条")
print(f"  体脂: {df['体脂分析'].notna().sum()}条")

# 任务3：响应时间
print("\n平均响应时间：", round(df['响应时间'].mean(), 2))