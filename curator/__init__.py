"""Curator package initialization."""

from __future__ import annotations

import logging

__all__ = ("__version__", "USER_AGENT")
__version__ = "0.1.0"

# Constant used for HTTP requests
USER_AGENT = "TimeTunnelTV/0.1"

# Configure logging once package is imported. We keep the format simple
# but swap level names to match the README's `[i]/[!]/[DEBUG]/[x]` style.
_LEVEL_MAP = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "i",
    logging.WARNING: "!",
    logging.ERROR: "x",
    logging.CRITICAL: "x",
}
for _level, _name in _LEVEL_MAP.items():
    logging.addLevelName(_level, _name)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
