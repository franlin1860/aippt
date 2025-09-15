#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用型四阶段AI演示文稿智能设计框架实现
基于JSON数据合同的四阶段PPT设计流程
"""

import json
import argparse
import sys
import os
import requests
from typing import Dict, List, Any, Optional

class PPTDesignFramework:
    """四阶段AI演示文稿设计框架主类"""
    
    def __init__(self, api_key: str):
        """初始化框架"""
        self.api_key = api_key
        self.model_name = "glm-4.5-flash"
        # 使用智谱AI API
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 检查API密钥格式
        if not api_key or '.' not in api_key:
            print("警告: 智谱AI API密钥格式可能不正确，应该包含点号分隔符")
        
        # 模板定义
        self.templates = {
            "TEMPLATE_SUMMARY": "摘要模板 - 用于可提炼为几个关键点的内容",
            "TEMPLATE_BLOCKS": "区块模板 - 用于描述多个并行项目的内容",
            "TEMPLATE_FLOW": "流程模板 - 用于描述序列、过程、时间线或步骤",
            "TEMPLATE_COMPARE": "比较模板 - 用于明确或隐含比较两个或多个项目",
            "TEMPLATE_DATA": "数据模板 - 用于数字、百分比、趋势或需要图表的内容",
            "TEMPLATE_CONCEPTUAL_MODEL": "概念模型模板 - 用于抽象的战略内容"
        }
        
        # 布局类型定义
        self.layout_types = {
            "vertical_list": "垂直列表",
            "horizontal_list": "水平列表",
            "grid_2x2": "2x2网格",
            "grid_3x1": "3x1网格", 
            "cards_freeform": "自由卡片布局",
            "table_compare": "表格比较",
            "side_by_side_panels": "并排面板",
            "horizontal_timeline": "水平时间线",
            "vertical_steps": "垂直步骤",
            "circular_flow": "循环流程",
            "quadrant_diagram_with_arrows": "带箭头的四象限图",
            "pyramid_diagram": "金字塔图",
            "swot_matrix": "SWOT矩阵"
        }
    
    def call_llm(self, prompt: str, system_message: str) -> Dict:
        """调用智谱AI API"""
        try:
            data = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # 提取JSON内容
            if content.startswith('```json'):
                content = content[7:-3].strip()
            elif content.startswith('```'):
                content = content[3:-3].strip()
                
            return json.loads(content)
            
        except Exception as e:
            print(f"智谱AI API调用错误: {e}")
            return {}
    
    def stage1_strategy_layout(self, page_title: str, reference_content: str) -> Dict:
        """阶段一：策略与布局选择"""
        system_message = """You are a Senior Presentation Strategist. Your expertise lies in analyzing raw text to determine the most effective visual and structural way to present it on a slide."""
        
        prompt = f"""
Analyze the provided `page_title` and `reference_content`. Based on your analysis, you must select the single most suitable layout template from the list below. You must also provide a confidence score for your choice and a brief reasoning.

AVAILABLE TEMPLATES:
- TEMPLATE_SUMMARY: Use for content that can be distilled into a few key, distinct points or takeaways.
- TEMPLATE_BLOCKS: Use for content that describes several parallel items, such as different products, features, or categories.
- TEMPLATE_FLOW: Use for content that describes a sequence, process, timeline, or series of steps.
- TEMPLATE_COMPARE: Use for content that explicitly or implicitly compares two or more items (e.g., pros/cons, before/after, problem/solution).
- TEMPLATE_DATA: Use for content that is heavily focused on numbers, percentages, trends, or requires a chart/graph for effective communication.
- TEMPLATE_CONCEPTUAL_MODEL: Use for abstract, strategic content that fits a known consulting model (e.g., 4-quadrant matrix, SWOT, pyramid, cycle).

INPUT DATA:
- page_title: {page_title}
- reference_content: {reference_content}

You MUST respond with a single, valid JSON object. Do not add any text before or after the JSON object. The JSON object must strictly adhere to the following structure:
{{
  "step1_output": {{
    "layout_choice": "string",
    "confidence_score": "float (0.0 to 1.0)",
    "reasoning": "string"
  }}
}}
"""
        return self.call_llm(prompt, system_message)
    
    def stage2_content_structured(self, layout_choice: str, page_title: str, reference_content: str) -> Dict:
        """阶段二：内容结构化与精炼"""
        system_message = """You are an Expert Content Creator and Information Architect. Your task is to transform raw text into concise, structured content perfectly suited for a presentation slide, based on a predefined template."""
        
        # 为不同模板类型提供具体的格式要求
        template_formats = {
            "TEMPLATE_SUMMARY": """{
  "step2_output": {
    "page_title": "优化后的页面标题",
    "template_type": "TEMPLATE_SUMMARY",
    "content": {
      "key_points": [
        {
          "point": "关键点1的详细描述"
        },
        {
          "point": "关键点2的详细描述"
        },
        {
          "point": "关键点3的详细描述"
        }
      ]
    }
  }
}""",
            "TEMPLATE_BLOCKS": """{
  "step2_output": {
    "page_title": "优化后的页面标题",
    "template_type": "TEMPLATE_BLOCKS",
    "content": {
      "content_blocks": [
        {
          "sub_heading": "区块1的小标题",
          "content": "区块1的详细内容描述"
        },
        {
          "sub_heading": "区块2的小标题",
          "content": "区块2的详细内容描述"
        },
        {
          "sub_heading": "区块3的小标题",
          "content": "区块3的详细内容描述"
        }
      ]
    }
  }
}"""
        }
        
        format_guide = template_formats.get(layout_choice, """{
  "step2_output": {
    "page_title": "优化后的页面标题",
    "template_type": "布局模板名称",
    "content": {
      // 根据模板类型定义具体结构
    }
  }
}""")
        
        prompt = f"""
Based on the `layout_choice` provided, you will process the `reference_content`. You will refine the text, potentially optimize the `page_title`, and structure the output according to the specific JSON format for that template. Ensure all text is clear, concise, and professional.

TEMPLATE REQUIREMENTS:
- For TEMPLATE_SUMMARY: Extract 3-5 key points, each as a separate concise statement
- For TEMPLATE_BLOCKS: Identify 2-4 parallel content blocks, each with a clear sub-heading and detailed content

REQUIRED JSON FORMAT for {layout_choice}:
{format_guide}

INPUT DATA:
- layout_choice: {layout_choice}
- page_title: {page_title}
- reference_content: {reference_content}

You MUST generate a single, valid JSON object strictly following the specified format for the chosen template. Include the template_type field in the output.
"""
        return self.call_llm(prompt, system_message)
    
    def stage3_visual_enhancement(self, step2_output: Dict) -> Dict:
        """阶段三：视觉增强与版式规格定义"""
        system_message = """You are a Creative Director and Visual Designer. Your task is to take structured slide content and define a complete set of visual specifications for it."""
        
        step2_json = json.dumps(step2_output, ensure_ascii=False)
        
        prompt = f"""
Analyze the provided structured content from `step2_output`. Based on this content, you must generate a set of visual design specifications. This includes relevant search keywords, icon suggestions for key items, a specific layout instruction, and a color palette suggestion.

LAYOUT SPECIFICATION (`content_type`):
Choose a specific visual layout ID that best represents the content structure:
- For lists: `vertical_list`, `horizontal_list`
- For blocks: `grid_2x2`, `grid_3x1`, `cards_freeform`
- For comparisons: `table_compare`, `side_by_side_panels`
- For flows: `horizontal_timeline`, `vertical_steps`, `circular_flow`
- For models: `quadrant_diagram_with_arrows`, `pyramid_diagram`, `swot_matrix`

INPUT DATA:
- step2_output: {step2_json}

You MUST respond with a single, valid JSON object. Do not add any text before or after the JSON object. The JSON object must strictly adhere to the following structure:
{{
  "step3_output": {{
    "image_search_keywords": "string (comma-separated)",
    "icon_suggestions": [
      {{
        "item": "string (matches a sub_heading or key point)",
        "icon_name": "string (comma-separated, e.g., 'strategy, brain, lightbulb')"
      }}
    ],
    "layout_constraints": {{
      "content_type": "string (one of the specified layout IDs)",
      "axis_labels": {{ 
        "x_axis": "string (optional)",
        "y_axis": "string (optional)"
      }},
      "path_flow": "string (optional, e.g., '1 -> 2, 1 -> 3, 2&3 -> 4')"
    }},
    "color_palette_suggestion": "string (e.g., 'professional_blue_grey', 'vibrant_tech_green')"
  }}
}}
"""
        return self.call_llm(prompt, system_message)
    
    def stage4_quality_control(self, page_metadata_list: List[Dict]) -> Dict:
        """阶段四：质量与一致性控制"""
        system_message = """You are a Quality Assurance Director for presentations. Your job is to review the metadata of an entire presentation to ensure its overall quality, consistency, and professionalism."""
        
        metadata_json = json.dumps(page_metadata_list, ensure_ascii=False)
        
        prompt = f"""
Analyze the provided `page_metadata_list`, which contains summary information for each slide. Identify any potential issues related to consistency and quality. If there are no issues, return an empty list.

REVIEW CHECKLIST:
1. Content Granularity: Are the titles similar in length and style? Is there a slide with a significantly higher `item_count` than others?
2. Titling Convention: Do any titles contain artifacts like document numbering (e.g., "1.", "4.2") that should be removed?
3. Flow & Logic: Does the sequence of `layout_choice` make sense?

INPUT DATA:
- page_metadata_list: {metadata_json}

You MUST respond with a single, valid JSON object. Do not add any text before or after the JSON object. The JSON object must strictly adhere to the following structure:
{{
  "step4_output": {{
    "overall_consistency_score": "float (0.0 to 1.0)",
    "consistency_issues": [
      {{
        "page_index": "integer",
        "issue": "string (A clear description of the problem)",
        "suggestion": "string (A clear, actionable recommendation)"
      }}
    ]
  }}
}}
"""
        return self.call_llm(prompt, system_message)
    
    def process_single_page(self, page_title: str, reference_content: str) -> Dict:
        """处理单个页面（阶段1-3）"""
        print(f"处理页面: {page_title}")
        
        # 阶段1：策略与布局选择
        print("阶段1: 策略与布局选择...")
        stage1_result = self.stage1_strategy_layout(page_title, reference_content)
        if not stage1_result:
            return {}
        
        layout_choice = stage1_result["step1_output"]["layout_choice"]
        print(f"  选择的布局: {layout_choice}")
        
        # 阶段2：内容结构化
        print("阶段2: 内容结构化...")
        stage2_result = self.stage2_content_structured(layout_choice, page_title, reference_content)
        if not stage2_result:
            return {}
        
        # 阶段3：视觉增强
        print("阶段3: 视觉增强...")
        stage3_result = self.stage3_visual_enhancement(stage2_result["step2_output"])
        if not stage3_result:
            return {}
        
        return {
            "stage1": stage1_result,
            "stage2": stage2_result,
            "stage3": stage3_result
        }
    
    def process_presentation(self, pages: List[Dict]) -> Dict:
        """处理整个演示文稿"""
        results = []
        page_metadata = []
        
        # 处理每个页面
        for i, page in enumerate(pages):
            result = self.process_single_page(page["title"], page["content"])
            if result:
                results.append(result)
                
                # 收集元数据用于阶段4
                item_count = len(result["stage2"]["step2_output"].get("content", {}).get("content_blocks", []))
                page_metadata.append({
                    "page_index": i,
                    "page_title": result["stage2"]["step2_output"].get("page_title", ""),
                    "layout_choice": result["stage1"]["step1_output"]["layout_choice"],
                    "item_count": item_count
                })
        
        # 阶段4：质量控制
        print("阶段4: 质量控制...")
        stage4_result = self.stage4_quality_control(page_metadata)
        
        return {
            "pages": results,
            "quality_control": stage4_result
        }


def parse_text_file(file_path: str) -> Dict:
    """解析文本格式的输入文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析文本格式
        document_title = None
        page_data = None
        
        lines = content.split('\n')
        for line in lines:
            if line.startswith('document_title:'):
                document_title = line.replace('document_title:', '').strip()
            elif line.startswith('page_data:'):
                page_data = line.replace('page_data:', '').strip()
        
        if not document_title or not page_data:
            raise ValueError("文本文件格式不正确，必须包含document_title和page_data")
        
        return {
            "pages": [
                {
                    "title": document_title,
                    "content": page_data
                }
            ]
        }
        
    except Exception as e:
        print(f"解析文本文件错误: {e}")
        return {"pages": []}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='通用型四阶段AI演示文稿智能设计框架')
    parser.add_argument('input_file', help='输入文件路径（支持JSON或文本格式）')
    parser.add_argument('--api-key', help='智谱AI API密钥（可选，优先使用环境变量）')
    parser.add_argument('--output', help='输出JSON文件路径（可选，默认自动生成）')
    
    args = parser.parse_args()
    
    try:
        # 获取API密钥（优先使用环境变量）
        api_key = args.api_key or os.environ.get('ZHIPUAI_API_KEY')
        if not api_key:
            print("错误: 请提供智谱AI API密钥（通过--api-key参数或ZHIPUAI_API_KEY环境变量）")
            sys.exit(1)
        
        # 自动生成输出文件名
        if args.output:
            output_file = args.output
        else:
            # 从输入文件名生成结果文件名（如：input.txt → input_result.json）
            base_name = os.path.splitext(args.input_file)[0]
            output_file = f"{base_name}_result.json"
        
        # 读取输入文件
        if args.input_file.endswith('.txt'):
            input_data = parse_text_file(args.input_file)
        else:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        
        if not input_data.get("pages"):
            print("错误: 输入文件不包含有效的页面数据")
            sys.exit(1)
        
        # 初始化框架
        framework = PPTDesignFramework(api_key)
        
        # 处理演示文稿
        result = framework.process_presentation(input_data["pages"])
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"处理完成！结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()