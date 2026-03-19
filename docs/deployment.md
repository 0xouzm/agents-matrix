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
cd agents/cast
cp .env.example .env
```

Edit `.env` — set your LLM key and at least one RPC URL:

```env
AM_LLM_API_KEY=sk-...                                        # DeepSeek / OpenAI / any compatible
AM_DEFAULT_CHAIN=ethereum                                     # Default chain for queries
AM_RPC_ETHEREUM=https://your-ethereum-rpc.quiknode.pro/key/   # At least one chain required
AM_RPC_ARBITRUM=https://your-arbitrum-rpc.quiknode.pro/key/   # Add more chains as needed
```

### 2. Deploy

```bash
cd agents/cast

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

# Install Python dependencies (needs CLI-Anything repo cloned at ../../CLI-Anything)
uv sync --prerelease=allow --all-packages

# Configure
cd agents/cast
cp .env.example .env
# Edit .env

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
cd agents/cast
uv run mcp dev mcp_tools.py
```

Or add as Claude Code MCP server:

```bash
cd agents/cast
claude mcp add cast -- uv run python -m mcp_entry
```

### Level 3: A2A Task (No Payment)

Leave `AM_WALLET_ADDRESS` empty in `.env`, then:

```bash
curl -s -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "SendMessage",
    "id": "test-1",
    "params": {
      "message": {
        "role": "ROLE_USER",
        "parts": [{"text": "Show me the latest Ethereum block"}]
      }
    }
  }' | python3 -m json.tool
```

> **Protocol versions** (both work, `enable_v0_3_compat=True` is on by default):
>
> | | v0.3 (legacy) | v1.0 (current) |
> |---|---|---|
> | Method | `message/send` | `SendMessage` |
> | Role | `"user"` | `"ROLE_USER"` |
> | Part | `{"kind": "text", "text": "..."}` | `{"text": "..."}` |
> | messageId | required | not needed |
> | Result | `result.kind == "message"` | `result.message` |
>
> Note: `tasks/send` does not exist in any version. The correct v0.3 method is `message/send`.

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

`register.sh` uses `uv run` from the workspace root — this requires the CLI-Anything harness to be present locally. On production servers the harness path doesn't exist, so **run registration inside the Docker container instead**:

```bash
# Works on any server (no local uv/harness required)
# Container name pattern: <agent>-<agent>-agent-1  (e.g. cast-cast-agent-1, sui-sui-agent-1)
docker exec $(docker ps -q -f name=cast-cast-agent) uv run python -c "
from agents_core.settings import get_settings
from agents_core.registration import register
from agent_config import build_agent_card
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s  %(message)s')
settings = get_settings()
card = build_agent_card(settings)
register(settings, name=card.name, description=card.description)
"
```

Requires `AM_PRIVATE_KEY`, `AM_RPC_URL`, and `AM_PINATA_JWT` set in `.env`.

On success you'll see:
```
INFO  Agent registered!
INFO    TX Hash:   0xabc123...
INFO    Agent ID:  <chain_id>:<id>
INFO    Agent URI: ipfs://...
```

> **Note:** The `Registered` on-chain event always has an empty `agentURI` — this is normal. The URI is set in a separate `URIUpdated` transaction. Verify the final state with `tokenURI(<agentId>)` on the identity registry contract (`0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`).

---

## Nginx Reverse Proxy (Production)

To expose the agent at a path prefix (e.g. `https://aliasai.io/cast/`), add a location block to your nginx server config:

```nginx
location = /cast {
    return 301 /cast/;
}
location ^~ /cast/ {
    rewrite ^/cast/(.*) /$1 break;
    proxy_pass http://localhost:9000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;
}
```

Then update `.env`:
```env
AM_BASE_URL=https://aliasai.io/cast
```

The `rewrite` strips the `/cast/` prefix before proxying, so the app receives all paths relative to `/`.

**Verify via nginx:**
```bash
curl -s https://aliasai.io/cast/health
curl -s https://aliasai.io/cast/.well-known/agent-card.json | python3 -m json.tool
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `deploy.sh` fails: `AM_RPC_BSC not set` | deploy.sh checks per-chain var only | Fixed in current version — checks `AM_RPC` universal fallback too |
| Docker build fails at `foundryup` | Network issue | Retry, or check proxy settings |
| Docker build fails at `git clone` | Can't reach GitHub | Check network; or use `--build-arg HARNESS_REPO=<mirror>` |
| Container exits: `ImportError: Database models require SQLAlchemy` | `a2a-sdk>=1.0.0` needs SQLAlchemy | Use extra `a2a-sdk[http-server,sqlite]` in `framework/pyproject.toml` |
| Container exits: `AgentCapabilities has no "pushNotifications" field` | `a2a-sdk 1.0.0` renamed field | Use `push_notifications=False` (snake_case) |
| Container exits: `AgentCard has no "url" field` | `a2a-sdk 1.0.0` removed `url` from AgentCard | Use `supported_interfaces=[AgentInterface(url=...)]` instead |
| `register.sh` fails: `Distribution not found at: file:///home/CLI-Anything/...` | Local harness path doesn't exist on server | Run registration inside Docker container (see Level 5 above) |
| Docker build fails: `curl: (22) ... 404` on sui binary download | `SUI_VERSION` in `agents/sui/Dockerfile` is outdated | Update `ARG SUI_VERSION=vX.Y.Z` to the latest mainnet release from [github.com/MystenLabs/sui/releases](https://github.com/MystenLabs/sui/releases) |
| `AuthenticationError` | Bad API key | Verify `AM_LLM_API_KEY` in `.env` |
| `500` on `POST /` with `Facilitator get_supported failed (401)` | CDP JWT auth wrong — ES256 or wrong claims | CDP keys use **EdDSA** (Ed25519), `uri` (singular string), `aud: ["cdp_service"]`; see `payment.py` |
| `403` on `/.well-known/agent-card.json` via nginx | `location ~ /\.` deny rule intercepts path | Use `location ^~ /cast/` (with `^~`) to take priority over regex rules |
| `502` from reverse proxy | App not ready | Wait for healthcheck; `docker compose logs -f` |
| `402` on every request | Payment gate active | Unset `AM_WALLET_ADDRESS` for testing |
| RPC errors | Bad RPC URL | Test with `curl -X POST <rpc_url> -d '{"jsonrpc":"2.0","method":"eth_blockNumber","id":1}'` |
