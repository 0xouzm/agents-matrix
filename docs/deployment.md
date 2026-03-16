# Deployment Guide

## Prerequisites

- Docker & Docker Compose v2
- LLM API key (DeepSeek, OpenAI, or any OpenAI-compatible provider)
- (Optional) EVM wallet for x402 payment gate

That's it. No need to install Foundry, Python, uv, or anything else on the host.
The Docker image handles everything: Foundry cast, Python, cli-anything-cast harness.

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` — only two fields required:

```env
AM_LLM_API_KEY=sk-...                     # DeepSeek / OpenAI / any compatible
AM_DEFAULT_RPC_URL=https://eth.drpc.org    # Public Ethereum RPC (free tier is fine)
```

### 2. Deploy

```bash
# Option A: one-line
docker compose up -d --build

# Option B: with env validation
./scripts/deploy.sh
```

The Dockerfile will:
1. Install Foundry cast via `foundryup`
2. Clone `cli-anything-cast` harness from GitHub (sparse checkout)
3. Install all Python dependencies via uv
4. Start the agent on port 9000

### 3. Verify

```bash
# Health check
curl http://localhost:9000/health
# → {"status":"ok","service":"cast-transaction-agent"}

# Agent card (A2A discovery)
curl -s http://localhost:9000/.well-known/agent-card.json | python3 -m json.tool

# Logs
docker compose logs -f
```

---

## Bare Metal (local development, no Docker)

Only needed for development. Requires Foundry and uv on the host.

```bash
# Install Foundry cast
curl -L https://foundry.paradigm.xyz | bash && foundryup

# Install Python dependencies (needs CLI-Anything repo cloned nearby)
uv sync --prerelease=allow

# Run
uv run python main.py
```

---

## Verification Flow

### Level 1: Health & Agent Card

```bash
curl -s http://localhost:9000/health | python3 -m json.tool
curl -s http://localhost:9000/.well-known/agent-card.json | python3 -m json.tool
```

Expected: agent card with 6 skills, version "0.1.0".

### Level 2: MCP Server (requires bare metal setup)

```bash
uv run mcp dev mcp_server/cast_tools.py
```

Or add as Claude Code MCP server:

```bash
claude mcp add cast -- uv run python -m mcp_server
```

### Level 3: A2A Task (No Payment)

Leave `AM_WALLET_ADDRESS` empty in `.env`, then:

```bash
curl -s -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "id": "test-1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Show me the latest Ethereum block"}]
      }
    }
  }' | python3 -m json.tool
```

Expected: task artifact with block details.

### Level 4: A2A + x402 Payment

With `AM_WALLET_ADDRESS` set, `POST /` requires x402 payment headers.

```bash
# Without payment — should get 402
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tasks/send","id":"1","params":{"message":{"role":"user","parts":[{"kind":"text","text":"hello"}]}}}'
```

### Level 5: On-Chain Registration

```bash
# Set AM_PRIVATE_KEY, AM_RPC_URL, AM_PINATA_JWT in .env
./scripts/register.sh
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Docker build fails at `foundryup` | Network issue | Retry, or check proxy settings |
| Docker build fails at `git clone` | Can't reach GitHub | Check network; or use `--build-arg HARNESS_REPO=<mirror>` |
| `AuthenticationError` | Bad API key | Verify `AM_LLM_API_KEY` in `.env` |
| `502` from reverse proxy | App not ready | Wait for healthcheck; `docker compose logs -f` |
| `402` on every request | Payment gate active | Unset `AM_WALLET_ADDRESS` for testing |
| RPC errors | Bad RPC URL | Test with `curl -X POST <rpc_url> -d '{"jsonrpc":"2.0","method":"eth_blockNumber","id":1}'` |

## Architecture

```
Client (A2A)
    |
    v
FastAPI + x402 middleware (payment gate)
    |
    v
CastExecutor (A2A AgentExecutor)
    |  spawns stdio subprocess
    v
MCP Server (8 Cast tools)
    |  subprocess calls
    v
cli-anything-cast CLI
    |
    v
Foundry cast (tx, receipt, run, 4byte-decode, sig, logs, call, block)
```

The LLM agent loop sits between the executor and MCP server, using tool-use to understand intent and chain multiple tool calls as needed.
