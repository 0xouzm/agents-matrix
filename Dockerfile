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

# Copy application code
COPY . .

# Rewrite path dependency for Docker context
RUN sed -i 's|path = "../../CLI-Anything/cast/agent-harness"|path = "cast-harness"|' pyproject.toml

# Install dependencies
RUN uv lock --prerelease=allow && uv sync --prerelease=allow

EXPOSE 9000

CMD ["uv", "run", "python", "main.py"]
