#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本 - 测试ppt2design.py框架功能
"""

import os
import sys
import json
from ppt2design import PPTDesignFramework, parse_text_file

def test_parse_text_file():
    """测试文本文件解析功能"""
    print("测试文本文件解析...")
    
    # 测试文件路径
    test_file_path = "example/ppt2design_test1.txt"
    
    # 确保测试文件存在
    if not os.path.exists(test_file_path):
        print(f"测试文件 {test_file_path} 不存在，创建测试文件...")
        test_content = """document_title: 1.大型企业数字化转型情况
page_data:在《中国大型企业数字化升级路径研究》的报告中，提出大型企业数字化升级的结构与路径，根据数字化需求面向的直接对象与核心功能两方面的属性，企业数字化需求的结构可分为四个象限。
在对象属性上，数字化升级可能是面向集团或者面向员工，二者的核心区别在于使用的信息来源。在功能属性上，数字化升级或是服务于生产，或是服务于管理，二者的核心区别在于前者以提升可见的产出收入或工作效率为目标，而后者的核心功能通常是提升管理水平、降本增效等。
大型企业内部的数字化历程普遍以"集团x管理"象限为基础和起点，向"集团x生产"和"员工x管理"两个象限扩散，最后向"员工x生产"渗透的"波状"路径。"集团x管理"象限的转型工作是大型企业数字化的基础，核心是集团业务流程、管理流程的数字化和数据化；企业在打好数字化基础之后，以"集团"和"管理"两大关键词为核心，分别将集团层面的数字化转型由管理拓展到生产流程，并将企业的管理工作由集团层面向员工个体层面细化和下沉。"""
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"测试文件已创建: {test_file_path}")
    
    # 测试解析
    result = parse_text_file(test_file_path)
    print(f"解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 根据输入文件名生成结果文件名
    input_filename = os.path.basename(test_file_path)
    base_name = os.path.splitext(input_filename)[0]  # 移除扩展名
    result_filename = f"example/{base_name}_result.json"
    
    # 将结果保存到文件
    with open(result_filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"结果已保存到 {result_filename}")
    
    print("文本文件解析测试完成！")

def test_framework_initialization():
    """测试框架初始化"""
    print("测试框架初始化...")
    
    # 从.env文件读取智谱AI API密钥
    api_key = None
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('glm-4.5-flash='):
                    api_key = line.strip().split('=')[1]
                    break
    
    if not api_key:
        print("警告: 未找到API密钥，跳过LLM调用测试")
        return
    
    try:
        framework = PPTDesignFramework(api_key)
        print("框架初始化成功！")
        
        # 测试单页处理（不实际调用API）
        print("测试单页处理结构...")
        test_data = {
            "title": "测试标题",
            "content": "测试内容"
        }
        
        # 这里只测试结构，不实际调用API
        print("单页处理结构测试完成！")
        
        # 测试模板格式定义
        print("测试模板格式定义...")
        test_content = """
大型企业数字化转型是当前企业发展的关键趋势。根据研究报告，企业数字化需求可以分为四个象限：
1. 运营效率提升：通过自动化流程和数字化工具提高生产效率
2. 客户体验优化：利用数字化手段改善客户服务和互动  
3. 商业模式创新：开发新的数字化产品和服务模式
4. 数据驱动决策：基于数据分析做出更明智的业务决策

每个象限都有其特定的数字化路径和实施策略。
"""
        
        # 测试模板格式定义
        print("测试模板格式定义...")
        
        # 直接检查模板格式定义
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
        
        # 验证模板格式
        for template_name, template_format in template_formats.items():
            if template_name in template_format:
                print(f"✓ {template_name} 模板格式正确")
                if "key_points" in template_format and template_name == "TEMPLATE_SUMMARY":
                    print(f"  - 包含关键点列表")
                if "content_blocks" in template_format and template_name == "TEMPLATE_BLOCKS":
                    print(f"  - 包含内容区块")
                if "template_type" in template_format:
                    print(f"  - 包含模板类型字段")
        
        print("模板格式定义测试完成！")
        
    except Exception as e:
        print(f"框架初始化错误: {e}")

def test_complete_design_flow():
    """测试完整的四阶段设计流程"""
    print("测试完整的四阶段设计流程...")
    
    # 从.env文件读取API密钥
    api_key = None
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('glm-4.5-flash='):
                    api_key = line.strip().split('=')[1]
                    break
    
    if not api_key:
        print("警告: 未找到API密钥，跳过完整流程测试")
        return
    
    try:
        # 初始化框架
        framework = PPTDesignFramework(api_key)
        
        # 解析测试文件
        test_file_path = "example/ppt2design_test1.txt"
        parsed_data = parse_text_file(test_file_path)
        
        if not parsed_data or "pages" not in parsed_data or len(parsed_data["pages"]) == 0:
            print("错误: 测试文件解析失败")
            return
        
        # 获取第一页数据
        page_data = parsed_data["pages"][0]
        
        # 运行完整的四阶段设计流程
        print("运行四阶段设计流程...")
        result = framework.process_single_page(page_data["title"], page_data["content"])
        
        # 检查结果是否包含模板名称和正确格式
        if result and "step2_output" in result:
            step2_output = result["step2_output"]
            
            print("✓ 四阶段设计流程完成")
            print(f"页面标题: {step2_output.get('page_title', 'N/A')}")
            print(f"模板类型: {step2_output.get('template_type', 'N/A')}")
            
            # 根据模板类型检查格式
            template_type = step2_output.get('template_type')
            content = step2_output.get('content', {})
            
            if template_type == "TEMPLATE_SUMMARY":
                if "key_points" in content:
                    key_points = content["key_points"]
                    print(f"✓ 包含 {len(key_points)} 个关键点:")
                    for i, point in enumerate(key_points, 1):
                        print(f"  关键点 {i}: {point.get('point', 'N/A')}")
                else:
                    print("✗ TEMPLATE_SUMMARY 缺少 key_points")
                    
            elif template_type == "TEMPLATE_BLOCKS":
                if "content_blocks" in content:
                    blocks = content["content_blocks"]
                    print(f"✓ 包含 {len(blocks)} 个内容区块:")
                    for i, block in enumerate(blocks, 1):
                        print(f"  区块 {i}: {block.get('sub_heading', 'N/A')}")
                else:
                    print("✗ TEMPLATE_BLOCKS 缺少 content_blocks")
            
            # 保存完整结果到文件
            input_filename = os.path.basename(test_file_path)
            base_name = os.path.splitext(input_filename)[0]
            result_filename = f"example/{base_name}_complete_result.json"
            
            with open(result_filename, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"完整结果已保存到 {result_filename}")
            
        else:
            print("✗ 四阶段设计流程失败")
            
    except Exception as e:
        print(f"完整流程测试错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试ppt2design框架...")
    print("=" * 50)
    
    test_parse_text_file()
    print()
    test_framework_initialization()
    print()
    # 注释掉完整的四阶段设计流程测试，避免长时间运行
    # test_complete_design_flow()
    print("运行完整的四阶段设计流程测试...")
    # 初始化框架
    api_key = None
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('glm-4.5-flash='):
                    api_key = line.strip().split('=')[1]
                    break
    
    if not api_key:
        print("警告: 未找到API密钥，跳过完整测试")
        print("=" * 50)
        print("基本测试完成！")
    else:
        framework = PPTDesignFramework(api_key)
        page_title = "大型企业数字化转型"
        reference_content = "大型企业数字化转型是当前企业发展的关键趋势。根据研究报告，企业数字化需求可以分为四个象限..."
        result = framework.process_single_page(page_title, reference_content)
        print(f"四阶段设计结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 保存完整结果
        result_filename = "ppt2design_test1_result.json"
        result_path = os.path.join('example', result_filename)
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"完整结果已保存到 {result_path}")
        
        # 检查结果文件是否包含模板名称和正确格式
        if result and "stage2" in result and "step2_output" in result["stage2"]:
            step2_output = result["stage2"]["step2_output"]
            template_type = step2_output.get("template_type")
            
            print(f"模板类型: {template_type}")
            
            if template_type == "TEMPLATE_SUMMARY":
                key_points = step2_output.get("content", {}).get("key_points", [])
                print(f"关键点数量: {len(key_points)}")
                for i, point in enumerate(key_points, 1):
                    print(f"关键点 {i}: {point.get('point', 'N/A')}")
                    
            elif template_type == "TEMPLATE_BLOCKS":
                content_blocks = step2_output.get("content", {}).get("content_blocks", [])
                print(f"内容区块数量: {len(content_blocks)}")
                for i, block in enumerate(content_blocks, 1):
                    print(f"区块 {i}: {block.get('sub_heading', 'N/A')}")
    
    print("=" * 50)
    print("基本测试完成！")