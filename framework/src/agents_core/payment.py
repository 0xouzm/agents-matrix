"""x402 payment middleware configuration for the A2A task endpoint."""

from __future__ import annotations

from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer

from agents_core.settings import Settings, Pricing


def build_resource_server(settings: Settings) -> x402ResourceServer:
    """Create an x402 resource server with EVM payment verification."""
    facilitator = HTTPFacilitatorClient(
        FacilitatorConfig(url=settings.facilitator_url)
    )
    server = x402ResourceServer(facilitator)
    server.register(settings.chain_network, ExactEvmServerScheme())
    return server


def build_route_config(settings: Settings, pricing: Pricing) -> dict[str, RouteConfig]:
    """Build x402 route config protecting the A2A JSON-RPC endpoint.

    The A2A protocol uses POST / for all task operations.
    Agent card at /.well-known/agent-card.json stays free.
    """
    return {
        "POST /": RouteConfig(
            accepts=[
                PaymentOption(
                    scheme="exact",
                    price=pricing.default_price,
                    network=settings.chain_network,
                    pay_to=settings.wallet_address,
                ),
            ],
            mime_type="application/json",
            description="A2A task execution",
        ),
    }
