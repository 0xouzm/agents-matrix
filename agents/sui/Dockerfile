FROM python:3.12-slim

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Sui CLI (pre-built binary)
ARG SUI_VERSION=v1.67.3
RUN curl -fsSL "https://github.com/MystenLabs/sui/releases/download/mainnet-${SUI_VERSION}/sui-mainnet-${SUI_VERSION}-ubuntu-x86_64.tgz" \
      -o /tmp/sui.tgz && \
    tar -xzf /tmp/sui.tgz -C /usr/local/bin && \
    rm /tmp/sui.tgz && \
    chmod +x /usr/local/bin/sui

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy workspace root + framework + this agent
# NOTE: build context is agents-matrix/ root (set in docker-compose.yml)
COPY pyproject.toml /app/pyproject.toml
COPY framework /app/framework
COPY agents/sui /app/agents/sui

# Install dependencies
RUN cd /app && uv lock --prerelease=allow && uv sync --prerelease=allow --package sui-agent

WORKDIR /app/agents/sui

EXPOSE 9003

CMD ["uv", "run", "--package", "sui-agent", "python", "main.py"]
