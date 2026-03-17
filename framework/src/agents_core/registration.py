"""ERC-8004 on-chain agent registration via agent0-sdk."""

from __future__ import annotations

import logging
import sys

from agent0_sdk import SDK

from agents_core.settings import Settings

logger = logging.getLogger(__name__)


def register(
    settings: Settings,
    *,
    name: str,
    description: str,
    skill: str = "data_engineering/data_transformation_pipeline",
    domain: str = "technology/blockchain",
) -> None:
    """Register an agent on-chain (ERC-721 mint + IPFS metadata).

    Args:
        settings: Application settings (keys, RPC, etc.).
        name: Agent display name.
        description: Agent description for the registry.
        skill: OASF skill identifier.
        domain: OASF domain identifier.
    """
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

    agent = sdk.createAgent(name=name, description=description)

    # A2A endpoint
    a2a_url = settings.base_url + "/.well-known/agent-card.json"
    agent.setA2A(a2a_url)

    # OASF skills and domains
    agent.addSkill(skill, validate_oasf=True)
    agent.addDomain(domain, validate_oasf=True)

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
