"""Terminal formatting for import trace reports."""

from __future__ import annotations

from pywho._terminal import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    WHITE,
    YELLOW,
)
from pywho._terminal import (
    colorize as _c,
)
from pywho.tracer import ModuleType, SearchResult, TraceReport


def format_trace(report: TraceReport) -> str:
    """Format a TraceReport for terminal display."""
    lines: list[str] = []

    lines.append("")
    header = f"  Import Resolution: {report.module_name}"
    lines.append(_c(header, BOLD + CYAN))
    lines.append(_c("  " + "=" * (len(header) - 2), DIM))

    # Shadows — show warnings first if any
    if report.shadows:
        lines.append("")
        for shadow in report.shadows:
            lines.append(_c(f"  WARNING: {shadow.description}", BOLD + RED))
        lines.append("")

    # Resolution
    lines.append("")
    if report.resolved_path:
        lines.append(f"    {_c('Resolved to:', WHITE)} {_c(report.resolved_path, GREEN)}")
    else:
        lines.append(f"    {_c('Resolved to:', WHITE)} {_c('NOT FOUND', RED)}")

    # Module type
    type_color = {
        ModuleType.STDLIB: CYAN,
        ModuleType.THIRD_PARTY: GREEN,
        ModuleType.LOCAL: YELLOW,
        ModuleType.BUILTIN: MAGENTA,
        ModuleType.FROZEN: MAGENTA,
        ModuleType.NOT_FOUND: RED,
    }
    mtype = report.module_type.value
    if report.is_package:
        mtype += " (package)"
    color = type_color.get(report.module_type, WHITE)
    lines.append(f"    {_c('Module type:', WHITE)} {_c(mtype, color)}")

    # Cached
    cached_str = "Yes (in sys.modules)" if report.is_cached else "No"
    cached_color = GREEN if report.is_cached else DIM
    lines.append(f"    {_c('Cached:', WHITE)}      {_c(cached_str, cached_color)}")

    # Submodule
    if report.submodule_of:
        lines.append(f"    {_c('Submodule of:', WHITE)} {_c(report.submodule_of, CYAN)}")

    # Search order
    if report.search_log:
        lines.append("")
        lines.append(f"    {_c('Search order:', BOLD + WHITE)}")
        for i, entry in enumerate(report.search_log):
            idx = _c(f"[{i}]", DIM)
            path = entry.path

            if entry.result == SearchResult.FOUND:
                status = _c("FOUND", BOLD + GREEN)
                lines.append(f"      {idx} {path}")
                lines.append(f"           -> {status} {_c(entry.candidate or '', GREEN)}")
            elif entry.result == SearchResult.NOT_FOUND:
                status = _c("not found", DIM)
                lines.append(f"      {idx} {path} -> {status}")
            else:
                status = _c("skipped", DIM)
                lines.append(f"      {idx} {path} -> {status}")

    lines.append("")
    return "\n".join(lines)
