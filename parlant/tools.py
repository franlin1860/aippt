# aippt/parlant/tools.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import os
import re
from typing import List, Dict, Any

def count_cn_len(s: str) -> int:
    return len((s or "").strip())

def truncate_to_limit(text: str, limit: int) -> str:
    t = (text or "").strip()
    # 去多余空白
    t = re.sub(r"\s+", "", t)
    if count_cn_len(t) <= limit:
        return t
    t = t[:limit]
    # 去尾部标点
    t = re.sub(r"[，、；。,.!;:]+$", "", t)
    return t

def parse_kv_lines(s: str) -> Dict[str, str]:
    out = {}
    for line in (s or "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out

def load_plain_text(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"data_file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    kv = parse_kv_lines(raw)
    if "document_title" not in kv:
        raise ValueError("Missing key: document_title")
    if "page_data" not in kv:
        kv["page_data"] = ""
    return kv

def dedup_blocks(blocks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out = []
    for b in blocks:
        key = (b.get("title", "").strip(), (b.get("content", "")[:10]).strip())
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out

def ensure_titles(blocks: List[Dict[str, str]], fallbacks: List[str]) -> None:
    i = 0
    for b in blocks:
        if not b.get("title"):
            b["title"] = fallbacks[i % len(fallbacks)]
            i += 1

def validate_blocks(
    blocks: List[Dict[str, str]],
    max_len: int,
    min_blocks: int,
    max_blocks: int,
    document_title: str
) -> List[Dict[str, str]]:
    cleaned = []
    for b in blocks or []:
        title = truncate_to_limit(b.get("title", ""), 15)  # 标题限制15字
        content = truncate_to_limit(b.get("content", ""), max_len)
        if not title and not content:
            continue
        cleaned.append({"title": title or "要点", "content": content})

    cleaned = dedup_blocks(cleaned)

    if len(cleaned) > max_blocks:
        cleaned.sort(key=lambda x: len(x.get("content", "")), reverse=True)
        cleaned = cleaned[:max_blocks]

    fallback_titles = ["问题痛点", "解决思路", "核心能力", "落地路径", "预期价值", "风险与对策"]
    if len(cleaned) < min_blocks:
        needed = min_blocks - len(cleaned)
        for i in range(needed):
            cleaned.append({
                "title": fallback_titles[i % len(fallback_titles)],
                "content": truncate_to_limit(document_title, max_len)
            })

    ensure_titles(cleaned, fallback_titles)

    for b in cleaned:
        b["content"] = truncate_to_limit(b["content"], max_len)

    return cleaned

def export_design_json(data: Dict[str, Any], out_path: str) -> None:
    parent = os.path.dirname(out_path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
