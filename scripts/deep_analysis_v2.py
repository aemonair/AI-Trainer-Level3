#!/usr/bin/env python3
"""
考试代码知识体系 - 第二轮深度分析
基于考试任务而非孤立API，建立考前最终知识体系
"""
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'
OUTPUT_DIR = ROOT / 'analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_all_exam_data():
    """加载所有exam评分结果"""
    results = []
    for scoring_path in SESSIONS_DIR.rglob('scoring_result_v2_exam.json'):
        try:
            with open(scoring_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['source'] = str(scoring_path)
                data['session_name'] = scoring_path.parent.parent.name
                match = re.search(r'chapter(\d+\.\d+\.\d+)', scoring_path.parent.parent.name)
                data['chapter'] = match.group(1) if match else 'unknown'
                results.append(data)
        except Exception as e:
            pass
    return results

def classify_task(chapter: str, description: str, code: str) -> str:
    """根据章节、描述和代码分类考试任务"""
    ch = chapter
    
    if ch.startswith('1.'):
        if 'read_csv' in code.lower() or '读取' in description:
            return '数据读取'
        if 'RiskLevel' in code or 'np.where' in code.lower() or '风险' in description:
            return '条件分类'
        if 'cut' in code.lower() or '区间' in description or 'bins' in code.lower():
            return '区间分组'
        if 'groupby' in code.lower() and 'apply' in code.lower():
            return '分组统计'
        if 'value_counts' in code.lower():
            return '计数统计'
        if 'fillna' in code.lower():
            return '缺失值处理'
        if 'drop' in code.lower() and 'columns' in code.lower():
            return '列删除'
        if 'duplicated' in code.lower():
            return '重复值检测'
        if 'isnull' in code.lower():
            return '缺失值检测'
        if 'between' in code.lower():
            return '区间过滤'
        if 'to_csv' in code.lower():
            return '数据保存'
        if 'astype' in code.lower():
            return '类型转换'
        return 'Pandas基础操作'
    
    elif ch.startswith('2.1'):
        if 'read_csv' in code.lower() or '读取' in description:
            return '数据读取'
        if 'isnull' in code.lower() or '缺失' in description:
            return '缺失值检测'
        if 'dropna' in code.lower():
            return '缺失值处理'
        if 'fillna' in code.lower():
            return '缺失值填充'
        if 'duplicated' in code.lower() or '重复' in description:
            return '重复值处理'
        if 'drop' in code.lower() and 'columns' in code.lower():
            return '列删除'
        if 'astype' in code.lower() or 'to_numeric' in code.lower():
            return '类型转换'
        if 'between' in code.lower():
            return '区间过滤'
        if 'to_csv' in code.lower() or '保存' in description:
            return '数据保存'
        if 'len(' in code.lower():
            return '数据统计'
        return '数据清洗'
    
    elif ch.startswith('2.2'):
        if 'read_csv' in code.lower() or '加载' in description:
            return '数据读取'
        if 'drop' in code.lower() and ('Unnamed' in code or 'columns' in code.lower()):
            return '特征选择'
        if 'train_test_split' in code.lower():
            return '数据集划分'
        if 'LogisticRegression' in code.lower():
            return 'LogisticRegression建模'
        if 'RandomForest' in code.lower() or 'RandomForestRegressor' in code.lower():
            return 'RandomForest建模'
        if 'XGBoost' in code.lower() or 'xgb' in code.lower():
            return 'XGBoost建模'
        if 'LinearRegression' in code.lower():
            return 'LinearRegression建模'
        if 'StandardScaler' in code.lower() or 'scaler' in code.lower():
            return '数据标准化'
        if 'fit(' in code.lower() and ('model' in code.lower() or 'pipeline' in code.lower()):
            return '模型训练'
        if 'predict' in code.lower():
            return '模型预测'
        if 'classification_report' in code.lower():
            return '分类评估'
        if 'score(' in code.lower():
            return '回归评估'
        if '(y_test == y_pred).mean()' in code.replace(' ', '') or \
           '(y_test==y_pred).mean()' in code.replace(' ', '') or \
           '==' in code and 'mean()' in code.lower():
            return '准确率计算'
        if 'to_csv' in code.lower() or '保存' in description:
            return '结果保存'
        if 'pickle' in code.lower() or 'pkl' in code.lower():
            return '模型保存'
        if 'SMOTE' in code.lower():
            return '数据不平衡处理'
        if 'Pipeline' in code.lower():
            return 'Pipeline构建'
        return '机器学习操作'
    
    elif ch.startswith('3.'):
        if 'InferenceSession' in code or 'ort.' in code.lower() or 'onnxruntime' in code.lower():
            return 'ONNX模型加载'
        if 'get_inputs' in code.lower():
            return 'ONNX输入获取'
        if 'ort_session.run' in code.lower() or 'session.run' in code.lower():
            return 'ONNX推理'
        if 'Image.open' in code.lower() or 'image.open' in code.lower():
            return 'PIL图像加载'
        if 'convert(' in code.lower() and ('L' in code or 'RGB' in code):
            return '图像模式转换'
        if 'resize' in code.lower() and ('image' in code.lower() or 'img' in code.lower()):
            return '图像resize'
        if 'cv2.imread' in code.lower():
            return 'OpenCV图像加载'
        if 'cv2.resize' in code.lower():
            return 'OpenCV图像resize'
        if 'np.array' in code.lower():
            return '图像转numpy'
        if 'np.float32' in code.lower() or 'float32' in code.lower():
            return '类型转换float32'
        if 'expand_dims' in code.lower():
            return '维度扩展'
        if 'softmax' in code.lower():
            return 'Softmax概率'
        if 'argmax' in code.lower():
            return 'Top-K预测'
        if 'emotion_table' in code.lower() or 'class_names' in code.lower():
            return '类别映射'
        if 'readlines' in code.lower() or 'strip()' in code.lower():
            return '标签文件读取'
        if 'os.makedirs' in code.lower():
            return '目录创建'
        return 'ONNX推理操作'
    
    return '其他'

def analyze_all_tasks(exam_data):
    """分析所有考试任务"""
    task_stats = defaultdict(lambda: {
        'total': 0,
        'correct': 0,
        'wrong': 0,
        'chapters': set(),
        'wrong_details': [],
        'code_examples': [],
        'descriptions': set(),
    })
    
    for exam in exam_data:
        chapter = exam['chapter']
        for detail in exam.get('details', []):
            code = detail.get('user_code', '')
            is_correct = detail.get('correct', True)
            desc = detail.get('description', '')
            
            task = classify_task(chapter, desc, code)
            ts = task_stats[task]
            ts['total'] += 1
            ts['chapters'].add(chapter)
            ts['descriptions'].add(desc)
            
            if code.strip():
                ts['code_examples'].append(code)
            
            if is_correct:
                ts['correct'] += 1
            else:
                ts['wrong'] += 1
                ts['wrong_details'].append({
                    'chapter': chapter,
                    'code': code,
                    'description': desc,
                })
    
    return dict(task_stats)

def generate_ability_map(task_stats):
    """生成考试代码能力地图"""
    lines = []
    lines.append("# 🗺️ 考试代码能力地图")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    ability_config = {
        '数据读取': {'stars': 5, 'anki': False, 'retest': False},
        '条件分类': {'stars': 5, 'anki': True, 'retest': False},
        '区间分组': {'stars': 5, 'anki': False, 'retest': False},
        '分组统计': {'stars': 5, 'anki': False, 'retest': False},
        '计数统计': {'stars': 4, 'anki': False, 'retest': False},
        '缺失值处理': {'stars': 5, 'anki': False, 'retest': False},
        '缺失值填充': {'stars': 4, 'anki': False, 'retest': False},
        '缺失值检测': {'stars': 4, 'anki': False, 'retest': False},
        '重复值处理': {'stars': 4, 'anki': False, 'retest': False},
        '重复值检测': {'stars': 3, 'anki': False, 'retest': False},
        '列删除': {'stars': 4, 'anki': False, 'retest': False},
        '类型转换': {'stars': 4, 'anki': False, 'retest': False},
        '区间过滤': {'stars': 4, 'anki': False, 'retest': False},
        '数据保存': {'stars': 5, 'anki': True, 'retest': True},
        '数据统计': {'stars': 3, 'anki': True, 'retest': True},
        '特征选择': {'stars': 4, 'anki': False, 'retest': False},
        '数据集划分': {'stars': 5, 'anki': False, 'retest': False},
        'LogisticRegression建模': {'stars': 5, 'anki': False, 'retest': False},
        'RandomForest建模': {'stars': 5, 'anki': False, 'retest': False},
        'XGBoost建模': {'stars': 4, 'anki': False, 'retest': False},
        'LinearRegression建模': {'stars': 4, 'anki': False, 'retest': False},
        '数据标准化': {'stars': 4, 'anki': False, 'retest': False},
        '模型训练': {'stars': 5, 'anki': False, 'retest': False},
        '模型预测': {'stars': 5, 'anki': False, 'retest': False},
        '分类评估': {'stars': 5, 'anki': False, 'retest': False},
        '回归评估': {'stars': 4, 'anki': False, 'retest': False},
        '准确率计算': {'stars': 5, 'anki': True, 'retest': True},
        '结果保存': {'stars': 4, 'anki': False, 'retest': False},
        '模型保存': {'stars': 4, 'anki': False, 'retest': False},
        '数据不平衡处理': {'stars': 3, 'anki': False, 'retest': False},
        'Pipeline构建': {'stars': 4, 'anki': False, 'retest': False},
        'ONNX模型加载': {'stars': 5, 'anki': False, 'retest': False},
        'ONNX输入获取': {'stars': 4, 'anki': False, 'retest': False},
        'ONNX推理': {'stars': 5, 'anki': False, 'retest': False},
        'PIL图像加载': {'stars': 4, 'anki': False, 'retest': False},
        '图像模式转换': {'stars': 4, 'anki': False, 'retest': False},
        '图像resize': {'stars': 5, 'anki': True, 'retest': True},
        'OpenCV图像加载': {'stars': 3, 'anki': False, 'retest': False},
        'OpenCV图像resize': {'stars': 3, 'anki': False, 'retest': False},
        '图像转numpy': {'stars': 4, 'anki': False, 'retest': False},
        '类型转换float32': {'stars': 4, 'anki': False, 'retest': False},
        '维度扩展': {'stars': 5, 'anki': False, 'retest': False},
        'Softmax概率': {'stars': 4, 'anki': False, 'retest': False},
        'Top-K预测': {'stars': 4, 'anki': True, 'retest': True},
        '类别映射': {'stars': 4, 'anki': False, 'retest': False},
        '标签文件读取': {'stars': 3, 'anki': False, 'retest': False},
        '目录创建': {'stars': 3, 'anki': False, 'retest': False},
    }
    
    lines.append("| 能力 | 重要程度 | 出现次数 | 正确率 | 当前掌握 | 是否Anki | 是否需要重新做题 |\n")
    lines.append("|------|---------|---------|--------|---------|---------|----------------|\n")
    
    for task, stats in sorted(task_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        total = stats['total']
        correct = stats['correct']
        wrong = stats['wrong']
        accuracy = (correct / total * 100) if total > 0 else 100
        
        config = ability_config.get(task, {'stars': 3, 'anki': False, 'retest': False})
        stars = '⭐' * config['stars']
        
        if accuracy >= 95:
            mastery = '🟢'
        elif accuracy >= 80:
            mastery = '🟡'
        else:
            mastery = '🔴'
        
        anki = '是' if config['anki'] else '否'
        retest = '是' if config['retest'] else '否'
        
        lines.append(
            f"| {task} | {stars} | {total} | {accuracy:.1f}% | {mastery} | {anki} | {retest} |"
        )
    
    return '\n'.join(lines)

def generate_weak_points(task_stats):
    """生成真正薄弱点分析"""
    lines = []
    lines.append("# 🚨 真正薄弱点分析")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    weak_tasks = []
    for task, stats in task_stats.items():
        total = stats['total']
        wrong = stats['wrong']
        accuracy = (stats['correct'] / total * 100) if total > 0 else 100
        
        if wrong > 0:
            weak_tasks.append({
                'task': task,
                'total': total,
                'wrong': wrong,
                'accuracy': accuracy,
                'details': stats['wrong_details'],
                'chapters': sorted(stats['chapters']),
            })
    
    weak_tasks.sort(key=lambda x: x['wrong'], reverse=True)
    
    lines.append("## 🔴 A级：必须马上复习\n")
    lines.append("满足条件：正确率<80% 或 多次重复犯同一个错误 或 高频考试任务\n")
    
    a_level = [t for t in weak_tasks if t['accuracy'] < 80 or t['wrong'] >= 2]
    for t in a_level:
        lines.append(f"\n### {t['task']}")
        lines.append(f"- **错误次数**: {t['wrong']}/{t['total']}")
        lines.append(f"- **正确率**: {t['accuracy']:.1f}%")
        lines.append(f"- **涉及章节**: {', '.join(t['chapters'])}")
        
        for d in t['details'][:3]:
            lines.append(f"- [{d['chapter']}] {d['description']}")
            lines.append(f"  - 代码: `{d['code'][:80]}`")
    
    lines.append("\n## 🟡 B级：需要建立记忆\n")
    lines.append("满足条件：正确率80%~95% 或 高频 或 偶尔忘参数\n")
    
    b_level = [t for t in weak_tasks if 80 <= t['accuracy'] < 95 and t['task'] not in [a['task'] for a in a_level]]
    for t in b_level:
        lines.append(f"\n### {t['task']}")
        lines.append(f"- **错误次数**: {t['wrong']}/{t['total']}")
        lines.append(f"- **正确率**: {t['accuracy']:.1f}%")
        lines.append(f"- **涉及章节**: {', '.join(t['chapters'])}")
    
    lines.append("\n## 🟢 C级：已经掌握\n")
    lines.append("满足条件：正确率>95% 且 高频使用且多次正确\n")
    
    mastered = []
    for task, stats in task_stats.items():
        total = stats['total']
        accuracy = (stats['correct'] / total * 100) if total > 0 else 100
        if accuracy >= 95 and total >= 5:
            mastered.append((task, total, accuracy))
    
    mastered.sort(key=lambda x: x[1], reverse=True)
    for task, total, acc in mastered:
        lines.append(f"- ✅ {task}: {total}次，{acc:.1f}%")
    
    return '\n'.join(lines)

def generate_templates():
    """生成考试代码模板"""
    lines = []
    lines.append("# 💻 考试代码模板（最终版）")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    templates = [
        {
            'name': '模板1：Pandas读取与检查',
            'trigger': '看到"读取数据"、"加载数据集"、"显示前五行"',
            'code': """import pandas as pd
import numpy as np

# 读取数据
data = pd.read_csv('filename.csv')

# 检查数据
data.head()
data.info()
data.describe()""",
            'pitfalls': '文件名要匹配，注意路径',
            'anki': False,
        },
        {
            'name': '模板2：数据清洗完整流程',
            'trigger': '看到"缺失值"、"重复值"、"异常值"、"清洗"',
            'code': """# 1. 检查缺失值
data.isnull().sum()

# 2. 处理缺失值
data.dropna()  # 删除
data['col'].fillna(method='ffill', inplace=True)  # 前向填充
data['col'].fillna(method='bfill', inplace=True)  # 后向填充

# 3. 检查重复值
data.duplicated().sum()

# 4. 删除无关列
data = data.drop(columns=['col1', 'col2'])

# 5. 类型转换
data['col'] = data['col'].astype(int)
data['col'] = pd.to_numeric(data['col'], errors='coerce')""",
            'pitfalls': 'fillna的method参数，inplace=True才生效',
            'anki': False,
        },
        {
            'name': '模板3：条件分类（np.where）',
            'trigger': '看到"根据...判断"、"创建新列"、"风险等级"',
            'code': """# 单条件
data['new_col'] = np.where(data['col'] > threshold, '高', '低')

# 多条件
data['new_col'] = np.where(
    (data['col1'] > 0) & (data['col2'] < 100),
    '正常',
    '异常'
)""",
            'pitfalls': '多条件用&连接，每个条件加括号',
            'anki': False,
        },
        {
            'name': '模板4：区间分组（pd.cut）',
            'trigger': '看到"区间"、"划分"、"BMI区间"、"年龄段"',
            'code': """# 定义区间和标签
bins = [0, 18.5, 24, 28, np.inf]
labels = ['偏瘦', '正常', '超重', '肥胖']

# 划分区间（right=False表示左闭右开）
data['category'] = pd.cut(data['col'], bins=bins, labels=labels, right=False)

# 统计各区间数量
data['category'].value_counts()""",
            'pitfalls': 'bins比labels多一个，np.inf表示无穷大',
            'anki': False,
        },
        {
            'name': '模板5：分组统计（groupby+agg/apply）',
            'trigger': '看到"按...分组"、"统计...平均值"、"比例"',
            'code': """# 单列分组+单聚合
stats = data.groupby('col')['target'].mean()

# 单列分组+多聚合
stats = data.groupby('col')['target'].agg(['count', 'mean', 'std'])

# 分组+自定义函数（计算比例）
rate = data.groupby('col')['target'].apply(lambda x: (x == '目标值').mean())

# 多列分组+unstack
stats = data[data['col'].isin(['A', 'B'])].groupby(['col1', 'col2'])['val'].mean().unstack()""",
            'pitfalls': 'apply中lambda x的x是Series，(x==val).mean()计算比例',
            'anki': False,
        },
        {
            'name': '模板6：数据保存',
            'trigger': '看到"保存到"、"输出到"、"保存结果"',
            'code': """# 保存DataFrame到CSV
data.to_csv('output.csv', index=False)

# 注意：变量名要和题目中的一致！""",
            'pitfalls': '变量名要匹配，index=False不保存行索引',
            'anki': True,
        },
        {
            'name': '模板7：机器学习完整流程',
            'trigger': '看到"训练模型"、"划分数据集"、"预测"',
            'code': """from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import pickle

# 1. 特征和标签
X = data.drop(['target', 'Unnamed: 0'], axis=1)
y = data['target']

# 2. 划分数据集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 创建模型
model = LogisticRegression(max_iter=1000)
# 或 model = RandomForestClassifier(n_estimators=100, random_state=42)

# 4. 训练模型
model.fit(X_train, y_train)

# 5. 预测
y_pred = model.predict(X_test)

# 6. 评估
accuracy = (y_test == y_pred).mean()
report = classification_report(y_test, y_pred, zero_division=1)

# 7. 保存模型
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)

# 8. 保存结果
pd.DataFrame(y_pred, columns=['预测结果']).to_csv('results.txt', index=False)""",
            'pitfalls': 'test_size=0.2表示20%测试集，random_state=42保证可重复',
            'anki': False,
        },
        {
            'name': '模板8：准确率计算',
            'trigger': '看到"准确率"、"得分"、"预测正确率"',
            'code': """# 利用布尔值计算准确率（True=1, False=0）
accuracy = (y_test == y_pred).mean()

# 或者用model.score()
accuracy = model.score(X_test, y_test)""",
            'pitfalls': '(y_test == y_pred)返回布尔Series，.mean()计算True的比例',
            'anki': True,
        },
        {
            'name': '模板9：PIL图像预处理',
            'trigger': '看到"加载图片"、"图像"、"resize"、"灰度"',
            'code': """from PIL import Image
import numpy as np

# 1. 加载图片并转换模式
image = Image.open('image.png').convert('L')  # 灰度图
# 或 image = Image.open('image.png').convert('RGB')  # 彩色图

# 2. 调整大小（注意：width, height顺序！）
image = image.resize((28, 28))  # (width, height)

# 3. 转为numpy数组
image_array = np.array(image, dtype=np.float32)

# 4. 扩展维度（添加batch维度）
image_array = np.expand_dims(image_array, axis=0)""",
            'pitfalls': 'resize((width, height))不是(height, width)！',
            'anki': True,
        },
        {
            'name': '模板10：ONNX推理完整流程',
            'trigger': '看到"ONNX"、"模型推理"、"预测"、"InferenceSession"',
            'code': """import onnxruntime as ort
import numpy as np

# 1. 加载模型
ort_session = ort.InferenceSession('model.onnx')

# 2. 获取输入名称
input_name = ort_session.get_inputs()[0].name

# 3. 构造输入字典
ort_inputs = {input_name: image_array}

# 4. 执行推理
ort_outs = ort_session.run(None, ort_inputs)

# 5. 获取预测结果
predicted_class = np.argmax(ort_outs[0])""",
            'pitfalls': 'run(None, inputs)第一个参数为None表示获取所有输出',
            'anki': False,
        },
        {
            'name': '模板11：Softmax+Top-K预测',
            'trigger': '看到"概率"、"softmax"、"Top-K"、"最高概率"',
            'code': """import scipy.special
import numpy as np

# 1. 应用softmax获取概率
probabilities = scipy.special.softmax(ort_outs[0], axis=-1)

# 2. 获取预测类别
predicted_idx = np.argmax(probabilities[0])

# 3. 获取概率值
prob_value = probabilities[0][predicted_idx] * 100  # 百分比

# 4. Top-K（获取最高的K个）
top_k_idx = np.argsort(probabilities[0])[-K:][::-1]
top_k_probs = probabilities[0][top_k_idx]""",
            'pitfalls': 'argsort返回升序索引，[-K:][::-1]获取降序Top-K',
            'anki': True,
        },
        {
            'name': '模板12：类别映射',
            'trigger': '看到"类别名称"、"标签"、"映射"、"emotion"',
            'code': """# 方式1：字典映射
emotion_table = {'neutral': 0, 'happiness': 1, 'surprise': 2}
predicted_emotion = list(emotion_table.keys())[predicted_label]

# 方式2：从文件读取
class_names = [name.strip() for name in open('labels.txt').readlines()]
predicted_label = class_names[predicted_idx]""",
            'pitfalls': 'strip()去除换行符，list(keys())[idx]通过索引获取键名',
            'anki': False,
        },
    ]
    
    for t in templates:
        lines.append(f"\n## {t['name']}\n")
        lines.append(f"**触发关键词**: {t['trigger']}\n")
        lines.append("```python")
        lines.append(t['code'])
        lines.append("```\n")
        lines.append(f"**易错点**: {t['pitfalls']}\n")
        if t['anki']:
            lines.append("📌 **建议加入Anki**\n")
    
    return '\n'.join(lines)

def generate_error_analysis(task_stats):
    """生成高频易错点分析"""
    lines = []
    lines.append("# ⚠️ 高频易错点分析")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    error_patterns = {
        '图像resize': {
            'error_type': 'API记忆错误',
            'wrong_code': 'image.resize(image, (320, 240))',
            'correct_code': 'image.resize((320, 240))',
            'reason': 'PIL的resize只接受一个参数：(width, height)元组',
            'fix': '记住：image.resize((width, height))',
        },
        '数据保存': {
            'error_type': '变量名错误',
            'wrong_code': 'cleaned_data.to_csv(...) 但实际变量名是data_cleaned',
            'correct_code': '确保变量名与题目中的一致',
            'reason': '填空题中变量名必须与上下文匹配',
            'fix': '仔细看题目中的变量名，不要自己改名',
        },
        '准确率计算': {
            'error_type': '概念错误',
            'wrong_code': 'train_score = (x_test == y_pred).mean() 变量名错误',
            'correct_code': '(y_test == y_pred).mean()',
            'reason': '不理解(y_test == y_pred).mean()的原理：布尔值True=1, False=0',
            'fix': '记住：比较返回布尔Series，.mean()计算True的比例',
        },
        'Top-K预测': {
            'error_type': '流程错误',
            'wrong_code': 'np.argmax(probabilities[0])[-5:][::-1]',
            'correct_code': 'np.argsort(probabilities[0])[-5:][::-1]',
            'reason': 'argmax返回单个索引，argsort返回排序后的索引数组',
            'fix': 'Top-K用argsort，不是argmax',
        },
        '维度扩展': {
            'error_type': 'API使用错误',
            'wrong_code': 'np.expand_dims()[0].name',
            'correct_code': 'ort_session.get_inputs()[0].name',
            'reason': '混淆了expand_dims和get_inputs的用途',
            'fix': 'get_inputs()获取模型输入信息，expand_dims()扩展数组维度',
        },
        '列删除': {
            'error_type': '参数错误',
            'wrong_code': 'data.drop(columns=[...]) 变量名或列名错误',
            'correct_code': 'data.drop(columns=[\'Unnamed: 0\', target_variable])',
            'reason': '列名要准确匹配，变量名要与题目一致',
            'fix': '仔细检查列名拼写和变量名',
        },
        '数据统计': {
            'error_type': '粗心错误',
            'wrong_code': 'initial_row_count = len(data) 但data还未定义或已修改',
            'correct_code': '确保在正确的时机调用len(data)',
            'reason': '代码执行顺序问题，或变量名错误',
            'fix': '注意代码执行顺序，确保变量已定义',
        },
        '重复值检测': {
            'error_type': '粗心错误',
            'wrong_code': 'data.duplicated() 缺少上下文',
            'correct_code': 'data.duplicated().sum() 或 data.duplicated()',
            'reason': '根据题目要求选择是否.sum()',
            'fix': '看题目要求：检测用duplicated()，统计数量用duplicated().sum()',
        },
    }
    
    for task, stats in sorted(task_stats.items(), key=lambda x: x[1]['wrong'], reverse=True):
        if stats['wrong'] == 0:
            continue
        
        if task in error_patterns:
            ep = error_patterns[task]
            lines.append(f"\n### {task}")
            lines.append(f"- **错误类型**: {ep['error_type']}")
            lines.append(f"- **错误次数**: {stats['wrong']}/{stats['total']}")
            lines.append(f"- **错误代码**: `{ep['wrong_code']}`")
            lines.append(f"- **正确代码**: `{ep['correct_code']}`")
            lines.append(f"- **原因**: {ep['reason']}")
            lines.append(f"- **修正**: {ep['fix']}")
            
            for d in stats['wrong_details'][:2]:
                lines.append(f"- 实际错误: `{d['code'][:80]}`")
    
    return '\n'.join(lines)

def generate_anki(task_stats):
    """生成最终Anki卡片"""
    lines = []
    lines.append("Front\tBack\tTags")
    
    anki_cards = [
        {
            'front': 'PIL Image.resize 参数顺序是什么？',
            'back': 'image.resize((width, height))\n注意：只有一个参数，是(width, height)元组\n不是resize(width, height)两个参数',
            'tags': '图像处理::易错',
        },
        {
            'front': 'DataFrame保存CSV的考试模板是什么？',
            'back': 'data.to_csv(\'output.csv\', index=False)\n⚠️ 变量名必须与题目中的一致！\nindex=False不保存行索引',
            'tags': 'Pandas::高频',
        },
        {
            'front': '如何计算分类准确率？',
            'back': '(y_test == y_pred).mean()\n原理：==返回布尔Series，True=1, False=0\n.mean()计算True的比例',
            'tags': 'ML::易错',
        },
        {
            'front': 'ONNX如何构造输入字典？',
            'back': 'input_name = ort_session.get_inputs()[0].name\nort_inputs = {input_name: input_data}\n⚠️ 不是np.expand_dims()[0].name',
            'tags': 'ONNX::高频',
        },
        {
            'front': 'ONNX推理的完整流程？',
            'back': '1. ort_session = ort.InferenceSession(\'model.onnx\')\n2. input_name = ort_session.get_inputs()[0].name\n3. ort_inputs = {input_name: data}\n4. ort_outs = ort_session.run(None, ort_inputs)\n5. predicted = np.argmax(ort_outs[0])',
            'tags': 'ONNX::流程',
        },
        {
            'front': 'PIL图像预处理的完整流程？',
            'back': '1. image = Image.open(\'img.png\').convert(\'L\')  # 或RGB\n2. image = image.resize((28, 28))  # (width, height)\n3. arr = np.array(image, dtype=np.float32)\n4. arr = np.expand_dims(arr, axis=0)',
            'tags': '图像处理::流程',
        },
        {
            'front': 'Top-K预测如何实现？',
            'back': 'top_k_idx = np.argsort(probs[0])[-K:][::-1]\n⚠️ 用argsort不是argmax\nargsort返回升序索引\n[-K:]取最后K个，[::-1]反转变降序',
            'tags': 'ML::易错',
        },
        {
            'front': 'pd.cut的right=False是什么意思？',
            'back': 'right=False表示左闭右开区间 [a, b)\n例如：bins=[0, 18.5, 24], right=False\n[0, 18.5) 包含0不包含18.5\n默认right=True是左开右闭 (a, b]',
            'tags': 'Pandas::易错',
        },
        {
            'front': 'groupby+apply计算比例的模板？',
            'back': 'rate = data.groupby(\'col\')[\'target\'].apply(\n    lambda x: (x == \'目标值\').mean()\n)\n(x==val)返回布尔Series\n.mean()计算True的比例',
            'tags': 'Pandas::高频',
        },
        {
            'front': 'fillna的method参数用法？',
            'back': 'data[\'col\'].fillna(method=\'ffill\', inplace=True)  # 前向填充\ndata[\'col\'].fillna(method=\'bfill\', inplace=True)  # 后向填充\n⚠️ 必须inplace=True才生效',
            'tags': 'Pandas::易错',
        },
        {
            'front': 'np.where多条件怎么写？',
            'back': 'data[\'new\'] = np.where(\n    (data[\'col1\'] > 0) & (data[\'col2\'] < 100),\n    \'满足\',\n    \'不满足\'\n)\n⚠️ 每个条件加括号，用&连接',
            'tags': 'Pandas::高频',
        },
        {
            'front': '机器学习完整流程模板？',
            'back': '1. X = data.drop([\'target\'], axis=1); y = data[\'target\']\n2. X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n3. model = LogisticRegression(max_iter=1000)\n4. model.fit(X_train, y_train)\n5. y_pred = model.predict(X_test)\n6. accuracy = (y_test == y_pred).mean()',
            'tags': 'ML::流程',
        },
        {
            'front': 'Softmax+获取概率值？',
            'back': 'probs = scipy.special.softmax(output, axis=-1)\npredicted_idx = np.argmax(probs[0])\nprob_value = probs[0][predicted_idx] * 100  # 百分比\naxis=-1表示沿最后一个维度计算',
            'tags': 'ML::高频',
        },
        {
            'front': '类别映射的两种方式？',
            'back': '方式1: emotion_table = {\'neutral\': 0, ...}\n         predicted = list(emotion_table.keys())[idx]\n方式2: names = [l.strip() for l in open(\'labels.txt\').readlines()]\n         predicted = names[idx]',
            'tags': 'ONNX::高频',
        },
        {
            'front': 'PIL convert(\'L\')和convert(\'RGB\')区别？',
            'back': 'convert(\'L\') → 灰度图（单通道）\nconvert(\'RGB\') → 彩色图（三通道）\n根据模型输入要求选择',
            'tags': '图像处理::基础',
        },
        {
            'front': 'np.expand_dims的axis参数？',
            'back': 'np.expand_dims(arr, axis=0) → 在第0维扩展\n例如: (28,28) → (1,28,28) 添加batch维度\nnp.expand_dims(arr, axis=-1) → 在最后一维扩展\n例如: (28,28) → (28,28,1) 添加通道维度',
            'tags': 'NumPy::易错',
        },
        {
            'front': '数据清洗中dropna和fillna的区别？',
            'back': 'dropna() → 删除包含NaN的行\ndata.dropna() 删除任何有NaN的行\ndata.dropna(subset=[\'col\']) 只检查指定列\n\nfillna() → 填充NaN值\nmethod=\'ffill\' 前向填充\nmethod=\'bfill\' 后向填充',
            'tags': 'Pandas::基础',
        },
        {
            'front': 'unstack的作用？',
            'back': '将最内层行索引转为列名\n常用于groupby后的多列分组结果\n例: data.groupby([\'A\',\'B\'])[\'C\'].mean().unstack()\n将B的值转为列名',
            'tags': 'Pandas::高频',
        },
        {
            'front': 'train_test_split参数含义？',
            'back': 'train_test_split(X, y, test_size=0.2, random_state=42)\ntest_size=0.2 → 20%数据作为测试集\nrandom_state=42 → 保证每次划分一致\n返回: X_train, X_test, y_train, y_test',
            'tags': 'ML::基础',
        },
        {
            'front': 'classification_report参数zero_division？',
            'back': 'classification_report(y_test, y_pred, zero_division=1)\nzero_division=1 → 当某类别无预测时返回1而不是warning\n防止除零错误',
            'tags': 'ML::易错',
        },
    ]
    
    for card in anki_cards:
        lines.append(f"{card['front']}\t{card['back']}\t{card['tags']}")
    
    return '\n'.join(lines)

def generate_priority(task_stats):
    """生成考前复习优先级"""
    lines = []
    lines.append("# 📋 考前复习优先级")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    lines.append("## 🔴 P0：今晚必须掌握（最多8项）\n")
    lines.append("这些是高频且你容易出错的内容，必须立即复习：\n")
    
    p0 = [
        ('图像resize参数顺序', 'PIL resize((width, height))，不是两个参数', '2次错误'),
        ('数据保存变量名', 'to_csv时变量名必须与题目一致', '6次错误'),
        ('准确率计算原理', '(y_test == y_pred).mean()，布尔值求平均', '3次错误'),
        ('ONNX输入构造', 'get_inputs()[0].name构造字典，不是expand_dims', '1次错误'),
        ('Top-K用argsort', 'argsort不是argmax，[-K:][::-1]降序', '1次错误'),
        ('fillna的method参数', 'method=\'ffill\'/\'bfill\'，inplace=True', '高频考点'),
        ('np.where多条件', '每个条件加括号，用&连接', '高频考点'),
    ]
    
    for i, (item, desc, status) in enumerate(p0, 1):
        lines.append(f"{i}. **{item}** - {desc} ({status})")
    
    lines.append("\n## 🟡 P1：明天掌握（最多12项）\n")
    lines.append("这些是高频但相对容易掌握的内容：\n")
    
    p1 = [
        'pd.cut的right=False含义',
        'groupby+apply计算比例',
        'unstack的作用',
        'train_test_split参数',
        'classification_report的zero_division',
        'np.expand_dims的axis参数',
        'PIL convert(L)和convert(RGB)区别',
        'Softmax+概率值计算',
        '类别映射两种方式',
        '数据清洗流程（dropna/fillna/drop）',
        '机器学习完整流程',
        '类别映射字典和文件读取',
    ]
    
    for i, item in enumerate(p1, 1):
        lines.append(f"{i}. {item}")
    
    lines.append("\n## 🟢 P2：已经掌握，不再复习\n")
    lines.append("这些你已经稳定掌握，不需要继续刷题：\n")
    
    p2 = [
        'pd.read_csv读取数据',
        'data.head()查看前五行',
        'data.isnull().sum()检查缺失值',
        'data.value_counts()计数统计',
        'data.groupby().mean()/agg()分组聚合',
        'data.astype()类型转换',
        'data.between()区间过滤',
        'data.isin()布尔过滤',
        'data.drop(columns=[])删除列',
        'data.duplicated()重复值检测',
        'ONNX模型加载InferenceSession',
        'ONNX推理session.run',
        'np.argmax获取最大值索引',
        'np.array创建数组',
        'Image.open加载图片',
        'os.makedirs创建目录',
    ]
    
    for item in p2:
        lines.append(f"- ✅ {item}")
    
    lines.append("\n## ❌ 不需要继续刷的题型\n")
    lines.append("这些题型已经没有继续刷题的必要：\n")
    
    no_need = [
        'pd.read_csv - 100%正确率，31次出现',
        'data.between - 100%正确率，20次出现',
        'data.groupby - 100%正确率，20次出现',
        'pd.cut - 100%正确率，19次出现',
        'data.astype - 100%正确率，18次出现',
        'ONNX推理 - 100%正确率，17次出现',
        'ONNX加载 - 100%正确率，16次出现',
        'data.apply - 100%正确率，15次出现',
        'np.array - 100%正确率，14次出现',
        'data.value_counts - 100%正确率，11次出现',
        'Image.open - 100%正确率，10次出现',
    ]
    
    for item in no_need:
        lines.append(f"- {item}")
    
    lines.append("\n---\n")
    lines.append("## 🎯 最值得投入时间的3件事情\n")
    lines.append("1. **图像resize参数顺序** - 2次错误，66.7%正确率，考试必考")
    lines.append("2. **数据保存变量名匹配** - 6次错误，每次都是变量名不一致")
    lines.append("3. **准确率计算原理** - 3次错误，不理解(y_test==y_pred).mean()的原理")
    
    return '\n'.join(lines)

def generate_conclusion(task_stats):
    """生成考前结论"""
    total_tasks = sum(s['total'] for s in task_stats.values())
    total_correct = sum(s['correct'] for s in task_stats.values())
    total_wrong = sum(s['wrong'] for s in task_stats.values())
    accuracy = (total_correct / total_tasks * 100) if total_tasks > 0 else 100
    
    mastered = sum(1 for s in task_stats.values() if s['wrong'] == 0 and s['total'] >= 5)
    weak = sum(1 for s in task_stats.values() if s['wrong'] > 0)
    
    lines = []
    lines.append("# 【考前结论】\n")
    lines.append(f"**代码题总体掌握度**: {accuracy:.1f}% ({total_correct}/{total_tasks})")
    lines.append(f"- 已掌握任务: {mastered}个")
    lines.append(f"- 薄弱任务: {weak}个")
    lines.append(f"- 总任务类型: {len(task_stats)}个\n")
    
    lines.append("**P0必须解决**:")
    lines.append("1. 图像resize参数顺序")
    lines.append("2. 数据保存变量名匹配")
    lines.append("3. 准确率计算原理")
    lines.append("4. ONNX输入构造")
    lines.append("5. Top-K用argsort\n")
    
    lines.append("**P1应该解决**:")
    lines.append("1. pd.cut的right=False")
    lines.append("2. groupby+apply计算比例")
    lines.append("3. fillna的method参数")
    lines.append("4. np.where多条件\n")
    
    lines.append("**已经掌握**:")
    lines.append("- pd.read_csv, data.groupby, pd.cut, data.astype")
    lines.append("- ONNX推理, np.array, Image.open")
    lines.append("- data.value_counts, data.between, data.isin\n")
    
    lines.append("**不需要再刷**:")
    lines.append("- 所有100%正确率且出现10次以上的API\n")
    
    lines.append("**最值得投入时间的3件事情**:")
    lines.append("1. 图像resize参数顺序 - 考试必考，已错2次")
    lines.append("2. 数据保存变量名匹配 - 已错6次，都是粗心")
    lines.append("3. 准确率计算原理 - 理解(y_test==y_pred).mean()")
    
    return '\n'.join(lines)

def main():
    print("加载考试数据...")
    exam_data = load_all_exam_data()
    print(f"  找到 {len(exam_data)} 个exam文件")
    
    print("分析考试任务...")
    task_stats = analyze_all_tasks(exam_data)
    print(f"  识别出 {len(task_stats)} 个考试任务类型")
    
    print("生成考试代码能力地图...")
    content = generate_ability_map(task_stats)
    path = OUTPUT_DIR / '01_考试代码能力地图.md'
    path.write_text(content, encoding='utf-8')
    print(f"  已生成: {path}")
    
    print("生成真正薄弱点...")
    content = generate_weak_points(task_stats)
    path = OUTPUT_DIR / '02_真正薄弱点.md'
    path.write_text(content, encoding='utf-8')
    print(f"  已生成: {path}")
    
    print("生成考试代码模板...")
    content = generate_templates()
    path = OUTPUT_DIR / '03_考试代码模板.md'
    path.write_text(content, encoding='utf-8')
    print(f"  已生成: {path}")
    
    print("生成高频易错点...")
    content = generate_error_analysis(task_stats)
    path = OUTPUT_DIR / '04_高频易错点.md'
    path.write_text(content, encoding='utf-8')
    print(f"  已生成: {path}")
    
    print("生成Anki卡片...")
    content = generate_anki(task_stats)
    path = OUTPUT_DIR / '05_Anki_Final.tsv'
    path.write_text(content, encoding='utf-8')
    print(f"  已生成: {path}")
    
    print("生成考前复习优先级...")
    content = generate_priority(task_stats)
    path = OUTPUT_DIR / '06_考前复习优先级.md'
    path.write_text(content, encoding='utf-8')
    print(f"  已生成: {path}")
    
    print("生成考前结论...")
    content = generate_conclusion(task_stats)
    path = OUTPUT_DIR / '07_考前结论.md'
    path.write_text(content, encoding='utf-8')
    print(f"  已生成: {path}")
    
    print("\n✅ 第二轮深度分析完成！")

if __name__ == '__main__':
    main()