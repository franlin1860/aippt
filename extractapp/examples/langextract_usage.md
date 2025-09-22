# LangExtract 最佳实践手册（结合 LiteLLM 与 Qwen）

本手册总结在本项目中集成 LangExtract + LiteLLM（Qwen 模型）的稳定用法、提示词与解析策略、调试与诊断方法，以及常见问题排查建议。所有实践均基于本仓库内现有代码与运行记录，避免臆造。

- 参考实现文件：
  - `examples/minimal_extract.py` (推荐入门)
  - `examples/advanced_extract.py` (高级用法)

## 一、安装与依赖

- **依赖文件**: 使用 `extractapp/requirements.txt` 安装所有必需的包。
  - `langextract`
  - `langextract-litellm` (LiteLLM provider 插件)
  - `litellm`
  - `python-dotenv`
- **环境变量**: 在项目根目录创建 `.env` 文件并配置 `DASHSCOPE_API_KEY`。
  - **最佳实践**: 永远不要将密钥硬编码到代码中。

## 二、Provider 注册与模型配置

- **导入顺序**:
  1. `import langextract as lx`
  2. `import langextract_litellm` (确保 LiteLLM provider 被自动注册)
- **结构化配置**: 使用 `lx.factory.ModelConfig` 来组织模型参数，使代码更清晰。
- **关键 `provider_kwargs`**:
  - `temperature`: 建议 `0.1` 以获得稳定、可复现的输出。
  - `max_tokens`: 至少 `4096`，防止因输出截断导致 JSON 解析失败。
  - `stream=False`: 对于提取任务，一次性获取完整响应更易于处理。
  - `extra_body={"enable_thinking": False}`: **此参数对 `qwen3-32b` 模型至关重要**，可防止其输出非 JSON 的“思考”内容，否则极易导致调用挂起或解析失败。

## 三、调用方式与解析策略

- **首选 `lx.extract`**: 这是最直接、最简单的端到端提取方法。
- **简化提示词**: 无需复杂的规则列表。一个清晰、直接的描述性提示（`prompt_description`）通常效果很好，如 `minimal_extract.py` 中所示。
- **移除 Few-shot 示例**: 对于 `qwen3-32b` 这类能力较强的模型，通常不再需要 few-shot 示例即可获得良好的结构化输出，移除它们可以简化代码。
- **移除 `response_format`**: **不要使用 `provider_kwargs` 中的 `response_format={"type": "json_object"}`**。这会强制模型输出纯 JSON，与 `langextract` 内部依赖标记（marker）的解析器冲突，是导致 `ResolverParsingError` 的主要原因。让 `langextract` 自行处理提示和解析。

## 四、输出与可视化

- **保存 JSONL**: 使用 `lx.io.save_annotated_documents` 将结果保存为 JSONL 格式。
- **处理 `IsADirectoryError`**:
  - `lx.io.save_annotated_documents` 会创建一个**目录**（而不是文件），并在其中保存 `data.jsonl`。
  - 因此，传递给 `lx.visualize` 的路径必须是 `os.path.join(your_output_dir, "data.jsonl")`，直接传递目录会导致 `IsADirectoryError`。
- **生成 HTML**: 使用 `lx.visualize(jsonl_path)` 创建一个交互式的 HTML 可视化文件。

## 五、常见问题与排查 (Troubleshooting)

- **`langextract.resolver.ResolverParsingError: Failed to parse content.`**
  - **原因**: 最常见的原因是 `provider_kwargs` 中设置了 `response_format={"type": "json_object"}`，这与 `langextract` 的解析机制冲突。
  - **解决方案**: 从 `provider_kwargs` 中**移除 `response_format`**。让模型根据提示词自然生成带标记的 JSON。

- **`IsADirectoryError: [Errno 21] Is a directory`**
  - **原因**: `lx.io.save_annotated_documents` 函数创建的是一个目录，而 `lx.visualize` 期望接收一个文件路径。
  - **解决方案**: 修正代码，将 `os.path.join(save_dir, "data.jsonl")` 作为 `lx.visualize` 的输入路径，而不是只传入 `save_dir`。

- **调用挂起或超时**:
  - **检查模型特定参数**: 确认 `provider_kwargs` 中包含了 `extra_body={"enable_thinking": False}`，这对于 `qwen3-32b` 是必需的。
  - **网络问题**: 确保可以访问模型服务提供商的 API 端点。
  - **依赖版本**: 检查 `litellm` 和其他相关库的版本是否兼容。

- **版本兼容与弃用提示**:
  - 日志中可能会出现 `langextract.inference` 的弃用警告。这是正常的，在未来的版本中会迁移。当前可锁定 `langextract` 的主版本（例如 `<2.0.0`）并关注官方升级指引。

## 六、推荐工作流 (基于 `minimal_extract.py`)

1.  **初始化**: 加载 `.env`，检查密钥。
2.  **配置模型**: 使用 `lx.factory.ModelConfig` 和 `lx.factory.create_model` 创建模型实例。确保 `provider_kwargs` 包含 `extra_body`。
3.  **提取**: 使用 `lx.extract`，传入一个简单的 `prompt_description` 和要处理的文本。
4.  **保存与可视化**:
    - 使用 `lx.io.save_annotated_documents` 保存到**目录**。
    - 构造指向 `data.jsonl` 的**文件路径**。
    - 使用 `lx.visualize` 生成 HTML 报告。

---

*本手册根据实际调试经验编写，旨在提供稳定、可靠的最佳实践。*