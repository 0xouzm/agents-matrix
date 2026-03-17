#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run python -c "
from agents_core.settings import get_settings
from agents_core.registration import register
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s  %(message)s')
register(
    get_settings(),
    name='Cast Transaction Agent',
    description=(
        'Paid AI agent for Ethereum transaction analysis — decode transactions, '
        'parse receipts, trace execution, query logs, and inspect blocks. '
        'Powered by Foundry cast. Accepts USDC payment via x402 protocol.'
    ),
)
"
