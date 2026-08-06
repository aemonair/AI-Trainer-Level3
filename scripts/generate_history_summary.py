#!/usr/bin/env python3
"""
生成IPython历史命令分析摘要报告
"""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

def generate_summary():
    """生成历史分析摘要"""
    
    # 收集所有result.json文件
    result_files = sorted(ROOT.rglob('*_result.json'))
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_practices': len(result_files),
        'matched_sessions': 0,
        'unmatched_sessions': 0,
        'total_commands': 0,
        'total_corrections': 0,
        'total_error_patterns': 0,
        'details': []
    }
    
    for rf in result_files:
        try:
            with open(rf, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
        
        chapter = data.get('chapter', '未知')
        history = data.get('ipython_history')
        
        detail = {
            'chapter': chapter,
            'score': data.get('score', 0),
            'has_history': history is not None
        }
        
        if history:
            summary['matched_sessions'] += 1
            summary['total_commands'] += history.get('total_commands', 0)
            summary['total_corrections'] += history.get('correction_count', 0)
            summary['total_error_patterns'] += len(history.get('error_patterns', []))
            
            detail['session_id'] = history.get('session_id')
            detail['total_commands'] = history.get('total_commands', 0)
            detail['correction_count'] = history.get('correction_count', 0)
            detail['error_patterns'] = len(history.get('error_patterns', []))
            detail['suggestions'] = len(history.get('suggestions', []))
        else:
            summary['unmatched_sessions'] += 1
        
        summary['details'].append(detail)
    
    # 打印摘要
    print("="*80)
    print("📊 IPython历史命令分析摘要")
    print("="*80)
    print(f"\n总练习数: {summary['total_practices']}")
    print(f"匹配到session: {summary['matched_sessions']}")
    print(f"未匹配session: {summary['unmatched_sessions']}")
    print(f"总命令数: {summary['total_commands']}")
    print(f"总修正次数: {summary['total_corrections']}")
    print(f"总错误模式: {summary['total_error_patterns']}")
    
    print("\n" + "-"*80)
    print("详细分析:")
    print("-"*80)
    
    for d in summary['details']:
        chapter = d['chapter']
        score = d['score']
        
        if d['has_history']:
            print(f"\n{chapter} (得分: {score}):")
            print(f"  Session: {d.get('session_id')}")
            print(f"  命令数: {d.get('total_commands')}")
            print(f"  修正次数: {d.get('correction_count')}")
            print(f"  错误模式: {d.get('error_patterns')}")
            print(f"  建议: {d.get('suggestions')}")
        else:
            print(f"\n{chapter} (得分: {score}): ⚠️ 未匹配到session")
    
    # 保存摘要
    output_path = ROOT / 'reports' / 'ipython_history_summary.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n摘要已保存: {output_path}")

if __name__ == '__main__':
    generate_summary()