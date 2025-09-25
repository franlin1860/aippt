"""
This example demonstrates how to create a chat bot that helps a user generate a prompt.

The bot first collects requirements from the user and then generates the prompt,
refining it based on user input. These two phases are modeled as separate states
in the graph, and the LLM decides when to transition between them.
"""
import os
from dotenv import load_dotenv

import uuid
from typing import List, Annotated

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from typing_extensions import TypedDict

from langchain_community.chat_models import ChatTongyi
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel


# --- 1. Define the State ---
class State(TypedDict):
    """
    Represents the state of our conversation.
    - messages: A list of messages in the conversation.
    """

    messages: Annotated[list, add_messages]


# --- 2. Define the Tools ---
class PromptInstructions(BaseModel):
    """
    Instructions on how to generate a prompt for the LLM.
    This tool is called when all necessary information has been gathered from the user.
    """

    objective: str
    variables: List[str]
    constraints: List[str]
    requirements: List[str]


# --- 3. Initialize the Model and Tools ---
# Load environment variables
load_dotenv()

# Check for the API key
if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("Please set DASHSCOPE_API_KEY in your .env file")

llm = ChatTongyi(
    model="qwen3-32b",
    temperature=0.3,
    streaming=False,
    max_tokens=2048,
    model_kwargs={"enable_thinking": False},
)
llm_with_tool = llm.bind_tools([PromptInstructions])

# --- 4. Define Graph Nodes ---

# System prompt for the information gathering phase
INFO_GATHERING_SYSTEM_PROMPT = """Your job is to get information from a user about what type of prompt template they want to create.

You should get the following information from them:

- What the objective of the prompt is
- What variables will be passed into the prompt template
- Any constraints for what the output should NOT do
- Any requirements that the output MUST adhere to

If you are not able to discern this info, ask them to clarify! Do not attempt to wildly guess.

After you are able to discern all the information, call the relevant tool."""


def info_gathering_node(state: State) -> State:
    """
    This node is responsible for gathering information from the user.
    It invokes the LLM with the tool to decide when to transition to prompt generation.
    """
    print("---INFO GATHERING---")
    messages = [SystemMessage(content=INFO_GATHERING_SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tool.invoke(messages)
    return {"messages": [response]}


# System prompt for the prompt generation phase
PROMPT_GENERATION_SYSTEM_PROMPT = """Based on the following requirements, write a good prompt template:

{reqs}"""


def prompt_generation_node(state: State) -> State:
    """
    This node generates the final prompt based on the gathered requirements.
    """
    print("---PROMPT GENERATION---")
    # Find the tool call with the prompt instructions
    tool_call = None
    other_msgs = []
    for m in state["messages"]:
        if isinstance(m, AIMessage) and m.tool_calls:
            tool_call = m.tool_calls[0]["args"]
        elif isinstance(m, ToolMessage):
            continue
        elif tool_call is not None:
            other_msgs.append(m)

    # Create the messages for the prompt generation call
    messages = [
        SystemMessage(content=PROMPT_GENERATION_SYSTEM_PROMPT.format(reqs=tool_call))
    ] + other_msgs
    response = llm.invoke(messages)
    return {"messages": [response]}


def add_tool_message_node(state: State) -> State:
    """
    Adds a ToolMessage to the state to confirm that the prompt has been generated.
    This is a necessary step to connect the two phases of the graph.
    """
    print("---PROMPT GENERATED---")
    last_message = state["messages"][-1]
    tool_call_id = last_message.tool_calls[0]["id"]
    return {
        "messages": [
            ToolMessage(
                content="Prompt requirements received. Generating prompt now.",
                tool_call_id=tool_call_id,
            )
        ]
    }


# --- 5. Define the Router ---
def router(state: State) -> str:
    """
    This function decides the next step in the graph based on the current state.
    """
    print("---ROUTING---")
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # If the AI calls the tool, we move to add the tool message
        return "add_tool_message"
    elif not isinstance(last_message, HumanMessage):
        # If the last message is not from the user, end the turn
        return END
    # Otherwise, continue gathering information
    return "info_gathering"


# --- 6. Construct the Graph ---
memory = InMemorySaver()
workflow = StateGraph(State)

workflow.add_node("info_gathering", info_gathering_node)
workflow.add_node("prompt_generation", prompt_generation_node)
workflow.add_node("add_tool_message", add_tool_message_node)

workflow.add_conditional_edges(
    "info_gathering", router, ["add_tool_message", "info_gathering", END]
)
workflow.add_edge("add_tool_message", "prompt_generation")
workflow.add_edge("prompt_generation", END)
workflow.add_edge(START, "info_gathering")

graph = workflow.compile(checkpointer=memory)

# --- 7. Main Execution Loop ---
if __name__ == "__main__":
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    print("Hello! I'm here to help you create a prompt. What is the objective?")

    while True:
        user_input = input("User: ")
        if user_input.lower() in {"q", "quit"}:
            print("AI: Goodbye!")
            break

        events = graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="values",
        )
        for event in events:
            last_message = event["messages"][-1]
            if isinstance(last_message, AIMessage):
                print("AI:", last_message.content)

