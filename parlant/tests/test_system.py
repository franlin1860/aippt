# aippt/parlant/tests/test_system.py
# -*- coding: utf-8 -*-
"""
系统级测试（端到端）
- 直接调用 PageDesignJourney().run(...)，不走子进程
- 覆盖三类输入：极短/常规/超长
- 校验：结构、块数量、长度约束、字段完整性
"""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from journey import PageDesignJourney

DATA_DIR = Path("data")
OUT_DIR = Path("out")

CASES = [
    # (输入文件名, 输出文件名, 期望最小块数, 期望最大块数)
    ("example_short.txt",  "out_short.json",  3, 6),
    ("example_normal.txt", "out_normal.json", 3, 6),
    ("example_long.txt",   "out_long.json",   3, 6),
]

@pytest.mark.parametrize("in_name,out_name,min_blocks,max_blocks", CASES)
@pytest.mark.asyncio
async def test_end_to_end(in_name: str, out_name: str, min_blocks: int, max_blocks: int):
    data_file = DATA_DIR / in_name
    # 输出到实际的 out/ 目录
    OUT_DIR.mkdir(exist_ok=True)
    out_file = OUT_DIR / out_name

    j = PageDesignJourney()
    res = await j.run(str(data_file), str(out_file))

    # 基本字段
    assert res["ok"] is True
    design = res["design"]
    assert "document_title" in design
    assert "page_title" in design
    assert "layout_hint" in design
    assert "blocks" in design

    # 块数量
    blocks = design["blocks"]
    assert isinstance(blocks, list)
    assert min_blocks <= len(blocks) <= max_blocks

    # 每块校验
    for b in blocks:
        assert "title" in b and "content" in b
        assert isinstance(b["title"], str) and isinstance(b["content"], str)
        # 长度约束（≤ 150 字）
        assert len(b["content"].strip()) <= 150

    # 文件已落盘
    assert out_file.exists()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert "constraints" in payload
    assert payload["constraints"]["max_content_len_cn"] == 150
