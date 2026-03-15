"""Terminal formatting for scan results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pywho._terminal import BOLD, DIM, GREEN, RED, WHITE, YELLOW
from pywho._terminal import colorize as _c
from pywho.scanner import Severity, ShadowResult

if TYPE_CHECKING:
    from pathlib import Path


def format_scan(results: list[ShadowResult], root: Path) -> str:
    """Format scan results for terminal display."""
    if not results:
        return _c("\n  No shadows detected.\n", GREEN)

    lines: list[str] = []
    high = sum(1 for r in results if r.severity == Severity.HIGH)
    medium = sum(1 for r in results if r.severity == Severity.MEDIUM)

    lines.append("")
    lines.append(_c(f"  Found {len(results)} shadow(s)", BOLD + WHITE))
    if high:
        lines.append(_c(f"    {high} HIGH (stdlib)", RED))
    if medium:
        lines.append(_c(f"    {medium} MEDIUM (installed)", YELLOW))
    lines.append("")

    for result in results:
        try:
            rel = result.path.relative_to(root)
        except ValueError:
            rel = result.path

        if result.severity == Severity.HIGH:
            tag = _c("HIGH", BOLD + RED)
        else:
            tag = _c("MEDIUM", BOLD + YELLOW)

        lines.append(f"  [{tag}] {rel}")
        lines.append(f"         {_c(result.description, DIM)}")

    lines.append("")
    return "\n".join(lines)
