#!/usr/bin/env bash
# Sui agent: install Sui CLI binary.
# Sourced by scripts/docker-gen.sh during Dockerfile generation.
set -euo pipefail

# System deps
apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Sui CLI (pre-built binary)
SUI_VERSION="${SUI_VERSION:-v1.67.3}"
curl -fsSL "https://github.com/MystenLabs/sui/releases/download/mainnet-${SUI_VERSION}/sui-mainnet-${SUI_VERSION}-ubuntu-x86_64.tgz" \
  -o /tmp/sui.tgz
tar -xzf /tmp/sui.tgz -C /usr/local/bin
rm /tmp/sui.tgz
chmod +x /usr/local/bin/sui
