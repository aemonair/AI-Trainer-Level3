#!/usr/bin/env python3
"""
AI智能评分系统 - 基于AI评分标准的本地评分工具
不依赖PDF答案，使用AI理解题目和选项后进行智能评分
"""

import csv
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path

class QuestionLoader:
    def __init__(self, csv_dir='anki_cards'):
        self.csv_dir = Path(csv_dir)
        self.questions = {
            '单选题': [],
            '多选题': [],
            '判断题': []
        }
        self._load_questions()
    
    def _load_questions(self):
        """加载所有题目"""
        csv_files = {
            '单选题': '理论知识_单选题.csv',
            '多选题': '理论知识_多选题.csv',
            '判断题': '理论知识_判断题.csv'
        }
        
        for q_type, filename in csv_files.items():
            filepath = self.csv_dir / filename
            if filepath.exists():
                self._load_csv(filepath, q_type)
                print(f"✅ 加载{q_type}: {len(self.questions[q_type])}题")
    
    def _load_csv(self, filepath, q_type):
        """加载CSV文件中的题目"""
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)  # Skip header
            
            for row in reader:
                if len(row) >= 2:
                    front = row[0]
                    back = row[1]
                    
                    # 提取题目信息
                    question_data = self._parse_question(front, back, q_type)
                    if question_data:
                        self.questions[q_type].append(question_data)
    
    def _parse_question(self, front, back, q_type):
        """解析题目内容"""
        # 清理题目文本
        clean_front = re.sub(r'\s+', ' ', front).strip()
        
        # 提取题干（选项之前的部分）
        question_text = clean_front
        options = []
        
        # 提取选项
        if q_type in ['单选题', '多选题']:
            # 匹配 (A) (B) (C) (D) (E) 格式的选项
            option_pattern = r'\(([A-E])\)\s*([^\(]+?)(?=\([A-E]\)|$)'
            matches = re.findall(option_pattern, clean_front)
            if matches:
                options = [{'label': label, 'text': text.strip()} for label, text in matches]
                # 题干是选项之前的部分
                question_text = clean_front.split('(A)')[0].replace('【单选题】', '').replace('【多选题】', '').strip()
        
        elif q_type == '判断题':
            # 判断题通常只有题干
            question_text = clean_front.replace('【判断题】', '').strip()
            options = [{'label': 'A', 'text': '正确'}, {'label': 'B', 'text': '错误'}]
        
        # 提取PDF答案（用于对比，但不依赖）
        pdf_answer = None
        pdf_match = re.search(r'【PDF答案】([A-E]+)', back)
        if pdf_match:
            pdf_answer = pdf_match.group(1)
        
        return {
            'question': question_text,
            'options': options,
            'type': q_type,
            'pdf_answer': pdf_answer,
            'full_text': front
        }
    
    def get_questions(self, question_type=None, num_questions=None, random_order=True):
        """获取题目"""
        if question_type:
            questions = self.questions.get(question_type, [])
        else:
            questions = []
            for q_list in self.questions.values():
                questions.extend(q_list)
        
        if not questions:
            return []
        
        # 随机选择题目
        if num_questions and num_questions < len(questions):
            if random_order:
                return random.sample(questions, num_questions)
            else:
                return questions[:num_questions]
        elif random_order:
            random.shuffle(questions)
        
        return questions


def export_quiz_for_ai(questions, output_file='temp_quiz_for_ai.json'):
    """导出题目为JSON格式，方便用户复制给AI评分"""
    quiz_data = []
    
    for i, q in enumerate(questions, 1):
        quiz_data.append({
            'index': i,
            'type': q['type'],
            'question': q['question'],
            'options': q['options'],
            'pdf_answer': q['pdf_answer']  # 仅用于后续对比，评分时不显示
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(quiz_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 题目已导出到: {output_file}")
    print(f"📝 共{len(quiz_data)}题")
    
    return output_file


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI智能评分系统')
    parser.add_argument('--type', choices=['单选题', '多选题', '判断题', '全部'], 
                       default='全部', help='题目类型')
    parser.add_argument('--num', type=int, default=20, help='题目数量（默认20）')
    parser.add_argument('--export', action='store_true', help='仅导出题目，不运行测验')
    
    args = parser.parse_args()
    
    # 加载题目
    print("📚 正在加载题目...")
    loader = QuestionLoader()
    
    # 确定题目类型
    question_type = None if args.type == '全部' else args.type
    
    # 获取题目
    questions = loader.get_questions(
        question_type=question_type,
        num_questions=args.num
    )
    
    if not questions:
        print("❌ 没有找到题目")
        return
    
    print(f"\n📝 准备测验：共{len(questions)}题")
    
    if args.export:
        # 仅导出题目
        export_quiz_for_ai(questions)
        print("\n✅ 导出完成！你可以将题目复制给AI进行评分")
    else:
        # 显示使用说明
        print("\n" + "=" * 60)
        print("🎯 使用说明")
        print("=" * 60)
        print("1. 运行以下命令导出题目：")
        print(f"   uv run python3 scripts/ai_scorer.py --type {args.type} --num {args.num} --export")
        print("\n2. 将导出的JSON文件内容复制给我（AI助手）")
        print("\n3. 我会：")
        print("   ✅ 分析每道题目的考点")
        print("   ✅ 判断正确答案")
        print("   ✅ 给出详细解析")
        print("   ✅ 生成评分报告")
        print("\n4. 你告诉我你的答案，我会进行评分")
        print("=" * 60)


if __name__ == '__main__':
    main()