# MCP (多智能体协作协议) 设计文档

本文档概述了使用 `fastmcp` 和 `langgraph` 的 MCP 示例的设计和实现。

## 1. 概述

本项目实现了一个基于 MCP 协议的多智能体系统，其中客户端智能体可以通过 MCP 协议从服务器智能体请求服务。系统使用 `fastmcp` 作为 MCP 协议的实现框架，客户端和服务器都使用 `langgraph` 来管理智能体的工作流逻辑。

### 1.1 核心特性

- **MCP 协议通信**: 使用 FastMCP 的 SSE (Server-Sent Events) 传输机制实现客户端-服务器通信
- **LangGraph 工作流**: 客户端和服务器都采用 LangGraph 构建智能体工作流
- **多功能服务**: 支持天气查询、数学计算和通用对话
- **智能路由**: 服务器端智能体能够根据请求内容自动选择合适的工具
- **友好交互**: 客户端提供自然语言交互界面，支持中文对话

## 2. 组件

### 2.1. MCP 服务器 (`mcp_server.py`)

- **框架:** `fastmcp` 用于 MCP 协议实现，集成 `langgraph` 构建智能体工作流
- **模型:** 使用 `qwen2.5:32b` 作为底层语言模型（通过 LiteLLM 调用）
- **传输机制:** SSE (Server-Sent Events) 传输，监听端口 8000
- **核心服务:**
  - **天气查询服务:** 提供全球城市的实时天气信息
  - **数学计算服务:** 执行各种数学运算和计算
  - **通用对话服务:** 处理一般性问题和对话
- **LangGraph 工作流:** 
  - `analyze_request_node`: 分析用户请求并确定处理策略
  - `weather_node`: 处理天气相关查询
  - `calculator_node`: 处理数学计算请求
  - `general_chat_node`: 处理通用对话
  - `format_response_node`: 格式化最终响应

### 2.2. MCP 客户端 (`mcp_client.py`)

- **框架:** 使用 MCP 客户端库连接服务器，集成 `langgraph` 构建客户端工作流
- **模型:** `qwen2.5:32b` 用于请求预处理和响应后处理
- **连接方式:** 通过 SSE 传输连接到 `http://localhost:8000/sse`
- **核心功能:**
  - 交互式命令行界面
  - 智能请求预处理
  - MCP 协议通信
  - 响应后处理和展示
- **LangGraph 工作流:**
  - `preprocess_request_node`: 预处理用户输入
  - `send_to_server_node`: 通过 MCP 协议发送请求到服务器
  - `postprocess_response_node`: 后处理服务器响应

### 2.3. 工具模块 (`tools.py`)

- **天气工具 (`get_weather`):** 
  - 支持全球主要城市天气查询
  - 返回温度、天气状况、湿度等信息
  - 内置城市数据库，支持中英文城市名
- **计算器工具 (`calculator`):**
  - 支持基本算术运算（+、-、*、/）
  - 支持高级数学函数（sin、cos、log、sqrt等）
  - 安全的表达式求值机制

## 3. 技术架构

### 3.1. MCP 协议通信

- **传输层:** 使用 FastMCP 的 SSE (Server-Sent Events) 传输机制
- **协议:** 遵循 MCP (Model Context Protocol) 规范
- **端点:** 服务器监听 `http://localhost:8000/sse`
- **工具调用:** 客户端通过 `process_request` 工具与服务器交互

### 3.2. LangGraph 工作流架构

#### 服务器端工作流
```
用户请求 → analyze_request_node → 路由决策
                ↓
    ┌─ weather_node (天气查询)
    ├─ calculator_node (数学计算)  
    └─ general_chat_node (通用对话)
                ↓
        format_response_node → 格式化响应
```

#### 客户端工作流
```
用户输入 → preprocess_request_node → send_to_server_node → postprocess_response_node → 输出结果
```

### 3.3. 状态管理

- **服务器状态:** 包含 `request`、`analysis`、`tool_result`、`response` 等字段
- **客户端状态:** 包含 `user_input`、`processed_request`、`server_response`、`final_response` 等字段
- **状态流转:** 通过 LangGraph 的状态机制管理数据流

## 4. 目录结构

```
mcpapp/
├── mcp_design.md          # 设计文档
├── mcp_server.py          # MCP 服务器实现
├── mcp_client.py          # MCP 客户端实现
├── tools.py               # 工具函数实现
├── requirements.txt       # 依赖包列表
├── .env                   # 环境变量配置
└── venv/                  # 虚拟环境
```

## 5. 实现细节

### 5.1. FastMCP 服务器集成

服务器使用 FastMCP 框架，通过 `@mcp.tool` 装饰器暴露 `process_request` 工具。该工具接收客户端请求，通过 LangGraph 工作流处理，并返回结构化响应。

### 5.2. LangGraph 智能体工作流

#### 服务器端智能路由
- `analyze_request_node`: 使用 LLM 分析请求类型（天气、计算、对话）
- 条件路由: 根据分析结果选择对应的处理节点
- 工具调用: 各节点调用相应的工具函数处理具体请求

#### 客户端端到端处理
- `preprocess_request_node`: 优化用户输入格式
- `send_to_server_node`: 处理 MCP 通信和错误处理
- `postprocess_response_node`: 格式化服务器响应为用户友好的输出

### 5.3. 错误处理和容错机制

- **连接错误处理:** 客户端检测服务器连接状态，提供友好错误提示
- **工具调用错误:** 服务器端捕获工具执行异常，返回错误信息
- **响应解析:** 客户端正确解析 `CallToolResult` 对象，提取实际内容

### 5.4. 模型配置

系统使用 `qwen2.5:32b` 模型，通过 LiteLLM 进行统一调用。模型配置支持本地部署和云端API调用。

## 6. 工作流程

### 6.1. 完整交互流程

1. **启动服务器**: 运行 `python mcp_server.py`，启动 FastMCP 服务器
2. **启动客户端**: 运行 `python mcp_client.py`，建立与服务器的 MCP 连接
3. **用户输入**: 用户在客户端输入查询（如"北京天气"、"5*3"、"你好"）
4. **客户端预处理**: `preprocess_request_node` 优化用户输入格式
5. **MCP 通信**: `send_to_server_node` 通过 `process_request` 工具发送请求
6. **服务器分析**: `analyze_request_node` 分析请求类型和意图
7. **智能路由**: 根据分析结果路由到相应处理节点：
   - 天气查询 → `weather_node` → 调用 `get_weather` 工具
   - 数学计算 → `calculator_node` → 调用 `calculator` 工具  
   - 通用对话 → `general_chat_node` → LLM 直接回复
8. **响应格式化**: `format_response_node` 格式化最终响应
9. **返回客户端**: 服务器通过 MCP 协议返回处理结果
10. **客户端后处理**: `postprocess_response_node` 格式化显示给用户
11. **用户查看**: 客户端展示最终结果

### 6.2. 错误处理流程

- **服务器未启动**: 客户端检测连接失败，提示用户启动服务器
- **工具执行错误**: 服务器捕获异常，返回友好错误信息
- **网络中断**: 客户端重试连接，超时后提示网络问题
- **响应解析错误**: 客户端使用备用解析方法，确保用户获得反馈

### 6.3. 示例交互

#### 天气查询示例
```
用户输入: "北京天气怎么样？"
↓ 客户端预处理
处理后请求: "请查询北京的天气情况"
↓ MCP 通信
服务器分析: 识别为天气查询请求
↓ 路由到天气节点
工具调用: get_weather("北京")
↓ 工具返回
结果: {"city": "北京", "temperature": "22°C", "condition": "晴朗"}
↓ 响应格式化
最终响应: "北京当前天气：晴朗，温度22°C，适合外出活动。"
```

#### 数学计算示例
```
用户输入: "5*3"
↓ 客户端预处理  
处理后请求: "请计算 5 乘以 3"
↓ MCP 通信
服务器分析: 识别为数学计算请求
↓ 路由到计算器节点
工具调用: calculator("5*3")
↓ 工具返回
结果: 15
↓ 响应格式化
最终响应: "5 × 3 = 15"
```

## 8. 故障排除

### 8.1. 已知问题及解决方案

#### 问题1: 客户端无法正确解析服务器响应
**症状**: 客户端收到服务器响应但显示错误或无内容
**原因**: `CallToolResult` 对象解析不正确
**解决方案**: 更新 `send_to_server_node` 函数中的响应处理逻辑：
```python
# 正确的响应解析方法
if hasattr(response, 'data') and response.data:
    return response.data
elif hasattr(response, 'content'):
    if isinstance(response.content, list):
        return ' '.join([item.text for item in response.content if hasattr(item, 'text')])
    return response.content
else:
    return str(response)
```

#### 问题2: 客户端响应包含不必要的前缀
**症状**: 响应中出现"回复: 当然！以下是..."等前缀
**原因**: `postprocess_response_node` 使用LLM重新格式化响应
**解决方案**: 直接使用服务器响应，仅在错误情况下使用LLM格式化

#### 问题3: MCP 连接失败
**症状**: 客户端无法连接到服务器
**排查步骤**:
1. 确认服务器已启动: `python mcp_server.py`
2. 检查端口占用: `lsof -i :8000`
3. 验证网络连接: `curl http://localhost:8000/sse`
4. 检查防火墙设置

#### 问题4: 工具调用异常
**症状**: 服务器返回工具执行错误
**排查方法**:
1. 检查 `tools.py` 中工具函数实现
2. 验证输入参数格式
3. 查看服务器日志输出
4. 测试工具函数独立运行

### 8.2. 调试技巧

#### 启用详细日志
在 `.env` 文件中设置:
```
DEBUG=true
LOG_LEVEL=debug
```

#### 测试MCP连接
使用独立测试脚本验证客户端-服务器通信:
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 测试连接和工具调用
async def test_connection():
    async with stdio_client(StdioServerParameters(command="python", args=["mcp_server.py"])) as (read, write):
        async with ClientSession(read, write) as session:
            tools = await session.list_tools()
            result = await session.call_tool("process_request", {"message": "test"})
            print(result)
```

#### 分步调试
1. **服务器端**: 在各个节点添加日志输出
2. **客户端**: 检查每个工作流步骤的状态
3. **网络层**: 使用网络抓包工具监控MCP通信

### 8.3. 性能优化

#### 响应时间优化
- 使用本地模型部署减少网络延迟
- 实现响应缓存机制
- 优化LangGraph工作流路径

#### 内存使用优化  
- 限制LangGraph状态大小
- 定期清理客户端会话状态
- 使用流式响应处理大型结果

## 7. 部署和测试

### 7.1. 环境准备

1. **创建虚拟环境**:
   ```bash
   cd mcpapp
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 或 venv\Scripts\activate  # Windows
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **环境配置**:
   创建 `.env` 文件并配置必要的环境变量：
   ```
   # 模型配置
   LITELLM_MODEL=qwen2.5:32b
   
   # 调试配置（可选）
   DEBUG=false
   LOG_LEVEL=info
   ```

### 7.2. 启动和运行

1. **启动MCP服务器**:
   ```bash
   python mcp_server.py
   ```
   服务器将在 `http://localhost:8000` 启动，显示启动信息。

2. **启动MCP客户端**:
   在新终端中：
   ```bash
   source venv/bin/activate
   python mcp_client.py
   ```

3. **交互测试**:
   客户端启动后，可以进行以下测试：
   - **天气查询**: `北京天气怎么样？`
   - **数学计算**: `123 * 456`
   - **通用对话**: `你好，介绍一下自己`
   - **退出程序**: `quit` 或 `exit`

### 7.3. 功能验证

#### 天气查询测试
```
输入: 上海天气
预期输出: 显示上海的天气信息（温度、天气状况等）
```

#### 数学计算测试  
```
输入: 2^10
预期输出: 2 的 10 次方 = 1024
```

#### 错误处理测试
```
输入: 火星天气
预期输出: 友好的错误提示，说明不支持该城市
```

### 7.4. 性能基准

- **响应时间**: 正常情况下 < 3秒
- **并发支持**: 支持多个客户端同时连接
- **内存使用**: 服务器端 < 500MB，客户端 < 100MB