"""
3.1.1 智能音箱产品的数据分析与优化 - 答案验证脚本
"""
import pandas as pd
import numpy as np

# 读取数据
FILE_PATH = 'template/3.1.1/智能音箱数据集.xlsx'
df = pd.read_excel(FILE_PATH)

print("=" * 60)
print("3.1.1 智能音箱产品的数据分析与优化 - 答案验证")
print("=" * 60)

# ============================================
# 任务1：用户使用习惯 - 最常被使用的功能（前3个）
# ============================================
print("\n📊 任务1：用户使用习惯 - 最常被使用的功能（前3个）")
print("-" * 60)

func_counts = df['功能调用类型'].value_counts()
top3 = func_counts.head(3)

print("\n功能使用频率统计：")
for func, count in func_counts.items():
    print(f"  {func}: {count}次")

print(f"\n✅ 前3个最常被使用的功能：")
for i, (func, count) in enumerate(top3.items(), 1):
    print(f"  {i}. {func} ({count}次)")

# 验证答案
expected_top3 = ['调整音量', '查询新闻', '查天气']
actual_top3 = top3.index.tolist()
match = all(a == e for a, e in zip(actual_top3, expected_top3))
print(f"\n🎯 标准答案：{expected_top3}")
print(f"📝 实际结果：{actual_top3}")
print(f"{'✅ 答案正确！' if match else '❌ 答案不匹配！'}")

# ============================================
# 任务2：功能使用频率 - 最受欢迎和较少使用的功能
# ============================================
print("\n\n📊 任务2：功能使用频率 - 最受欢迎和较少使用的功能")
print("-" * 60)

most_popular = func_counts.index[0]
least_used = func_counts.index[-2:].tolist()

print(f"\n✅ 最受欢迎的功能：{most_popular} ({func_counts.iloc[0]}次)")
print(f"✅ 较少使用的功能：{', '.join(least_used)}")

# 验证答案
expected_popular = '调整音量'
expected_least = ['播放音乐', '控制家居']
print(f"\n🎯 标准答案：")
print(f"  最受欢迎：{expected_popular}")
print(f"  较少使用：{expected_least}")
print(f"{'✅ 答案正确！' if most_popular == expected_popular and set(least_used) == set(expected_least) else '❌ 答案不匹配！'}")

# ============================================
# 任务3：响应时间分析 - 不同功能的平均响应时间
# ============================================
print("\n\n📊 任务3：响应时间分析 - 不同功能的平均响应时间")
print("-" * 60)

avg_response = df.groupby('功能调用类型')['响应时间'].mean().sort_values(ascending=False)

print("\n各功能平均响应时间：")
for func, avg_time in avg_response.items():
    print(f"  {func}: {avg_time:.2f}秒")

# 分类
long_response = avg_response.index[0]  # 最长
short_response = avg_response.index[-1]  # 最短
medium_response = avg_response.index[1:-1].tolist()  # 中间

print(f"\n✅ 响应时间较长的功能：{long_response} ({avg_response.iloc[0]:.2f}秒)")
print(f"✅ 响应时间适中的功能：{', '.join(medium_response)}")
print(f"✅ 响应时间较短的功能：{short_response} ({avg_response.iloc[-1]:.2f}秒)")

# 验证答案
expected_long = '控制家居'
expected_medium = ['查询知识', '调整音量', '提醒事项']
expected_short = '查询新闻'
print(f"\n🎯 标准答案：")
print(f"  较长：{expected_long}")
print(f"  适中：{expected_medium}")
print(f"  较短：{expected_short}")
print(f"{'✅ 答案正确！' if long_response == expected_long and short_response == expected_short else '❌ 答案不匹配！'}")

# ============================================
# 任务4：优化方向及解决方案
# ============================================
print("\n\n📊 任务4：优化方向及解决方案")
print("-" * 60)
print("\n优化方向1：网络连接与设备交互优化")
print("  解决方案：强化网络连接稳定性，采用更高效的通信协议")
print("\n优化方向2：提升信息检索效率")
print("  解决方案：优化查询知识的检索算法，加快数据处理速度")
print("\n优化方向3：用户界面与语音识别优化")
print("  解决方案：提升语音识别准确率，简化用户界面设计")

print("\n" + "=" * 60)
print("✅ 验证完成！")
print("=" * 60)