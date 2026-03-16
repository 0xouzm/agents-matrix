# Deployment Guide

## Prerequisites

- Docker & Docker Compose v2
- A Calibre library directory on the host
- LLM API key (DeepSeek, OpenAI, or any OpenAI-compatible provider)
- (Optional) EVM wallet for x402 payment gate

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Required
AM_LLM_API_KEY=sk-...
AM_LIBRARY_PATH=/path/to/calibre/library

# Payment (optional — omit AM_WALLET_ADDRESS to disable x402)
AM_WALLET_ADDRESS=0x...
AM_FACILITATOR_URL=https://x402.org/facilitator
AM_CHAIN_NETWORK=eip155:84532

# Tuning
AM_PORT=9000
AM_LLM_MODEL=deepseek-chat
```

### 2. Deploy

```bash
./scripts/deploy.sh
```

This script:
1. Validates required env vars
2. Copies `cli-anything-calibre` into Docker build context
3. Builds the image and starts the container
4. Cleans up the temporary copy

### 3. Verify

```bash
# Health check
curl http://localhost:9000/health
# Expected: {"status":"ok","service":"calibre-agent"}

# Agent card
curl http://localhost:9000/.well-known/agent-card.json
# Expected: JSON with name, skills, capabilities

# View logs
docker compose logs -f
```

---

## Manual Docker Build

If you prefer not to use the deploy script:

```bash
# Copy path dependency into build context
cp -r ../../calibre/agent-harness ./calibre-harness

# Build
docker compose build

# Start
docker compose up -d

# Cleanup
rm -rf ./calibre-harness
```

## Bare Metal (no Docker)

```bash
# Install Calibre CLI tools
# macOS: brew install calibre
# Ubuntu: sudo apt install calibre

# Install dependencies
uv sync --prerelease=allow

# Run
uv run python main.py
```

---

## Verification Flow

### Level 1: Health & Agent Card

```bash
# 1. Health endpoint
curl -s http://localhost:9000/health | python -m json.tool

# 2. Agent card (A2A discovery)
curl -s http://localhost:9000/.well-known/agent-card.json | python -m json.tool
```

Expected: agent card with 8 skills, version "0.1.0".

### Level 2: MCP Server Standalone

Verify the MCP tool layer works independently:

```bash
# List available tools via MCP inspector
uv run mcp dev mcp_server/calibre_tools.py
```

Or test directly in Claude Code:

```bash
claude mcp add calibre -- uv run python -m mcp_server
```

Then ask Claude to "list supported ebook formats" — it should call `list_formats`.

### Level 3: A2A Task (No Payment)

Disable x402 by leaving `AM_WALLET_ADDRESS` empty, then send a task:

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
        "parts": [{"kind": "text", "text": "What ebook formats are supported for conversion?"}]
      }
    }
  }' | python -m json.tool
```

Expected: response containing a task with artifact text listing supported formats.

### Level 4: A2A + x402 Payment

With `AM_WALLET_ADDRESS` set, the `POST /` endpoint requires x402 payment headers.

```bash
# Without payment — should get 402
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tasks/send","id":"1","params":{"message":{"role":"user","parts":[{"kind":"text","text":"hello"}]}}}'
# Expected: 402

# With x402 client (Python)
uv run python -c "
from a2a.client import A2AClient
# Use x402-enabled HTTP client for real payment flow
# See x402 docs: https://docs.x402.org
"
```

### Level 5: On-Chain Registration

```bash
# Set AM_PRIVATE_KEY, AM_RPC_URL, AM_PINATA_JWT in .env
./scripts/register.sh
```

Expected: ERC-721 minted on Base Sepolia with agent metadata on IPFS.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `CLI error: command not found` | Calibre not installed in container | Check Dockerfile installs `calibre` package |
| `AuthenticationError` | Bad API key | Verify `AM_LLM_API_KEY` in `.env` |
| `FileNotFoundError: cli-anything-calibre` | MCP subprocess can't find CLI binary | Ensure `cli-anything-calibre` is installed: `uv run which cli-anything-calibre` |
| `502` from reverse proxy | App not ready yet | Wait for health check to pass; check `docker compose logs` |
| `402` on every request | x402 payment gate active | Either provide payment headers or unset `AM_WALLET_ADDRESS` for testing |

## Architecture

```
Client (A2A)
    │
    ▼
FastAPI + x402 middleware (payment gate)
    │
    ▼
CalibreExecutor (A2A AgentExecutor)
    │  spawns stdio subprocess
    ▼
MCP Server (12 Calibre tools)
    │  subprocess calls
    ▼
cli-anything-calibre CLI
    │
    ▼
Calibre backends (ebook-convert, calibredb, ebook-meta)
```

The LLM agent loop sits between the executor and MCP server, using tool-use to understand intent and chain multiple tool calls as needed.
