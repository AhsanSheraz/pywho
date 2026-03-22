"""Shared terminal utilities for ANSI color support."""

from __future__ import annotations

import functools
import os
import sys

# ANSI escape codes
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
RED = "\033[91m"
WHITE = "\033[37m"


@functools.lru_cache(maxsize=1)
def supports_color() -> bool:
    """Check if stdout supports ANSI colors.

    Respects ``NO_COLOR`` (https://no-color.org/) and ``FORCE_COLOR``
    environment variables.
    """
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return True
    if "ANSICON" in os.environ:
        return True
    return "WT_SESSION" in os.environ


def colorize(text: str, code: str) -> str:
    """Colorize text if terminal supports it."""
    if supports_color():
        return f"{code}{text}{RESET}"
    return text
