import os
import json
import uvicorn
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from fastmcp import FastMCP
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from tools import calculator, weather

# Load environment variables
load_dotenv()

# Check for the API key
if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("Please set DASHSCOPE_API_KEY in your .env file")

# Initialize the Qwen model
llm = ChatTongyi(
    model="qwen3-32b",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.3,
    streaming=False,
    max_tokens=2048,
    model_kwargs={"enable_thinking": False}
)

# Define the state for the LangGraph workflow
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_input: str
    tool_result: str
    response: str

# Tool routing function
# 添加缓存机制优化性能
from functools import lru_cache
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def cached_route_to_tool(user_input: str) -> str:
    """缓存路由决策以提高性能"""
    # 简单的关键词匹配，避免每次都调用LLM
    user_input_lower = user_input.lower()
    
    # 天气相关关键词
    weather_keywords = ['天气', '气温', '温度', '下雨', '晴天', '阴天', '多云', 'weather', 'temperature']
    if any(keyword in user_input_lower for keyword in weather_keywords):
        return "weather_tool"
    
    # 数学计算关键词
    math_keywords = ['计算', '加', '减', '乘', '除', '+', '-', '*', '/', '等于', '多少']
    if any(keyword in user_input_lower for keyword in math_keywords):
        return "calculator_tool"
    
    return "general_response"

def route_to_tool(state: AgentState) -> str:
    """Route user input to appropriate tool with caching optimization."""
    user_input = state["user_input"]
    
    # 首先尝试缓存的快速路由
    cached_result = cached_route_to_tool(user_input)
    if cached_result != "general_response":
        logger.info(f"使用缓存路由: {user_input} -> {cached_result}")
        return cached_result
    
    # 对于复杂情况，使用LLM进行路由
    logger.info(f"使用LLM路由: {user_input}")
    messages = [
        HumanMessage(content=f"""
            用户输入: {user_input}
            
            请判断用户需要什么服务：
            1. 如果是询问天气相关信息，回复 "weather"
            2. 如果是数学计算相关，回复 "calculator"
            3. 如果不确定，回复 "general"
            
            只回复一个词：weather、calculator 或 general
            """)
    ]
    
    try:
        response = llm.invoke(messages)
        tool_choice = response.content.strip().lower()
        
        if "weather" in tool_choice:
            return "weather_tool"
        elif "calculator" in tool_choice:
            return "calculator_tool"
        else:
            return "general_response"
    except Exception as e:
        logger.error(f"LLM路由失败: {e}")
        return "general_response"

# Tool execution nodes
def weather_tool_node(state: AgentState) -> AgentState:
    """Execute weather tool with enhanced error handling."""
    user_input = state["user_input"]
    
    try:
        # Extract location from user input using LLM
        messages = [
            HumanMessage(content=f"""
            从以下用户输入中提取地点信息："{user_input}"
            
            如果找到地点，只返回地点名称。
            如果没有找到地点，返回 "北京"（默认地点）。
            """)
        ]
        
        response = llm.invoke(messages)
        location = response.content.strip()
        
        # Call weather tool
        result = weather(location)
        logger.info(f"天气查询成功: {location} -> {result[:50]}...")
        
        return {
            **state,
            "tool_result": result,
            "messages": state["messages"] + [AIMessage(content=f"调用天气工具，地点：{location}，结果：{result}")]
        }
    except Exception as e:
        logger.error(f"天气工具执行失败: {e}")
        error_msg = f"抱歉，无法获取天气信息：{str(e)}"
        return {
            **state,
            "tool_result": error_msg,
            "messages": state["messages"] + [AIMessage(content=error_msg)]
        }

def calculator_tool_node(state: AgentState) -> AgentState:
    """Execute calculator tool with enhanced error handling."""
    user_input = state["user_input"]
    
    try:
        # Extract mathematical expression using LLM
        messages = [
            HumanMessage(content=f"""
            从以下用户输入中提取数学表达式："{user_input}"
            
            请提取出需要计算的数学表达式，例如：
            - "2+2是多少？" -> "2+2"
            - "计算5乘以3" -> "5*3"
            - "100除以4等于多少" -> "100/4"
            
            只返回数学表达式，不要其他文字。
            """)
        ]
        
        response = llm.invoke(messages)
        expression = response.content.strip()
        
        # Call calculator tool
        result = calculator(expression)
        logger.info(f"计算成功: {expression} -> {result}")
        
        return {
            **state,
            "tool_result": result,
            "messages": state["messages"] + [AIMessage(content=f"调用计算器工具，表达式：{expression}，结果：{result}")]
        }
    except Exception as e:
        logger.error(f"计算工具执行失败: {e}")
        error_msg = f"抱歉，无法完成计算：{str(e)}"
        return {
            **state,
            "tool_result": error_msg,
            "messages": state["messages"] + [AIMessage(content=error_msg)]
        }

def general_response_node(state: AgentState) -> AgentState:
    """Handle general queries with enhanced error handling."""
    user_input = state["user_input"]
    
    try:
        messages = [
            HumanMessage(content=f"""
            用户询问：{user_input}
            
            这个问题不需要使用天气或计算器工具。请直接回答用户的问题。
            如果无法回答，请礼貌地说明你只能提供天气查询和数学计算服务。
            """)
        ]
        
        response = llm.invoke(messages)
        result = response.content
        logger.info(f"通用回复生成成功: {user_input[:30]}...")
        
        return {
            **state,
            "tool_result": result,
            "messages": state["messages"] + [AIMessage(content=f"通用回复：{result}")]
        }
    except Exception as e:
        logger.error(f"通用回复生成失败: {e}")
        error_msg = "抱歉，我目前只能提供天气查询和数学计算服务。"
        return {
            **state,
            "tool_result": error_msg,
            "messages": state["messages"] + [AIMessage(content=error_msg)]
        }

def format_response_node(state: AgentState) -> AgentState:
    """Format the final response."""
    tool_result = state["tool_result"]
    user_input = state["user_input"]
    
    # Use LLM to format a natural response
    messages = [
        HumanMessage(content=f"""
        用户问题：{user_input}
        工具结果：{tool_result}
        
        请基于工具结果，给用户一个自然、友好的回复。
        """)
    ]
    
    response = llm.invoke(messages)
    formatted_response = response.content
    
    return {
        **state,
        "response": formatted_response,
        "messages": state["messages"] + [AIMessage(content=formatted_response)]
    }

# Create the LangGraph workflow
def create_agent_workflow():
    """Create the LangGraph workflow for the MCP server."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("weather_tool", weather_tool_node)
    workflow.add_node("calculator_tool", calculator_tool_node)
    workflow.add_node("general_response", general_response_node)
    workflow.add_node("format_response", format_response_node)
    
    # Add conditional routing from START
    workflow.add_conditional_edges(
        "__start__",
        route_to_tool,
        {
            "weather_tool": "weather_tool",
            "calculator_tool": "calculator_tool",
            "general_response": "general_response"
        }
    )
    
    # Add edges to format_response
    workflow.add_edge("weather_tool", "format_response")
    workflow.add_edge("calculator_tool", "format_response")
    workflow.add_edge("general_response", "format_response")
    workflow.add_edge("format_response", END)
    
    return workflow.compile()

# Create the agent workflow
agent_workflow = create_agent_workflow()

# Create the FastMCP server
mcp = FastMCP("QwenMCPServer")

@mcp.tool
def process_request(message: str) -> str:
    """Process user request using LangGraph agent."""
    try:
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_input": message,
            "tool_result": "",
            "response": ""
        }
        
        # Run the workflow
        result = agent_workflow.invoke(initial_state)
        
        return result["response"]
    
    except Exception as e:
        return f"处理请求时出错：{str(e)}"

def create_app():
    """Create the ASGI application."""
    return mcp.http_app()

# Create the ASGI app for deployment
app = create_app()

if __name__ == "__main__":
    print("启动MCP服务器，集成LangGraph智能体...")
    print("服务器将在 http://0.0.0.0:8000 上运行")
    mcp.run(transport="sse", host="0.0.0.0", port=8000)