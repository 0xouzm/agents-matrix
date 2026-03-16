# Agents Matrix

Paid Agent-as-a-Service platform — Calibre ebook operations via A2A protocol + x402 payment.

## Architecture

```
Client (A2A) → FastAPI + x402 middleware → CalibreExecutor → MCP Server → cli-anything-calibre → Calibre backends
```

- **Entry point**: `main.py` → `server/app.py` app factory
- **Config**: `config/settings.py` (pydantic-settings, `AM_` env prefix), `config/pricing.toml`
- **A2A executor**: `executor/calibre_executor.py` — handles A2A task lifecycle
- **Agent loop**: `agent/loop.py` — LLM tool-use loop (OpenAI-compatible API) between executor and MCP
- **MCP tools**: `mcp_server/calibre_tools.py` — 12 Calibre tools exposed via MCP
- **Payment**: `server/payment.py` — x402 ASGI middleware on `POST /`
- **Agent card**: `server/agent_card.py` — A2A discovery endpoint
- **Registration**: `register/register_agent.py` — ERC-8004 on-chain registration

## Key Dependencies

- `a2a-sdk[http-server]` — Google A2A protocol
- `x402[fastapi,httpx,evm]` — Coinbase payment middleware
- `agent0-sdk` — ERC-8004 on-chain registration
- `openai` — LLM agent loop (DeepSeek / any OpenAI-compatible API)
- `mcp[cli]` — MCP tool server
- `cli-anything-calibre` — path dependency from `../../calibre/agent-harness`

## Commands

```bash
# Dev: run locally
uv run python main.py

# Deploy: Docker
./scripts/deploy.sh

# Register on-chain
./scripts/register.sh
```

## Environment

- Python 3.12+, managed by `uv`
- `uv sync --prerelease=allow` required (agent0-sdk → ipfshttpclient)
- All env vars use `AM_` prefix — see `.env.example`
- Never commit `.env` — it contains secrets (API keys, private keys)

## Conventions

- Keep files under 300 lines
- Use strong types (pydantic models), avoid unstructured dicts
- Logs output to `logs/` directory
