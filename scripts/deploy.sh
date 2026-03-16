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
  echo "  # Then set AM_LLM_API_KEY and AM_DEFAULT_RPC_URL"
  exit 1
fi

# Source .env for local variable access
set -a; source .env; set +a

# Validate required vars
for var in AM_LLM_API_KEY AM_DEFAULT_RPC_URL; do
  if [ -z "${!var:-}" ]; then
    echo "ERROR: $var is not set in .env"
    exit 1
  fi
done

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
