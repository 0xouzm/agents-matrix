"""Calibre A2A Agent Service — entry point."""

from __future__ import annotations

import logging
from pathlib import Path

import uvicorn

from config.settings import get_settings, get_pricing
from server.app import create_app


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "agents-matrix.log"),
        ],
    )


def main() -> None:
    settings = get_settings()
    pricing = get_pricing()

    setup_logging(Path("logs"))

    app = create_app(settings, pricing)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
