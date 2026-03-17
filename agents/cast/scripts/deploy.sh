#!/usr/bin/env bash
# Deploy Cast Transaction Agent via Docker Compose.
# Usage: ./scripts/deploy.sh
#
# Requires only: Docker, .env file
# The Dockerfile handles everything else (Foundry, cast harness, Python deps).
set -euo pipefail
cd "$(dirname "$0")/.."

# ── Pre-flight checks ──
if [ ! -f .env ]; then
  echo "ERROR: .env file not found. Create one:"
  echo "  cp .env.example .env"
  echo "  # Then set AM_LLM_API_KEY and AM_RPC_<CHAIN> for your default chain"
  exit 1
fi

# Source .env for local variable access
set -a; source .env; set +a

# Validate LLM key
if [ -z "${AM_LLM_API_KEY:-}" ]; then
  echo "ERROR: AM_LLM_API_KEY is not set in .env"
  exit 1
fi

# Validate default chain has RPC configured
DEFAULT_CHAIN="${AM_DEFAULT_CHAIN:-base_sepolia}"
RPC_VAR="AM_RPC_$(echo "$DEFAULT_CHAIN" | tr '[:lower:]' '[:upper:]')"
if [ -z "${!RPC_VAR:-}" ]; then
  echo "ERROR: $RPC_VAR is not set in .env (required for default chain '$DEFAULT_CHAIN')"
  exit 1
fi

if [ -z "${AM_WALLET_ADDRESS:-}" ]; then
  echo "NOTICE: AM_WALLET_ADDRESS not set — x402 payment gate disabled"
fi

# ── Build & Deploy ──
echo "Building and starting services..."
echo "  (Dockerfile will install Foundry + clone cast harness from git)"
docker compose up -d --build

echo ""
echo "Deployment complete. Service running at http://localhost:${AM_PORT:-9000}"
echo ""
echo "  Verify:"
echo "    curl http://localhost:${AM_PORT:-9000}/health"
echo "    curl http://localhost:${AM_PORT:-9000}/.well-known/agent-card.json"
echo ""
echo "  Logs:"
echo "    docker compose logs -f"
