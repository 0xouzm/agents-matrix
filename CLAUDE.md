# Agents Matrix — Cast Transaction Agent

Paid Agent-as-a-Service platform — multi-chain EVM transaction analysis via A2A protocol + x402 payment.

## Architecture

```
Client (A2A) → FastAPI + x402 middleware → CastExecutor → MCP Server → cli-anything-cast → Foundry cast
```

- **Entry point**: `main.py` → `server/app.py` app factory
- **Config**: `config/settings.py` (pydantic-settings, `AM_` env prefix), `config/pricing.toml`, `config/chains.toml`
- **Chain registry**: `config/chains.toml` (chain metadata) + `AM_RPC_*` env vars (RPC URLs)
- **A2A executor**: `executor/cast_executor.py` — handles A2A task lifecycle
- **Agent loop**: `agent/loop.py` — LLM tool-use loop (OpenAI-compatible API) between executor and MCP
- **MCP tools**: `mcp_server/cast_tools.py` — 9 Cast tools exposed via MCP (multi-chain)
- **Payment**: `server/payment.py` — x402 ASGI middleware on `POST /`
- **Agent card**: `server/agent_card.py` — A2A discovery endpoint (6 skills)
- **Registration**: `register/register_agent.py` — ERC-8004 on-chain registration

## Multi-Chain Support

All RPC-dependent tools accept a `chain` parameter (e.g. `"ethereum"`, `"arbitrum"`, `"base"`).
Chain metadata lives in `config/chains.toml`. RPC URLs are resolved from `AM_RPC_{CHAIN}` env vars.

Supported chains: ethereum, arbitrum, base, polygon, optimism, bsc, avalanche, linea, scroll, zksync, blast.

Resolution order: `chain` param → `AM_DEFAULT_CHAIN` env → `default` key in chains.toml.

## Key Dependencies

- `a2a-sdk[http-server]` — Google A2A protocol
- `x402[fastapi,httpx,evm]` — Coinbase payment middleware
- `agent0-sdk` — ERC-8004 on-chain registration
- `openai` — LLM agent loop (DeepSeek / any OpenAI-compatible API)
- `mcp[cli]` — MCP tool server
- `cli-anything-cast` — path dependency from `../../CLI-Anything/cast/agent-harness`

## MCP Tools (9)

| Tool | Cast Command | Output | RPC | Chain param |
|------|-------------|--------|-----|-------------|
| `list_supported_chains` | — | JSON | No | No |
| `get_transaction` | `cast tx --json` | JSON | Yes | Yes |
| `get_receipt` | `cast receipt --json` | JSON | Yes | Yes |
| `trace_transaction` | `cast run` | Text | Yes | Yes |
| `decode_calldata` | `cast 4byte-decode` | Text | No | No |
| `get_selector` | `cast sig` | Text | No | No |
| `query_logs` | `cast logs --json` | JSON | Yes | Yes |
| `call_contract` | `cast call` | Text | Yes | Yes |
| `get_block` | `cast block --json` | JSON | Yes | Yes |

## Commands

```bash
# Dev: run locally
uv run python main.py

# Deploy: Docker
./scripts/deploy.sh

# Register on-chain
./scripts/register.sh

# Test MCP server standalone
uv run mcp dev mcp_server/cast_tools.py
```

## Environment

- Python 3.12+, managed by `uv`
- `uv sync --prerelease=allow` required (agent0-sdk → ipfshttpclient)
- All env vars use `AM_` prefix — see `.env.example`
- `AM_DEFAULT_CHAIN` — default chain slug (default: `ethereum`)
- `AM_RPC_ETHEREUM`, `AM_RPC_ARBITRUM`, etc. — per-chain RPC URLs
- Requires Foundry `cast` on PATH
- Never commit `.env` — it contains secrets (API keys, RPC URLs with API keys)

## Conventions

- Keep files under 300 lines
- Use strong types (pydantic models, dataclasses), avoid unstructured dicts
- Logs output to `logs/` directory
