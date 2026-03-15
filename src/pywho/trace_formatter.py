"""Terminal formatting for import trace reports."""

from __future__ import annotations

import sys
from typing import List

from pywho.tracer import ModuleType, SearchResult, TraceReport


# ANSI escape codes
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[91m"
_MAGENTA = "\033[35m"
_WHITE = "\033[37m"


def _supports_color() -> bool:
    """Check if stdout supports ANSI colors."""
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


def format_trace(report: TraceReport) -> str:
    """Format a TraceReport for terminal display."""
    lines: List[str] = []

    lines.append("")
    header = f"  Import Resolution: {report.module_name}"
    lines.append(_c(header, _BOLD + _CYAN))
    lines.append(_c("  " + "=" * (len(header) - 2), _DIM))

    # Shadows — show warnings first if any
    if report.shadows:
        lines.append("")
        for shadow in report.shadows:
            lines.append(_c(f"  WARNING: {shadow.description}", _BOLD + _RED))
        lines.append("")

    # Resolution
    lines.append("")
    if report.resolved_path:
        lines.append(f"    {_c('Resolved to:', _WHITE)} {_c(report.resolved_path, _GREEN)}")
    else:
        lines.append(f"    {_c('Resolved to:', _WHITE)} {_c('NOT FOUND', _RED)}")

    # Module type
    type_color = {
        ModuleType.STDLIB: _CYAN,
        ModuleType.THIRD_PARTY: _GREEN,
        ModuleType.LOCAL: _YELLOW,
        ModuleType.BUILTIN: _MAGENTA,
        ModuleType.FROZEN: _MAGENTA,
        ModuleType.NOT_FOUND: _RED,
    }
    mtype = report.module_type.value
    if report.is_package:
        mtype += " (package)"
    lines.append(f"    {_c('Module type:', _WHITE)} {_c(mtype, type_color.get(report.module_type, _WHITE))}")

    # Cached
    cached_str = "Yes (in sys.modules)" if report.is_cached else "No"
    lines.append(f"    {_c('Cached:', _WHITE)}      {_c(cached_str, _GREEN if report.is_cached else _DIM)}")

    # Submodule
    if report.submodule_of:
        lines.append(f"    {_c('Submodule of:', _WHITE)} {_c(report.submodule_of, _CYAN)}")

    # Search order
    if report.search_log:
        lines.append("")
        lines.append(f"    {_c('Search order:', _BOLD + _WHITE)}")
        for i, entry in enumerate(report.search_log):
            idx = _c(f"[{i}]", _DIM)
            path = entry.path

            if entry.result == SearchResult.FOUND:
                status = _c("FOUND", _BOLD + _GREEN)
                lines.append(f"      {idx} {path}")
                lines.append(f"           -> {status} {_c(entry.candidate or '', _GREEN)}")
            elif entry.result == SearchResult.NOT_FOUND:
                status = _c("not found", _DIM)
                lines.append(f"      {idx} {path} -> {status}")
            else:
                status = _c("skipped", _DIM)
                lines.append(f"      {idx} {path} -> {status}")

    lines.append("")
    return "\n".join(lines)
