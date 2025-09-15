#!/usr/bin/env python3
"""
md2top: Markdown文档结构化信息提取工具
使用Google Langextract从Markdown文档中提取标题、要点、代码块等结构化信息
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

try:
    from langextract import extract
    from langextract.core.data import ExampleData, Extraction, FormatType
except ImportError as e:
    print(f"错误: 无法导入 langextract - {e}")
    print("请检查安装: pip install langextract")
    print("Python路径:", sys.path)
    sys.exit(1)

class MarkdownExtractor:
    """Markdown文档结构化信息提取器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化提取器"""
        # 加载.env文件
        load_dotenv()
        
        self.api_key = api_key or os.environ.get('LANGEXTRACT_API_KEY')
        if not self.api_key:
            print("警告: 未设置API密钥，请设置LANGEXTRACT_API_KEY环境变量")
            print("您可以通过以下方式设置:")
            print("1. 在.env文件中设置 LANGEXTRACT_API_KEY=your_api_key")
            print("2. 使用命令行参数 --api-key your_api_key")
            print("3. 设置环境变量 export LANGEXTRACT_API_KEY=your_api_key")
        
        # 定义提取示例
        self.examples = self._create_examples()
    
    def _create_examples(self) -> List[ExampleData]:
        """创建提取示例"""
        examples = []
        
        # 示例1: 标准Markdown标题
        examples.append(ExampleData(
            text="# 项目介绍\n这是一个示例项目",
            extractions=[
                Extraction(
                    extraction_class="heading",
                    extraction_text="项目介绍",
                    attributes={"level": "1", "type": "heading"}
                )
            ]
        ))
        
        # 示例2: 中文数字标题格式（一、二、三）
        examples.append(ExampleData(
            text="一、数字化转型的定义与参考\n相关内容",
            extractions=[
                Extraction(
                    extraction_class="heading",
                    extraction_text="数字化转型的定义与参考",
                    attributes={"level": "1", "type": "heading", "format": "chinese_number"}
                )
            ]
        ))
        
        # 示例3: 中文括号标题格式（（一）（二））
        examples.append(ExampleData(
            text="（一）数字化转型是什么\n相关内容",
            extractions=[
                Extraction(
                    extraction_class="heading",
                    extraction_text="数字化转型是什么",
                    attributes={"level": "2", "type": "heading", "format": "chinese_parentheses"}
                )
            ]
        ))
        
        # 示例4: 带页码的目录格式
        examples.append(ExampleData(
            text="一、数字化转型的定义与参考\t3\n（一）数字化转型是什么\t3",
            extractions=[
                Extraction(
                    extraction_class="heading",
                    extraction_text="数字化转型的定义与参考",
                    attributes={"level": "1", "type": "heading", "format": "chinese_number"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="数字化转型是什么",
                    attributes={"level": "2", "type": "heading", "format": "chinese_parentheses"}
                )
            ]
        ))
        
        # 示例5: 二级标题
        examples.append(ExampleData(
            text="## 功能特点\n- 功能1\n- 功能2",
            extractions=[
                Extraction(
                    extraction_class="heading",
                    extraction_text="功能特点",
                    attributes={"level": "2", "type": "heading"}
                ),
                Extraction(
                    extraction_class="list_item",
                    extraction_text="功能1",
                    attributes={"type": "unordered_list"}
                ),
                Extraction(
                    extraction_class="list_item",
                    extraction_text="功能2",
                    attributes={"type": "unordered_list"}
                )
            ]
        ))
        
        # 示例6: 代码块
        examples.append(ExampleData(
            text="```python\nprint('Hello World')\n```",
            extractions=[
                Extraction(
                    extraction_class="code_block",
                    extraction_text="print('Hello World')",
                    attributes={"language": "python", "type": "code"}
                )
            ]
        ))
        
        # 示例7: 有序列表
        examples.append(ExampleData(
            text="1. 第一步\n2. 第二步",
            extractions=[
                Extraction(
                    extraction_class="list_item",
                    extraction_text="第一步",
                    attributes={"type": "ordered_list", "order": "1"}
                ),
                Extraction(
                    extraction_class="list_item",
                    extraction_text="第二步",
                    attributes={"type": "ordered_list", "order": "2"}
                )
            ]
        ))
        
        # 示例8: 复杂中文标题层级结构
        examples.append(ExampleData(
            text="三、集团管控大模型工作进展\n（一）主要工作方式\n1. 组建专班，专题推进大模型相关工作\n2. 开展重点企业技术调研\n（二）研究确定大模型开发与应用技术路线\n（三）重点工作成果\n1. 实现AI算力资源部署\n2. 实现AI大模型混合部署\n3. 构建集团专有知识库\n4. 开发四大AI赋能的管控数字化应用\n（1）全流程工作质效管理平台\n（2）智能会议管理系统\n（3）合同风险管控模块\n（4）AI合同评审系统",
            extractions=[
                Extraction(
                    extraction_class="heading",
                    extraction_text="集团管控大模型工作进展",
                    attributes={"level": "2", "type": "heading", "format": "chinese_number"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="主要工作方式",
                    attributes={"level": "3", "type": "heading", "format": "chinese_parentheses"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="组建专班，专题推进大模型相关工作",
                    attributes={"level": "4", "type": "heading", "format": "arabic_number"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="开展重点企业技术调研",
                    attributes={"level": "4", "type": "heading", "format": "arabic_number"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="重点工作成果",
                    attributes={"level": "3", "type": "heading", "format": "chinese_parentheses"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="全流程工作质效管理平台",
                    attributes={"level": "4", "type": "heading", "format": "chinese_parentheses"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="智能会议管理系统",
                    attributes={"level": "4", "type": "heading", "format": "chinese_parentheses"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="合同风险管控模块",
                    attributes={"level": "4", "type": "heading", "format": "chinese_parentheses"}
                ),
                Extraction(
                    extraction_class="heading",
                    extraction_text="AI合同评审系统",
                    attributes={"level": "4", "type": "heading", "format": "chinese_parentheses"}
                )
            ]
        ))
        
        # 示例8: 段落文本
        examples.append(ExampleData(
            text="这是一个段落文本，包含重要信息。",
            extractions=[
                Extraction(
                    extraction_class="paragraph",
                    extraction_text="这是一个段落文本，包含重要信息。",
                    attributes={"type": "paragraph"}
                )
            ]
        ))
        
        return examples
    
    def extract_structure(self, markdown_content: str) -> Dict[str, Any]:
        """从Markdown内容中提取结构化信息"""
        try:
            result = extract(
                text_or_documents=markdown_content,
                prompt_description="从Markdown文档中提取所有结构化元素，包括标题、列表项、代码块、段落等",
                examples=self.examples,
                api_key=self.api_key,
                model_id="gemini-2.5-flash",
                format_type=FormatType.JSON,
                max_char_buffer=2000,
                temperature=0.1,
                use_schema_constraints=True,
                debug=False
            )
            
            # 转换结果为结构化数据
            return self._format_result(result)
            
        except Exception as e:
            raise RuntimeError(f"提取失败: {e}")
    
    def _format_result(self, result) -> Dict[str, Any]:
        """格式化提取结果"""
        structured_data = {
            "headings": [],
            "lists": [],
            "code_blocks": [],
            "paragraphs": [],
            "metadata": {}
        }
        
        if hasattr(result, 'extractions'):
            for extraction in result.extractions:
                extraction_data = {
                    "class": extraction.extraction_class,
                    "text": extraction.extraction_text,
                    "attributes": extraction.attributes or {}
                }
                
                # 分类存储
                if extraction.extraction_class == "heading":
                    structured_data["headings"].append(extraction_data)
                elif extraction.extraction_class == "list_item":
                    structured_data["lists"].append(extraction_data)
                elif extraction.extraction_class == "code_block":
                    structured_data["code_blocks"].append(extraction_data)
                elif extraction.extraction_class == "paragraph":
                    structured_data["paragraphs"].append(extraction_data)
        
        return structured_data
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """从文件中提取结构化信息，跳过目录部分"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 跳过目录部分（包含页码的内容）
            lines = content.split('\n')
            content_without_toc = []
            in_toc_section = False
            toc_end_markers = ['关于集团数字化转型的工作报告', '河北交投智能科技股份有限公司']
            
            for line in lines:
                # 检测目录开始
                if '目录' in line and not in_toc_section:
                    in_toc_section = True
                    continue
                
                # 检测目录结束
                if in_toc_section:
                    if any(marker in line for marker in toc_end_markers):
                        in_toc_section = False
                    # 跳过带页码的行（包含制表符和数字）
                    if '\t' in line and any(char.isdigit() for char in line.split('\t')[-1]):
                        continue
                    # 跳过明显的目录格式行
                    if any(pattern in line for pattern in ['一、', '二、', '三、', '（一）', '（二）', '（三）']):
                        if any(char.isdigit() for char in line[-3:]):  # 行尾有数字（页码）
                            continue
                
                if not in_toc_section:
                    content_without_toc.append(line)
            
            # 重新组合内容
            clean_content = '\n'.join(content_without_toc)
            
            return self.extract_structure(clean_content)
            
        except Exception as e:
            raise RuntimeError(f"读取文件失败: {e}")

class MD2TopConverter:
    """Markdown转结构化信息转换器"""
    
    def __init__(self):
        self.extractor = MarkdownExtractor()
    
    def convert(self, input_file: str, output_file: Optional[str] = None, 
                format: str = "json") -> bool:
        """转换Markdown文件为结构化信息"""
        try:
            # 验证输入文件
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"文件不存在: {input_file}")
            
            # 验证文件格式
            if not input_file.lower().endswith('.md'):
                print("警告: 输入文件可能不是Markdown格式")
            
            # 执行提取
            print(f"正在处理: {input_file}")
            structured_data = self.extractor.extract_from_file(input_file)
            
            # 处理输出
            if output_file:
                output_path = Path(output_file)
            else:
                input_path = Path(input_file)
                if format == "md":
                    output_path = input_path.parent / f"{input_path.stem}-top.md"
                else:
                    output_path = input_path.parent / f"{input_path.stem}-structured.{format}"
            
            # 写入输出文件
            with open(output_path, 'w', encoding='utf-8') as f:
                if format == "json":
                    json.dump(structured_data, f, ensure_ascii=False, indent=2)
                elif format == "md":
                    # Markdown格式输出 - 简洁目录
                    self._write_markdown_format(structured_data, f)
                else:
                    # 文本格式输出
                    self._write_text_format(structured_data, f)
            
            print(f"转换完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"转换失败: {str(e)}")
            return False
    
    def _write_text_format(self, data: Dict[str, Any], file_handle) -> None:
        """以文本格式写入结果"""
        # 写入标题
        if data["headings"]:
            file_handle.write("=== 标题 ===\n")
            for heading in data["headings"]:
                level = heading["attributes"].get("level", "1")
                file_handle.write(f"{'#' * int(level)} {heading['text']}\n")
            file_handle.write("\n")
        
        # 写入列表
        if data["lists"]:
            file_handle.write("=== 列表项 ===\n")
            current_type = None
            for item in data["lists"]:
                item_type = item["attributes"].get("type", "")
                if item_type != current_type:
                    if current_type:
                        file_handle.write("\n")
                    current_type = item_type
                
                if item_type == "ordered_list":
                    order = item["attributes"].get("order", "1")
                    file_handle.write(f"{order}. {item['text']}\n")
                else:
                    file_handle.write(f"- {item['text']}\n")
            file_handle.write("\n")
        
        # 写入代码块
        if data["code_blocks"]:
            file_handle.write("=== 代码块 ===\n")
            for code in data["code_blocks"]:
                language = code["attributes"].get("language", "")
                file_handle.write(f"```{language}\n")
                file_handle.write(f"{code['text']}\n")
                file_handle.write("```\n\n")
        
        # 写入段落
        if data["paragraphs"]:
            file_handle.write("=== 段落 ===\n")
            for para in data["paragraphs"]:
                file_handle.write(f"{para['text']}\n\n")

    def _write_markdown_format(self, data: Dict[str, Any], file_handle) -> None:
        """以Markdown格式写入简洁目录"""
        # 只输出标题，生成简洁的目录结构，限制层级深度（最大到###）
        if data["headings"]:
            for heading in data["headings"]:
                level = min(int(heading["attributes"].get("level", "1")), 3)  # 限制最大层级为###
                file_handle.write(f"{'#' * level} {heading['text']}\n")
        else:
            file_handle.write("# 目录\n")
            file_handle.write("(未检测到标题结构)\n")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Markdown文档结构化信息提取工具')
    parser.add_argument('input_file', help='输入的Markdown文件路径')
    parser.add_argument('-o', '--output', help='输出文件名')
    parser.add_argument('-f', '--format', choices=['json', 'text', 'md'], default='json',
                       help='输出格式: json (默认), text 或 md (简洁目录)')
    parser.add_argument('--api-key', help='Langextract API密钥')
    
    args = parser.parse_args()
    
    # 处理输入路径
    input_path = Path(args.input_file)
    
    # 执行转换
    try:
        converter = MD2TopConverter()
        if args.api_key:
            converter.extractor.api_key = args.api_key
        
        success = converter.convert(
            str(input_path), 
            args.output,
            args.format
        )
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()