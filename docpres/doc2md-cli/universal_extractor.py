#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import json
import os
from typing import List, Dict, Optional
from pathlib import Path

try:
    from langextract import extract
    from dotenv import load_dotenv
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False

class UniversalExtractor:
    def __init__(self):
        self.rules = self._load_extraction_rules()
        if LANGEXTRACT_AVAILABLE:
            load_dotenv()
    
    def _load_extraction_rules(self) -> Dict:
        """加载通用的提取规则"""
        return {
            'chinese_headings': [
                r'^([一二三四五六七八九十]+)、(.+)$',
                r'^（([一二三四五六七八九十]+)）(.+)$',
                r'^([0-9]+)\.(.+)$',
                r'^([0-9]+)\.([0-9]+)(.+)$',
                r'^#+ (.+)$'
            ],
            'heading_levels': {
                'main': 1,      # 一级标题
                'section': 2,   # 二级标题
                'subsection': 3, # 三级标题
                'detail': 4      # 四级标题
            }
        }
    
    def extract_with_langextract(self, content: str) -> List[Dict]:
        """使用langextract提取结构化信息"""
        if not LANGEXTRACT_AVAILABLE:
            return []
        
        try:
            examples = self._create_examples()
            
            # 修复API调用参数
            result = extract(
                text=content,
                examples=examples,
                model="gemini-1.5-flash",
                format="json"
            )
            
            if result and isinstance(result, list):
                return result
            elif isinstance(result, dict) and 'headings' in result:
                return result['headings']
            else:
                return []
                
        except Exception as e:
            print(f"langextract提取失败: {e}")
            return []
    
    def extract_with_rules(self, content: str) -> List[Dict]:
        """使用规则提取标题"""
        headings = []
        lines = content.split('\n')
        
        # 先跳过目录部分
        content_start = 0
        for i, line in enumerate(lines):
            if "目录" in line and len(line.strip()) < 10:
                content_start = i + 1
                break
        
        for i in range(content_start, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            
            # 检测各种格式的标题
            heading_info = self._detect_heading(line, lines, i)
            if heading_info:
                headings.append(heading_info)
        
        return self._refine_headings(headings)
    
    def _detect_heading(self, line: str, lines: List[str], index: int) -> Optional[Dict]:
        """检测单行是否为标题"""
        # 跳过过长的行（可能是正文）
        if len(line) > 100:
            return None
        
        # Markdown标题
        md_match = re.match(r'^(#+)\s+(.+)$', line)
        if md_match:
            level = len(md_match.group(1))
            return {'text': md_match.group(2).strip(), 'level': level}
        
        # 中文数字标题（一、二、三）
        chinese_match = re.match(r'^([一二三四五六七八九十]+)、\s*(.+)$', line)
        if chinese_match:
            return {'text': chinese_match.group(2).strip(), 'level': 1}
        
        # 中文括号标题（（一）（二））
        bracket_match = re.match(r'^（([一二三四五六七八九十]+)）\s*(.+)$', line)
        if bracket_match:
            return {'text': bracket_match.group(2).strip(), 'level': 2}
        
        # 阿拉伯数字标题（1. 2.）
        digit_match = re.match(r'^([0-9]+)\.\s*(.+)$', line)
        if digit_match:
            level = 3 if int(digit_match.group(1)) > 5 else 2
            return {'text': digit_match.group(2).strip(), 'level': level}
        
        # 带括号的数字标题（(1) (2)）
        paren_digit_match = re.match(r'^\(([0-9]+)\)\s*(.+)$', line)
        if paren_digit_match:
            return {'text': paren_digit_match.group(2).strip(), 'level': 3}
        
        # 多级数字标题（1.1 1.2）
        multi_digit_match = re.match(r'^([0-9]+)\.([0-9]+)\s*(.+)$', line)
        if multi_digit_match:
            return {'text': multi_digit_match.group(3).strip(), 'level': 3}
        
        # 跳过明显的正文内容
        if re.search(r'[。，；：！？]$', line):
            return None
        
        # 对于短文本，检查是否是标题
        if len(line) < 50 and not line.isdigit():
            # 检查下一行是否是正文
            if index + 1 < len(lines):
                next_line = lines[index + 1].strip()
                if next_line and len(next_line) > 20:
                    return {'text': line, 'level': self._guess_level(line)}
        
        return None
    
    def _looks_like_heading(self, text: str) -> bool:
        """判断文本是否看起来像标题"""
        if len(text) > 100:
            return False
        if re.match(r'^([一二三四五六七八九十]+|[0-9]+)', text):
            return True
        if re.search(r'[。，；：！？]$', text):
            return False
        return True
    
    def _guess_level(self, text: str) -> int:
        """根据文本内容猜测标题级别"""
        length = len(text)
        if length <= 10:
            return 1
        elif length <= 20:
            return 2
        elif length <= 30:
            return 3
        else:
            return 4
    
    def _refine_headings(self, headings: List[Dict]) -> List[Dict]:
        """精炼标题列表，去除重复和调整层级"""
        if not headings:
            return []
        
        # 去重
        seen = set()
        unique_headings = []
        for heading in headings:
            text = heading['text']
            if text not in seen:
                seen.add(text)
                unique_headings.append(heading)
        
        # 调整层级关系
        return self._adjust_hierarchy(unique_headings)
    
    def _adjust_hierarchy(self, headings: List[Dict]) -> List[Dict]:
        """调整标题的层级关系"""
        if not headings:
            return []
        
        result = []
        current_level = 1
        
        for i, heading in enumerate(headings):
            # 如果是第一个标题，保持原级别
            if i == 0:
                result.append(heading)
                current_level = heading['level']
                continue
            
            # 调整级别，确保层级合理
            level_diff = heading['level'] - current_level
            if level_diff > 1:
                heading['level'] = current_level + 1
            elif level_diff < -1:
                heading['level'] = max(1, current_level - 1)
            
            result.append(heading)
            current_level = heading['level']
        
        return result
    
    def _create_examples(self) -> List[Dict]:
        """创建langextract示例"""
        return [
            {
                "input": "一、数字化转型的定义与参考\n（一）数字化转型是什么\n（二）数字化转型不是什么\n二、同行业企业数字化转型情况\n（一）中交集团\n（二）江苏交控集团",
                "output": [
                    {"text": "数字化转型的定义与参考", "level": 1},
                    {"text": "数字化转型是什么", "level": 2},
                    {"text": "数字化转型不是什么", "level": 2},
                    {"text": "同行业企业数字化转型情况", "level": 1},
                    {"text": "中交集团", "level": 2},
                    {"text": "江苏交控集团", "level": 2}
                ]
            },
            {
                "input": "# 主要工作方式\n## 组建专班，专题推进大模型相关工作\n## 开展重点企业技术调研\n# 重点工作成果\n## 全流程工作质效管理平台\n## 智能会议管理系统",
                "output": [
                    {"text": "主要工作方式", "level": 1},
                    {"text": "组建专班，专题推进大模型相关工作", "level": 2},
                    {"text": "开展重点企业技术调研", "level": 2},
                    {"text": "重点工作成果", "level": 1},
                    {"text": "全流程工作质效管理平台", "level": 2},
                    {"text": "智能会议管理系统", "level": 2}
                ]
            }
        ]
    
    def _create_prompt(self) -> str:
        """创建提取提示"""
        return """请从文档内容中提取所有标题，并确定它们的层级关系。标题可能使用中文数字（一、二、三）、括号数字（（一）（二））、阿拉伯数字（1. 2.）或Markdown格式（# ## ###）。

返回JSON格式的标题列表，每个标题包含text和level字段，level表示标题级别（1-4）。"""
    
    def validate_results(self, langextract_result: List[Dict], rule_result: List[Dict]) -> bool:
        """验证两种方法的结果是否一致"""
        if not langextract_result or not rule_result:
            return False
        
        # 比较标题数量
        if len(langextract_result) != len(rule_result):
            return False
        
        # 比较每个标题的文本和大致级别
        for lr, rr in zip(langextract_result, rule_result):
            if lr['text'] != rr['text']:
                return False
            if abs(lr['level'] - rr['level']) > 1:
                return False
        
        return True
    
    def resolve_conflict(self, langextract_result: List[Dict], rule_result: List[Dict]) -> List[Dict]:
        """解决两种方法结果不一致的情况"""
        # 优先使用langextract结果
        if langextract_result:
            return langextract_result
        elif rule_result:
            return rule_result
        else:
            return []
    
    def extract_headings(self, file_path: str) -> List[Dict]:
        """主提取方法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return []
        
        # 使用两种方法提取
        langextract_result = self.extract_with_langextract(content)
        rule_result = self.extract_with_rules(content)
        
        # 验证结果
        is_consistent = self.validate_results(langextract_result, rule_result)
        
        if is_consistent:
            print("✓ 两种方法结果一致，使用langextract结果")
            return langextract_result
        else:
            print("⚠ 两种方法结果不一致，进行冲突解决")
            resolved = self.resolve_conflict(langextract_result, rule_result)
            if resolved:
                print("✓ 冲突解决成功")
            else:
                print("✗ 冲突解决失败，返回空结果")
            return resolved
    
    def generate_markdown(self, headings: List[Dict]) -> str:
        """生成Markdown格式的输出"""
        if not headings:
            return ""
        
        output = []
        for heading in headings:
            level = heading['level']
            text = heading['text']
            output.append(f"{'#' * level} {text}")
        
        return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(description='通用文档标题提取器')
    parser.add_argument('file_path', help='要处理的Markdown文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（可选）')
    parser.add_argument('-f', '--format', choices=['json', 'md'], default='md', 
                       help='输出格式：json或md（默认md）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"文件不存在: {args.file_path}")
        return
    
    extractor = UniversalExtractor()
    headings = extractor.extract_headings(args.file_path)
    
    if not headings:
        print("未提取到任何标题")
        return
    
    if args.format == 'json':
        output_content = json.dumps(headings, ensure_ascii=False, indent=2)
    else:
        output_content = extractor.generate_markdown(headings)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"结果已保存到: {args.output}")
    else:
        print(output_content)

if __name__ == '__main__':
    main()