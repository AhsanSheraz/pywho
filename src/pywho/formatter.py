"""Terminal formatting for environment reports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pywho._terminal import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    WHITE,
    YELLOW,
)
from pywho._terminal import (
    colorize as _c,
)

if TYPE_CHECKING:
    from pywho.inspector import EnvironmentReport


def _section(title: str) -> str:
    return f"\n{_c(f'  {title}', BOLD + CYAN)}"


def _kv(key: str, value: str, indent: int = 4) -> str:
    """Format a key-value pair."""
    pad = " " * indent
    return f"{pad}{_c(key + ':', WHITE)} {_c(value, GREEN)}"


def format_report(report: EnvironmentReport, *, show_packages: bool = False) -> str:
    """
    Format an EnvironmentReport for terminal display.

    Args:
        report: The environment report to format.
        show_packages: Whether to show the installed packages list.

    Returns:
        Formatted string for terminal output.
    """
    lines: list[str] = []

    # Header
    lines.append("")
    lines.append(_c("  pywho", BOLD + MAGENTA) + _c(" - Python Environment Inspector", DIM))
    lines.append(_c("  " + "=" * 46, DIM))

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
        lines.append(_kv("Active", _c("Yes", GREEN)))
        lines.append(_kv("Type", vtype))
        if report.venv.path:
            lines.append(_kv("Path", report.venv.path))
        if report.venv.prompt:
            lines.append(_kv("Prompt", report.venv.prompt))
    else:
        lines.append(_kv("Active", _c("No (system Python)", YELLOW)))

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
        idx = _c(f"[{i}]", DIM)
        lines.append(f"    {idx} {_c(p, GREEN) if p else _c('(empty string = cwd)', YELLOW)}")

    # Packages section
    if show_packages and report.packages:
        lines.append(_section(f"Installed Packages ({len(report.packages)})"))
        max_name = max(len(p.name) for p in report.packages)
        for pkg in report.packages:
            name = pkg.name.ljust(max_name)
            lines.append(f"    {_c(name, WHITE)} {_c(pkg.version, GREEN)}")

    lines.append("")
    return "\n".join(lines)
