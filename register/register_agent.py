"""ERC-8004 on-chain agent registration via agent0-sdk."""

from __future__ import annotations

import logging
import sys

from agent0_sdk import SDK

from config.settings import get_settings

logger = logging.getLogger(__name__)


def register() -> None:
    """Register the Calibre agent on-chain (ERC-721 mint + IPFS metadata)."""
    settings = get_settings()

    if not settings.private_key:
        logger.error("AM_PRIVATE_KEY is required for registration")
        sys.exit(1)
    if not settings.rpc_url:
        logger.error("AM_RPC_URL is required for registration")
        sys.exit(1)
    if not settings.pinata_jwt:
        logger.error("AM_PINATA_JWT is required for registration")
        sys.exit(1)

    sdk = SDK(
        chainId=settings.chain_id,
        rpcUrl=settings.rpc_url,
        signer=settings.private_key,
        ipfs="pinata",
        pinataJwt=settings.pinata_jwt,
    )

    agent = sdk.createAgent(
        name="Calibre Agent",
        description=(
            "Paid AI agent for Calibre ebook operations — format conversion, "
            "metadata management, library search, and more. "
            "Accepts USDC payment via x402 protocol."
        ),
    )

    # A2A endpoint
    a2a_url = settings.base_url + "/.well-known/agent-card.json"
    agent.setA2A(a2a_url)

    # OASF skills and domains
    agent.addSkill("data_engineering/data_transformation_pipeline", validate_oasf=True)
    agent.addDomain("technology/data_science/data_visualization", validate_oasf=True)

    # Payment support
    agent.setX402Support(True)
    if settings.wallet_address:
        agent.setWallet(settings.wallet_address, chainId=settings.chain_id)

    # Trust model
    agent.setTrust(reputation=True)
    agent.setActive(True)

    # Custom metadata
    agent.setMetadata({
        "version": "0.1.0",
        "framework": "agents-matrix",
        "payment_network": settings.chain_network,
    })

    # Register on-chain (mint ERC-721 + upload metadata to IPFS)
    logger.info("Registering agent on chain %d...", settings.chain_id)
    reg_tx = agent.registerIPFS()
    reg = reg_tx.wait_confirmed(timeout=180).result

    logger.info("Agent registered!")
    logger.info("  Agent ID:  %s", reg.agentId)
    logger.info("  Agent URI: %s", reg.agentURI)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    register()
