import os
from typing import List, Optional, TypedDict

from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from pydantic import BaseModel
from langgraph.graph import END, StateGraph

# --- 1. 环境与模型配置 ---

load_dotenv()

# 检查 DashScope API 密钥是否存在
if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("请在 .env 文件中设置 DASHSCOPE_API_KEY")

# 【关键变更】初始化 Qwen-32B 模型
# 我们使用 LangChain 的原生 ChatTongyi 集成
llm = ChatTongyi(
    model="qwen3-32b",
    temperature=0.3,
    streaming=False,
    max_tokens=2048,
    model_kwargs={"enable_thinking": False},
)
print("模型已初始化: Qwen-32B (via DashScope)")


# --- 2. 定义图的状态 (State) ---

class PptContentState(TypedDict):
    """定义了工作流中传递的数据结构"""
    raw_text: str  # 原始的报告段落文本
    title: Optional[str]  # 生成的PPT页面标题
    bullet_points: Optional[List[str]]  # 提炼出的核心要点列表


# --- 3. 定义结构化输出模型 (Pydantic Model for Structured Output) ---

class PptContent(BaseModel):
    """用于强制LLM输出标题和要点列表的结构"""
    title: str
    points: List[str]


# --- 4. 定义图的节点 (Node) ---

def generate_content_node(state: PptContentState) -> dict:
    """
    节点: 从原始文本中，一次性生成PPT标题和核心要点。
    """
    print("--- 正在使用 Qwen-32B 生成PPT核心内容 ---")
    
    prompt = f"""
    你的角色是一位顶级的商业顾问和演示文稿专家。
    请仔细阅读下面的报告段落，并将其浓缩成一页 PowerPoint 的核心内容。你需要提供一个引人注目的**标题**和一组简洁、有力的**项目符号要点**。

    内容转化规则:
    1.  **标题**: 必须简短、有力，能够瞬间抓住观众的注意力并概括核心信息。
    2.  **要点**: 每个要点都应聚焦于一个关键行动、量化结果或核心结论。要点数量应在3到5个之间。
    
    原始文本:
    ---
    {state['raw_text']}
    ---
    
    请严格按照指定的JSON格式输出你的结果，包含 "title" 和 "points" 两个字段。
    """
    
    # 使用 .with_structured_output 来保证可靠的JSON返回
    # ChatTongyi 支持此功能，可以强制 Qwen 模型输出合规的 JSON
    structured_llm = llm.with_structured_output(PptContent)
    response = structured_llm.invoke(prompt)
    
    print("  > 成功生成内容！")
    return {"title": response.title, "bullet_points": response.points}


# --- 5. 构建并编译图 (Graph) ---

def create_workflow():
    """Creates and compiles the LangGraph workflow."""
    print("\n正在构建 LangGraph 工作流...")
    workflow = StateGraph(PptContentState)

    # 添加节点
    workflow.add_node("generate_content", generate_content_node)

    # 设置流程的起点和终点
    workflow.set_entry_point("generate_content")
    workflow.add_edge("generate_content", END)

    # 编译图，使其成为可执行的应用
    app = workflow.compile()
    print("工作流构建完成！\n")
    return app

app = create_workflow()