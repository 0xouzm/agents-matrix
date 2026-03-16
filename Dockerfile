FROM python:3.12-slim

# Install Calibre CLI tools and system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends calibre curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy cli-anything-calibre (path dependency, placed by deploy.sh)
COPY calibre-harness/ /app/calibre-harness/

# Copy application code
COPY . .

# Rewrite path dependency for Docker context
RUN sed -i 's|path = "../../calibre/agent-harness"|path = "calibre-harness"|' pyproject.toml

# Install dependencies (regenerate lockfile for new path)
RUN uv lock --prerelease=allow && uv sync --prerelease=allow

EXPOSE 9000

CMD ["uv", "run", "python", "main.py"]
