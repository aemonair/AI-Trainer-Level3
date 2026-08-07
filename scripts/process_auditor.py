#!/usr/bin/env python3
"""
回溯审计模块（Process Auditor）

核心功能：
1. 读取execution_log.json，分析考试过程中的错误尝试
2. 对比最终代码和历史尝试，识别"中间犯过错"的题目
3. 生成process_penalty（过程罚分）和detected_errors列表

用法:
    from scripts.process_auditor import ProcessAuditor
    
    auditor = ProcessAuditor(
        execution_log_path="path/to/execution_log.json",
        practice_nb_path="path/to/practice.ipynb",
        answer_nb_path="path/to/answer.ipynb"
    )
    
    result = auditor.audit()
    print(f"过程罚分: {result['process_penalty']}")
    print(f"检测到的错误: {result['detected_errors']}")
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher


class ProcessAuditor:
    """回溯审计器"""
    
    def __init__(self, execution_log_path: Path, practice_nb_path: Path, 
                 answer_nb_path: Optional[Path] = None):
        """
        初始化审计器
        
        参数:
            execution_log_path: 执行日志文件路径
            practice_nb_path: 练习文件路径（最终答案）
            answer_nb_path: 参考答案文件路径（可选）
        """
        self.execution_log_path = execution_log_path
        self.practice_nb_path = practice_nb_path
        self.answer_nb_path = answer_nb_path
        
        # 加载数据
        self.execution_log = self._load_execution_log()
        self.practice_nb = self._load_notebook(practice_nb_path)
        self.answer_nb = self._load_notebook(answer_nb_path) if answer_nb_path else None
    
    def _load_execution_log(self) -> Dict:
        """加载执行日志"""
        if not self.execution_log_path.exists():
            return {'entries': []}
        
        try:
            with open(self.execution_log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载执行日志失败: {e}")
            return {'entries': []}
    
    def _load_notebook(self, nb_path: Path) -> Optional[Dict]:
        """加载notebook文件"""
        try:
            with open(nb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载notebook失败 {nb_path}: {e}")
            return None
    
    def _normalize_code(self, code: str) -> str:
        """标准化代码（用于对比）"""
        # 移除注释
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        # 移除多余空白
        code = re.sub(r'\s+', ' ', code).strip()
        # 统一引号
        code = code.replace("'", '"')
        return code
    
    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """计算两段代码的相似度"""
        norm1 = self._normalize_code(code1)
        norm2 = self._normalize_code(code2)
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _get_final_code_for_cell(self, cell_index: int) -> Optional[str]:
        """获取特定Cell的最终代码"""
        if not self.practice_nb:
            return None
        
        cells = self.practice_nb.get('cells', [])
        if cell_index >= len(cells):
            return None
        
        cell = cells[cell_index]
        if cell.get('cell_type') != 'code':
            return None
        
        return ''.join(cell.get('source', []))
    
    def _get_answer_code_for_cell(self, cell_index: int) -> Optional[str]:
        """获取参考答案中特定Cell的代码"""
        if not self.answer_nb:
            return None
        
        cells = self.answer_nb.get('cells', [])
        if cell_index >= len(cells):
            return None
        
        cell = cells[cell_index]
        if cell.get('cell_type') != 'code':
            return None
        
        return ''.join(cell.get('source', []))
    
    def _is_error_different_from_final(self, error_code: str, final_code: str) -> bool:
        """判断错误代码是否与最终代码不同"""
        if not final_code:
            return True
        
        similarity = self._calculate_similarity(error_code, final_code)
        return similarity < 0.85  # 相似度低于85%视为不同尝试
    
    def _classify_error_severity(self, error_msg: str, error_code: str) -> str:
        """分类错误严重程度"""
        error_msg_lower = error_msg.lower() if error_msg else ""
        
        # 语法错误
        if any(kw in error_msg_lower for kw in ['syntaxerror', 'indentationerror', 'nameerror']):
            return 'high'
        
        # 运行时错误
        if any(kw in error_msg_lower for kw in ['typeerror', 'valueerror', 'keyerror', 'attributeerror']):
            return 'medium'
        
        # 逻辑错误（无明显报错但结果不对）
        if any(kw in error_msg_lower for kw in ['assertionerror', 'incorrect', 'mismatch']):
            return 'medium'
        
        # 其他
        return 'low'
    
    def audit(self) -> Dict[str, Any]:
        """
        执行回溯审计
        
        返回:
            {
                'process_penalty': 5,  # 过程罚分
                'total_attempts': 10,  # 总尝试次数
                'error_attempts': 3,   # 错误尝试次数
                'detected_errors': [   # 检测到的错误列表
                    {
                        'cell_index': 2,
                        'error_code': 'data.dropna()',
                        'final_code': 'data.dropna(subset=["horsepower"])',
                        'error_message': 'ValueError: ...',
                        'severity': 'medium',
                        'attempt_number': 2,
                    },
                    ...
                ],
                'stability_score': 85,  # 稳定性得分（0-100）
            }
        """
        # 支持新旧两种格式：'events' (v1.0.0) 和 'entries' (旧版)
        entries = self.execution_log.get('events', self.execution_log.get('entries', []))
        
        if not entries:
            return {
                'process_penalty': 0,
                'total_attempts': 0,
                'error_attempts': 0,
                'detected_errors': [],
                'stability_score': 100,
                'message': '无执行历史记录',
            }
        
        detected_errors = []
        error_attempts = 0
        
        # 按Cell分组执行历史
        cell_history = {}
        for entry in entries:
            cell_idx = entry['cell_index']
            if cell_idx not in cell_history:
                cell_history[cell_idx] = []
            cell_history[cell_idx].append(entry)
        
        # 分析每个Cell的执行历史
        for cell_idx, history in cell_history.items():
            final_code = self._get_final_code_for_cell(cell_idx)
            answer_code = self._get_answer_code_for_cell(cell_idx)
            
            for attempt_num, entry in enumerate(history, 1):
                # 只关注有错误的执行
                if entry.get('error'):
                    # 支持新旧两种格式：'source' (v1.0.0) 和 'code' (旧版)
                    error_code = entry.get('source', entry.get('code', ''))
                    # 支持新旧两种格式：error对象 (v1.0.0) 和 error字符串 (旧版)
                    error_obj = entry.get('error')
                    if isinstance(error_obj, dict):
                        error_msg = error_obj.get('message', error_obj.get('type', 'Unknown'))
                    else:
                        error_msg = error_obj
                    
                    # 判断是否与最终代码不同（避免记录最终调试过程中的正常尝试）
                    if final_code and self._is_error_different_from_final(error_code, final_code):
                        severity = self._classify_error_severity(error_msg, error_code)
                        
                        detected_errors.append({
                            'cell_index': cell_idx,
                            'error_code': error_code[:200],  # 限制长度
                            'final_code': final_code[:200] if final_code else 'N/A',
                            'error_message': error_msg[:300],
                            'severity': severity,
                            'attempt_number': attempt_num,
                            'timestamp': entry.get('timestamp', ''),
                        })
                        error_attempts += 1
        
        # 计算过程罚分
        process_penalty = self._calculate_penalty(detected_errors, error_attempts)
        
        # 计算稳定性得分
        total_attempts = len(entries)
        stability_score = max(0, 100 - (error_attempts / max(total_attempts, 1) * 100))
        
        return {
            'process_penalty': process_penalty,
            'total_attempts': total_attempts,
            'error_attempts': error_attempts,
            'detected_errors': detected_errors,
            'stability_score': round(stability_score, 1),
            'message': f'检测到{error_attempts}次错误尝试' if error_attempts > 0 else '过程完美',
        }
    
    def _calculate_penalty(self, detected_errors: List[Dict], error_attempts: int) -> int:
        """
        计算过程罚分
        
        规则:
        - 每个high severity错误: 扣3分
        - 每个medium severity错误: 扣2分
        - 每个low severity错误: 扣1分
        - 最多扣20分（避免过度惩罚）
        """
        penalty = 0
        
        for error in detected_errors:
            severity = error.get('severity', 'low')
            if severity == 'high':
                penalty += 3
            elif severity == 'medium':
                penalty += 2
            else:
                penalty += 1
        
        return min(penalty, 20)  # 最多扣20分


def audit_practice(execution_log_path: Path, practice_nb_path: Path, 
                   answer_nb_path: Optional[Path] = None) -> Dict:
    """
    便捷函数：审计单个练习
    
    参数:
        execution_log_path: 执行日志路径
        practice_nb_path: 练习文件路径
        answer_nb_path: 参考答案路径（可选）
    
    返回:
        审计结果字典
    """
    auditor = ProcessAuditor(execution_log_path, practice_nb_path, answer_nb_path)
    return auditor.audit()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='回溯审计工具')
    parser.add_argument('--log', type=str, required=True, help='执行日志文件路径')
    parser.add_argument('--practice', type=str, required=True, help='练习文件路径')
    parser.add_argument('--answer', type=str, help='参考答案文件路径（可选）')
    parser.add_argument('--output-json', type=str, help='输出JSON报告路径')
    
    args = parser.parse_args()
    
    result = audit_practice(
        Path(args.log),
        Path(args.practice),
        Path(args.answer) if args.answer else None
    )
    
    print(f"\n📊 回溯审计结果")
    print(f"=" * 50)
    print(f"总尝试次数: {result['total_attempts']}")
    print(f"错误尝试: {result['error_attempts']}")
    print(f"过程罚分: -{result['process_penalty']}分")
    print(f"稳定性得分: {result['stability_score']}/100")
    print(f"\n{result['message']}")
    
    if result['detected_errors']:
        print(f"\n❌ 检测到的错误:")
        for i, error in enumerate(result['detected_errors'], 1):
            print(f"\n错误{i}:")
            print(f"  Cell索引: {error['cell_index']}")
            print(f"  错误代码: {error['error_code'][:100]}...")
            print(f"  最终代码: {error['final_code'][:100]}...")
            print(f"  严重程度: {error['severity']}")
    
    if args.output_json:
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ JSON报告已保存: {args.output_json}")