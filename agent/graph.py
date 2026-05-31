"""LangGraph agent pipeline for the Market Intelligence AI."""
import os
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agent.prompts import SYSTEM_PROMPT
from agent.tools import (
    get_top_hiring_companies,
    get_trending_skills,
    query_database,
    summarize_recent_news,
)

tools = [query_database, get_trending_skills, get_top_hiring_companies, summarize_recent_news]


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def _get_llm():
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    ).bind_tools(tools)


def agent_node(state: AgentState) -> AgentState:
    llm = _get_llm()
    msgs = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in msgs):
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + list(msgs)
    response = llm.invoke(msgs)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))
builder.set_entry_point("agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

graph = builder.compile()
