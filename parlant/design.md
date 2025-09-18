下面是**完整且已修正目录为 `aippt/parlant/`、运行环境为 Python 3** 的设计文档（Markdown）。

---

# AIPPT 单页设计生成（Parlant 模块 · Python 3 · glm-4.5-flash）

## 1. 概述与目标

* **目标**：将输入的纯文本数据文件（含 `document_title` 与 `page_data`）转换为一页 PPT 的**设计 JSON**，供渲染引擎直接使用。
* **范围**：仅覆盖**单页**设计生成能力；不负责实际 PPT 渲染与导出（由上层引擎处理）。
* **模型**：智谱 AI `glm-4.5-flash`（OpenAI 兼容协议调用）。
* **语言风格**：中文、专业、简洁、科技商务风。
* **硬约束**：输出 3–6 个文本块（可配），每块包含 `title` 与 `content`；`content` ≤ **50 个中文字符**。

---

## 2. 目录结构（固定为 `aippt/parlant/`）

```
aippt/
└─ parlant/
   ├─ __init__.py
   ├─ .env                       # 环境变量（模型与阈值）
   ├─ requirements.txt           # 依赖清单
   ├─ data/                      # 输入数据目录
   │  └─ xxxx.txt
   ├─ out/                       # 输出设计目录
   │  └─ xxx.json
   ├─ tools.py                   # 工具函数：加载/校验/导出
   ├─ journey.py                 # Parlant Journey & Guidelines 定义
   ├─ style.py                   # 风格与术语表
   ├─ app.py                     # 服务/CLI 入口（Python 3）
   └─ README.md                  # 使用说明（面向开发）
```

---

## 3. 输入/输出规范

### 3.1 输入（`aippt/parlant/data/xxxx.txt`，UTF-8）

```txt
document_title: 企业专属AI伙伴
page_data: AIPPT助手赋能企业演示效率提升；核心能力包括模板管理、自动排版、数据驱动内容生成……
```

**要求**

* 两行键值对，键名固定（`document_title`、`page_data`）。
* `page_data` 可为长文本；允许标点与中英混排（最终输出只保留中文要点）。

### 3.2 输出（`aippt/parlant/out/xxx.json`）

```json
{
  "document_title": "企业专属AI伙伴",
  "page_title": "AIPPT助手赋能企业演示效率提升",
  "layout_hint": "grid-2-2",
  "blocks": [
    { "title": "问题痛点", "content": "传统PPT制作耗时高、风格不统一、复用率低" },
    { "title": "解决思路", "content": "以模板与数据驱动稿件生成，自动排版与校验" },
    { "title": "核心能力", "content": "模板库、样式一致性、数据到图文的自动映射" },
    { "title": "预期价值", "content": "效率提升60%+，品牌风格统一，易于复用" }
  ],
  "constraints": {
    "min_blocks": 3,
    "max_blocks": 6,
    "max_content_len_cn": 50
  }
}
```

**说明**

* `layout_hint` 为布局建议（示例：`title-top`、`grid-2-2`、`grid-3` 等）；渲染端可自行解释。
* 字段键名固定；不允许额外字段或非 JSON 输出。

---

## 4. 运行环境与配置

### 4.1 Python 版本

* **Python 3.10+**（推荐 3.10 或 3.11）

### 4.2 依赖（`aippt/parlant/requirements.txt`）

```
parlant
python-dotenv
fastapi
uvicorn
pydantic
```

> 说明：若使用纯 CLI 可不装 FastAPI/uvicorn；保留以便 HTTP 服务模式。

### 4.3 环境变量（`aippt/parlant/.env`）

```ini
# 模型配置（OpenAI 兼容协议指向智谱）
ZHIPUAI_API_KEY=your_zhipu_api_key
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
MODEL_NAME=glm-4.5-flash

# 设计约束
MIN_BLOCKS=3
MAX_BLOCKS=6
MAX_CONTENT_LEN_CN=50
DEFAULT_LAYOUT_HINT=grid-2-2
```

---

## 5. Parlant 组件设计

### 5.1 行为准则（Guidelines）

* **长度与合规**

  * 必做：每个 `content` ≤ `MAX_CONTENT_LEN_CN`（默认 50）。
  * 必做：若超限，对句子进行“保核心语义”截断（保主干名词/动宾）。
  * 禁止：输出英文/emoji/夸张营销词；禁止输出非 JSON 文本。
* **结构完整**

  * 必做：输出 `MIN_BLOCKS`–`MAX_BLOCKS` 个文本块（默认 3–6）。
  * 必做：每块包含 `title` 与 `content`，不得为空。
  * 必做：`page_title` 从 `document_title` 与 `page_data` 摘要生成；保持主题一致。
* **风格一致**

  * 必做：中文、简洁、专业；使用短句；“结论优先，补充随后”。
  * 必做：语义去重，避免同义重复块。

### 5.2 术语表（Glossary）

* 「模板库」：标准化页面结构与样式集合
* 「自动排版」：规则/模型驱动的文本块位置与层级分配
* 「一致性」：跨页/跨文档的术语与风格统一

> 术语表由 `style.py` 提供，供模型对齐表达。

### 5.3 工具（Tools，`tools.py`）

* `load_plain_text(path: str) -> dict`
  读取 `xxxx.txt`，解析 `document_title` 与 `page_data`。
* `validate_blocks(blocks: list, max_len: int, min_blocks: int, max_blocks: int) -> list`
  校验块数量与长度；必要时截断/补足（基于 `document_title` 生成纲要）。
* `export_design_json(data: dict, out_path: str) -> None`
  将设计 JSON 写入 `xxx.json`。

### 5.4 旅程（Journey，`journey.py`）

* **名称**：`aippt_page_design_flow`
* **触发**：收到 `data_file`（输入路径）与 `design_file`（输出路径）
* **步骤**：

  1. 调用 `load_plain_text` 解析输入
  2. 规划文本块（LLM 基于 `page_data` 摘要 → 3–6 要点）
  3. 生成草案 JSON（含 `document_title`、`page_title`、`layout_hint`、`blocks`）
  4. 调用 `validate_blocks` 严格校验与修正
  5. `export_design_json` 输出终稿

### 5.5 风格指南（Styleguide，`style.py`）

* 语言：`zh-CN`
* 语气：礼貌、简洁、专业
* 结构：标题 → 要点（短句，结果导向）
* 结尾禁语：过度营销词/emoji/英文缩写（非必要）

---

## 6. 交互设计（HTTP 与 CLI 二选一）

### 6.1 HTTP 服务（`app.py` · FastAPI）

* **POST** `/generate`

  * **Request JSON**：

    ```json
    {
      "data_file": "aippt/parlant/data/xxxx.txt",
      "design_file": "aippt/parlant/out/xxx.json",
      "layout_hint": "grid-2-2"   // 可选，默认走 .env
    }
    ```
  * **Response JSON**（成功）：

    ```json
    { "ok": true, "design_file": "aippt/parlant/out/xxx.json" }
    ```
  * **错误码**：

    * `400`：参数缺失/格式错误
    * `422`：输入解析失败（缺字段）
    * `500`：模型/写盘/未知错误

**启动**

```bash
cd aippt/parlant
python3 -m uvicorn app:api --reload --port 8000
```

### 6.2 CLI（`app.py`）

```bash
python3 aippt/parlant/app.py \
  --data-file aippt/parlant/data/xxxx.txt \
  --design-file aippt/parlant/out/xxx.json \
  --layout-hint grid-2-2
```

---

## 7. 校验与异常处理

* **长度计算**：按 Python 字符计数（Unicode 码点），中文/英文/数字均按 1 计；不计首尾空白。
* **截断策略**：优先保留“名词短语 + 结果/作用”；删除冗余修饰；必要时用顿号压缩列举项。
* **数量边界**：若生成块数 < `MIN_BLOCKS`，从主题自动补全纲要；若 > `MAX_BLOCKS`，按信息密度合并。
* **去重**：块 `content` 语义近似则合并，保信息更全且更短的版本。
* **健壮性**：空文件/缺字段 → 返回 `422` 与示例模板；写盘失败 → 返回 `500`。

---

## 8. 示例（端到端）

**输入**：`aippt/parlant/data/xxxx.txt`

```txt
document_title: 企业专属AI伙伴
page_data: AIPPT助手赋能企业演示效率提升；核心能力包括模板管理、自动排版、数据驱动内容生成……
```

**调用（HTTP）**：

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"data_file":"aippt/parlant/data/xxxx.txt","design_file":"aippt/parlant/out/xxx.json"}'
```

**输出**：`aippt/parlant/out/xxx.json`（示例见 3.2）

---

## 9. 测试用例（最少覆盖）

1. **常规**：`page_data` 信息充分 → 4–5 块，均 ≤ 50 字。
2. **极短**：仅有 `document_title` → 自动补全 3 块，主题一致。
3. **超长**：`page_data` > 500 字 → 摘要 + 截断，仍满足限长。
4. **含英文**：混排文本 → 输出仅保中文要点，去英文与符号噪声。
5. **边界**：`MAX_BLOCKS=3`、`MAX_CONTENT_LEN_CN=20` → 严格压缩仍可读。
6. **异常**：输入缺 `page_data` → 返回 `422` 与提示模板。

---

## 10. 性能与扩展

* **并发**：FastAPI + uvicorn，默认 1 worker，可按 CPU 核扩展；I/O 轻量。
* **缓存**：相同输入可用哈希键缓存最终 JSON（可选）。
* **可观测性**：记录每次 Guideline 触发与工具调用；落库便于回溯。
* **多布局**：`layout_hint` 可由 LLM 预测（如 `title-top + grid-2-2`），或由调用方指定。
* **多语言**：当前固定中文；后续可在 `.env` 增加语言开关与 Styleguide 选择。

---

## 11. 安全与合规

* 不返回与输入无关的内容；不输出个人隐私字段。
* 禁止英文、emoji、夸张营销词；避免虚假承诺。
* 仅写入 `aippt/parlant/out/`；其余路径拒绝写盘。

---

## 12. 版本里程碑

* **v0.1**：单页 JSON 生成（本设计）。
* **v0.2**：`layout_hint` 智能预测与多模板对齐。
* **v0.3**：质量评估指标（信息密度/重复率/阅读时长估计）。

---

## 13. 附录：计数规则（≤ 50 字）

* 以 `len(content.strip())` 计数；中文/英文/数字/标点均计 1。
* 超长时优先删除冗余从句、修饰语与多余列举项；保核心名词与动宾结构。



