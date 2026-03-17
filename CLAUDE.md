# Agents Matrix

Multi-agent platform — each agent wraps a CLI tool as a paid Agent-as-a-Service via A2A protocol + x402 payment.

## Monorepo Structure

```
agents-matrix/
  framework/                    ← agents-core shared package
    src/agents_core/
      settings.py               ← Settings, ChainRegistry, Pricing, ChainInfo
      executor.py               ← Generic MCPAgentExecutor
      loop.py                   ← run_agent_loop() (system_prompt as param)
      app.py                    ← create_app() factory (generic)
      payment.py                ← x402 middleware helpers
      registration.py           ← ERC-8004 helper (generic)
  agents/
    cast/                       ← Cast Transaction Agent
      main.py                   ← thin entry point
      agent_config.py           ← SYSTEM_PROMPT, SKILLS, build_agent_card()
      mcp_tools.py              ← @mcp.tool() functions (cast-specific)
      mcp_entry.py              ← mcp.run() (2 lines)
      config/chains.toml, pricing.toml
      Dockerfile, docker-compose.yml, .env.example
      scripts/run.sh, deploy.sh, register.sh
  pyproject.toml                ← uv workspace
```

## CLI-Anything Integration

Agents are backed by CLI harnesses from [CLI-Anything (HKUDS)](https://github.com/HKUDS/CLI-Anything) and our own [CLI-Anything fork](https://github.com/0xouzm/CLI-Anything). Each harness wraps a software tool as a structured CLI with `--json` output, making it trivially callable from MCP tools via `subprocess`.

```
CLI-Anything repo              agents-matrix
─────────────────              ─────────────
cast/agent-harness        →    agents/cast/      (live)
<tool>/agent-harness      →    agents/<tool>/    (add next)
```

The harness can be written in any framework (CLI-Anything uses Click, but argparse, typer, etc. all work). The only requirement is structured `--json` output so MCP tools can parse results.

## Adding a New Agent

1. Get or write a CLI harness in the CLI-Anything repo (`<tool>/agent-harness/`)
2. Create `agents/<name>/` with these files:
   - `agent_config.py` — SYSTEM_PROMPT, SKILLS, build_agent_card()
   - `mcp_tools.py` — @mcp.tool() functions calling the CLI harness via subprocess
   - `mcp_entry.py` — `from mcp_tools import mcp; mcp.run()`
   - `main.py` — thin entry point using `agents_core.app.create_app()`
   - `pyproject.toml` — depends on `agents-core` + CLI harness (path or git dep)
   - `config/` — chains.toml, pricing.toml
3. Framework (`agents-core`) handles: A2A server, x402 payment, LLM loop, MCP executor, registration

## Current Agent: Cast Transaction Agent

Multi-chain EVM transaction analysis powered by Foundry cast.

```
Client (A2A) → FastAPI + x402 → MCPAgentExecutor → MCP Server → cli-anything-cast → Foundry cast
```

- **Entry**: `agents/cast/main.py`
- **Config**: `agents/cast/config/chains.toml` + `agents/cast/config/pricing.toml`
- **MCP tools**: `agents/cast/mcp_tools.py` (9 tools, multi-chain)
- **Agent card**: `agents/cast/agent_config.py` (6 skills)

## Multi-Chain Support

All RPC-dependent tools accept a `chain` parameter. Chain metadata in `config/chains.toml`. RPC URLs from `AM_RPC_{CHAIN}` env vars.

Supported chains: ethereum, arbitrum, base, polygon, optimism, bsc, avalanche, linea, scroll, zksync, blast.

## Key Dependencies

- `a2a-sdk[http-server]` — Google A2A protocol
- `x402[fastapi,httpx,evm]` — Coinbase payment middleware
- `agent0-sdk` — ERC-8004 on-chain registration
- `openai` — LLM agent loop (DeepSeek / any OpenAI-compatible API)
- `mcp[cli]` — MCP tool server
- `cli-anything-cast` — path dependency from CLI-Anything repo

## Commands

```bash
# Install workspace
uv sync --prerelease=allow --all-packages

# Run cast agent locally
cd agents/cast && uv run python main.py

# Deploy cast agent (Docker)
cd agents/cast && ./scripts/deploy.sh

# Register on-chain
cd agents/cast && ./scripts/register.sh

# Test MCP server standalone
cd agents/cast && uv run mcp dev mcp_tools.py
```

## Environment

- Python 3.12+, managed by `uv` (workspace mode)
- `uv sync --prerelease=allow --all-packages` required
- All env vars use `AM_` prefix — see `agents/cast/.env.example`
- Requires Foundry `cast` on PATH for cast agent
- Never commit `.env` — it contains secrets

## Conventions

- Keep files under 300 lines
- Use strong types (pydantic models, dataclasses), avoid unstructured dicts
- Logs output to `logs/` directory
