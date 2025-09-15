# 通用型四阶段AI演示文稿智能设计框架

基于JSON数据合同的四阶段PPT设计自动化框架，将AI驱动的PPT设计流程分解为四个独立的、可编程的阶段。

## 框架概述

### 四个设计阶段

1. **策略与布局选择** - 深度理解输入文本，匹配最合适的演示模板
2. **内容结构化与精炼** - 依据选定模板，对原始文本进行专业编辑和重组
3. **视觉增强与版式规格定义** - 将结构化内容转化为具体的视觉设计方案
4. **质量与一致性控制** - 从全局视角审查设计方案，发现潜在问题

## 安装要求

```bash
pip install google-generativeai
```

## 使用方法

### 1. 准备输入文件

支持两种输入格式：

**JSON格式** (`input.json`):
```json
{
  "pages": [
    {
      "title": "页面标题",
      "content": "页面内容文本"
    }
  ]
}
```

**文本格式** (`input.txt`):
```
document_title: 页面标题
page_data: 页面内容文本
```

### 2. 运行框架

**JSON格式输入:**
```bash
python ppt2design.py --api-key YOUR_GEMINI_API_KEY --input input.json --output result.json
```

**文本格式输入:**
```bash
python ppt2design.py --api-key YOUR_GEMINI_API_KEY --input input.txt --text-format --output result.json
```

或者自动检测文本格式:
```bash
python ppt2design.py --api-key YOUR_GEMINI_API_KEY --input input.txt --output result.json
```

### 3. 参数说明

- `--api-key`: OpenAI API密钥（必需）
- `--input`: 输入JSON文件路径（必需）
- `--output`: 输出JSON文件路径（可选，默认为output.json）

## 输出格式

框架输出包含四个阶段的完整结果：

```json
{
  "pages": [
    {
      "stage1": {
        "step1_output": {
          "layout_choice": "TEMPLATE_CONCEPTUAL_MODEL",
          "confidence_score": 0.95,
          "reasoning": "分析说明..."
        }
      },
      "stage2": {
        "step2_output": {
          "page_title": "优化后的标题",
          "content": {...}
        }
      },
      "stage3": {
        "step3_output": {
          "image_search_keywords": "关键词1, 关键词2",
          "icon_suggestions": [...],
          "layout_constraints": {...},
          "color_palette_suggestion": "配色方案"
        }
      }
    }
  ],
  "quality_control": {
    "step4_output": {
      "overall_consistency_score": 0.9,
      "consistency_issues": [...]
    }
  }
}
```

## 支持的模板类型

- `TEMPLATE_SUMMARY` - 摘要模板
- `TEMPLATE_BLOCKS` - 区块模板  
- `TEMPLATE_FLOW` - 流程模板
- `TEMPLATE_COMPARE` - 比较模板
- `TEMPLATE_DATA` - 数据模板
- `TEMPLATE_CONCEPTUAL_MODEL` - 概念模型模板

## 示例

查看 `example_input.json` 文件作为输入示例，运行后生成完整的设计方案。

## 注意事项

1. 需要有效的Google Gemini API密钥（在.env文件中配置）
2. 输入文本应为中文内容以获得最佳效果
3. 框架会调用Gemini Pro模型
4. 输出结果为JSON格式，可进一步集成到PPT生成工具中

## 许可证

MIT License