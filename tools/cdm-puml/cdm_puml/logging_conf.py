"""Logging helpers for the CLI."""

from __future__ import annotations

import logging
from typing import Optional


def configure_logging(level: str | int = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name)
