# AIPPT Parlant · 单页 PPT 设计生成器

基于 [Parlant](https://github.com/emcie-co/parlant) 与智谱大模型 **glm-4.5-flash** 的单页 PPT 设计生成模块。  
输入原始文档标题与页面数据，输出符合约束的 JSON 设计文件，支持自动校验与落盘。

---

## ✨ 功能特性

- **输入**：`xxxx.txt` 文件，包含：
  - `document_title: ...`
  - `page_data: ...`
- **输出**：`xxx.json` 文件，包含：
  - 页面标题 (`page_title`)
  - 布局提示 (`layout_hint`)
  - 3–6 个文本块（每个包含 `title` 与 `content`）
- **约束**：
  - `content` ≤ 50 个中文字符
  - 中文输出、简洁、科技商务风
  - 自动去重与长度校验
- **鲁棒性**：
  - 优先调用 Parlant SDK；若不可用则回退直连智谱 OpenAI 兼容 API
  - 支持启发式回退，确保始终输出合法 JSON
  - Pydantic 强校验，自动修复 JSON 常见错误
- **测试**：
  - 内置系统测试（pytest）
  - 支持批量测试输入文件，自动校验输出约束

---

## 📂 项目结构

```

aippt/
└─ parlant/
├─ **init**.py
├─ .env
├─ requirements.txt
├─ README.md
├─ data/                # 输入样例
│  ├─ example\_short.txt
│  ├─ example\_normal.txt
│  └─ example\_long.txt
├─ out/                 # 输出结果
│  └─ ...
├─ tools.py             # 工具函数：解析/校验/导出
├─ style.py             # 风格与术语表
├─ journey.py           # 核心流程：调用 LLM + 校验 + 落盘
├─ app.py               # CLI / HTTP API 入口
├─ tests/
│  └─ test\_system.py    # 系统测试（pytest）
└─ run\_system\_tests.py  # 批量系统测试脚本

````

---

## ⚙️ 环境准备

### 1. Python
- 推荐 **Python 3.10+**

### 2. 安装依赖
```bash
pip install -r requirements.txt
````

`requirements.txt` 示例：

```txt
python-dotenv>=1.0.0
httpx>=0.27.0
fastapi>=0.111.0
uvicorn>=0.30.0
pydantic>=2.8.0
parlant>=0.2.0      # 可选
pytest>=8.2.0       # 开发测试
pytest-asyncio>=0.23.8
```

### 3. 配置 `.env`

在 `aippt/parlant/.env` 中设置：

```ini
ZHIPUAI_API_KEY=your_zhipu_api_key
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
MODEL_NAME=glm-4.5-flash

MIN_BLOCKS=3
MAX_BLOCKS=6
MAX_CONTENT_LEN_CN=50
DEFAULT_LAYOUT_HINT=grid-2-2
```

---

## 🚀 使用方式

### 方式一：CLI 模式

```bash
python3 aippt/parlant/app.py \
  --data-file aippt/parlant/data/example_normal.txt \
  --design-file aippt/parlant/out/out_normal.json \
  --layout-hint grid-2-2
```

运行后会在 `out/` 下生成 JSON 文件，并在终端打印结果概要。

---

### 方式二：HTTP 服务

启动服务：

```bash
cd aippt/parlant
python3 -m uvicorn app:api --reload --port 8000
```

调用接口：

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
        "data_file": "aippt/parlant/data/example_normal.txt",
        "design_file": "aippt/parlant/out/out_normal.json",
        "layout_hint": "grid-2-2"
      }'
```

健康检查：

```bash
curl http://localhost:8000/health
```

---

## 📄 输入/输出示例

### 输入文件：`data/example_normal.txt`

```
document_title: AIPPT助手 · 赋能企业演示智能化
page_data: 团队希望减少PPT制作时间，统一风格并提升复用率；AIPPT通过模板库、自动排版和数据驱动内容生成实现高效创作；适合营销汇报、经营分析、项目方案；计划先在销售与运营部门试点推广。
```

### 输出文件：`out/out_normal.json`

```json
{
  "document_title": "AIPPT助手 · 赋能企业演示智能化",
  "page_title": "AIPPT助手赋能企业演示效率提升",
  "layout_hint": "grid-2-2",
  "blocks": [
    { "title": "问题痛点", "content": "PPT制作耗时长、风格不统一、复用率低" },
    { "title": "解决思路", "content": "通过模板库与自动排版提升效率与一致性" },
    { "title": "核心能力", "content": "模板管理、样式统一、数据驱动内容生成" },
    { "title": "应用场景", "content": "营销汇报、经营分析、项目方案、复盘报告" }
  ],
  "constraints": {
    "min_blocks": 3,
    "max_blocks": 6,
    "max_content_len_cn": 50
  }
}
```

---

## 🧪 测试

### 1) 单次系统测试（pytest）

```bash
pytest -q
```

测试用例：`tests/test_system.py`

* 覆盖 **短输入**（补足 3 块）、**常规输入**（4～5 块）、**长输入**（自动摘要 5～6 块）
* 校验块数量、长度约束、字段完整性、落盘文件。

### 2) 批量系统测试

```bash
python3 aippt/parlant/run_system_tests.py --data-glob "aippt/parlant/data/*.txt"
```

输出示例：

```json
{
  "total": 3,
  "ok": 3,
  "constraints_ok": 3,
  "items": [
    {"file": "aippt/parlant/data/example_short.txt",  "ok": true, "blocks": 3, "constraints_ok": true, "out": "aippt/parlant/out/example_short.json"},
    {"file": "aippt/parlant/data/example_normal.txt", "ok": true, "blocks": 4, "constraints_ok": true, "out": "aippt/parlant/out/example_normal.json"},
    {"file": "aippt/parlant/data/example_long.txt",   "ok": true, "blocks": 6, "constraints_ok": true, "out": "aippt/parlant/out/example_long.json"}
  ]
}
```

---

## 📌 开发说明

* **风格注入**：`style.py` 定义的规则和术语表会自动拼接进 System Prompt。
* **容错性**：

  * 自动提取 JSON（剥离 Markdown/解释文本）
  * 自动修复常见 JSON 错误（尾随逗号、引号）
  * 启发式回退生成最小骨架
* **观测性**：返回结果包含 `version`、`model`、风格规则数、术语数量，便于前端调试。

---

## 📜 License

Apache-2.0

```


