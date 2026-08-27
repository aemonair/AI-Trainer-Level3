#!/usr/bin/env python3
"""
考试代码知识体系构建器

功能：
1. 统计每个API/知识点出现次数
2. 找出重复考点、容易出错点和实际做错的点
3. 生成知识点总表、薄弱点表、代码模板和Anki TSV

用法:
  python3 scripts/build_knowledge_system.py
  python3 scripts/build_knowledge_system.py --output-dir reports/knowledge_system
"""
import json
import re
import os
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / 'sessions'


API_KNOWLEDGE_MAP = {
    'pd.read_csv': {'category': '数据读取', 'api': 'read_csv', 'desc': '读取CSV文件'},
    'data.isnull()': {'category': '缺失值检测', 'api': 'isnull', 'desc': '检测缺失值'},
    'data.duplicated()': {'category': '重复值检测', 'api': 'duplicated', 'desc': '检测重复行'},
    'data.dropna()': {'category': '缺失值处理', 'api': 'dropna', 'desc': '删除缺失值'},
    'data.fillna()': {'category': '缺失值处理', 'api': 'fillna', 'desc': '填充缺失值'},
    'data.drop()': {'category': '数据删除', 'api': 'drop', 'desc': '删除列或行'},
    'data.astype()': {'category': '类型转换', 'api': 'astype', 'desc': '数据类型转换'},
    'data.between()': {'category': '区间判断', 'api': 'between', 'desc': '检查值是否在区间内'},
    'data.value_counts()': {'category': '计数统计', 'api': 'value_counts', 'desc': '统计各值出现次数'},
    'data.groupby()': {'category': '分组聚合', 'api': 'groupby', 'desc': '按列分组'},
    'data.agg()': {'category': '分组聚合', 'api': 'agg', 'desc': '聚合计算'},
    'data.apply()': {'category': '函数应用', 'api': 'apply', 'desc': '应用自定义函数'},
    'data.unstack()': {'category': '数据重塑', 'api': 'unstack', 'desc': '行转列'},
    'pd.cut()': {'category': '区间分组', 'api': 'cut', 'desc': '将连续值划分到区间'},
    'np.where()': {'category': '条件判断', 'api': 'where', 'desc': '条件选择'},
    'data.to_csv()': {'category': '数据保存', 'api': 'to_csv', 'desc': '保存为CSV文件'},
    'data.isin()': {'category': '布尔过滤', 'api': 'isin', 'desc': '检查值是否在列表中'},
    'data.mean()': {'category': '统计计算', 'api': 'mean', 'desc': '计算平均值'},
    'data.std()': {'category': '统计计算', 'api': 'std', 'desc': '计算标准差'},
    'data.sum()': {'category': '统计计算', 'api': 'sum', 'desc': '求和'},
    'len(data)': {'category': '数据长度', 'api': 'len', 'desc': '获取数据行数'},
    'data.all()': {'category': '逻辑判断', 'api': 'all', 'desc': '检查是否全部为True'},
    'data.sort_index()': {'category': '排序', 'api': 'sort_index', 'desc': '按索引排序'},
    'onnxruntime.InferenceSession': {'category': 'ONNX模型加载', 'api': 'InferenceSession', 'desc': '加载ONNX模型创建推理会话'},
    'ort_session.run': {'category': 'ONNX模型推理', 'api': 'run', 'desc': '执行ONNX模型推理'},
    'ort_session.get_inputs': {'category': 'ONNX模型输入', 'api': 'get_inputs', 'desc': '获取模型输入信息'},
    'np.array': {'category': 'Numpy数组', 'api': 'array', 'desc': '创建numpy数组'},
    'np.expand_dims': {'category': 'Numpy数组', 'api': 'expand_dims', 'desc': '扩展数组维度'},
    'np.argmax': {'category': 'Numpy数组', 'api': 'argmax', 'desc': '返回最大值索引'},
    'np.float32': {'category': 'Numpy类型', 'api': 'float32', 'desc': '32位浮点类型'},
    'Image.open': {'category': '图像处理', 'api': 'Image.open', 'desc': '打开图像文件'},
    'image.resize': {'category': '图像处理', 'api': 'resize', 'desc': '调整图像大小'},
    'image.convert': {'category': '图像处理', 'api': 'convert', 'desc': '转换图像模式'},
    'cv2.imread': {'category': 'OpenCV图像读取', 'api': 'imread', 'desc': '使用OpenCV读取图像'},
    'cv2.resize': {'category': 'OpenCV图像处理', 'api': 'resize', 'desc': '使用OpenCV调整图像大小'},
    'scipy.special.softmax': {'category': 'Softmax函数', 'api': 'softmax', 'desc': '应用softmax函数计算概率'},
    'os.makedirs': {'category': '目录操作', 'api': 'makedirs', 'desc': '创建目录'},
    'open().readlines': {'category': '文件读取', 'api': 'readlines', 'desc': '读取文件所有行'},
    'dict映射': {'category': '字典映射', 'api': 'dict', 'desc': '使用字典进行标签映射'},
    'list().keys': {'category': '字典操作', 'api': 'list_keys', 'desc': '将字典键转为列表'},
    'with open': {'category': '文件读取', 'api': 'with_open', 'desc': '使用with语句安全打开文件'},
    'strip()': {'category': '字符串处理', 'api': 'strip', 'desc': '去除字符串首尾空白'},
}


def extract_chapter(session_name: str) -> Optional[str]:
    match = re.search(r'chapter(\d+\.\d+\.\d+)', session_name)
    return match.group(1) if match else None


def load_all_scoring_results() -> List[Dict]:
    results = []
    for scoring_path in SESSIONS_DIR.rglob('scoring_result_v2_*.json'):
        try:
            with open(scoring_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['source'] = str(scoring_path)
                data['session_name'] = scoring_path.parent.parent.name
                data['chapter'] = extract_chapter(scoring_path.parent.parent.name)
                data['scoring_type'] = 'exam' if 'exam' in scoring_path.name else 'practice'
                results.append(data)
        except Exception as e:
            logger.warning(f"加载失败 {scoring_path}: {e}")
    return results


def extract_apis_from_code(code: str) -> List[str]:
    apis = []
    code_lower = code.lower()
    
    if 'read_csv' in code_lower and ('pd.' in code_lower or 'pandas.' in code_lower):
        apis.append('pd.read_csv')
    if '.isnull()' in code_lower:
        apis.append('data.isnull()')
    if '.duplicated()' in code_lower:
        apis.append('data.duplicated()')
    if '.dropna(' in code_lower:
        apis.append('data.dropna()')
    if '.fillna(' in code_lower:
        apis.append('data.fillna()')
    if '.drop(' in code_lower and 'columns' in code_lower:
        apis.append('data.drop()')
    if '.astype(' in code_lower:
        apis.append('data.astype()')
    if '.between(' in code_lower:
        apis.append('data.between()')
    if '.value_counts()' in code_lower:
        apis.append('data.value_counts()')
    if '.groupby(' in code_lower:
        apis.append('data.groupby()')
    if '.agg(' in code_lower:
        apis.append('data.agg()')
    if '.apply(' in code_lower:
        apis.append('data.apply()')
    if '.unstack()' in code_lower:
        apis.append('data.unstack()')
    if 'pd.cut(' in code_lower or 'pandas.cut(' in code_lower:
        apis.append('pd.cut()')
    if 'np.where(' in code_lower:
        apis.append('np.where()')
    if '.to_csv(' in code_lower:
        apis.append('data.to_csv()')
    if '.isin(' in code_lower:
        apis.append('data.isin()')
    if '.mean()' in code_lower:
        apis.append('data.mean()')
    if '.std()' in code_lower:
        apis.append('data.std()')
    if '.sum()' in code_lower:
        apis.append('data.sum()')
    if 'len(' in code_lower:
        apis.append('len(data)')
    if '.all(' in code_lower and 'axis' in code_lower:
        apis.append('data.all()')
    if '.sort_index()' in code_lower:
        apis.append('data.sort_index()')
    
    if 'onnxruntime.inferencesession' in code_lower or 'ort.inferencesession' in code_lower:
        apis.append('onnxruntime.InferenceSession')
    if 'ort_session.run' in code_lower or 'session.run' in code_lower:
        apis.append('ort_session.run')
    if 'get_inputs()' in code_lower:
        apis.append('ort_session.get_inputs')
    if 'np.array(' in code_lower:
        apis.append('np.array')
    if 'np.expand_dims(' in code_lower:
        apis.append('np.expand_dims')
    if 'np.argmax(' in code_lower:
        apis.append('np.argmax')
    if 'np.float32' in code_lower:
        apis.append('np.float32')
    if 'image.open(' in code_lower:
        apis.append('Image.open')
    if '.resize(' in code_lower and ('image' in code_lower or 'img' in code_lower):
        apis.append('image.resize')
    if '.convert(' in code_lower and ('image' in code_lower or 'img' in code_lower):
        apis.append('image.convert')
    if 'cv2.imread(' in code_lower:
        apis.append('cv2.imread')
    if 'cv2.resize(' in code_lower:
        apis.append('cv2.resize')
    if 'softmax(' in code_lower:
        apis.append('scipy.special.softmax')
    if 'os.makedirs(' in code_lower:
        apis.append('os.makedirs')
    if '.readlines()' in code_lower:
        apis.append('open().readlines')
    if "': " in code and ('{' in code and '}' in code) and ('emotion' in code_lower or 'label' in code_lower or 'class' in code_lower):
        apis.append('dict映射')
    if '.keys()' in code_lower and 'list(' in code_lower:
        apis.append('list().keys')
    if 'with open(' in code_lower:
        apis.append('with open')
    if '.strip()' in code_lower:
        apis.append('strip()')
    
    return apis


def analyze_knowledge_points(scoring_results: List[Dict]) -> Dict:
    knowledge_stats = defaultdict(lambda: {
        'total_appearances': 0,
        'correct_count': 0,
        'wrong_count': 0,
        'chapters': set(),
        'sessions': [],
        'wrong_sessions': [],
        'difficulty_levels': [],
        'descriptions': set(),
        'wrong_details': [],
    })
    
    for result in scoring_results:
        chapter = result.get('chapter', 'unknown')
        session = result.get('session_name', '')
        scoring_type = result.get('scoring_type', '')
        
        for detail in result.get('details', []):
            code = detail.get('user_code', '')
            is_correct = detail.get('correct', True)
            item_id = detail.get('item_id', '')
            description = detail.get('description', '')
            difficulty = detail.get('difficulty', 'medium')
            
            apis = extract_apis_from_code(code)
            
            for api in apis:
                ks = knowledge_stats[api]
                ks['total_appearances'] += 1
                ks['chapters'].add(chapter)
                ks['sessions'].append(session)
                ks['descriptions'].add(description)
                ks['difficulty_levels'].append(difficulty)
                
                if is_correct:
                    ks['correct_count'] += 1
                else:
                    ks['wrong_count'] += 1
                    ks['wrong_sessions'].append(session)
                    ks['wrong_details'].append({
                        'chapter': chapter,
                        'session': session,
                        'item_id': item_id,
                        'code': code,
                        'description': description,
                    })
    
    return dict(knowledge_stats)


def calculate_accuracy(knowledge_stats: Dict) -> List[Dict]:
    accuracy_list = []
    
    for api, stats in knowledge_stats.items():
        total = stats['correct_count'] + stats['wrong_count']
        accuracy = (stats['correct_count'] / total * 100) if total > 0 else 100
        
        accuracy_list.append({
            'api': api,
            'category': API_KNOWLEDGE_MAP.get(api, {}).get('category', '其他'),
            'api_name': API_KNOWLEDGE_MAP.get(api, {}).get('api', api),
            'description': API_KNOWLEDGE_MAP.get(api, {}).get('desc', ''),
            'total_appearances': stats['total_appearances'],
            'correct_count': stats['correct_count'],
            'wrong_count': stats['wrong_count'],
            'accuracy': accuracy,
            'chapters': sorted(stats['chapters']),
            'sessions_count': len(set(stats['sessions'])),
            'wrong_sessions_count': len(set(stats['wrong_sessions'])),
            'descriptions': list(stats['descriptions']),
            'wrong_details': stats['wrong_details'],
        })
    
    accuracy_list.sort(key=lambda x: x['total_appearances'], reverse=True)
    return accuracy_list


def generate_knowledge_summary(accuracy_list: List[Dict]) -> str:
    lines = []
    lines.append("# 📚 考试代码知识体系总表")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    lines.append("\n## 📊 总体统计\n")
    total_apis = len(accuracy_list)
    total_appearances = sum(a['total_appearances'] for a in accuracy_list)
    total_correct = sum(a['correct_count'] for a in accuracy_list)
    total_wrong = sum(a['wrong_count'] for a in accuracy_list)
    overall_accuracy = (total_correct / (total_correct + total_wrong) * 100) if (total_correct + total_wrong) > 0 else 100
    
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 涉及API/知识点数 | {total_apis} |")
    lines.append(f"| 总出现次数 | {total_appearances} |")
    lines.append(f"| 正确次数 | {total_correct} |")
    lines.append(f"| 错误次数 | {total_wrong} |")
    lines.append(f"| 总体正确率 | {overall_accuracy:.1f}% |")
    lines.append("")
    
    lines.append("\n## 🎯 知识点详细统计\n")
    lines.append("| 排名 | API | 分类 | 出现次数 | 正确率 | 涉及章节 | 说明 |\n")
    lines.append("|------|-----|------|---------|--------|---------|------|\n")
    
    for i, item in enumerate(accuracy_list, 1):
        chapters = ', '.join(item['chapters'])
        accuracy_icon = "✅" if item['accuracy'] >= 90 else ("🟡" if item['accuracy'] >= 70 else "❌")
        
        lines.append(
            f"| {i} | `{item['api']}` | {item['category']} | "
            f"{item['total_appearances']} | {accuracy_icon} {item['accuracy']:.1f}% | "
            f"{chapters} | {item['description']} |"
        )
    
    lines.append("\n\n## 📈 按分类统计\n")
    
    category_stats = defaultdict(lambda: {'count': 0, 'appearances': 0, 'correct': 0, 'wrong': 0})
    for item in accuracy_list:
        cat = item['category']
        category_stats[cat]['count'] += 1
        category_stats[cat]['appearances'] += item['total_appearances']
        category_stats[cat]['correct'] += item['correct_count']
        category_stats[cat]['wrong'] += item['wrong_count']
    
    lines.append("| 分类 | 知识点数 | 总出现次数 | 正确率 |\n")
    lines.append("|------|---------|-----------|--------|\n")
    
    for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['appearances'], reverse=True):
        acc = (stats['correct'] / (stats['correct'] + stats['wrong']) * 100) if (stats['correct'] + stats['wrong']) > 0 else 100
        lines.append(f"| {cat} | {stats['count']} | {stats['appearances']} | {acc:.1f}% |")
    
    return '\n'.join(lines)


def generate_weak_points(accuracy_list: List[Dict]) -> str:
    lines = []
    lines.append("# 🚨 薄弱点分析表")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    weak_points = [a for a in accuracy_list if a['wrong_count'] > 0]
    weak_points.sort(key=lambda x: x['wrong_count'], reverse=True)
    
    if not weak_points:
        lines.append("\n✅ 暂无薄弱点！所有知识点都正确！\n")
        return '\n'.join(lines)
    
    lines.append(f"\n共发现 **{len(weak_points)}** 个薄弱知识点\n")
    
    lines.append("\n## 📊 薄弱点总览\n")
    lines.append("| 排名 | API | 分类 | 错误次数 | 正确率 | 错误章节 | 错误说明 |\n")
    lines.append("|------|-----|------|---------|--------|---------|---------|\n")
    
    for i, item in enumerate(weak_points, 1):
        chapters = ', '.join(item['chapters'])
        desc = item['descriptions'][0] if item['descriptions'] else ''
        
        lines.append(
            f"| {i} | `{item['api']}` | {item['category']} | "
            f"{item['wrong_count']} | {item['accuracy']:.1f}% | "
            f"{chapters} | {desc[:50]} |"
        )
    
    lines.append("\n\n## 🔍 详细错误记录\n")
    
    for item in weak_points:
        if not item['wrong_details']:
            continue
        
        lines.append(f"\n### {item['api']} ({item['category']})\n")
        lines.append(f"- **错误次数**: {item['wrong_count']}")
        lines.append(f"- **正确率**: {item['accuracy']:.1f}%")
        lines.append(f"- **涉及章节**: {', '.join(item['chapters'])}\n")
        
        for detail in item['wrong_details'][:5]:
            lines.append(f"- [{detail['chapter']}] {detail['description']}")
            lines.append(f"  - 代码: `{detail['code'][:80]}`")
    
    return '\n'.join(lines)


def generate_code_templates(accuracy_list: List[Dict]) -> str:
    lines = []
    lines.append("# 💻 考试代码模板")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    templates = {
        'pd.read_csv': {
            'title': '数据读取',
            'code': "import pandas as pd\nimport numpy as np\n\ndata = pd.read_csv('data.csv')",
            'tips': '读取CSV文件，返回DataFrame对象'
        },
        'data.isnull()': {
            'title': '缺失值检测',
            'code': "missing_values = data.isnull().sum()\nprint(missing_values)",
            'tips': 'isnull()检测缺失值，sum()统计每列缺失数量'
        },
        'data.duplicated()': {
            'title': '重复值检测',
            'code': "duplicate_count = data.duplicated().sum()\nprint(f'重复行数: {duplicate_count}')",
            'tips': 'duplicated()检测重复行'
        },
        'data.dropna()': {
            'title': '删除缺失值',
            'code': "data = data.dropna()\n# 或删除特定列的缺失值\ndata = data.dropna(subset=['column_name'])",
            'tips': 'dropna()删除包含NaN的行，返回新DataFrame'
        },
        'data.fillna()': {
            'title': '填充缺失值',
            'code': "# 前向填充\ndata['col'].fillna(method='ffill', inplace=True)\n# 后向填充\ndata['col'].fillna(method='bfill', inplace=True)\n# 固定值填充\ndata['col'].fillna(0, inplace=True)",
            'tips': 'ffill=前向填充, bfill=后向填充, inplace=True直接修改原数据'
        },
        'data.drop()': {
            'title': '删除列/行',
            'code': "# 删除列\ndata = data.drop(columns=['col1', 'col2'])\n# 删除行\ndata = data.drop(index=[0, 1, 2])",
            'tips': 'columns参数删除列，index参数删除行'
        },
        'data.astype()': {
            'title': '数据类型转换',
            'code': "# 转换为整数\ndata['col'] = data['col'].astype(int)\n# 转换为浮点数\ndata['col'] = data['col'].astype(float)\n# 转换为字符串\ndata['col'] = data['col'].astype(str)",
            'tips': 'astype()用于类型转换，注意处理NaN值'
        },
        'data.between()': {
            'title': '区间判断',
            'code': "# 检查值是否在区间内\ndata['col'].between(18, 70)\n# 结合布尔索引筛选\ndata = data[data['Age'].between(18, 70)]",
            'tips': 'between(left, right)包含边界值'
        },
        'data.value_counts()': {
            'title': '计数统计',
            'code': "# 统计各值出现次数\ncounts = data['col'].value_counts()\n# 按索引排序\ncounts = data['col'].value_counts().sort_index()",
            'tips': '返回Series，索引为唯一值，值为出现次数'
        },
        'data.groupby()': {
            'title': '分组聚合',
            'code': "# 单列分组\nstats = data.groupby('col')['target'].mean()\n# 多列分组\nstats = data.groupby(['col1', 'col2'])['target'].mean()\n# 使用agg进行多聚合\nstats = data.groupby('col').agg({'col1': 'mean', 'col2': 'count'})",
            'tips': 'groupby后接聚合函数：mean(), sum(), count(), agg()'
        },
        'data.agg()': {
            'title': '聚合计算',
            'code': "# 单列多聚合\nstats = data.groupby('col')['target'].agg(['count', 'mean', 'std'])\n# 多列不同聚合\nstats = data.groupby('col').agg({\n    'col1': 'mean',\n    'col2': ['count', 'sum']\n})",
            'tips': 'agg()可同时进行多种聚合计算'
        },
        'data.apply()': {
            'title': '应用自定义函数',
            'code': "# 对每组应用自定义函数\nresult = data.groupby('col')['target'].apply(lambda x: (x > 0).mean())\n# 对列应用函数\ndata['new_col'] = data['col'].apply(lambda x: x * 2)",
            'tips': 'apply()灵活应用自定义函数，常用于复杂聚合'
        },
        'data.unstack()': {
            'title': '行转列',
            'code': "# 将行索引转为列名\nresult = data.groupby(['col1', 'col2'])['target'].mean().unstack()",
            'tips': 'unstack()将最内层行索引转为列名'
        },
        'pd.cut()': {
            'title': '区间分组',
            'code': "# 定义区间边界\nbins = [0, 18.5, 24, 28, np.inf]\nlabels = ['偏瘦', '正常', '超重', '肥胖']\n# 划分区间\ndata['category'] = pd.cut(data['col'], bins=bins, labels=labels, right=False)",
            'tips': 'right=False表示左闭右开区间，np.inf表示正无穷'
        },
        'np.where()': {
            'title': '条件选择',
            'code': "# 根据条件创建新列\ndata['new_col'] = np.where(\n    data['col'] > threshold,\n    '满足条件',\n    '不满足条件'\n)",
            'tips': 'np.where(条件, 真值, 假值)，类似Excel的IF函数'
        },
        'data.to_csv()': {
            'title': '保存数据',
            'code': "# 保存为CSV文件\ndata.to_csv('output.csv', index=False)",
            'tips': 'index=False不保存行索引'
        },
        'data.isin()': {
            'title': '布尔过滤',
            'code': "# 筛选包含在列表中的值\nmask = data['col'].isin(['value1', 'value2'])\nfiltered_data = data[mask]",
            'tips': 'isin()等价于多个OR条件'
        },
        'data.mean()': {
            'title': '计算平均值',
            'code': "# 计算列平均值\nmean_val = data['col'].mean()\n# Z-score标准化分子\nnormalized = (data['col'] - data['col'].mean()) / data['col'].std()",
            'tips': 'mean()计算算术平均值'
        },
        'data.std()': {
            'title': '计算标准差',
            'code': "# 计算列标准差\nstd_val = data['col'].std()\n# Z-score标准化分母\nnormalized = (data['col'] - data['col'].mean()) / data['col'].std()",
            'tips': 'std()计算样本标准差'
        },
        'data.sum()': {
            'title': '求和',
            'code': "# 布尔值求和（统计True的数量）\ncount = data['is_abnormal'].sum()\n# 列求和\ntotal = data['col'].sum()",
            'tips': 'True被视为1，False为0，sum()可统计True的数量'
        },
        'len(data)': {
            'title': '获取数据行数',
            'code': "# 获取DataFrame行数\ntotal_rows = len(data)\n# 计算占比\nratio = count / len(data)",
            'tips': 'len(data)获取DataFrame的行数'
        },
        'data.all()': {
            'title': '全部为True检查',
            'code': "# 检查每行是否所有条件都为True\nvalidity = data[['is_age_valid', 'is_income_valid']].all(axis=1)",
            'tips': 'all(axis=1)检查每行是否全部为True'
        },
        'data.sort_index()': {
            'title': '按索引排序',
            'code': "# 按索引排序（常用于value_counts后）\ncounts = data['col'].value_counts().sort_index()",
            'tips': 'sort_index()按索引值排序，使输出更有序'
        },
        'onnxruntime.InferenceSession': {
            'title': '加载ONNX模型',
            'code': "import onnxruntime as ort\n\n# 加载ONNX模型，创建推理会话\nort_session = ort.InferenceSession('model.onnx')",
            'tips': 'InferenceSession加载ONNX模型，创建推理会话用于后续预测'
        },
        'ort_session.run': {
            'title': '执行ONNX推理',
            'code': "# 执行模型推理\nort_outs = ort_session.run(None, ort_inputs)\n# ort_inputs是字典，格式: {input_name: input_data}",
            'tips': 'run(None, inputs)第一个参数为None表示获取所有输出，第二个参数是输入数据字典'
        },
        'ort_session.get_inputs': {
            'title': '获取模型输入信息',
            'code': "# 获取模型输入的名称\ninput_name = ort_session.get_inputs()[0].name\n# 构建输入字典\nort_inputs = {input_name: input_data}",
            'tips': 'get_inputs()返回模型输入列表，[0].name获取第一个输入的名称'
        },
        'np.array': {
            'title': '创建Numpy数组',
            'code': "# 从图像创建numpy数组\nimage_array = np.array(image, dtype=np.float32)\n# 直接创建数组\narr = np.array([1, 2, 3])",
            'tips': 'dtype=np.float32指定32位浮点，常用于模型输入'
        },
        'np.expand_dims': {
            'title': '扩展数组维度',
            'code': "# 添加batch维度 (H,W) -> (1,H,W)\nimage_array = np.expand_dims(image_array, axis=0)\n# 添加通道维度 (H,W) -> (H,W,1)\nimage_array = np.expand_dims(image_array, axis=-1)",
            'tips': 'axis=0在第0维扩展，axis=-1在最后一维扩展，模型输入通常需要batch维度'
        },
        'np.argmax': {
            'title': '获取最大值索引',
            'code': "# 获取预测概率最高的类别\npredicted_class = np.argmax(ort_outs[0])\n# 沿指定轴获取最大值索引\npredicted_classes = np.argmax(output, axis=1)",
            'tips': 'argmax返回最大值索引，常用于获取预测类别'
        },
        'np.float32': {
            'title': '32位浮点类型',
            'code': "# 创建数组时指定类型\nimage_array = np.array(image, dtype=np.float32)\n# 类型转换\narr = arr.astype(np.float32)",
            'tips': 'ONNX模型输入通常要求float32类型'
        },
        'Image.open': {
            'title': '打开图像文件',
            'code': "from PIL import Image\n\n# 打开图像并转为灰度图\nimage = Image.open('test.png').convert('L')\n# 打开图像并转为RGB\nimage = Image.open('test.png').convert('RGB')",
            'tips': 'convert("L")转灰度图，convert("RGB")转彩色图'
        },
        'image.resize': {
            'title': '调整图像大小',
            'code': "# 调整图像大小\nimage = image.resize((28, 28))  # MNIST尺寸\nimage = image.resize((320, 240))  # 自定义尺寸",
            'tips': 'resize((width, height))注意参数顺序是(宽, 高)'
        },
        'image.convert': {
            'title': '转换图像模式',
            'code': "# 转为灰度图\nimage = Image.open('test.png').convert('L')\n# 转为RGB\nimage = Image.open('test.png').convert('RGB')",
            'tips': '"L"=灰度(单通道), "RGB"=彩色(三通道)'
        },
        'cv2.imread': {
            'title': 'OpenCV读取图像',
            'code': "import cv2\n\n# 读取图像\norig_image = cv2.imread('image.png')\n# 读取灰度图\ngray_image = cv2.imread('image.png', cv2.IMREAD_GRAYSCALE)",
            'tips': 'cv2.imread返回numpy数组，默认BGR格式'
        },
        'cv2.resize': {
            'title': 'OpenCV调整图像大小',
            'code': "# 调整图像大小\nimage = cv2.resize(image, (320, 240))  # (宽, 高)",
            'tips': 'cv2.resize(image, (width, height))参数顺序是(宽, 高)'
        },
        'scipy.special.softmax': {
            'title': 'Softmax函数',
            'code': "import scipy.special\n\n# 应用softmax获取概率分布\nprobabilities = scipy.special.softmax(output, axis=-1)",
            'tips': 'softmax将输出转为概率分布，axis=-1表示沿最后一个维度计算'
        },
        'os.makedirs': {
            'title': '创建目录',
            'code': "import os\n\n# 创建目录（如果不存在）\nos.makedirs(result_path, exist_ok=True)",
            'tips': 'exist_ok=True避免目录已存在时报错'
        },
        'open().readlines': {
            'title': '读取文件所有行',
            'code': "# 读取文件所有行\nlines = open('labels.txt').readlines()\n# 去除空白字符\nclass_names = [name.strip() for name in open('labels.txt').readlines()]",
            'tips': 'readlines()返回包含换行符的列表，常用strip()去除空白'
        },
        'dict映射': {
            'title': '字典标签映射',
            'code': "# 定义情感类别映射\nemotion_table = {\n    'neutral': 0, 'happiness': 1, 'surprise': 2,\n    'sadness': 3, 'anger': 4, 'disgust': 5\n}\n# 通过标签获取数字\nlabel = emotion_table['happiness']  # 返回1",
            'tips': '字典用于标签和数字之间的映射，常用于分类任务'
        },
        'list().keys': {
            'title': '字典键转列表',
            'code': "# 将字典键转为列表\nemotion_names = list(emotion_table.keys())\n# 通过索引获取键名\npredicted_emotion = list(emotion_table.keys())[predicted_label]",
            'tips': 'list(dict.keys())将字典的键转为列表，可通过索引访问'
        },
        'with open': {
            'title': '安全打开文件',
            'code': "# 使用with语句安全打开文件\nwith open('labels.txt') as f:\n    labels = f.read().strip().split('\\n')",
            'tips': 'with语句自动关闭文件，推荐使用'
        },
        'strip()': {
            'title': '去除字符串空白',
            'code': "# 去除首尾空白字符\nname = '  hello  '.strip()  # 'hello'\n# 列表推导式去除所有行的空白\nclass_names = [line.strip() for line in open('labels.txt').readlines()]",
            'tips': 'strip()去除首尾空白(空格、换行、制表符)'
        },
    }
    
    for item in accuracy_list:
        api = item['api']
        if api in templates:
            t = templates[api]
            lines.append(f"\n## {t['title']} - `{api}`\n")
            lines.append(f"**出现次数**: {item['total_appearances']} | **正确率**: {item['accuracy']:.1f}%\n")
            lines.append("```python")
            lines.append(t['code'])
            lines.append("```\n")
            lines.append(f"**要点**: {t['tips']}\n")
    
    return '\n'.join(lines)


def generate_anki_tsv(accuracy_list: List[Dict]) -> str:
    lines = []
    lines.append("正面\t背面\t标签")
    
    for item in accuracy_list:
        api = item['api']
        category = item['category']
        desc = item['description']
        accuracy = item['accuracy']
        
        front = f"【{category}】{api}\n{desc}"
        
        back = f"出现次数: {item['total_appearances']}\n正确率: {accuracy:.1f}%"
        if item['wrong_count'] > 0:
            back += f"\n❌ 错误{item['wrong_count']}次"
        
        tag = f"pandas:{category.lower()}"
        if accuracy < 80:
            tag += " 薄弱点"
        
        lines.append(f"{front}\t{back}\t{tag}")
    
    return '\n'.join(lines)


def main():
    logger.info("加载所有评分结果...")
    scoring_results = load_all_scoring_results()
    logger.info(f"  找到 {len(scoring_results)} 个评分结果")
    
    if not scoring_results:
        logger.error("未找到评分结果，无法分析")
        return
    
    logger.info("\n分析知识点...")
    knowledge_stats = analyze_knowledge_points(scoring_results)
    
    logger.info("计算正确率...")
    accuracy_list = calculate_accuracy(knowledge_stats)
    
    output_dir = ROOT / 'reports' / 'knowledge_system'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("生成知识体系总表...")
    summary_content = generate_knowledge_summary(accuracy_list)
    summary_path = output_dir / 'knowledge_summary.md'
    summary_path.write_text(summary_content, encoding='utf-8')
    logger.info(f"  已生成: {summary_path}")
    
    logger.info("生成薄弱点表...")
    weak_content = generate_weak_points(accuracy_list)
    weak_path = output_dir / 'weak_points.md'
    weak_path.write_text(weak_content, encoding='utf-8')
    logger.info(f"  已生成: {weak_path}")
    
    logger.info("生成代码模板...")
    template_content = generate_code_templates(accuracy_list)
    template_path = output_dir / 'code_templates.md'
    template_path.write_text(template_content, encoding='utf-8')
    logger.info(f"  已生成: {template_path}")
    
    logger.info("生成Anki TSV...")
    anki_content = generate_anki_tsv(accuracy_list)
    anki_path = output_dir / 'anki_cards.tsv'
    anki_path.write_text(anki_content, encoding='utf-8')
    logger.info(f"  已生成: {anki_path}")
    
    print("\n" + "="*80)
    print("📚 考试代码知识体系分析完成")
    print("="*80)
    
    total_apis = len(accuracy_list)
    total_appearances = sum(a['total_appearances'] for a in accuracy_list)
    total_correct = sum(a['correct_count'] for a in accuracy_list)
    total_wrong = sum(a['wrong_count'] for a in accuracy_list)
    overall_accuracy = (total_correct / (total_correct + total_wrong) * 100) if (total_correct + total_wrong) > 0 else 100
    
    print(f"\n📊 总体统计:")
    print(f"  涉及API/知识点数: {total_apis}")
    print(f"  总出现次数: {total_appearances}")
    print(f"  正确次数: {total_correct}")
    print(f"  错误次数: {total_wrong}")
    print(f"  总体正确率: {overall_accuracy:.1f}%")
    
    weak_points = [a for a in accuracy_list if a['wrong_count'] > 0]
    print(f"\n🚨 薄弱点: {len(weak_points)} 个")
    for wp in sorted(weak_points, key=lambda x: x['wrong_count'], reverse=True)[:5]:
        print(f"  ❌ {wp['api']}: 错误{wp['wrong_count']}次，正确率{wp['accuracy']:.1f}%")
    
    print(f"\n📁 输出文件:")
    print(f"  知识体系总表: {summary_path}")
    print(f"  薄弱点表: {weak_path}")
    print(f"  代码模板: {template_path}")
    print(f"  Anki卡片: {anki_path}")


if __name__ == '__main__':
    main()