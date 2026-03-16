"""LLM agentic loop with MCP tool bridge (OpenAI-compatible API)."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI
from mcp import ClientSession

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a blockchain transaction analysis agent powered by Foundry cast. "
    "You support multiple EVM chains: Ethereum, Arbitrum, Base, Polygon, Optimism, "
    "BSC, Avalanche, Linea, Scroll, zkSync, and Blast. "
    "Use the available tools to decode transactions, parse receipts, trace execution, "
    "query event logs, and inspect blocks. Each RPC tool accepts an optional 'chain' "
    "parameter (e.g. 'ethereum', 'arbitrum', 'base'). If the user mentions a chain, "
    "pass it as the 'chain' argument. Use list_supported_chains to show available chains. "
    "Call tools as needed, then provide a clear, human-readable summary of the results."
)

MAX_TURNS = 10


def mcp_tools_to_openai(mcp_tools: list) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to OpenAI function-calling format."""
    openai_tools = []
    for tool in mcp_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            },
        })
    return openai_tools


async def run_agent_loop(
    prompt: str,
    mcp_session: ClientSession,
    *,
    api_key: str,
    model: str,
    base_url: str,
) -> str:
    """Run an agentic loop: LLM calls MCP tools until it produces a final answer."""
    tools_result = await mcp_session.list_tools()
    openai_tools = mcp_tools_to_openai(tools_result.tools)
    logger.info("MCP tools loaded: %s", [t["function"]["name"] for t in openai_tools])

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    for turn in range(MAX_TURNS):
        response = await client.chat.completions.create(
            model=model,
            max_tokens=4096,
            tools=openai_tools,
            messages=messages,
        )

        choice = response.choices[0]

        if choice.finish_reason != "tool_calls":
            return choice.message.content or ""

        messages.append(choice.message)

        for tool_call in choice.message.tool_calls:
            fn = tool_call.function
            logger.info("Tool call [turn %d]: %s(%s)", turn + 1, fn.name, fn.arguments)
            try:
                args = json.loads(fn.arguments) if fn.arguments else {}
                result = await mcp_session.call_tool(fn.name, arguments=args)
                content = _format_tool_result(result)
            except Exception as exc:
                logger.warning("Tool %s failed: %s", fn.name, exc)
                content = f"Error: {exc}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": content,
            })

    return choice.message.content or ""


def _format_tool_result(result: Any) -> str:
    """Format MCP tool result as string."""
    if hasattr(result, "content") and result.content:
        parts = []
        for item in result.content:
            if hasattr(item, "text"):
                parts.append(item.text)
        return "\n".join(parts) if parts else str(result)
    return str(result)
