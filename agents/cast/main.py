"""Cast Transaction A2A Agent Service — entry point."""

from __future__ import annotations

import logging
from pathlib import Path

import uvicorn

from agents_core.app import create_app
from agents_core.settings import get_settings, Pricing
from agent_config import SYSTEM_PROMPT, build_agent_card


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "cast-agent.log"),
        ],
    )


def main() -> None:
    settings = get_settings()
    pricing = Pricing(Path(__file__).parent / "config" / "pricing.toml")

    setup_logging(Path("logs"))

    app = create_app(
        settings,
        pricing,
        agent_card=build_agent_card(settings),
        mcp_module="mcp_entry",
        system_prompt=SYSTEM_PROMPT,
    )
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
