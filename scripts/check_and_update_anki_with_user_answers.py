#!/usr/bin/env python3
"""
检查用户提供的标准答案与DeepSeek/个人答案的差异
并更新Anki卡片
"""
import pdfplumber
import os
import re
import csv
import logging

logging.getLogger('pdfplumber').setLevel(logging.ERROR)

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

print("="*60)
print("检查用户提供的标准答案")
print("="*60)

# 用户提供的标准答案
user_answers_str = """1. 道德评价的关键是看其行为是否符合社会道德规范。答案：✓
2. 人工智能训练师在处理敏感数据时，可以不经用户同意直接使用这些数据进行模型训练。答案：×
3. 随着全球化的发展，职业道德也呈现出单一化的趋势，不同国家和地区的职业道德规范不存在差异。答案：×
4. 人工智能训练师在职业道德建设中，无需考虑数据的质量与适用性，只需关注模型的训练效果。答案：×
5. 人工智能训练师在开发和训练AI模型时，不需要对模型可能产生的歧视性或偏见性结果负责。答案：×
6. 人工智能训练师的职业道德不包括对用户隐私的保护。答案：×
7. 人工智能训练师的主要任务是设计和开发新的算法。答案：×
8. 职业守则仅仅是一种软约束，不具备法律效力。答案：✓
9. 职业守则的特点之一是具有普遍性，适用于所有行业。答案：×
10. 职业守则核心内容不包括遵守法律。答案：×
11. 人工智能训练师在制定职业守则的过程中，应该充分考虑到人工智能技术的发展趋势和潜在风险。答案：✓
12. 职业守则的实施与监督应该完全依靠员工个人的自觉性。答案：×
13. 职业守则中的奉献社会是指从业人员在工作中要正确处理个人利益和社会整体利益的关系，把个人利益放在首位。答案：×
14. 从业人员能否做到爱岗敬业，取决于他是否具有过硬的专业技能。答案：×
15. 人工智能训练师在训练过程中，可以根据自己的经验和直觉来调整模型参数，以提高模型性能。答案：×
16. 语音输入是Windows输入法的一种智能应用。答案：✓
17. Windows系统的维护利器是一款可以帮助用户优化系统性能、清理垃圾文件和修复系统问题的软件。答案：✓
18. 如果鼠标和键盘都无法使用，可以通过按F8键进入Windows的高级启动选项进行修复。答案：×
19. Windows10中小工具中的时钟可以锁定前端显示。答案：×
20. 在浏览器中，可以通过点击地址栏输入网址来访问网页。答案：✓
21. 浏览器的高级探索功能可以帮助用户更好地了解和管理浏览器的设置和功能。答案：×
22. 使用Ctrl+C可以复制选中的文本或对象。答案：✓
23. 使用Word进行高效办公时，可以同时打开多个文档进行编辑。答案：✓
24. Word样式库中的样式可以快速应用到文档中的多个段落或文本框中。答案：✓
25. 在Word中进行图文混排时，图片和文本框的位置是可以随意调整的。答案：✓
26. 在Excel中，可以使用公式计算单元格中的数据。答案：✓
27. 在Excel中，使用MAX函数可以找到一列数据中的最大值。答案：✓
28. Excel图表的数据可视化功能只能用于静态展示数据，无法进行动态交互。答案：×
29. 工作簿的扩展名是.xls。答案：×
30. 通过利用Excel宏，我们可以将繁琐的重复性任务自动化，使我们的工作变得高效和轻松。答案：✓
31. 用人单位与劳动者订立的劳动合同中，约定了试用期满后自动转正的条款，这样的约定是合法的。答案：×
32. 劳动合同中必须包含劳动合同期限。答案：✓
33. 劳动者在试用期内可以随时解除劳动合同。答案：×
34. 网络运营者应当采取技术措施和其他必要措施，确保其收集的个人信息安全，防止信息泄露、损毁、丢失。答案：✓
35. 网络接入的规范要求中，用户必须使用实名制进行注册。答案：✓
36. 关键信息基础设施的运营者应当自行或者委托网络安全服务机构对其网络的安全性和可能存在的风险每年至少进行一次检测评估。答案：✓
37. 只有发明人和设计人才能成为专利申请主体。答案：×
38. 如果一项发明创造具有新颖性、创造性和实用性，那么它一定可以获得专利授权。答案：×
39. 在专利申请流程中，申请人需要提交详细的专利说明书、权利要求书和摘要等文件。答案：✓
40. 遵纪守法是社会成员的基本义务，因此每个人都应该自觉遵守法律法规。答案：✓
41. 根据我国相关法律法规，人工智能训练师在工作过程中应当享有与其他职业相同的劳动保护权益，包括工作安全、健康保障和合理的工作时间安排等。答案：✓
42. 在人工智能训练师的工作中，使用、复制或分发数据、算法或模型时，必须遵守知识产权法的基本原则，包括尊重知识产权的专有性、保护创作者权益和禁止未经授权的使用。答案：✓
43. 著作权法只保护原创性的作品。答案：✓
44. 专利权的主体只能是发明人或设计人。答案：×
45. 知识产权的保护措施只针对原创性作品。答案：×
46. 数据采集的常用工具包括Python、Excel和SQLServer。答案：✓
47. 使用Python编写网络爬虫时，可以安装requests库，来完成任务。答案：✓
48. 在数据采集流程中，工具应用的意义仅限于提高数据收集的速度。答案：×
49. 数据治理工具主要用于优化人工智能算法训练过程中的数据输入，以确保训练数据集的质量和一致性。答案：×
50. ETL工具的基本原理包括数据抽取、数据转换和数据加载三个步骤。答案：✓
51. 数据存储和管理相关工具通常具有自动备份和恢复功能。答案：✓
52. 云服务是一种基于互联网的计算方式，通过这种方式，共享软硬件资源和信息可以按需求提供给计算机各种终端和其他设备。答案：✓
53. 使用Excel可以将CSV文件转换为JSON格式。答案：×
54. 所有的大数据处理平台都专门用于处理结构化数据，并且不能处理非结构化数据。答案：×
55. 所有的常用数据处理工具都只能处理数值型数据，无法处理文本或图像数据。答案：×
56. 在特征工程中，所有工具都自动选择最佳的特征集，无需人工干预或领域知识。答案：×
57. 数据质量监控工具的主要意义在于减少数据集的大小，以便更快地处理数据。答案：×
58. 数据审核平台是一种专门用于审核和处理数据的软件工具。答案：×
59. PowerBI是微软推出的一款商业智能工具，主要用于数据分析和报告制作。答案：✓
60. 业务流程管理与优化工具只能用于制造业企业。答案：×
61. 数据采集策略应该避免使用自动化工具，以确保数据的原始性。答案：×
62. 数据源选择只要基于数据的准确性，不需要可靠性。答案：×
63. 数据抓取技术中，正则表达式是一种非常强大的工具，可以用于匹配和提取网页中的特定信息。答案：✓
64. 数据抓取策略的优化方法包括使用更快的抓取工具。答案：×
65. 关系型数据库通常用于存储结构化数据，而非关系型数据库则更适合存储半结构化或非结构化数据。答案：✓
66. 数据清洗与预处理流程的第一步是对数据进行缺失值处理。答案：×
67. 数据清洗的主要目的确实是解决数据中的重复值、缺失值和异常值问题。答案：✓
68. 加密技术可以保证数据的机密性，但无法防止数据泄露。答案：×
69. 实时数据处理技术可以处理大量数据并实时产生结果。答案：✓
70. 特征提取的主要方法包括主成分分析和线性判别分析。答案：✓
71. 容器化技术可以完全替代传统的虚拟化技术来管理业务数据处理流程。答案：×
72. 数据质量评估通常是通过对数据进行抽样检查来进行的。答案：✓
73. 数据校验和异常数据检测的方法都是为了确保数据的准确性和完整性。答案：✓
74. 高效业务流程的设计方法应该包括对现有流程的详细分析。答案：✓
75. 合规性检查通常只关注数据的安全性，而不涉及数据的完整性和可用性。答案：×
76. 业务数据产生的场合包括企业内部和外部的各种业务流程。答案：✓
77. 人工智能业务可以根据应用场景分为智能客服、智能家居、自动驾驶和智能医疗等类别。答案：✓
78. 综合人工智能系统中的智能控制模块不能用于实现设备控制。答案：×
79. 推荐系统的功能模块包括用户画像、物品画像和推荐算法三个部分。答案：✓
80. 智能搜索业务不能通过自然语言处理技术来解析和理解搜索查询。答案：×
81. 智能交互功能模块具有自然语言处理能力，可以理解用户的语音指令和文本输入。答案：✓
82. 自动数据处理能够通过人工智能模型和算力，挖掘出稳定且准确的分析结果。答案：✓
83. 最优化决策支持利用人工智能计算来实现系统的最优性能，以及得出达到最优业务指标的分配或决策。答案：✓
84. 智能控制功能模块的原理是通过模拟人类大脑的思维方式来实现对设备的自动控制。答案：×
85. 自然语言处理技术可以自动分析和理解人类语言，从而实现人机交互。答案：✓
86. 生物特征识别是一种身份验证技术，因此可以不经许可获取用户生物特征。答案：×
87. 计算机视觉的功能包括图像处理、目标检测和识别等。答案：✓
88. 图像识别是智能计算在人工智能领域的主要应用之一。答案：✓
89. 数据挖掘和知识发现的流程中，数据清洗和预处理步骤是可选的。答案：×
90. 数据挖掘和知识发现的方法包括监督学习、无监督学习和强化学习。答案：✓
91. 业务模块构建方法的原则包括可扩展性、可重用性和可维护性。答案：✓
92. 业务流程优化方法主要包括流程再造、流程改进和流程分析三种。答案：×
93. 业务数据的收集方法只有通过问卷调查一种方式。答案：×
94. 单据流是企业业务流程的核心流程之一。答案：✓
95. 简单业务流程分析流程的第一步是对现有流程进行详细的记录和描述。答案：✓
96. 简化业务流程就是减少流程中的环节和步骤。答案：×
97. 业务流程优化中的监测和评估阶段的目的是确定优化目标。答案：×
98. 在复杂综合业务流程分析中，控制图和帕累托图是常用的分析工具。答案：✓
99. 技术更新是复杂业务系统改进措施的唯一方法。答案：×
100. 综合业务流程优化方法的原则包括以客户为中心、以流程为导向和持续改进。答案：✓"""

# 解析用户答案
user_answers = {}
pattern = r'(\d+)\.\s*[^\n]+?答案[：:]\s*([✓×])'
for match in re.finditer(pattern, user_answers_str):
    num = int(match.group(1))
    answer = match.group(2)
    # 将✓转换为√
    if answer == '✓':
        answer = '√'
    user_answers[num] = answer

print(f"用户提供的标准答案: {len(user_answers)} 题")
print(f"题号范围: {min(user_answers.keys())} - {max(user_answers.keys())}")

# DeepSeek判断题答案
deepseek_judgment_str = """1√ 2× 3× 4× 5× 6× 7× 8× 9× 10×
11√ 12× 13× 14× 15√ 16√ 17√ 18√ 19√ 20√
21√ 22√ 23√ 24√ 25√ 26√ 27√ 28× 29× 30√
31× 32√ 33× 34√ 35√ 36√ 37× 38× 39√ 40√
41√ 42√ 43√ 44× 45× 46√ 47√ 48× 49√ 50√
51√ 52√ 53√ 54× 55× 56× 57× 58√ 59√ 60×
61× 62× 63√ 64√ 65√ 66× 67√ 68√ 69√ 70√
71× 72√ 73√ 74√ 75× 76√ 77√ 78× 79√ 80×
81√ 82√ 83√ 84× 85√ 86× 87√ 88√ 89× 90√
91√ 92√ 93× 94√ 95√ 96× 97× 98√ 99× 100√"""

deepseek_answers = {}
pattern = r'(\d+)([√×])'
for match in re.finditer(pattern, deepseek_judgment_str):
    num = int(match.group(1))
    answer = match.group(2)
    deepseek_answers[num] = answer

# 提取个人答案
answers_pdf = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'
personal_answers = {}

print("\n提取个人答案PDF...")
with pdfplumber.open(answers_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
    judgment_pattern = r'(\d+)\.\s*([^\n]+?)\s*答案[：:]\s*([√×])'
    for match in re.finditer(judgment_pattern, full_text):
        num = int(match.group(1))
        answer = match.group(3).strip()
        personal_answers[num] = answer

print(f"提取个人答案: {len(personal_answers)} 题")

# 检查差异
print("\n" + "="*60)
print("检查答案差异（前100题）")
print("="*60)

disagreements = []
for num in range(1, 101):
    user_ans = user_answers.get(num)
    deepseek_ans = deepseek_answers.get(num)
    personal_ans = personal_answers.get(num)
    
    if user_ans and deepseek_ans and user_ans != deepseek_ans:
        disagreements.append({
            'num': num,
            'user': user_ans,
            'deepseek': deepseek_ans,
            'personal': personal_ans
        })

print(f"\n用户答案 vs DeepSeek答案 不一致的题目: {len(disagreements)} 题")
for d in disagreements[:10]:
    print(f"  题号{d['num']}: 用户={d['user']}, DeepSeek={d['deepseek']}, 个人={d['personal']}")

# 提取题目PDF
questions_pdf = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

print("\n提取题目PDF...")
with pdfplumber.open(questions_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

judgment_pattern = r'[（(]\s*[）)]\s*\d+\.\s*([^\n]+)'
questions = re.findall(judgment_pattern, full_text)

print(f"题目PDF中判断题: {len(questions)} 题")

# 生成更新后的Anki卡片
print("\n" + "="*60)
print("生成更新后的Anki卡片（含用户标准答案）")
print("="*60)

os.makedirs('anki_cards', exist_ok=True)

# 判断题
with open('anki_cards/理论知识_判断题.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['正面', '背面'])
    for i, q in enumerate(questions):
        front = f"【判断题】{q}"
        
        question_num = i + 1
        user_answer = user_answers.get(question_num)
        deepseek_answer = deepseek_answers.get(question_num)
        personal_answer = personal_answers.get(question_num)
        
        back_parts = []
        
        if user_answer:
            back_parts.append(f"【标准答案】{user_answer}")
        
        if deepseek_answer:
            back_parts.append(f"【DeepSeek答案】{deepseek_answer}")
            if user_answer and deepseek_answer != user_answer:
                back_parts.append("❌ DeepSeek答案错误")
        
        if personal_answer:
            back_parts.append(f"【个人答案】{personal_answer}")
            if user_answer and personal_answer != user_answer:
                back_parts.append("❌ 个人答案错误")
        
        if user_answer:
            if deepseek_answer and personal_answer:
                if deepseek_answer == user_answer and personal_answer == user_answer:
                    back_parts.append("✅ 三者答案一致")
                elif deepseek_answer == user_answer:
                    back_parts.append("✅ DeepSeek与标准答案一致")
                elif personal_answer == user_answer:
                    back_parts.append("✅ 个人答案与标准答案一致")
        
        if not user_answer:
            back_parts.append("⚠️ 暂无标准答案，请人工确认")
        
        back_parts.append(f"\n【题目】\n{q}")
        back = '\n\n'.join(back_parts)
        
        writer.writerow([front, back])

print(f"✅ 判断题: {len(questions)}题 → anki_cards/理论知识_判断题.csv")

# 统计
user_count = len([q for q in questions if user_answers.get(questions.index(q) + 1)])
deepseek_correct = 0
personal_correct = 0
for i, q in enumerate(questions[:100]):
    question_num = i + 1
    user_ans = user_answers.get(question_num)
    deepseek_ans = deepseek_answers.get(question_num)
    personal_ans = personal_answers.get(question_num)
    
    if user_ans and deepseek_ans and user_ans == deepseek_ans:
        deepseek_correct += 1
    if user_ans and personal_ans and user_ans == personal_ans:
        personal_correct += 1

print("\n" + "="*60)
print("答案准确率统计（前100题）")
print("="*60)
print(f"用户标准答案: {user_count}题")
print(f"DeepSeek正确: {deepseek_correct}/100题 ({deepseek_correct}%)")
print(f"个人答案正确: {personal_correct}/100题 ({personal_correct}%)")

print("\n" + "="*60)
print("✅ 完成！")
print("="*60)