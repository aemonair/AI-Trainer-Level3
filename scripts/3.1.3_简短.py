"""
3.1.3 智能健康手环 - 考试简短脚本
⚠️ 时间段包含边界：6<=h<=8, 17<=h<=20
"""
import pandas as pd

df = pd.read_excel('template/3.1.3/智能健康手环数据集.xlsx')

# 任务1：提取小时 + 分时段（⚠️ 包含边界）
df['hour'] = pd.to_datetime(df['日期']).dt.hour
def get_period(h):
    if 6 <= h <= 8: return '06:00-08:00'  # 包含8点
    if 17 <= h <= 20: return '17:00-20:00'  # 包含20点
    return '其余时段'
df['period'] = df['hour'].apply(get_period)

# 各时段平均步数（步数>0）
df_active = df[df['步数'] > 0]
print("各时段平均步数：")
print(df_active.groupby('period')['步数'].mean())

# 任务2：健康指标关注度
print("\n各指标数据量：")
for col in df.columns:
    if col not in ['用户', '日期']:
        print(f"  {col}: {df[col].notna().sum()}条")

# 任务3：平均延迟时间
sync_col = [c for c in df.columns if '同步' in c or '延迟' in c]
if sync_col:
    print(f"\n平均延迟时间：{df[sync_col[0]].mean():.2f}秒")