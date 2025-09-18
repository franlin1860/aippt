# aippt/parlant/journey.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, re, json, asyncio
from typing import Dict, Any, List, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

from .tools import export_design_json, truncate_to_limit
from .style import get_styleguide, get_glossary
from .parlant_tools import (
    load_plain_text,
    validate_blocks_tool,
    export_design_json_tool,
    enforce_json_schema_hint,
)

VERSION = "0.3.0-parlant"

# —— Parlant 优先，若不可用再直连 ——
_PARLANT_AVAILABLE = True
try:
    import parlant.sdk as p
except Exception:
    _PARLANT_AVAILABLE = False

def _env(k: str, d: Optional[str] = None) -> Optional[str]:
    return os.getenv(k, d)

# —— 强Schema（最终仍由我们兜底，以免LLM偶发越界）——
class Block(BaseModel):
    title: str = Field(..., description="≤8字建议")
    content: str = Field(..., description="≤50字")

class DesignDoc(BaseModel):
    document_title: str
    page_title: str
    layout_hint: str
    blocks: List[Block]

# —— JSON提取（剥离围栏/噪声）——
def extract_json_str(s: str) -> str:
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", (s or "").strip(), flags=re.I|re.M)
    m = re.search(r"\{.*\}", s, re.S)
    return m.group(0) if m else s

def try_parse_json(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        s2 = (s or "").replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
        s2 = re.sub(r",\s*}", "}", s2)
        s2 = re.sub(r",\s*]", "]", s2)
        try:
            return json.loads(s2)
        except Exception:
            return None

# —— 直连智谱（回退路径）——
async def zhipu_chat(base_url: str, api_key: str, model: str, system: str, user: str) -> str:
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "system", "content": system},
                                            {"role": "user", "content": user}],
               "temperature": 0.1, "stream": False}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

# —— 构建系统提示（注入风格与术语）——
def build_system_prompt() -> str:
    style = get_styleguide()
    gloss = get_glossary()
    tone = style.get("tone", "")
    rules = "；".join(style.get("rules", []))
    gls = "；".join([f"{g['term']}={g['definition']}" for g in gloss])
    guard = "只许输出合法JSON对象，不要解释/Markdown/代码围栏/多余字符。"
    schema = "JSON键：document_title、page_title、layout_hint、blocks；blocks项含title与content。"
    return (
        "你是AIPPT页面设计助手。请根据输入生成单页PPT设计JSON，并严格遵守：\n"
        f"【语气】{tone}\n【规则】{rules}\n【术语表】{gls}\n"
        "硬性约束：全中文；blocks数量3–6；content≤50字；去重与简洁；科技商务风。\n"
        f"{guard}\n{schema}"
    )

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

    # —— Parlant 路径（强推荐）——
    async def _run_via_parlant(self, data_file: str, design_file: str, layout_hint: Optional[str]) -> Dict[str, Any]:
        async with p.Server(llm={
            "provider": "openai",
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "temperature": 0.1,
        }) as server:
            agent = await server.create_agent(
                name="AIPPT页面设计Agent",
                description="读取txt→生成设计JSON→校验→落盘，严格遵守JSON与长度约束。"
            )

            # 1) Variables（全局上下文参数）
            await agent.create_variable(name="min-blocks", value=self.min_blocks)
            await agent.create_variable(name="max-blocks", value=self.max_blocks)
            await agent.create_variable(name="max-len", value=self.max_len)
            await agent.create_variable(name="layout-hint-default", value=self.layout_hint_default)

            # 2) 注册工具（真正被 Agent 调用）
            await agent.register_tool(name="load_plain_text", tool=load_plain_text)
            await agent.register_tool(name="validate_blocks", tool=validate_blocks_tool)
            await agent.register_tool(name="export_design_json", tool=export_design_json_tool)
            await agent.register_tool(name="enforce_json_schema_hint", tool=enforce_json_schema_hint)

            # 3) 行为准则（把硬约束前移）
            await agent.create_guideline(
                condition="需要生成单页设计JSON",
                action=(
                    "先调用 enforce_json_schema_hint 获取模式提示；"
                    "然后基于输入仅生成JSON草案（不含解释/围栏）；"
                    "blocks数量应在变量min-blocks与max-blocks之间；"
                    "每条content长度不超过变量max-len；"
                    "layout_hint优先使用来参或变量layout-hint-default；"
                    "语言为中文、风格科技商务、用短句、避免重复要点。"
                )
            )
            await agent.create_guideline(
                condition="需要输出前的质量保证",
                action=(
                    "调用 validate_blocks 工具修正 blocks；"
                    "最后调用 export_design_json 写入 design_file；"
                    "对话返回最终JSON（不返回解释）。"
                ),
                tools=[validate_blocks_tool, export_design_json_tool]
            )

            # 4) Journey（把步骤串起来）
            await agent.create_journey(
                name="aippt_page_design_flow",
                trigger="收到 data_file 与 design_file",
                steps=[
                    {"name": "load", "action": "调用 load_plain_text 读取 document_title 与 page_data"},
                    {"name": "draft", "action": (
                        "调用 enforce_json_schema_hint 获取JSON模式提示；"
                        "基于系统提示与输入，产出仅包含JSON对象的草案："
                        "{document_title, page_title, layout_hint, blocks:[{title, content}]}"
                    )},
                    {"name": "fix", "action": (
                        "调用 validate_blocks 修正 blocks（长度、数量、去重）；"
                        "将修正后的JSON写回对话上下文"
                    )},
                    {"name": "export", "action": "调用 export_design_json 将最终JSON写入 design_file"},
                ]
            )

            # 5) 执行：一次 chat 触发 Journey（注意：系统提示拼接）
            user_prompt = (
                f"{self.system_prompt}\n\n"
                f"data_file={data_file}\n"
                f"design_file={design_file}\n"
                f"layout_hint={layout_hint or self.layout_hint_default}\n"
                "请触发 aippt_page_design_flow，并仅返回最终JSON。"
            )
            resp = await agent.chat(user_prompt)
            return {"raw": getattr(resp, "text", ""), "explanations": getattr(resp, "explanations", None)}

    # —— 直连回退（不建议，但保底）——
    async def _run_via_direct(self, data_file: str, design_file: str, layout_hint: Optional[str]) -> Dict[str, Any]:
        # 直连路径中，读取txt由我们做，草案由LLM做，之后再本地校验+落盘
        from .tools import load_plain_text as _load, validate_blocks as _validate
        kv = _load(data_file)
        document_title = kv.get("document_title", "")
        page_data = kv.get("page_data", "")
        user = (
            f"{self.system_prompt}\n"
            f"document_title: {document_title}\npage_data: {page_data}\n"
            f"layout_hint优先：{layout_hint or self.layout_hint_default}\n"
            "请仅输出JSON。"
        )
        raw = await zhipu_chat(self.base_url, self.api_key, self.model, self.system_prompt, user)
        return {"raw": raw, "explanations": None}

    # —— 最终整合：解析→强校验→落盘→返回可观测信息 —— 
    async def run(self, data_file: str, design_file: str, layout_hint: Optional[str] = None) -> Dict[str, Any]:
        use_parlant = _PARLANT_AVAILABLE and bool(self.api_key)
        res = await (self._run_via_parlant(data_file, design_file, layout_hint)
                     if use_parlant else self._run_via_direct(data_file, design_file, layout_hint))

        raw = res.get("raw", "")
        s = extract_json_str(raw)
        parsed = try_parse_json(s)

        if not isinstance(parsed, dict):
            # 极端兜底：启发式最小骨架（防止因LLM异常中断）
            from .tools import validate_blocks as _validate
            doc = {"document_title": "", "page_title": "", "layout_hint": layout_hint or self.layout_hint_default, "blocks": []}
        else:
            doc = parsed

        # 兜底字段 & 二次强校验（Pydantic）
        if not doc.get("document_title"):
            # 尽力从 data_file 中还原标题
            from .tools import load_plain_text as _load
            kv = _load(data_file)
            doc["document_title"] = kv.get("document_title", "").strip()
        if not doc.get("page_title"):
            doc["page_title"] = truncate_to_limit(f"{doc['document_title']} · 页面", 24)
        doc["layout_hint"] = (layout_hint or doc.get("layout_hint") or self.layout_hint_default)

        # 用我们自己的 validate_blocks 做最后兜底
        from .tools import validate_blocks as _validate
        blocks = _validate(
            blocks=doc.get("blocks", []),
            max_len=int(_env("MAX_CONTENT_LEN_CN", "50")),
            min_blocks=int(_env("MIN_BLOCKS", "3")),
            max_blocks=int(_env("MAX_BLOCKS", "6")),
            document_title=doc["document_title"]
        )
        final = {
            "document_title": doc["document_title"],
            "page_title": doc["page_title"],
            "layout_hint": doc["layout_hint"],
            "blocks": blocks
        }

        # Pydantic 再验一遍，保证输出干净
        try:
            obj = DesignDoc(**final)
            final = json.loads(obj.model_dump_json(ensure_ascii=False))
        except ValidationError:
            pass

        # 落盘（注意：Parlant路径已落盘一次；此处覆盖为一致语义&加入constraints）
        payload = {
            **final,
            "constraints": {
                "min_blocks": int(_env("MIN_BLOCKS", "3")),
                "max_blocks": int(_env("MAX_BLOCKS", "6")),
                "max_content_len_cn": int(_env("MAX_CONTENT_LEN_CN", "50"))
            }
        }
        export_design_json(payload, design_file)

        return {
            "ok": True,
            "version": VERSION,
            "mode": "parlant" if use_parlant else "direct",
            "model": self.model,
            "design": final,
            "design_file": design_file,
            "explanations": res.get("explanations")
        }
