

# 方案：使用 Langextract、LiteLLM 和 .env 配置调用Qwen模型

## 1. 概述

本文档旨在提供一个完整、安全且可维护的解决方案，用于在 Python 项目中集成 Google `Langextract` 库，通过 `LiteLLM` 调用阿里云Qwen大语言模型，并使用 `.env` 文件来统一管理项目密钥等敏感配置。

这种方法将配置与代码分离，遵循了十二要素应用（Twelve-Factor App）的最佳实践，使得项目在不同环境（开发、测试、生产）中迁移和部署时更加便捷和安全。

### 核心组件

| 组件 | 用途 | **组件** | **用途** |
| :--- | :--- |
| **Langextract** | Google 开源库，用于从文本中提取结构化信息，并确保结果可精确溯源。 |
| **LiteLLM** | 模型调用中间件，提供统一接口访问超过100种LLM，包括Qwen模型。 |
| **`langextract-litellm`** | 连接 Langextract 和 LiteLLM 的官方插件，自动注册并提供 LiteLLM 支持。 |
| **`python-dotenv`** | 用于从 `.env` 文件中加载环境变量，实现配置与代码的分离。 |
| **`.env` 文件** | 存储环境变量，如 API 密钥，应被版本控制系统（如 Git）忽略。 |
| **阿里云 Qwen 模型**| 本次方案中用于执行提取任务的目标大语言模型。 |

## 2. 环境与项目设置

### 2.1. 项目结构推荐

建议采用以下目录结构来组织您的项目：

```
/extract-app/
|
├── .env                  # 存储环境变量（API密钥等）
├── .gitignore            # Git忽略文件配置，必须包含.env
├── extract_app.py        # 核心业务逻辑Python脚本
├── requirements.txt      # 项目依赖列表
|
└── /outputs/             # (可选) 存放生成的提取结果和可视化文件
    ├── qwen_extraction_results.jsonl
    └── qwen_visualization.html
```

### 2.2. 安装项目依赖

首先，我们需要安装所有必要的 Python 库。

1.  创建一个 `requirements.txt` 文件，并填入以下内容：

    ```text
    langextract
    langextract-litellm
    litellm
    python-dotenv
    ```

2.  在您的终端中，使用 pip 安装这些依赖：

    ```bash
    pip install -r requirements.txt
    ```

### 2.3. 配置 `.env` 文件

在项目根目录下创建一个名为 `.env` 的文件。这个文件将存放您的阿里云DashScope API密钥。

打开 `.env` 文件并添加以下内容，将 `YOUR_DASHSCOPE_API_KEY` 替换为您的真实密钥：

```bash
# 阿里云DashScope API配置
DASHSCOPE_API_KEY="YOUR_DASHSCOPE_API_KEY"
```

### 2.4. 关于 langextract-litellm 的重要说明

`langextract-litellm` 是 LangExtract 的官方 LiteLLM provider 插件，安装后会自动注册到 LangExtract 中。这意味着：

1. **自动集成**：无需手动配置，安装后即可在 `lx.extract()` 中使用所有 LiteLLM 支持的模型
2. **模型标识符**：可以直接使用 LiteLLM 的标准模型标识符格式（如 `dashscope/qwen3-32b`）
3. **环境变量支持**：LiteLLM 会自动读取相应的环境变量（如 `DASHSCOPE_API_KEY`）

### 2.5. 配置 `.gitignore`

**这是一个至关重要的安全步骤。** 为了防止您的 API 密钥被意外提交到代码仓库（如 GitHub），请在项目根目录下创建或编辑 `.gitignore` 文件，确保其中包含 `.env`：

```text
# 忽略环境变量文件
.env

# 忽略Python缓存文件
__pycache__/
*.pyc

# 忽略输出文件
/outputs/
*.jsonl
*.html```

## 3. 核心代码实现

现在，我们可以编写核心的 Python 脚本 `extract_app.py`。此脚本将首先加载 `.env` 文件中的配置，然后执行 Langextract 的信息提取流程。

```python
# extract_app.py

import os
import textwrap
import json
from dotenv import load_dotenv

# 导入 langextract 和 langextract-litellm
try:
    import langextract as lx
    # 导入 langextract-litellm 以自动注册 LiteLLM provider
    import langextract_litellm
    print("✅ langextract 和 langextract-litellm 加载成功")
    
except ImportError as e:
    print(f"错误：缺少必要的依赖库: {e}")
    print("请安装以下依赖：")
    print("pip install langextract langextract-litellm litellm python-dotenv")
    exit(1)

def main():
    """
    主函数，执行从加载配置到信息提取的全过程。
    """
    # --- 步骤 1: 加载环境变量 ---
    print("正在加载 .env 文件中的环境变量...")
    load_dotenv()

    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope_api_key:
        print("错误：未找到 DASHSCOPE_API_KEY。请在 .env 文件中配置密钥。")
        return
    
    print("使用阿里云 Qwen API 密钥")
    
    # --- 步骤 2: 定义提取任务 ---
    print("正在定义信息提取任务...")
    prompt_description = textwrap.dedent("""        Extract all characters, locations, and events from the text.
        - The extracted text must exactly match the original text.
        - Provide meaningful attributes for each entity to add context.
    """)

    examples = [
        lx.data.ExampleData(
            text="2024年，李明在北京的故宫博物院参观时，偶然发现了一本尘封已久的古籍。",
            extractions=[
                lx.data.Extraction(extraction_class='character', extraction_text='李明', attributes={'year': 2024}),
                lx.data.Extraction(extraction_class='location', extraction_text='北京', attributes={'specific_place': '故宫博物院'}),
                lx.data.Extraction(extraction_class='event', extraction_text='发现了一本尘封已久的古籍', attributes={'protagonist': '李明'}),
            ]
        )
    ]

    # --- 步骤 3: 准备模型和输入文本 ---
    model_config = lx.factory.ModelConfig(
        model_id="litellm/dashscope/qwen3-32b",
        provider="LiteLLMLanguageModel",
        provider_kwargs={
            "temperature": 0.1,
            "max_tokens": 2048,
            "stream": False,
            "extra_body": {"enable_thinking": False},
        },
    )
    model = lx.factory.create_model(model_config)
    input_text = "项目启动会议于上周在上海的环球金融中心举行，由项目经理王伟主持，确定了项目的关键里程碑。"

    # --- 步骤 4: 执行提取并处理结果 ---
    try:
        print(f"开始使用 langextract 和 LiteLLM 进行信息提取...")
        
        result = lx.extract(
            text_or_documents=input_text,
            prompt_description=prompt_description,
            examples=examples,
            model=model
        )
        
        print("\n✅ 提取成功！")
        
        print("\n提取到的实体:")
        if result and result.extractions:
            for extraction in result.extractions:
                print(f"- 类别: {extraction.extraction_class}, "
                      f"文本: '{extraction.extraction_text}', "
                      f"属性: {extraction.attributes}")
        else:
            print("- 无提取结果")

        # --- 步骤 5: 保存结果 ---
        output_dir = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        docs = [result] if result else []
        # save_annotated_documents 需要一个目录路径，它会在该目录中创建 data.jsonl
        lx.io.save_annotated_documents(docs, output_dir)
        
        # langextract 默认保存为 data.jsonl
        jsonl_path = os.path.join(output_dir, "data.jsonl")
        print(f"\n结果已保存至: {jsonl_path}")

        html_path = os.path.join(output_dir, "langextract_visualization.html")
        html_content = lx.visualize(jsonl_path)
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(getattr(html_content, "data", html_content))
        print(f"可视化文件已生成: {html_path}")
        print("\n请用浏览器打开 HTML 文件查看高亮标注的提取结果。")
        
    except Exception as e:
        print(f"\n❌ 提取过程中发生错误: {e}")
        print("请检查：\n1. DASHSCOPE_API_KEY 是否有效。\n2. 网络连接是否可以访问阿里云DashScope服务。\n3. 项目依赖是否已正确安装。")

if __name__ == "__main__":
    main()
```

## 4. 运行与验证

1.  **准备工作**: 确保您的项目结构如 `2.1` 所示，`requirements.txt` 和 `.env` 文件已正确创建和配置。
2.  **执行脚本**: 在您的终端中，导航到项目根目录，并运行 Python 脚本：
    ```bash
    python extract_app.py
    ```
3.  **验证输出**:
    *   **控制台输出**: 您将看到脚本执行的日志，包括加载配置、开始提取、提取结果等信息。
    *   **文件输出**: 脚本执行成功后，`outputs` 文件夹下会生成两个文件：
        *   `qwen_extraction_results.jsonl`: 包含结构化提取结果的原始数据文件。
*   `qwen_visualization.html`: 一个独立的 HTML 文件。**用您的网页浏览器打开它**，您将看到原始文本，并且所有被成功提取的实体都会以不同颜色高亮显示，鼠标悬停可查看详细属性，非常便于审查和验证。

## 5. 示例代码

`examples` 目录下提供了一系列示例代码，帮助您快速上手和理解 `langextract` 的不同用法。

### 5.1. `minimal_extract.py`

这是一个最基础的示例，展示了如何使用 `langextract` 和 `litellm` 进行最简单的信息提取。它包含了以下核心步骤：

- **加载环境变量**: 从 `.env` 文件加载 `DASHSCOPE_API_KEY`。
- **定义提示和示例**: 创建一个简单的提示和 few-shot 示例来指导模型。
- **配置模型**: 使用 `lx.factory.ModelConfig` 配置 Qwen 模型。
- **执行提取**: 调用 `lx.extract` 函数进行提取。
- **保存结果**: 将结果保存为 JSONL 和 HTML 可视化文件。

### 5.2. `advanced_extract.py`

这是一个更高级的示例，展示了 `langextract` 的一些高级特性，包括：

- **多轮提取 (passes)**: 设置 `extraction_passes=3` 来运行多轮提取，以获得更鲁棒的结果。
- **错误抑制**: 使用 `suppress_parse_errors=True` 来避免在模型输出格式不正确时程序崩溃。
- **专用输出目录**: 为每次运行创建一个独立的输出目录，以避免文件名冲突。

### 5.3. `litellm_qwen.py`

这个脚本专注于测试 `litellm` 与 Qwen 模型的直接集成，不涉及 `langextract`。它主要用于验证：

- **API Key 和模型配置**: 确保 `litellm` 可以正确加载环境变量并调用 Qwen 模型。
- **模型响应**: 检查模型是否返回了预期的响应内容。

### 5.4. `debug_extract.py`

这是一个用于调试 `litellm` 调用的脚本。当您在集成 `langextract` 时遇到问题，可以使用此脚本来隔离问题，判断是 `langextract` 本身的问题还是底层 `litellm` 调用的问题。

---