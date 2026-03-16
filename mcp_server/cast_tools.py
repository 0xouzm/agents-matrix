"""MCP server exposing Foundry cast operations via cli-anything-cast CLI.

Community usage: claude mcp add cast -- uv run python -m mcp_server
"""

from __future__ import annotations

import json
import subprocess

from mcp.server.fastmcp import FastMCP

from config.settings import get_chains

mcp = FastMCP(
    "cast",
    instructions=(
        "Foundry cast tools for EVM chain transaction analysis, decoding, "
        "and block queries. Supports Ethereum, Arbitrum, Base, Polygon, and more."
    ),
)


def _run_cli(*args: str) -> str | dict | list:
    """Run cli-anything-cast with --json flag and return parsed output.

    For commands that return JSON, parses and returns dict/list.
    For plain-text commands (4byte-decode, sig, call, trace), returns
    the structured dict that the harness wraps around the text output.
    """
    cmd = ["cli-anything-cast", "--json", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"CLI error: {result.stderr.strip() or result.stdout.strip()}")
    return json.loads(result.stdout)


def _resolve_chain(chain: str | None) -> str:
    """Resolve chain slug to RPC URL via ChainRegistry."""
    return get_chains().resolve_rpc(chain)


# ── Chain Discovery ──


@mcp.tool()
def list_supported_chains() -> list[dict]:
    """List all supported EVM chains and whether they have an RPC URL configured."""
    return get_chains().list_chains()


# ── Transaction ──


@mcp.tool()
def get_transaction(tx_hash: str, chain: str | None = None) -> dict:
    """Get full transaction details by hash (from, to, value, gas, input data, etc.).

    Args:
        tx_hash: The transaction hash to look up.
        chain: Chain name (ethereum, arbitrum, base, polygon, etc.). Defaults to configured default.
    """
    rpc_url = _resolve_chain(chain)
    return _run_cli("-r", rpc_url, "tx", "info", tx_hash)


@mcp.tool()
def get_receipt(tx_hash: str, chain: str | None = None) -> dict:
    """Get transaction receipt (status, gas used, logs, contract address, etc.).

    Args:
        tx_hash: The transaction hash to look up.
        chain: Chain name (ethereum, arbitrum, base, polygon, etc.). Defaults to configured default.
    """
    rpc_url = _resolve_chain(chain)
    return _run_cli("-r", rpc_url, "receipt", "info", tx_hash)


# ── Trace ──


@mcp.tool()
def trace_transaction(tx_hash: str, chain: str | None = None) -> dict:
    """Trace a transaction execution showing internal calls and gas usage.

    Args:
        tx_hash: The transaction hash to trace.
        chain: Chain name (ethereum, arbitrum, base, polygon, etc.). Defaults to configured default.
    """
    rpc_url = _resolve_chain(chain)
    return _run_cli("-r", rpc_url, "decode", "trace", tx_hash)


# ── Decode ──


@mcp.tool()
def decode_calldata(calldata: str) -> dict:
    """Decode hex calldata using the 4byte signature database (no RPC needed).

    Args:
        calldata: Hex-encoded calldata starting with 0x (e.g. "0xa9059cbb...").
    """
    return _run_cli("decode", "calldata", calldata)


@mcp.tool()
def get_selector(signature: str) -> dict:
    """Get the 4-byte function selector for a Solidity function signature (no RPC needed).

    Args:
        signature: Function signature string (e.g. "transfer(address,uint256)").
    """
    return _run_cli("decode", "sig", signature)


# ── Logs ──


@mcp.tool()
def query_logs(
    address: str,
    sig: str | None = None,
    from_block: str | None = None,
    to_block: str | None = None,
    chain: str | None = None,
) -> list:
    """Query event logs from a contract address with optional filters.

    Args:
        address: Contract address to query logs from.
        sig: Event signature to filter (e.g. "Transfer(address,address,uint256)").
        from_block: Starting block number or tag.
        to_block: Ending block number or tag.
        chain: Chain name (ethereum, arbitrum, base, polygon, etc.). Defaults to configured default.
    """
    rpc_url = _resolve_chain(chain)
    args = ["-r", rpc_url, "logs", "query", address]
    if sig:
        args.extend(["--sig", sig])
    if from_block:
        args.extend(["--from-block", from_block])
    if to_block:
        args.extend(["--to-block", to_block])
    return _run_cli(*args)


# ── Call ──


@mcp.tool()
def call_contract(
    to: str,
    sig: str,
    args: list[str] | None = None,
    chain: str | None = None,
) -> dict:
    """Call a contract function (read-only, no state change).

    Args:
        to: Target contract address.
        sig: Function signature (e.g. "balanceOf(address)").
        args: Function arguments.
        chain: Chain name (ethereum, arbitrum, base, polygon, etc.). Defaults to configured default.
    """
    rpc_url = _resolve_chain(chain)
    cmd_args = ["-r", rpc_url, "decode", "call", to, sig]
    if args:
        cmd_args.extend(args)
    return _run_cli(*cmd_args)


# ── Block ──


@mcp.tool()
def get_block(block: str = "latest", chain: str | None = None) -> dict:
    """Get block information by number, hash, or tag (latest, earliest, etc.).

    Args:
        block: Block number, hash, or tag. Defaults to "latest".
        chain: Chain name (ethereum, arbitrum, base, polygon, etc.). Defaults to configured default.
    """
    rpc_url = _resolve_chain(chain)
    return _run_cli("-r", rpc_url, "block", "info", block)
