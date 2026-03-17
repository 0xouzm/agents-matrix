# Agents Matrix

A monorepo platform for building **paid AI agents** — each wrapping a CLI tool as an Agent-as-a-Service via [A2A protocol](https://github.com/google/A2A) + [x402 payment](https://www.x402.org/).

Each agent is backed by a CLI harness from [CLI-Anything (HKUDS)](https://github.com/HKUDS/CLI-Anything) — a collection of agent-friendly CLI wrappers for real-world software tools. The harness outputs structured JSON, the agent wraps it as MCP tools, the framework exposes it as a paid A2A service.

```
CLI-Anything harness        agents-matrix agent
────────────────────        ──────────────────────────────────────
cast/agent-harness     →    agents/cast/    EVM transaction analysis  (live)
<tool>/agent-harness   →    agents/<tool>/  <description>             (next)
```

## Architecture

```
agents-matrix/
  framework/                    ← agents-core: shared package for all agents
    src/agents_core/
      app.py                      create_app() factory
      executor.py                 MCPAgentExecutor (A2A → MCP bridge)
      loop.py                     LLM agentic loop (OpenAI-compatible)
      payment.py                  x402 middleware helpers
      registration.py             ERC-8004 on-chain registration
      settings.py                 Settings, ChainRegistry, Pricing
  agents/
    cast/                       ← Cast Transaction Agent
      agent_config.py             SYSTEM_PROMPT, skills, agent card
      mcp_tools.py                9 MCP tools (cast-specific)
      mcp_entry.py                MCP stdio entry point
      main.py                     thin entry (~25 lines)
  pyproject.toml                ← uv workspace
```

Each agent only needs 4–5 tool-specific files. The framework handles everything else: A2A server, x402 payment gate, LLM tool-use loop, MCP subprocess management, and on-chain registration.

## Request Flow

```
Client (A2A JSON-RPC)
    │
    ▼
FastAPI + x402 middleware ── payment verification
    │
    ▼
MCPAgentExecutor ── spawns MCP subprocess
    │
    ▼
LLM Agent Loop ── tool-use with OpenAI-compatible API
    │
    ▼
MCP Server ── @mcp.tool() functions
    │
    ▼
CLI Harness ── subprocess calls to CLI binary
```

## Quick Start

### Docker (recommended)

```bash
cd agents/cast
cp .env.example .env
# Edit .env: set AM_LLM_API_KEY and at least one AM_RPC_* URL

./scripts/deploy.sh
```

No need to install Foundry, Python, or uv on the host — the Docker image handles everything.

### Local Development

```bash
# Prerequisites: Python 3.12+, uv, Foundry cast
# Also need CLI-Anything repo cloned at ../../CLI-Anything

# Install workspace
uv sync --prerelease=allow --all-packages

# Configure
cd agents/cast
cp .env.example .env
# Edit .env

# Run
uv run python main.py
```

### Verify

```bash
# Health check
curl http://localhost:9000/health
# → {"status":"ok","service":"cast-transaction-agent"}

# A2A agent card
curl http://localhost:9000/.well-known/agent-card.json

# Send a task (with x402 payment disabled)
curl -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "id": "test-1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Decode tx 0xabc123... on ethereum"}]
      }
    }
  }'
```

## Cast Transaction Agent

Multi-chain EVM transaction analysis powered by [Foundry cast](https://book.getfoundry.sh/cast/).

### Skills

| Skill | Description |
|-------|-------------|
| Decode Transaction | Fetch and decode a transaction by hash on any EVM chain |
| Parse Receipt | Transaction receipt with status, gas usage, event logs |
| Trace Transaction | Full execution trace with internal calls |
| Decode Calldata | Decode hex calldata via 4byte signature database |
| Query Logs | Event logs with topic and block range filters |
| Block Info | Block details by number, hash, or tag |

### MCP Tools

| Tool | RPC | Chain param |
|------|-----|-------------|
| `list_supported_chains` | No | No |
| `get_transaction` | Yes | Yes |
| `get_receipt` | Yes | Yes |
| `trace_transaction` | Yes | Yes |
| `decode_calldata` | No | No |
| `get_selector` | No | No |
| `query_logs` | Yes | Yes |
| `call_contract` | Yes | Yes |
| `get_block` | Yes | Yes |

### Supported Chains

Ethereum, Arbitrum, Base, Polygon, Optimism, BSC, Avalanche, Linea, Scroll, zkSync, Blast.

Chain metadata lives in `agents/cast/config/chains.toml`. RPC URLs are resolved from `AM_RPC_{CHAIN}` environment variables.

### Use as Claude MCP Server

```bash
cd agents/cast
claude mcp add cast -- uv run python -m mcp_entry
```

## Adding a New Agent

The source of truth for CLI harnesses is [CLI-Anything (HKUDS)](https://github.com/HKUDS/CLI-Anything). Pick an existing harness (Blender, ComfyUI, Audacity, LibreOffice, etc.) or write a new one following the same pattern — any CLI framework works as long as it supports `--json` structured output.

1. Get or write a CLI harness (`<tool>/agent-harness/`) in the CLI-Anything repo
2. Create `agents/<name>/` with:

| File | Purpose |
|------|---------|
| `agent_config.py` | SYSTEM_PROMPT, SKILLS list, `build_agent_card()` |
| `mcp_tools.py` | `@mcp.tool()` functions calling CLI harness via subprocess |
| `mcp_entry.py` | `from mcp_tools import mcp; mcp.run()` |
| `main.py` | Thin entry point using `agents_core.app.create_app()` |
| `pyproject.toml` | Depends on `agents-core` + CLI harness |
| `config/` | chains.toml, pricing.toml |

3. Run `uv sync --prerelease=allow --all-packages` from workspace root

## Environment Variables

All variables use the `AM_` prefix. See [`agents/cast/.env.example`](agents/cast/.env.example) for the full list.

| Variable | Required | Description |
|----------|----------|-------------|
| `AM_LLM_API_KEY` | Yes | LLM API key (DeepSeek, OpenAI, etc.) |
| `AM_DEFAULT_CHAIN` | Yes | Default chain slug (e.g. `ethereum`) |
| `AM_RPC_ETHEREUM` | Per chain | RPC URL for Ethereum |
| `AM_RPC_ARBITRUM` | Per chain | RPC URL for Arbitrum |
| `AM_WALLET_ADDRESS` | No | EVM wallet — enables x402 payment gate |
| `AM_PRIVATE_KEY` | No | For ERC-8004 on-chain registration |

## Key Dependencies

| Package | Purpose |
|---------|---------|
| [a2a-sdk](https://github.com/google/A2A) | Google A2A protocol (agent-to-agent) |
| [x402](https://github.com/coinbase/x402) | Coinbase payment middleware (USDC) |
| [agent0-sdk](https://github.com/agent0-labs/agent0-sdk) | ERC-8004 on-chain agent registration |
| [mcp](https://modelcontextprotocol.io/) | Model Context Protocol tool server |
| [openai](https://github.com/openai/openai-python) | LLM agent loop (any OpenAI-compatible API) |

## License

MIT
