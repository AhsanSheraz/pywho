"""Terminal formatting for scan results."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from pywho.scanner import ShadowResult, Severity


# ANSI escape codes
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[91m"
_WHITE = "\033[37m"


def _supports_color() -> bool:
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return True
    if "ANSICON" in __import__("os").environ:
        return True
    if "WT_SESSION" in __import__("os").environ:
        return True
    return False


def _c(text: str, code: str) -> str:
    if _supports_color():
        return f"{code}{text}{_RESET}"
    return text


def format_scan(results: List[ShadowResult], root: Path) -> str:
    """Format scan results for terminal display."""
    if not results:
        return _c("\n  No shadows detected.\n", _GREEN)

    lines: List[str] = []
    high = sum(1 for r in results if r.severity == Severity.HIGH)
    medium = sum(1 for r in results if r.severity == Severity.MEDIUM)

    lines.append("")
    lines.append(_c(f"  Found {len(results)} shadow(s)", _BOLD + _WHITE))
    if high:
        lines.append(_c(f"    {high} HIGH (stdlib)", _RED))
    if medium:
        lines.append(_c(f"    {medium} MEDIUM (installed)", _YELLOW))
    lines.append("")

    for result in results:
        try:
            rel = result.path.relative_to(root)
        except ValueError:
            rel = result.path

        if result.severity == Severity.HIGH:
            tag = _c("HIGH", _BOLD + _RED)
        else:
            tag = _c("MEDIUM", _BOLD + _YELLOW)

        lines.append(f"  [{tag}] {rel}")
        lines.append(f"         {_c(result.description, _DIM)}")

    lines.append("")
    return "\n".join(lines)
