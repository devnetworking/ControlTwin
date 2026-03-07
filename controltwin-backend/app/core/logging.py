"""Structured logging setup for ControlTwin."""

import logging
import sys


def setup_logging() -> None:
    """Configure root logger with structured-like format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
