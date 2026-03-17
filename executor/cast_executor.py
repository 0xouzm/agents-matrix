"""A2A AgentExecutor that delegates to the LLM agentic loop + MCP tools."""

from __future__ import annotations

import logging
import os
import sys

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import get_default_environment, stdio_client

from agent.loop import run_agent_loop
from config.settings import Settings

logger = logging.getLogger(__name__)


class CastExecutor(AgentExecutor):
    """Execute Cast transaction analysis tasks via LLM loop backed by MCP tools."""

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
        # MCP's stdio_client only inherits a minimal env whitelist (PATH, HOME, etc.).
        # Explicitly forward all AM_* vars so the MCP subprocess gets RPC URLs,
        # default chain, and other config.
        mcp_env = {
            **get_default_environment(),
            **{k: v for k, v in os.environ.items() if k.startswith("AM_")},
        }
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_server"],
            env=mcp_env,
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await run_agent_loop(
                    prompt,
                    session,
                    api_key=self._settings.llm_api_key,
                    model=self._settings.llm_model,
                    base_url=self._settings.llm_base_url,
                )
