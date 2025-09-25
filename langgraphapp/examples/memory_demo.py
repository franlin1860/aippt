import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

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

def get_weather(city: str) -> str:
    """Gets the weather for a specified city."""
    return f"The weather in {city} is always sunny!"

# Create a memory saver
checkpointer = MemorySaver()

# Create the ReAct agent with memory
agent = create_react_agent(
    model=llm,
    tools=[get_weather],
    prompt="您是一个有记忆的乐于助人的助手",
    checkpointer=checkpointer
)

# Create a thread ID for the conversation
thread_id = "user-123"

# First interaction
result1 = agent.invoke(
    {"messages": [{"role": "user", "content": "我叫 Alice"}]},
    config={"configurable": {"thread_id": thread_id}}
)

# Second interaction (agent should remember the name)
result2 = agent.invoke(
    {"messages": [{"role": "user", "content": "我叫什么名字？"}]},
    config={"configurable": {"thread_id": thread_id}}
)

print(result2["messages"][-1].content)