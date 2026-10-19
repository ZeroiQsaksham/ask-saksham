"""The agent loop: the LLM decides which tools to call, we run them, and the
final answer is streamed back token by token."""
from collections.abc import AsyncIterator
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app import config
from app.prompts import SYSTEM_PROMPT
from app.tools import TOOLS, TOOLS_BY_NAME


@lru_cache(maxsize=1)
def get_llm():
    from langchain_groq import ChatGroq

    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
    llm = ChatGroq(
        model=config.GROQ_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0.2,
        max_retries=3,  # the Groq client backs off and retries on rate limits (HTTP 429)
    )
    return llm.bind_tools(TOOLS)


def build_messages(question: str, history: list[dict]) -> list:
    """Conversation memory: the browser sends recent turns with every request."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for turn in history[-config.MAX_HISTORY_MESSAGES:]:
        content = str(turn.get("content", ""))[: config.MAX_QUESTION_CHARS * 2]
        if turn.get("role") == "user":
            messages.append(HumanMessage(content=content))
        elif turn.get("role") == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=question))
    return messages


def run_tool(call: dict) -> ToolMessage:
    tool = TOOLS_BY_NAME.get(call["name"])
    try:
        output = tool.invoke(call["args"]) if tool else f"Unknown tool: {call['name']}"
    except Exception as exc:  # keep the conversation alive if a tool fails
        output = f"Tool error: {exc}"
    return ToolMessage(content=str(output), tool_call_id=call["id"])


async def stream_answer(question: str, history: list[dict]) -> AsyncIterator[str]:
    """Agent loop (think -> act -> observe), streaming the final answer's tokens."""
    llm = get_llm()
    messages = build_messages(question, history)

    for _ in range(config.MAX_TOOL_ROUNDS + 1):
        response = None
        async for chunk in llm.astream(messages):
            response = chunk if response is None else response + chunk
            if chunk.content:
                yield chunk.content

        if response is None or not response.tool_calls:
            return  # final answer has already been streamed

        messages.append(response)
        for call in response.tool_calls:
            messages.append(run_tool(call))

    yield "\n\nSorry, I couldn't finish that answer. Please try rephrasing your question."
