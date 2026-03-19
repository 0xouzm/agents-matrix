"""Sui Agent — skill definitions, system prompt, agent card."""

from __future__ import annotations

from a2a.types import AgentCard, AgentSkill, AgentCapabilities, AgentInterface

from agents_core.settings import Settings

SYSTEM_PROMPT = (
    "You are a Sui blockchain analysis agent powered by the sui client CLI. "
    "You support multiple environments: mainnet, devnet, and testnet.\n\n"
    "Use the available tools to query objects, check balances, inspect gas coins, "
    "look up transaction blocks, and get chain identifiers.\n\n"
    "Each tool accepts an optional 'env' parameter (e.g. 'mainnet', 'devnet', "
    "'testnet'). If the user mentions a network or environment, pass it as the "
    "'env' argument. If no env is specified, omit it — the server will use the "
    "configured default environment automatically.\n\n"
    "In list_supported_envs results, 'configured: true' means that environment is "
    "ready to use; 'configured: false' means no RPC URL is set for it. The entry "
    "with 'default: true' is the active default environment.\n\n"
    "IMPORTANT: Do NOT call list_supported_envs unless the user explicitly asks "
    "which environments are available. For all other requests, just call the "
    "appropriate tool directly.\n\n"
    "Call tools as needed, then provide a clear, human-readable summary of the "
    "results. Format SUI amounts with appropriate decimal places (1 SUI = 10^9 MIST)."
)

SKILLS: list[AgentSkill] = [
    AgentSkill(
        id="object_query",
        name="Object Query",
        description="Look up any Sui object by ID — type, owner, version, and content across mainnet/devnet/testnet.",
        tags=["object", "query", "sui", "multienv"],
        examples=[
            "Show object 0x2::coin::Coin<0x2::sui::SUI>",
            "List all objects owned by this address on devnet",
        ],
    ),
    AgentSkill(
        id="balance_check",
        name="Balance Check",
        description="Check SUI balance and gas coin details for any address.",
        tags=["balance", "gas", "sui", "multienv"],
        examples=[
            "What's the SUI balance of this address?",
            "Show gas coins for this address on testnet",
        ],
    ),
    AgentSkill(
        id="transaction_lookup",
        name="Transaction Lookup",
        description="Look up a transaction block by digest — status, gas cost, effects, and events.",
        tags=["transaction", "tx-block", "digest", "sui", "multienv"],
        examples=[
            "Show transaction block for digest abc123...",
            "What happened in this transaction on mainnet?",
        ],
    ),
    AgentSkill(
        id="network_info",
        name="Network Info",
        description="Get Sui network information — chain identifier, dynamic fields, and environment listing.",
        tags=["chain", "network", "env", "sui", "multienv"],
        examples=[
            "What chain ID is this?",
            "List configured Sui environments",
        ],
    ),
]


def build_agent_card(settings: Settings) -> AgentCard:
    return AgentCard(
        name="Sui Agent",
        description=(
            "Paid AI agent for Sui blockchain analysis — query objects, "
            "check balances, inspect gas coins, look up transaction blocks, "
            "and get chain info across mainnet, devnet, and testnet. "
            "Powered by sui client CLI. Accepts USDC payment via x402 protocol."
        ),
        supported_interfaces=[AgentInterface(url=settings.base_url + "/")],
        version="0.1.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        skills=SKILLS,
    )
