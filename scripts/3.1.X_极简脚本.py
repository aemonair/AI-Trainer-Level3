"""
3.1.X 极简考试脚本 - 只输出关键结果
"""
import pandas as pd

# ============================================
# 3.1.1 智能音箱
# ============================================
df = pd.read_excel('template/3.1.1/智能音箱数据集.xlsx')
print("=== 3.1.1 智能音箱 ===")
print(df['功能调用类型'].value_counts())  # 频率排序
print(df.groupby('功能调用类型')['响应时间'].mean().sort_values(ascending=False))  # 响应时间

# ============================================
# 3.1.2 智能照明
# ============================================
df = pd.read_excel('template/3.1.2/智能照明系统数据集.xlsx')
print("\n=== 3.1.2 智能照明 ===")
df['hour'] = pd.to_datetime(df['数据记录的时间戳']).dt.hour
df['period'] = df['hour'].apply(lambda h: '06:00-12:00' if 6<=h<12 else '12:00-18:00' if 12<=h<18 else '18:00-24:00')
print(df.groupby('period')[['光线亮度值（0-100）', '色温值（1000K-6500K）']].mean())
print(df['使用的场景'].value_counts())
print(df['响应时间（秒）'].mean())

# ============================================
# 3.1.3 健康手环（⚠️ 包含边界：6<=h<=8, 17<=h<=20）
# ============================================
df = pd.read_excel('template/3.1.3/智能健康手环数据集.xlsx')
print("\n=== 3.1.3 健康手环 ===")
df_active = df[df['步数'] > 0]  # 过滤步数>0
df_active['hour'] = pd.to_datetime(df_active['日期']).dt.hour
df_active['period'] = df_active['hour'].apply(lambda h: '06:00-08:00' if 6<=h<=8 else '17:00-20:00' if 17<=h<=20 else '其余时段')
print(df_active.groupby('period')['步数'].mean())
print(df['步数'].notna().sum())  # 数据量最多

# ============================================
# 3.1.4 健康监测
# ============================================
df = pd.read_excel('template/3.1.4/智能健康监测系统数据集.xlsx')
print("\n=== 3.1.4 健康监测 ===")
df['hour'] = pd.to_datetime(df['时间戳']).dt.hour
print(f"早晨血压: {df[(df['hour']>=6)&(df['hour']<=8)]['收缩压'].mean():.2f}")
print(f"凌晨血压: {df[(df['hour']>=0)&(df['hour']<=5)]['收缩压'].mean():.2f}")
print(f"血压数据: {df['收缩压'].notna().sum()}条")
print(f"血糖数据: {df['血糖'].notna().sum()}条")
print(f"体脂数据: {df['体脂分析'].notna().sum()}条")

# ============================================
# 3.1.5 智能家居
# ============================================
df = pd.read_excel('template/3.1.5/智能家居环境控制系统数据集.xlsx')
print("\n=== 3.1.5 智能家居 ===")
df['hour'] = pd.to_datetime(df['时间戳']).dt.hour
df['period'] = df['hour'].apply(lambda h: '06:00-12:00' if 6<=h<12 else '13:00-18:00' if 12<=h<18 else '19:00-05:00')
print(df.groupby('period')[['温度', '湿度', '光照水平']].mean())
print(df['响应时间'].mean())
print(df['能源消耗'].mean())