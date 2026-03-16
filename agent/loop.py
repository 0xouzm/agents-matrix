"""Claude API agentic loop with MCP tool bridge."""

from __future__ import annotations

import logging
from typing import Any

import anthropic
from mcp import ClientSession

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a Calibre ebook agent. Use the available tools to fulfill the user's "
    "request about ebook conversion, metadata management, or library operations. "
    "Call tools as needed, then provide a clear summary of what was done."
)

MAX_TURNS = 10


def mcp_tools_to_claude(mcp_tools: list) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to Anthropic API tool format."""
    claude_tools = []
    for tool in mcp_tools:
        claude_tools.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        })
    return claude_tools


async def run_agent_loop(
    prompt: str,
    mcp_session: ClientSession,
    *,
    api_key: str,
    model: str,
) -> str:
    """Run an agentic loop: Claude calls MCP tools until it produces a final answer.

    Returns the final text response from Claude.
    """
    tools_result = await mcp_session.list_tools()
    claude_tools = mcp_tools_to_claude(tools_result.tools)
    logger.info("MCP tools loaded: %s", [t["name"] for t in claude_tools])

    client = anthropic.AsyncAnthropic(api_key=api_key)
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

    for turn in range(MAX_TURNS):
        response = await client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=claude_tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return _extract_text(response)

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            return _extract_text(response)

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in tool_use_blocks:
            logger.info("Tool call [turn %d]: %s(%s)", turn + 1, block.name, block.input)
            try:
                result = await mcp_session.call_tool(block.name, arguments=block.input)
                content = _format_tool_result(result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": content,
                })
            except Exception as exc:
                logger.warning("Tool %s failed: %s", block.name, exc)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(exc),
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_results})

    return _extract_text(response)


def _extract_text(response: anthropic.types.Message) -> str:
    """Extract text content from a Claude response."""
    parts = [b.text for b in response.content if b.type == "text"]
    return "\n".join(parts) if parts else ""


def _format_tool_result(result: Any) -> str:
    """Format MCP tool result as string for Claude."""
    if hasattr(result, "content") and result.content:
        parts = []
        for item in result.content:
            if hasattr(item, "text"):
                parts.append(item.text)
        return "\n".join(parts) if parts else str(result)
    return str(result)
