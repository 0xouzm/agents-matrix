"""A2A AgentExecutor that delegates to the Claude agentic loop + MCP tools."""

from __future__ import annotations

import logging
import sys

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent.loop import run_agent_loop
from config.settings import Settings

logger = logging.getLogger(__name__)


class CalibreExecutor(AgentExecutor):
    """Execute Calibre tasks via Claude agentic loop backed by MCP tools."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        logger.info("Received task: %s", user_input[:200])

        try:
            result = await self._run_with_mcp(user_input)
            await event_queue.enqueue_event(new_agent_text_message(result))
        except Exception as exc:
            logger.exception("Task execution failed")
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: {exc}")
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            new_agent_text_message("Task cancellation is not supported.")
        )

    async def _run_with_mcp(self, prompt: str) -> str:
        """Spawn MCP server, create session, run agent loop."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_server"],
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await run_agent_loop(
                    prompt,
                    session,
                    api_key=self._settings.anthropic_api_key,
                    model=self._settings.anthropic_model,
                )
