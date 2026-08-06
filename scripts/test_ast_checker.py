#!/usr/bin/env python3
"""
测试 AST 检查功能
"""
import sys
sys.path.insert(0, 'scripts')

from scoring_validator import ASTChecker, check_ast_rule

# 测试代码
test_code = """
import pandas as pd
import numpy as np

# 加载数据
df = pd.read_csv('auto-mpg.csv')

# 数据清洗
df['horsepower'] = pd.to_numeric(df['horsepower'], errors='coerce')
df = df.dropna()

# 特征选择
X = df[['cylinders', 'displacement', 'weight']]
y = df['mpg']

# 划分数据集
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 创建 Pipeline
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('reg', LinearRegression())
])

# 训练模型
pipe.fit(X_train, y_train)

# 预测
predictions = pipe.predict(X_test)

# 保存结果
import pickle
with open('model.pkl', 'wb') as f:
    pickle.dump(pipe, f)
"""

def test_ast_checker():
    print("=" * 70)
    print("AST Checker 功能测试")
    print("=" * 70)
    
    checker = ASTChecker(test_code)
    
    # 测试 1: 函数调用检查
    print("\n1. 函数调用检查")
    tests = [
        ("pd.read_csv", True),
        ("read_csv", True),
        ("dropna", True),
        ("fit", True),
        ("predict", True),
        ("nonexistent", False),
    ]
    
    for func_name, expected in tests:
        result = checker.has_function_call(func_name)
        status = "✅" if result == expected else "❌"
        print(f"  {status} has_function_call('{func_name}'): {result} (期望: {expected})")
    
    # 测试 2: 模块限定函数调用
    print("\n2. 模块限定函数调用")
    tests = [
        ("read_csv", "pd", True),
        ("read_csv", "np", False),
        ("to_numeric", "pd", True),
    ]
    
    for func_name, module, expected in tests:
        result = checker.has_function_call(func_name, module)
        status = "✅" if result == expected else "❌"
        print(f"  {status} has_function_call('{func_name}', '{module}'): {result} (期望: {expected})")
    
    # 测试 3: 赋值检查
    print("\n3. 赋值检查")
    tests = [
        ("df", True),
        ("X", True),
        ("y", True),
        ("predictions", True),
        ("nonexistent", False),
    ]
    
    for target, expected in tests:
        result = checker.has_assignment(target)
        status = "✅" if result == expected else "❌"
        print(f"  {status} has_assignment('{target}'): {result} (期望: {expected})")
    
    # 测试 4: 导入检查
    print("\n4. 导入检查")
    tests = [
        ("pandas", True),
        ("numpy", True),
        ("sklearn", False),  # 是 ImportFrom，不是 Import
        ("pickle", True),
    ]
    
    for module, expected in tests:
        result = checker.has_import(module)
        status = "✅" if result == expected else "❌"
        print(f"  {status} has_import('{module}'): {result} (期望: {expected})")
    
    # 测试 5: 获取函数参数
    print("\n5. 获取函数参数")
    calls = checker.get_call_args('train_test_split')
    if calls:
        print(f"  ✅ train_test_split 调用: {calls[0]}")
    else:
        print(f"  ❌ 未找到 train_test_split 调用")
    
    # 测试 6: 方法链检查
    chain_code = "data.groupby('SensorType')['Value'].agg(['count', 'mean'])"
    chain_checker = ASTChecker(chain_code)
    result = chain_checker.has_method_chain(['groupby', 'agg'], 'data')
    print(f"\n6. 方法链检查")
    print(f"  {'✅' if result else '❌'} has_method_chain(['groupby', 'agg'], 'data'): {result}")


def test_check_ast_rule():
    print("\n" + "=" * 70)
    print("check_ast_rule 功能测试")
    print("=" * 70)
    
    # 测试 1: must_call
    print("\n1. must_call 规则")
    rule = {"must_call": "read_csv"}
    result = check_ast_rule(test_code, rule)
    print(f"  {'✅' if result else '❌'} must_call('read_csv'): {result}")
    
    # 测试 2: must_call with module
    rule = {"must_call": {"function": "read_csv", "module": "pd"}}
    result = check_ast_rule(test_code, rule)
    print(f"  {'✅' if result else '❌'} must_call(read_csv, pd): {result}")
    
    # 测试 3: must_assign
    rule = {"must_assign": "df"}
    result = check_ast_rule(test_code, rule)
    print(f"  {'✅' if result else '❌'} must_assign('df'): {result}")
    
    # 测试 4: must_have_arg
    rule = {
        "must_have_arg": {
            "function": "train_test_split",
            "param": "test_size",
            "value": "0.2"
        }
    }
    result = check_ast_rule(test_code, rule)
    print(f"  {'✅' if result else '❌'} must_have_arg(train_test_split, test_size=0.2): {result}")
    
    # 测试 5: must_import
    rule = {"must_import": "pandas"}
    result = check_ast_rule(test_code, rule)
    print(f"  {'✅' if result else '❌'} must_import('pandas'): {result}")
    
    # 测试 6: must_chain
    chain_code = "data.groupby('SensorType')['Value'].agg(['count', 'mean'])"
    rule = {
        "must_chain": {
            "methods": ["groupby", "agg"],
            "base": "data"
        }
    }
    result = check_ast_rule(chain_code, rule)
    print(f"  {'✅' if result else '❌'} must_chain(['groupby', 'agg'], 'data'): {result}")


if __name__ == '__main__':
    test_ast_checker()
    test_check_ast_rule()
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)