"""
3.1.2 智能照明系统的数据分析与优化 - 答案验证脚本
"""
import pandas as pd
import numpy as np

# 读取数据
FILE_PATH = 'template/3.1.2/智能照明系统数据集.xlsx'
df = pd.read_excel(FILE_PATH)

print("=" * 60)
print("3.1.2 智能照明系统的数据分析与优化 - 答案验证")
print("=" * 60)

# ============================================
# 任务1：用户使用习惯 - 不同时段对灯光亮度和颜色的偏好
# ============================================
print("\n📊 任务1：用户使用习惯 - 不同时段对灯光亮度和颜色的偏好")
print("-" * 60)

# 提取小时
df['hour'] = pd.to_datetime(df['数据记录的时间戳']).dt.hour

# 定义时间段
def get_period(hour):
    if 6 <= hour < 12:
        return '06:00-12:00'
    elif 12 <= hour < 18:
        return '12:00-18:00'
    else:
        return '18:00-24:00'

df['period'] = df['hour'].apply(get_period)

# 计算各时段的平均亮度和色温
period_stats = df.groupby('period')[['光线亮度值（0-100）', '色温值（1000K-6500K）']].mean()

print("\n各时段平均光线亮度和色温：")
for period in ['06:00-12:00', '12:00-18:00', '18:00-24:00']:
    if period in period_stats.index:
        brightness = period_stats.loc[period, '光线亮度值（0-100）']
        color_temp = period_stats.loc[period, '色温值（1000K-6500K）']
        print(f"  {period}: 亮度={brightness:.2f}, 色温={color_temp:.2f}")

# 验证答案
print(f"\n🎯 标准答案：")
print(f"  06:00-12:00: 51.74, 3689.52")
print(f"  12:00-18:00: 49.93, 3732.40")
print(f"  18:00-24:00: 48.06, 3661.35")

# ============================================
# 任务2：智能场景使用频率
# ============================================
print("\n\n📊 任务2：智能场景使用频率")
print("-" * 60)

scene_counts = df['使用的场景'].value_counts()

print("\n场景使用频率统计：")
for scene, count in scene_counts.items():
    print(f"  {scene}: {count}次")

# 分类
frequent = scene_counts.index[0]
moderate = scene_counts.index[1:3].tolist()
less_used = scene_counts.index[-1]

print(f"\n✅ 频繁使用的场景：{frequent}")
print(f"✅ 适中使用的场景：{', '.join(moderate)}")
print(f"✅ 较少使用的场景：{less_used}")

# 验证答案
expected_frequent = 'Relax Mode'
expected_moderate = ['Reading Mode', 'Work Mode']
expected_less = 'Sleep Mode'
print(f"\n🎯 标准答案：")
print(f"  频繁：{expected_frequent}")
print(f"  适中：{expected_moderate}")
print(f"  较少：{expected_less}")
print(f"{'✅ 答案正确！' if frequent == expected_frequent and less_used == expected_less else '❌ 答案不匹配！'}")

# ============================================
# 任务3：响应时间分析
# ============================================
print("\n\n📊 任务3：响应时间分析")
print("-" * 60)

avg_response = df['响应时间（秒）'].mean()
print(f"\n✅ 平均响应时间：{avg_response:.2f}秒")

# 验证答案
expected_avg = 1.06
print(f"\n🎯 标准答案：{expected_avg}秒")
print(f"{'✅ 答案正确！' if abs(avg_response - expected_avg) < 0.01 else '❌ 答案不匹配！'}")

print(f"\n延迟瓶颈：网络延迟、系统处理能力")

# ============================================
# 任务4：优化方向及解决方案
# ============================================
print("\n\n📊 任务4：优化方向及解决方案")
print("-" * 60)
print("\n优化方向1：提高系统处理能力")
print("  解决方案：优化系统算法，升级硬件性能，预加载常用场景")
print("\n优化方向2：提供个性化用户服务")
print("  解决方案：机器学习分析用户行为，增加自定义选项")
print("\n优化方向3：增强系统的可靠性和安全性")
print("  解决方案：集成自我诊断工具，自动检测潜在问题")

print("\n" + "=" * 60)
print("✅ 验证完成！")
print("=" * 60)