# aippt/parlant/style.py
# -*- coding: utf-8 -*-
"""
风格与术语表定义（最小实现）

- Styleguide: 全局风格规范
- Glossary: 专有术语及其定义，保证表达一致
"""

STYLEGUIDE = {
    "language": "zh-CN",
    "tone": "专业、简洁、科技商务",
    "rules": [
        "所有输出必须为简体中文",
        "优先使用短句，结论先行，补充随后",
        "避免使用夸张营销词（如'颠覆''极致'）",
        "禁止输出英文、emoji 或多余符号",
        "每个 content 字数不得超过 150 个中文字符",
        "title应保持原文术语的准确性和完整性",
        "content应包含核心功能描述和关键技术细节",
        "充分利用字数限制，提供高信息密度的内容"
    ],
    "structure": {
        "page": "标题 → 副标题 → 3-6 个要点块",
        "block": "title + content，title 控制在 15 字以内"
    }
}

GLOSSARY = [
    {"term": "模板库", "definition": "标准化页面结构与样式集合"},
    {"term": "自动排版", "definition": "基于规则或模型的文本块布局与层级分配"},
    {"term": "一致性", "definition": "保证跨页/跨文档的术语和风格统一"},
    {"term": "数据驱动", "definition": "利用输入数据自动生成或优化内容"},
    {"term": "复用率", "definition": "内容在不同场景下的可重复使用程度"},
    {"term": "AI Agent", "definition": "人工智能代理，大模型与业务应用的智能桥梁"},
    {"term": "PDCA闭环", "definition": "计划-执行-检查-改进的管理循环"},
    {"term": "穿透式管理", "definition": "跨层级、跨部门的一体化综合管控"}
]

def get_styleguide() -> dict:
    """返回全局风格规范"""
    return STYLEGUIDE

def get_glossary() -> list:
    """返回术语表"""
    return GLOSSARY