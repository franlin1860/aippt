import os
import asyncio
import logging
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from fastmcp.client import Client as McpClient
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for the API key
if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("Please set DASHSCOPE_API_KEY in your .env file")

# 初始化LLM
llm = ChatTongyi(
    model="qwen3-32b",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.3,
    streaming=False,
    max_tokens=2048,
    model_kwargs={"enable_thinking": False}
)

# Define the state for the client LangGraph workflow
class ClientState(TypedDict):
    messages: Annotated[list, add_messages]
    user_input: str
    processed_request: str
    server_response: str
    final_response: str

def preprocess_request_node(state: ClientState) -> ClientState:
    """Preprocess user input before sending to server."""
    user_input = state["user_input"]
    
    # Use LLM to enhance or clarify the user request
    messages = [
        HumanMessage(content=f"""
        用户输入：{user_input}
        
        请分析用户的意图，并将请求优化为更清晰的形式。
        如果是天气查询，确保包含地点信息。
        如果是数学计算，确保表达式清晰。
        如果是其他问题，保持原样。
        
        返回优化后的请求：
        """)
    ]
    
    response = llm.invoke(messages)
    processed_request = response.content.strip()
    
    return {
        **state,
        "processed_request": processed_request,
        "messages": state["messages"] + [AIMessage(content=f"预处理请求：{processed_request}")]
    }

import time
from contextlib import asynccontextmanager

# 添加连接池和重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1.0
CONNECTION_TIMEOUT = 10.0

@asynccontextmanager
async def get_mcp_client():
    """获取MCP客户端连接，带有连接池管理"""
    client = None
    try:
        client = McpClient("http://localhost:8000/sse")
        await client.__aenter__()
        yield client
    except Exception as e:
        logger.error(f"MCP客户端连接失败: {e}")
        raise
    finally:
        if client:
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"关闭MCP客户端时出错: {e}")

async def send_to_server_node(state: ClientState) -> ClientState:
    """Send request to MCP server with retry mechanism."""
    processed_request = state["processed_request"]
    
    for attempt in range(MAX_RETRIES):
        try:
            async with get_mcp_client() as client:
                # Send the processed request to the server using the correct method
                start_time = time.time()
                response = await client.call_tool("process_request", {"message": processed_request})
                response_time = time.time() - start_time
                
                # Extract the actual response content from the CallToolResult
                if hasattr(response, 'data') and response.data:
                    server_response = response.data
                elif hasattr(response, 'content') and response.content:
                    # Handle list of TextContent objects
                    if isinstance(response.content, list) and len(response.content) > 0:
                        server_response = response.content[0].text
                    else:
                        server_response = str(response.content)
                else:
                    server_response = str(response)
                
                logger.info(f"服务器响应成功 (耗时: {response_time:.2f}s, 尝试: {attempt + 1})")
                break
                
        except Exception as e:
            logger.warning(f"第 {attempt + 1} 次连接失败: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # 指数退避
                continue
            else:
                server_response = f"连接服务器失败（已重试 {MAX_RETRIES} 次）：{str(e)}"
                logger.error(f"所有重试均失败: {e}")
    
    return {
        **state,
        "server_response": server_response,
        "messages": state["messages"] + [AIMessage(content=f"服务器响应：{server_response}")]
    }

def postprocess_response_node(state: ClientState) -> ClientState:
    """Postprocess server response for better user experience."""
    server_response = state["server_response"]
    user_input = state["user_input"]
    
    # Check if server response contains error information
    if "连接服务器失败" in server_response or "出错" in server_response:
        # Use LLM to handle error cases
        messages = [
            HumanMessage(content=f"""
            用户问题：{user_input}
            错误信息：{server_response}
            
            请给用户一个友好的错误提示和建议，不要包含"以下是"、"这里是"等引导语。
            """)
        ]
        response = llm.invoke(messages)
        final_response = response.content
    else:
        # For successful responses, use the server response directly
        final_response = server_response
    
    return {
        **state,
        "final_response": final_response,
        "messages": state["messages"] + [AIMessage(content=final_response)]
    }

# Create the client LangGraph workflow
def create_client_workflow():
    """Create the LangGraph workflow for the MCP client."""
    workflow = StateGraph(ClientState)
    
    # Add nodes
    workflow.add_node("preprocess_request", preprocess_request_node)
    workflow.add_node("send_to_server", send_to_server_node)
    workflow.add_node("postprocess_response", postprocess_response_node)
    
    # Add edges
    workflow.add_edge("preprocess_request", "send_to_server")
    workflow.add_edge("send_to_server", "postprocess_response")
    workflow.add_edge("postprocess_response", END)
    
    # Set entry point
    workflow.set_entry_point("preprocess_request")
    
    return workflow.compile()

# Create the client workflow
client_workflow = create_client_workflow()

async def process_user_input(user_input: str) -> str:
    """Process user input through the client workflow."""
    try:
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_input": user_input,
            "processed_request": "",
            "server_response": "",
            "final_response": ""
        }
        
        # Run the workflow asynchronously
        result = await client_workflow.ainvoke(initial_state)
        
        return result["final_response"]
    
    except Exception as e:
        return f"处理请求时出错：{str(e)}"

async def main():
    """Main client loop with LangGraph integration."""
    print("MCP客户端已启动，集成LangGraph智能体")
    print("支持的功能：天气查询、数学计算")
    print("输入 'exit' 退出程序\n")
    
    while True:
        try:
            user_input = input("请输入您的问题: ").strip()
            
            if user_input.lower() in ["exit", "quit", "退出"]:
                print("再见！")
                break
            
            if not user_input:
                print("请输入有效的问题。")
                continue
            
            print("正在处理您的请求...")
            
            # Process through LangGraph workflow
            response = await process_user_input(user_input)
            
            print(f"\n回复: {response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"发生错误：{str(e)}")

if __name__ == "__main__":
    asyncio.run(main())