"""Build the A2A AgentCard with Cast transaction analysis skill definitions."""

from __future__ import annotations

from a2a.types import AgentCard, AgentSkill, AgentCapabilities

from config.settings import get_settings


SKILLS: list[AgentSkill] = [
    AgentSkill(
        id="tx_decode",
        name="Decode Transaction",
        description="Fetch and decode a transaction by hash on any supported EVM chain — shows from, to, value, gas, and input data.",
        tags=["transaction", "decode", "evm", "multichain"],
        examples=[
            "Decode transaction 0xabc123...",
            "Decode tx 0xdef456... on arbitrum",
        ],
    ),
    AgentSkill(
        id="receipt_parse",
        name="Parse Receipt",
        description="Get transaction receipt with status, gas usage analysis, and emitted event logs on any EVM chain.",
        tags=["receipt", "gas", "logs", "evm", "multichain"],
        examples=[
            "Show me the receipt for tx 0xabc123...",
            "Receipt for 0xdef456... on base",
        ],
    ),
    AgentSkill(
        id="trace",
        name="Trace Transaction",
        description="Trace the full execution of a transaction showing internal calls and state changes on any EVM chain.",
        tags=["trace", "debug", "execution", "evm", "multichain"],
        examples=[
            "Trace the execution of tx 0xabc123...",
            "Trace 0xdef456... on polygon",
        ],
    ),
    AgentSkill(
        id="calldata_decode",
        name="Decode Calldata",
        description="Decode hex-encoded calldata using the 4byte signature database (no RPC needed).",
        tags=["calldata", "decode", "4byte", "selector"],
        examples=[
            "Decode this calldata: 0xa9059cbb...",
            "What function does selector 0xa9059cbb call?",
        ],
    ),
    AgentSkill(
        id="log_query",
        name="Query Logs",
        description="Query event logs from a contract address with optional topic and block range filters on any EVM chain.",
        tags=["logs", "events", "contract", "evm", "multichain"],
        examples=[
            "Show Transfer events from USDC on ethereum",
            "Query logs from 0x1234... on arbitrum",
        ],
    ),
    AgentSkill(
        id="block_info",
        name="Block Info",
        description="Get block details by number, hash, or tag on any supported EVM chain.",
        tags=["block", "chain", "evm", "multichain"],
        examples=[
            "Show me the latest block on base",
            "Get info for block 18000000 on ethereum",
        ],
    ),
]


def build_agent_card() -> AgentCard:
    settings = get_settings()
    return AgentCard(
        name="Cast Transaction Agent",
        description=(
            "Paid AI agent for EVM chain transaction analysis — decode transactions, "
            "parse receipts, trace execution, query logs, and inspect blocks across "
            "Ethereum, Arbitrum, Base, Polygon, Optimism, BSC, and more. "
            "Powered by Foundry cast. Accepts USDC payment via x402 protocol."
        ),
        url=settings.base_url + "/",
        version="0.1.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=SKILLS,
    )
