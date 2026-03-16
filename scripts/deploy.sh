#!/usr/bin/env bash
# Deploy agents-matrix to a server via Docker Compose.
# Usage: ./scripts/deploy.sh [--build]
set -euo pipefail
cd "$(dirname "$0")/.."

# ── Pre-flight checks ──
if [ ! -f .env ]; then
  echo "ERROR: .env file not found. Copy .env.example and fill in values:"
  echo "  cp .env.example .env"
  exit 1
fi

# Source .env for local variable access
set -a; source .env; set +a

# Validate required vars
for var in AM_ANTHROPIC_API_KEY AM_WALLET_ADDRESS AM_LIBRARY_PATH; do
  if [ -z "${!var:-}" ]; then
    echo "ERROR: $var is not set in .env"
    exit 1
  fi
done

# ── Copy cli-anything-calibre for Docker build context ──
HARNESS_SRC="../../calibre/agent-harness"
HARNESS_DST="./calibre-harness"
if [ -d "$HARNESS_SRC" ]; then
  echo "Copying cli-anything-calibre into build context..."
  rm -rf "$HARNESS_DST"
  cp -r "$HARNESS_SRC" "$HARNESS_DST"
else
  echo "ERROR: cli-anything-calibre not found at $HARNESS_SRC"
  exit 1
fi

# ── Build & Deploy ──
echo "Building and starting services..."
docker compose up -d --build

# ── Cleanup build context copy ──
rm -rf "$HARNESS_DST"

echo ""
echo "Deployment complete. Service running at http://localhost:${AM_PORT:-9000}"
echo "  Health:     curl http://localhost:${AM_PORT:-9000}/health"
echo "  Agent card: curl http://localhost:${AM_PORT:-9000}/.well-known/agent-card.json"
echo "  Logs:       docker compose logs -f"
