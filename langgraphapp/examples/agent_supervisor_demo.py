# supervisor_qwen_full.py
# pip install -U langgraph langgraph-supervisor langchain-core langchain-community python-dotenv

import os
from typing import List, TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.chat_models.tongyi import ChatTongyi

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command, Send

# ============ 0) init ============
# Load environment variables
load_dotenv()

# Check for the API key
if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("Please set DASHSCOPE_API_KEY in your .env file")

# Initialize the Qwen model
llm = ChatTongyi(
    model="qwen3-32b",
    temperature=0.3,
    streaming=False,
    max_tokens=2048,
    model_kwargs={"enable_thinking": False},
)

class GraphState(TypedDict):
    messages: List[AnyMessage]
    done: bool

def show(ev):
    last = ev["messages"][-1]
    if getattr(last, "type", "") in ("ai", "tool"):
        print(f"[{last.type}] {str(last.content)[:240]}...")

# ============ 1) workers ============
@tool
def dummy_search(query: str) -> str:
    """Simulates a search query."""
    return f"[MockSearch] {query} -> (这里返回摘要/片段)"

@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b
@tool
def mul(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b
@tool
def div(a: float, b: float) -> float:
    """Divide two numbers."""
    return a / b

research_agent = create_react_agent(
    model=llm, tools=[dummy_search],
    prompt="You are a research agent. ONLY research; then report to supervisor.",
    name="research_agent",
)
math_agent = create_react_agent(
    model=llm, tools=[add, mul, div],
    prompt="You are a math agent. Use ONLY math tools; show brief reasoning then final.",
    name="math_agent",
)

# ============ 2) supervisor ============
app = create_supervisor(
    model=llm,
    agents=[research_agent, math_agent],
    prompt=(
        "You are a supervisor: route research to research_agent; math to math_agent. "
        "One agent per turn. Do NOT do work yourself."
    ),
    add_handoff_back_messages=False,
    output_mode="full_history",
).compile()


# ============ 3) run ============
if __name__ == "__main__":
    for ev in app.stream({"messages":[{"role":"user","content":"请调研：Qwen3-32B 的典型应用场景并举例"}]}, stream_mode="values"):
        show(ev)
    for ev in app.stream({"messages":[{"role":"user","content":"calculate 12 * 7 / 3"}]}, stream_mode="values"):
        show(ev)
