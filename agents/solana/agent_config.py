"""Solana Agent — skill definitions, system prompt, agent card."""

from __future__ import annotations

from a2a.types import AgentCard, AgentSkill, AgentCapabilities, AgentInterface

from agents_core.settings import Settings

SYSTEM_PROMPT = (
    "You are a Solana blockchain analysis agent powered by the solana CLI. "
    "You support multiple clusters: mainnet-beta, devnet, and testnet.\n\n"
    "Use the available tools to query accounts, check balances, inspect blocks, "
    "look up transaction history, get epoch/validator info, and check network supply.\n\n"
    "Each RPC tool accepts an optional 'cluster' parameter (e.g. 'mainnet_beta', "
    "'devnet', 'testnet'). If the user mentions a cluster or network, pass it as "
    "the 'cluster' argument. If no cluster is specified, omit the 'cluster' argument "
    "— the server will use the configured default cluster automatically.\n\n"
    "In list_supported_clusters results, 'configured: true' means that cluster is "
    "ready to use; 'configured: false' means no RPC URL is set for it. The entry "
    "with 'default: true' is the active default cluster.\n\n"
    "IMPORTANT: Do NOT call list_supported_clusters unless the user explicitly asks "
    "which clusters are available. For all other requests, just call the appropriate "
    "tool directly.\n\n"
    "Call tools as needed, then provide a clear, human-readable summary of the results. "
    "Format SOL amounts with appropriate decimal places and include USD estimates when "
    "the context makes it useful."
)

SKILLS: list[AgentSkill] = [
    AgentSkill(
        id="account_info",
        name="Account Info",
        description="Look up any Solana account — balance, owner program, data size, and executable status across mainnet/devnet/testnet.",
        tags=["account", "balance", "solana", "multicluster"],
        examples=[
            "Show account info for So11111111111111111111111111111111111111112",
            "What's the balance of this address on devnet?",
        ],
    ),
    AgentSkill(
        id="transaction_lookup",
        name="Transaction Lookup",
        description="Look up transaction history for a Solana address or confirm a transaction signature.",
        tags=["transaction", "history", "confirm", "solana", "multicluster"],
        examples=[
            "Show transaction history for this address",
            "Confirm transaction signature 5abc...",
        ],
    ),
    AgentSkill(
        id="block_inspect",
        name="Block Inspect",
        description="Inspect a Solana block by slot number — transactions, rewards, and block metadata.",
        tags=["block", "slot", "solana", "multicluster"],
        examples=[
            "Show block at slot 250000000",
            "What's the current slot on devnet?",
        ],
    ),
    AgentSkill(
        id="network_status",
        name="Network Status",
        description="Get Solana network status — current epoch info, total supply, and circulating supply.",
        tags=["epoch", "supply", "network", "solana", "multicluster"],
        examples=[
            "What epoch are we in on mainnet?",
            "Show the total SOL supply",
        ],
    ),
    AgentSkill(
        id="validator_info",
        name="Validator Info",
        description="Query Solana validators and stake accounts — active validators, stake delegation, and deactivation status.",
        tags=["validator", "stake", "delegation", "solana", "multicluster"],
        examples=[
            "List current validators on mainnet",
            "Show stake account details for this address",
        ],
    ),
]


def build_agent_card(settings: Settings) -> AgentCard:
    return AgentCard(
        name="Solana Agent",
        description=(
            "Paid AI agent for Solana blockchain analysis — query accounts, "
            "check balances, inspect blocks, look up transactions, and monitor "
            "validators across mainnet-beta, devnet, and testnet. "
            "Powered by solana CLI. Accepts USDC payment via x402 protocol."
        ),
        supported_interfaces=[AgentInterface(url=settings.base_url + "/")],
        version="0.1.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        skills=SKILLS,
    )
