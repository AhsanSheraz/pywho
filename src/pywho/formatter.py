"""Terminal formatting for environment reports."""

from __future__ import annotations

import sys
from typing import List

from pywho.inspector import EnvironmentReport


# ANSI escape codes
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
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
    """Colorize text if terminal supports it."""
    if _supports_color():
        return f"{code}{text}{_RESET}"
    return text


def _section(title: str) -> str:
    return f"\n{_c(f'  {title}', _BOLD + _CYAN)}"


def _kv(key: str, value: str, indent: int = 4) -> str:
    """Format a key-value pair."""
    pad = " " * indent
    return f"{pad}{_c(key + ':', _WHITE)} {_c(value, _GREEN)}"


def format_report(report: EnvironmentReport, *, show_packages: bool = False) -> str:
    """
    Format an EnvironmentReport for terminal display.

    Args:
        report: The environment report to format.
        show_packages: Whether to show the installed packages list.

    Returns:
        Formatted string for terminal output.
    """
    lines: List[str] = []

    # Header
    lines.append("")
    lines.append(_c("  pywho", _BOLD + _MAGENTA) + _c(" - Python Environment Inspector", _DIM))
    lines.append(_c("  " + "=" * 46, _DIM))

    # Interpreter section
    lines.append(_section("Interpreter"))
    lines.append(_kv("Executable", report.executable))
    lines.append(_kv("Version", f"{report.version} ({report.implementation})"))
    lines.append(_kv("Compiler", report.compiler))
    lines.append(_kv("Architecture", report.architecture))
    if report.build_date:
        lines.append(_kv("Build", report.build_date))

    # Platform section
    lines.append(_section("Platform"))
    lines.append(_kv("System", f"{report.platform_system} {report.platform_release}"))
    lines.append(_kv("Machine", report.platform_machine))

    # Virtual environment section
    lines.append(_section("Virtual Environment"))
    if report.venv.is_active:
        vtype = report.venv.type
        lines.append(_kv("Active", _c("Yes", _GREEN)))
        lines.append(_kv("Type", vtype))
        if report.venv.path:
            lines.append(_kv("Path", report.venv.path))
        if report.venv.prompt:
            lines.append(_kv("Prompt", report.venv.prompt))
    else:
        lines.append(_kv("Active", _c("No (system Python)", _YELLOW)))

    # Paths section
    lines.append(_section("Paths"))
    lines.append(_kv("Prefix", report.prefix))
    if report.prefix != report.base_prefix:
        lines.append(_kv("Base Prefix", report.base_prefix))
    for sp in report.site_packages:
        lines.append(_kv("Site-packages", sp))

    # Package manager section
    lines.append(_section("Package Manager"))
    lines.append(_kv("Detected", report.package_manager))
    if report.pip_version:
        lines.append(_kv("pip version", report.pip_version))

    # sys.path section
    lines.append(_section("sys.path"))
    for i, p in enumerate(report.sys_path):
        idx = _c(f"[{i}]", _DIM)
        lines.append(f"    {idx} {_c(p, _GREEN) if p else _c('(empty string = cwd)', _YELLOW)}")

    # Packages section
    if show_packages and report.packages:
        lines.append(_section(f"Installed Packages ({len(report.packages)})"))
        # Find the longest package name for alignment
        max_name = max(len(p.name) for p in report.packages)
        for pkg in report.packages:
            name = pkg.name.ljust(max_name)
            lines.append(f"    {_c(name, _WHITE)} {_c(pkg.version, _GREEN)}")

    lines.append("")
    return "\n".join(lines)
