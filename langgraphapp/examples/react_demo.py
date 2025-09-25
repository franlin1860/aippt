import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()

# Check for the API key
if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("Please set DASHSCOPE_API_KEY in your .env file")

# Initialize the Qwen-32B model
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

# Create the ReAct agent
agent = create_react_agent(
    model=llm,
    tools=[get_weather],
    prompt="You are a helpful assistant"
)

# Run the agent
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the weather like in San Francisco?"}]}
)

# Print the result
print(result["messages"][-1].content)