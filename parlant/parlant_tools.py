# aippt/parlant/parlant_tools.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from typing import Dict, Any, List
import parlant.sdk as p

from .tools import (
    load_plain_text as _load,
    validate_blocks as _validate,
    export_design_json as _export,
    truncate_to_limit,
)

@p.tool
async def load_plain_text(context: p.ToolContext, path: str) -> p.ToolResult:
    """
    读取输入txt，返回：
    {"document_title": "...", "page_data": "..."}
    """
    kv = _load(path)
    return p.ToolResult(kv)

@p.tool
async def validate_blocks_tool(
    context: p.ToolContext,
    blocks: list,
    max_len: int,
    min_blocks: int,
    max_blocks: int,
    document_title: str
) -> p.ToolResult:
    """
    对 LLM 生成的 blocks 进行强校验与修正，保证：
    - 数量在 [min_blocks, max_blocks] 内
    - 每条 content ≤ max_len
    - 标题/content 去空值/去重/截断
    """
    fixed = _validate(blocks, max_len, min_blocks, max_blocks, document_title)
    return p.ToolResult(fixed)

@p.tool
async def export_design_json_tool(context: p.ToolContext, data: dict, out_path: str) -> p.ToolResult:
    """
    将最终设计JSON写入目标文件
    """
    _export(data, out_path)
    return p.ToolResult({"ok": True, "out": out_path})

@p.tool
async def enforce_json_schema_hint(context: p.ToolContext) -> p.ToolResult:
    """
    返回简短JSON模式提示，便于在生成阶段内联引用。
    """
    hint = (
        "只输出JSON对象，键必须为：document_title、page_title、layout_hint、blocks；"
        "blocks为数组，每项含title与content；示例："
        "{\"document_title\":\"...\",\"page_title\":\"...\",\"layout_hint\":\"grid-2-2\","
        "\"blocks\":[{\"title\":\"...\",\"content\":\"...\"}]}"
    )
    return p.ToolResult(hint)
