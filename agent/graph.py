"""LangGraph agent pipeline — uses create_react_agent (LangGraph 1.x API)."""
import logging
import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# LangSmith tracing — enabled when LANGCHAIN_TRACING_V2=true in .env
if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true":
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    if api_key and not api_key.startswith("your-"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "ai-market-intelligence")
        logger.info("LangSmith tracing enabled — project: %s", os.environ["LANGCHAIN_PROJECT"])
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.prompts import SYSTEM_PROMPT
from agent.tools import (
    get_top_hiring_companies,
    get_trending_skills,
    query_database,
    summarize_recent_news,
)

tools = [query_database, get_trending_skills, get_top_hiring_companies, summarize_recent_news]


def _build_graph():
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    system_message = SystemMessage(
        content=SYSTEM_PROMPT.replace("{today}", date.today().isoformat())
    )
    return create_react_agent(model=llm, tools=tools, prompt=system_message)


graph = _build_graph()
