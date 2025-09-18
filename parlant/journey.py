# aippt/parlant/journey.py
# -*- coding: utf-8 -*-
"""
旅程逻辑（优化版）
- 严格JSON Schema校验（Pydantic）
- System Prompt 注入 style/glossary + 多重“只输出JSON”护栏
- JSON提取/修复更鲁棒
- 智谱API直连：带指数退避重试
- 可观测性：返回版本/风格/术语计数

依赖：httpx、python-dotenv、pydantic
"""
from __future__ import annotations
import os
import re
import json
import math
import asyncio
from typing import Dict, Any, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator
from dotenv import load_dotenv

from tools import (
    load_plain_text,
    validate_blocks,
    export_design_json,
    truncate_to_limit,
)
from style import get_styleguide, get_glossary

VERSION = "0.2.0"

# --- Parlant（可选） ---
_PARLANT_AVAILABLE = True
try:
    import parlant.sdk as p
except Exception:
    _PARLANT_AVAILABLE = False


# ------------------------
# 配置与系统提示拼装
# ------------------------
def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)

def build_system_prompt() -> str:
    style = get_styleguide()
    glossary = get_glossary()
    tone = style.get("tone", "")
    rules = "；".join(style.get("rules", []))
    glossary_str = "；".join([f"{g['term']}={g['definition']}" for g in glossary])

    guardrails = (
        "务必严格遵守：仅输出合法 JSON（一个对象），不要输出任何解释、前后缀文字、"
        "代码围栏、注释或多余字符。不要输出Markdown。"
    )

    schema_hint = (
        "JSON键必须为：document_title、page_title、layout_hint、blocks；"
        "blocks为数组，每项包含title与content两个键。"
    )

    sys = (
        "你是AIPPT页面设计助手，请严格按照以下风格与约束生成内容：\n"
        f"【语气】{tone}\n"
        f"【规则】{rules}\n"
        f"【术语表】{glossary_str}\n\n"
        "任务：根据输入的 document_title 与 page_data，输出**仅包含 JSON 的结构化结果**：\n"
        "{document_title, page_title, layout_hint, blocks:[{title, content}...]}\n"
        "硬性约束：\n"
        "1) 全中文；2) blocks 数量在 3–6 之间；3) 每个 content ≤ 150 中文字符；\n"
        "4) 语言风格专业、简洁、科技商务；5) 要点去重，避免同义重复。\n"
        "内容要求：\n"
        "- title必须使用原文中的完整准确名称，如'全流程工作质效管理平台'而非简化版本\n"
        "- content必须包含具体的技术实现和功能细节，如'通过4个AI Agent实现智能立项、岗位推荐等'\n"
        "- 每个content应尽量接近150字限制，包含关键词如'AI Agent'、'PDCA闭环'等专业术语\n"
        "- 保留原文的技术细节和实现方式，不要泛化描述\n"
        f"{guardrails}\n{schema_hint}"
    )
    return sys


# ------------------------
# 严格 Schema 定义
# ------------------------
class Block(BaseModel):
    title: str = Field(..., description="块标题，建议 ≤ 15 字")
    content: str = Field(..., description="块内容，必须 ≤ 150 字")

    @field_validator("title")
    @classmethod
    def _title_clean(cls, v: str) -> str:
        return v.strip()

    @field_validator("content")
    @classmethod
    def _content_clean(cls, v: str) -> str:
        return v.strip()

class DesignDoc(BaseModel):
    document_title: str
    page_title: str
    layout_hint: str
    blocks: List[Block]

# 详细示例（附在 user 提示尾部，强化稳输出）
USER_JSON_SCHEMA_HINT = (
    "JSON示例（注意content的详细程度）："
    "{\"document_title\":\"4.开发四大AI赋能的管控数字化应用\",\"page_title\":\"四大AI赋能的管控数字化应用\",\"layout_hint\":\"grid-2-2\","
    "\"blocks\":[{\"title\":\"全流程工作质效管理平台\",\"content\":\"通过项目化管理实现重点任务PDCA闭环，利用4个AI Agent赋能智能立项、岗位推荐、任务分解与预评价。\"},"
    "{\"title\":\"智能会议管理系统\",\"content\":\"优化会议全流程，核心是通过AI Agent根据语音转写自动生成会议纪要，并无缝推送到质效管理平台。\"}]}"
)


# ------------------------
# JSON 提取 / 修复
# ------------------------
JSON_OBJ_RE = re.compile(r"\{.*\}", re.S)

def extract_json_str(s: str) -> str:
    """从任意包裹文本中提取第一个JSON对象（去掉代码围栏等噪声）"""
    # 去掉```json/```包裹
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip(), flags=re.I|re.M)
    m = JSON_OBJ_RE.search(s)
    return m.group(0) if m else s.strip()

def try_parse_json(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        # 常见小错误修补：尾随逗号、非标准引号等（尽量保守）
        fixed = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
        fixed = re.sub(r",\s*}", "}", fixed)
        fixed = re.sub(r",\s*]", "]", fixed)
        try:
            return json.loads(fixed)
        except Exception:
            return None


# ------------------------
# 直连智谱 API（带重试）
# ------------------------
async def zhipu_chat_completions(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    max_retries: int = 3,
    timeout_s: float = 60.0,
) -> str:
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt + "\n" + USER_JSON_SCHEMA_HINT},
        ],
        "temperature": temperature,
        "stream": False,
    }
    backoff = 0.8
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        for i in range(max_retries):
            try:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                if i == max_retries - 1:
                    raise
                await asyncio.sleep(backoff * (2 ** i))
        return ""  # 理论到不了


# ------------------------
# Journey 主流程
# ------------------------
class PageDesignJourney:
    def __init__(self) -> None:
        load_dotenv()
        self.min_blocks = int(_env("MIN_BLOCKS", "3"))
        self.max_blocks = int(_env("MAX_BLOCKS", "6"))
        self.max_len = int(_env("MAX_CONTENT_LEN_CN", "50"))
        self.layout_hint_default = _env("DEFAULT_LAYOUT_HINT", "grid-2-2")

        self.base_url = _env("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        self.api_key = _env("ZHIPUAI_API_KEY", "")
        self.model = _env("MODEL_NAME", "glm-4.5-flash")

        self.system_prompt = build_system_prompt()
        self.style_count = len(get_styleguide().get("rules", []))
        self.glossary_count = len(get_glossary())

    async def _via_parlant(self, prompt: str) -> str:
        async with p.Server(llm={
            "provider": "openai",
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "temperature": 0.1
        }) as server:
            agent = await server.create_agent(
                name="AIPPT页面设计助手",
                description="从输入构造单页PPT的设计JSON，严格遵守约束。"
            )
            # 直接把系统+用户合并（Parlant简化用法）
            full = f"{self.system_prompt}\n\n{prompt}\n{USER_JSON_SCHEMA_HINT}"
            resp = await agent.chat(full)
            return getattr(resp, "text", "")

    async def _via_direct(self, prompt: str) -> str:
        return await zhipu_chat_completions(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            temperature=0.1,
        )

    def _fallback(self, document_title: str, page_data: str) -> Dict[str, Any]:
        # 按中文标点切段，选取信息密度高的前3~4段
        segs = re_split_multi(page_data)
        segs = [s for s in segs if s]
        if not segs:
            segs = [document_title]
        segs = segs[:4]
        blocks = []
        for s in segs:
            blocks.append({
                "title": truncate_to_limit(s, 8),
                "content": truncate_to_limit(s, self.max_len),
            })
        return {
            "document_title": document_title,
            "page_title": truncate_to_limit(f"{document_title} · 摘要", 24),
            "layout_hint": self.layout_hint_default,
            "blocks": blocks,
        }

    def _coerce_and_validate(self, draft: Dict[str, Any], document_title: str,
                             layout_hint: Optional[str]) -> Dict[str, Any]:
        # 字段兜底
        if not draft.get("document_title"):
            draft["document_title"] = document_title
        if not draft.get("page_title"):
            draft["page_title"] = truncate_to_limit(f"{document_title} · 页面", 24)
        draft["layout_hint"] = layout_hint or draft.get("layout_hint") or self.layout_hint_default

        # 二次兜底与清洗
        blocks = draft.get("blocks", [])
        blocks = validate_blocks(
            blocks=blocks,
            max_len=self.max_len,
            min_blocks=self.min_blocks,
            max_blocks=self.max_blocks,
            document_title=document_title,
        )
        norm = {
            "document_title": draft["document_title"].strip(),
            "page_title": draft["page_title"].strip(),
            "layout_hint": draft["layout_hint"].strip(),
            "blocks": blocks,
        }

        # 用 Pydantic 严格校验（可去除多余字段）
        try:
            obj = DesignDoc(**norm)
            return json.loads(obj.model_dump_json())
        except ValidationError:
            # 理论上经过 validate_blocks 不会出错；若遇到，回退最小骨架
            return {
                "document_title": draft["document_title"],
                "page_title": draft["page_title"],
                "layout_hint": draft["layout_hint"],
                "blocks": blocks,
            }

    async def run(self, data_file: str, design_file: str, layout_hint: Optional[str] = None) -> Dict[str, Any]:
        kv = load_plain_text(data_file)
        document_title = kv.get("document_title", "").strip()
        page_data = kv.get("page_data", "").strip()

        user_prompt = (
            f"document_title: {document_title}\n"
            f"page_data: {page_data}\n"
            f"请仅输出JSON，符合约束，layout_hint优先使用：{layout_hint or self.layout_hint_default}"
        )

        raw = ""
        if _PARLANT_AVAILABLE and self.api_key:
            try:
                raw = await self._via_parlant(user_prompt)
            except Exception:
                raw = ""

        if not raw and self.api_key:
            try:
                raw = await self._via_direct(user_prompt)
            except Exception:
                raw = ""

        if not raw:
            draft = self._fallback(document_title, page_data)
        else:
            s = extract_json_str(raw)
            parsed = try_parse_json(s)
            draft = parsed if isinstance(parsed, dict) else self._fallback(document_title, page_data)

        result = self._coerce_and_validate(draft, document_title, layout_hint)

        # 写盘
        export_design_json({
            **result,
            "constraints": {
                "min_blocks": self.min_blocks,
                "max_blocks": self.max_blocks,
                "max_content_len_cn": self.max_len,
            }
        }, design_file)

        # 返回带可观测信息，便于前端确认风格加载情况
        return {
            "ok": True,
            "version": VERSION,
            "model": self.model,
            "style_rules": self.style_count,
            "glossary_terms": self.glossary_count,
            "layout_hint": result.get("layout_hint"),
            "design": result,
            "design_file": design_file,
        }


# ------------------------
# 小工具
# ------------------------
def re_split_multi(text: str) -> List[str]:
    text = (text or "").replace("\n", "。")
    parts = re.split(r"[。；;！!？?\|，、]", text)
    return [p.strip() for p in parts if p and p.strip()]
