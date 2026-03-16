"""Application settings loaded from environment variables (AM_ prefix)."""

from __future__ import annotations

import tomli
from pathlib import Path
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AM_", env_file=".env")

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 9000
    base_url: str = "http://localhost:9000"

    # ── Calibre ──
    library_path: str = ""
    temp_dir: str = "/tmp/agents-matrix"

    # ── x402 Payment ──
    wallet_address: str = ""
    facilitator_url: str = "https://x402.org/facilitator"
    chain_network: str = "eip155:84532"

    # ── ERC-8004 Registration ──
    private_key: str = ""
    chain_id: int = 84532
    rpc_url: str = ""
    pinata_jwt: str = ""

    # ── LLM (agent loop — OpenAI-compatible API) ──
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"


class Pricing:
    """Per-skill USDC pricing loaded from pricing.toml."""

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            path = Path(__file__).parent / "pricing.toml"
        with open(path, "rb") as f:
            data = tomli.load(f)
        self._default: str = data.get("default", "$0.01")
        self._skills: dict[str, str] = data.get("skills", {})

    @property
    def default_price(self) -> str:
        return self._default

    def price_for(self, skill_id: str) -> str:
        return self._skills.get(skill_id, self._default)

    def all_prices(self) -> dict[str, str]:
        return {"default": self._default, **self._skills}


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_pricing() -> Pricing:
    return Pricing()
