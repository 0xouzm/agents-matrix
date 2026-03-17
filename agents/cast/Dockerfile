FROM python:3.12-slim

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git && \
    rm -rf /var/lib/apt/lists/*

# Install Foundry (cast)
RUN curl -L https://foundry.paradigm.xyz | bash && \
    /root/.foundry/bin/foundryup
ENV PATH="/root/.foundry/bin:${PATH}"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Clone cast harness from git (sparse checkout — only cast/agent-harness)
ARG HARNESS_REPO=https://github.com/0xouzm/CLI-Anything.git
ARG HARNESS_REF=main
RUN git clone --depth 1 --branch ${HARNESS_REF} --filter=blob:none --sparse \
      ${HARNESS_REPO} /tmp/cli-anything && \
    cd /tmp/cli-anything && git sparse-checkout set cast/agent-harness && \
    cp -r cast/agent-harness /app/cast-harness && \
    rm -rf /tmp/cli-anything

# Copy workspace root + framework + this agent
# NOTE: build context is agents-matrix/ root (set in docker-compose.yml)
COPY pyproject.toml /app/pyproject.toml
COPY framework /app/framework
COPY agents/cast /app/agents/cast

# Rewrite path dependency for Docker context
RUN sed -i 's|path = "../../../../CLI-Anything/cast/agent-harness"|path = "/app/cast-harness"|' /app/agents/cast/pyproject.toml

# Install dependencies
RUN cd /app && uv lock --prerelease=allow && uv sync --prerelease=allow --package cast-agent

WORKDIR /app/agents/cast

EXPOSE 9000

CMD ["uv", "run", "--package", "cast-agent", "python", "main.py"]
