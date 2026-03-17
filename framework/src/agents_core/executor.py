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

from agents_core.loop import run_agent_loop
from agents_core.settings import Settings

logger = logging.getLogger(__name__)


class MCPAgentExecutor(AgentExecutor):
    """Execute tasks via LLM loop backed by MCP tools.

    Generic executor — the MCP module and system prompt are injected,
    so the same class works for any agent (cast, solc, etc.).
    """

    def __init__(
        self,
        settings: Settings,
        *,
        mcp_module: str,
        system_prompt: str,
    ) -> None:
        self._settings = settings
        self._mcp_module = mcp_module
        self._system_prompt = system_prompt

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
        mcp_env = {
            **get_default_environment(),
            **{k: v for k, v in os.environ.items() if k.startswith("AM_")},
        }
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", self._mcp_module],
            env=mcp_env,
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await run_agent_loop(
                    prompt,
                    session,
                    system_prompt=self._system_prompt,
                    api_key=self._settings.llm_api_key,
                    model=self._settings.llm_model,
                    base_url=self._settings.llm_base_url,
                )
