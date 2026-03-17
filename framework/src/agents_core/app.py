"""App factory: compose FastAPI + A2A + x402 into a single ASGI application."""

from __future__ import annotations

import logging

from a2a.types import AgentCard
from fastapi import FastAPI
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from x402.http.middleware.fastapi import PaymentMiddlewareASGI

from agents_core.settings import Settings, Pricing
from agents_core.payment import build_resource_server, build_route_config
from agents_core.executor import MCPAgentExecutor

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings,
    pricing: Pricing,
    *,
    agent_card: AgentCard,
    mcp_module: str,
    system_prompt: str,
) -> FastAPI:
    """Build the full application stack.

    Args:
        settings: Application settings.
        pricing: Per-skill pricing config.
        agent_card: A2A AgentCard describing this agent's skills.
        mcp_module: Python module name for the MCP server (e.g. "mcp_entry").
        system_prompt: System prompt for the LLM agent loop.
    """
    app = FastAPI(title=agent_card.name, version=agent_card.version or "0.1.0")

    # -- A2A agent --
    executor = MCPAgentExecutor(
        settings=settings,
        mcp_module=mcp_module,
        system_prompt=system_prompt,
    )
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    a2a_app.add_routes_to_app(app)

    # -- x402 payment gate --
    if settings.wallet_address:
        resource_server = build_resource_server(settings)
        route_config = build_route_config(settings, pricing)
        app.add_middleware(PaymentMiddlewareASGI, routes=route_config, server=resource_server)
        logger.info("x402 payment gate enabled for POST /")
    else:
        logger.warning("No wallet address configured — x402 payment gate DISABLED")

    # -- Utility endpoints --
    service_name = agent_card.name.lower().replace(" ", "-")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": service_name}

    return app
