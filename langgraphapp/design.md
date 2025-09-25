

# LangGraph 方案设计：报告段落到 PPT 核心内容 (Qwen-32B版)

## 1. 方案目标

为 "aippt" 应用构建一个高效、可靠的内容转化工作流。该工作流接收一段来自 Word 报告的文本（例如，一个二级标题下的全部内容），并利用**通义千问 Qwen-32B 模型**的强大理解和生成能力，输出一个包含**页面标题**和**核心要点列表**的结构化 JSON 对象，直接用于 PPT 内容的填充。

## 2. 核心思路与技术栈

### 核心思路

*   **一步式结构化生成**: 鉴于 `qwen-32b` 模型强大的上下文理解和指令遵循能力，我们采用最简洁的**单节点、一次调用**策略。模型将在一次推理中，连贯地完成对原文的理解、页面标题的构思和核心要点的提炼。
*   **可靠性优先**: 整个流程的核心是确保输出的**格式绝对可靠**。我们将利用 LangChain 的原生能力，强制模型返回符合预定义数据结构的 JSON，从而完全避免在应用层出现解析错误。

### 技术栈

*   **流程编排**: `LangGraph` - 用于构建、编译和运行标准化的 AI 工作流。
*   **模型框架**: `LangChain` - 提供与模型交互、结构化输出等核心能力。
*   **核心模型**: `qwen3-32b` (通过阿里云 DashScope 服务)。
*   **模型集成**: `langchain_community.chat_models.ChatTongyi` - LangChain 官方提供的原生集成，确保与 DashScope API 的稳定、高效通信。

## 3. LangGraph 流程设计

### 3.1. 状态 (State)

工作流的“共享内存”，用于在流程的开始和结束时传递数据。其结构定义如下：

```python
from typing import List, Optional, TypedDict

class PptContentState(TypedDict):
    """定义了工作流中传递的数据结构"""
    # 输入
    raw_text: str  # 原始的报告段落文本

    # 输出
    title: Optional[str]            # 生成的PPT页面标题
    bullet_points: Optional[List[str]] # 提炼出的核心要点列表
```

### 3.2. 节点 (Node)

本方案仅包含一个核心处理节点。

*   **节点名称**: `generate_content_node`
*   **输入**:
    *   `state['raw_text']`: 原始的报告段落文本。
*   **任务**:
    1.  接收原始文本。
    2.  调用 `qwen3-32b` 模型，并附带一个精心设计的 Prompt，指示其同时生成**标题**和**要点列表**。
    3.  利用 LangChain 的 `.with_structured_output()` 方法，将模型的输出强制约束为一个预定义的 Pydantic 模型 (`PptContent`)。
*   **输出**:
    *   一个字典，包含 `title` 和 `bullet_points` 两个键，用于更新 `PptContentState`。

### 3.3. 图 (Graph) 的结构

这是一个最简化的线性图，确保了流程的清晰和高效。

```
[START] (入口点)
   |
   V
[generate_content_node] (核心处理)
   |
   V
[END] (结束)
```

## 4. 预期收益

*   **模型灵活性**: 展示了 LangGraph 框架的优势。只需修改模型初始化部分，即可无缝切换到不同的强大模型（如 Qwen, GPT, GLM），而无需重构整个工作流。
*   **成本效益**: `qwen3-32b` 作为一个极具竞争力的模型，通常能提供比同级别模型更高的性价比。
*   **高性能与高可靠性**: 结合 `qwen3-32b` 的强大文本处理性能和 LangChain 结构化输出的可靠性，确保了最终生成内容的质量和稳定性，可以直接被下游应用消费。