"""Application settings loaded from environment variables (AM_ prefix)."""

from __future__ import annotations

import os
import tomli
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AM_", env_file=".env")

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 9000
    base_url: str = "http://localhost:9000"

    # ── Cast (Foundry) — multi-chain ──
    default_chain: str = "ethereum"

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


@dataclass(frozen=True)
class ChainInfo:
    slug: str
    name: str
    chain_id: int
    explorer: str
    symbol: str


class ChainRegistry:
    """Chain metadata from chains.toml + RPC URLs from AM_RPC_* env vars."""

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            path = Path(__file__).parent / "chains.toml"
        with open(path, "rb") as f:
            data = tomli.load(f)

        self._default_chain = os.environ.get(
            "AM_DEFAULT_CHAIN", data.get("default", "ethereum"),
        )
        self._chains: dict[str, ChainInfo] = {}
        for slug, meta in data.get("chains", {}).items():
            self._chains[slug] = ChainInfo(
                slug=slug,
                name=meta["name"],
                chain_id=meta["chain_id"],
                explorer=meta["explorer"],
                symbol=meta["symbol"],
            )

    def resolve_rpc(self, chain: str | None = None) -> str:
        """Resolve a chain slug to its RPC URL from AM_RPC_{CHAIN} env var."""
        slug = chain or self._default_chain
        if slug not in self._chains:
            raise ValueError(
                f"Unknown chain '{slug}'. "
                f"Available: {', '.join(sorted(self._chains))}"
            )
        env_key = f"AM_RPC_{slug.upper()}"
        rpc_url = os.environ.get(env_key, "")
        if not rpc_url:
            raise ValueError(
                f"No RPC URL configured for chain '{slug}'. "
                f"Set {env_key} in your .env file."
            )
        return rpc_url

    def list_chains(self) -> list[dict]:
        """Return all chains, marking which have RPC URLs configured."""
        result = []
        for slug, info in sorted(self._chains.items()):
            env_key = f"AM_RPC_{slug.upper()}"
            result.append({
                "chain": slug,
                "name": info.name,
                "chain_id": info.chain_id,
                "explorer": info.explorer,
                "symbol": info.symbol,
                "configured": bool(os.environ.get(env_key)),
            })
        return result

    def chain_info(self, chain: str) -> ChainInfo:
        """Return metadata for a chain slug."""
        if chain not in self._chains:
            raise ValueError(
                f"Unknown chain '{chain}'. "
                f"Available: {', '.join(sorted(self._chains))}"
            )
        return self._chains[chain]

    @property
    def default_chain(self) -> str:
        return self._default_chain

    @property
    def supported_slugs(self) -> list[str]:
        return sorted(self._chains.keys())


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


@lru_cache
def get_chains() -> ChainRegistry:
    return ChainRegistry()
