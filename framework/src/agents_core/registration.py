"""ERC-8004 on-chain agent registration via agent0-sdk."""

from __future__ import annotations

import logging
import sys

from agent0_sdk import SDK
from web3.middleware import ExtraDataToPOAMiddleware

from agents_core.settings import Settings

# BSC PoA chain IDs that require ExtraDataToPOAMiddleware
_POA_CHAIN_IDS = {56, 97}  # BSC mainnet, BSC testnet

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

    # agent0-sdk only has a handful of chains in DEFAULT_REGISTRIES.
    # The ERC-8004 contracts are deployed at the same addresses on every chain,
    # so we can supply them via registryOverrides for any unsupported chain.
    REGISTRY_ADDRESSES = {
        "IDENTITY":   "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432",
        "REPUTATION": "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63",
    }
    sdk = SDK(
        chainId=settings.chain_id,
        rpcUrl=settings.rpc_url,
        signer=settings.private_key,
        ipfs="pinata",
        pinataJwt=settings.pinata_jwt,
        registryOverrides={settings.chain_id: REGISTRY_ADDRESSES},
    )

    agent = sdk.createAgent(name=name, description=description)

    # A2A endpoint
    a2a_url = settings.base_url + "/.well-known/agent-card.json"
    agent.setA2A(a2a_url)

    # OASF skills and domains
    agent.addSkill(skill, validate_oasf=False)
    agent.addDomain(domain, validate_oasf=False)

    # Payment support — setX402Support is metadata (before registration)
    # setWallet requires agentId so must come after registerIPFS()
    agent.setX402Support(True)

    # Trust model
    agent.setTrust(reputation=True)
    agent.setActive(True)

    # Custom metadata
    agent.setMetadata({
        "version": "0.1.0",
        "framework": "agents-matrix",
        "payment_network": settings.chain_network,
    })

    # PoA chains (e.g. BSC) need extra middleware so web3.py doesn't choke
    # on the oversized extraData field in block headers.
    if settings.chain_id in _POA_CHAIN_IDS:
        sdk.web3_client.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        logger.info("Injected PoA middleware for chain %d", settings.chain_id)

    # Register on-chain (mint ERC-721 + upload metadata to IPFS)
    logger.info("Registering agent on chain %d...", settings.chain_id)
    reg_tx = agent.registerIPFS()
    confirmed = reg_tx.wait_confirmed(timeout=180)
    reg = confirmed.result

    logger.info("Agent registered!")
    logger.info("  TX Hash:   %s", confirmed.receipt.get("transactionHash", b"").hex())
    logger.info("  Agent ID:  %s", reg.agentId)
    logger.info("  Agent URI: %s", reg.agentURI)

    # setWallet must be called after registration (requires agentId)
    # wallet chain may differ from registration chain
    # (e.g. register on BSC but accept x402 payments on Base)
    if settings.wallet_address:
        # AM_CHAIN_NETWORK format: "eip155:<chain_id>" (x402 payment chain)
        try:
            payment_chain_id = int(settings.chain_network.split(":")[-1])
        except (ValueError, IndexError):
            payment_chain_id = settings.chain_id
        agent.setWallet(settings.wallet_address, chainId=payment_chain_id)
