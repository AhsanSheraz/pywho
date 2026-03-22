"""Project-wide shadow scanner — detects .py files that shadow stdlib or installed packages."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pywho._stdlib import get_stdlib_names


class Severity(Enum):
    """How dangerous the shadow is."""

    HIGH = "high"  # shadows stdlib
    MEDIUM = "medium"  # shadows installed third-party package


@dataclass(frozen=True)
class ShadowResult:
    """A single detected shadow."""

    path: Path
    module_name: str
    shadows: str  # "stdlib" or "installed:<package>"
    severity: Severity

    @property
    def description(self) -> str:
        if self.severity == Severity.HIGH:
            return f"shadows stdlib module '{self.module_name}'"
        return f"shadows installed package '{self.module_name}'"


# Files that are common project files, not intended as importable modules
_IGNORE_NAMES: frozenset[str] = frozenset(
    {
        "setup",
        "conftest",
        "manage",
        "__init__",
        "__main__",
    }
)

# Directories to skip during scanning
_EXCLUDE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".tox",
        ".nox",
        ".mypy_cache",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".env",
        "site-packages",
        ".eggs",
        "dist",
        "build",
        ".ruff_cache",
    }
)


def _is_installed_package(name: str) -> bool:
    """Check if a name corresponds to an installed third-party package."""
    try:
        spec = importlib.util.find_spec(name)
        if spec is None:
            return False
        origin = spec.origin or ""
        # Exclude stdlib
        stdlib_path = os.path.dirname(os.__file__)
        if origin.startswith(stdlib_path) and "site-packages" not in origin:
            return False
        # Exclude builtins and frozen
        return origin not in ("built-in", "frozen")
    except (ModuleNotFoundError, ValueError):
        return False


def _walk_python_files(root: Path, exclude_dirs: frozenset[str]) -> list[Path]:
    """Walk directory tree yielding .py files, respecting exclusions."""
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.endswith(".egg-info")]
        for fname in filenames:
            if fname.endswith(".py"):
                files.append(Path(dirpath) / fname)
    return files


def scan_path(
    root: Path,
    *,
    check_installed: bool = True,
    exclude_dirs: frozenset[str] | None = None,
    ignore_names: frozenset[str] | None = None,
) -> list[ShadowResult]:
    """
    Scan a directory tree for Python files that shadow stdlib or installed packages.

    Args:
        root: Directory to scan (or a single .py file).
        check_installed: Also check against installed third-party packages.
        exclude_dirs: Directory names to skip.
        ignore_names: Module names to ignore.

    Returns:
        List of ShadowResult, sorted by severity (HIGH first).
    """
    if exclude_dirs is None:
        exclude_dirs = _EXCLUDE_DIRS
    if ignore_names is None:
        ignore_names = _IGNORE_NAMES

    stdlib = get_stdlib_names()
    results: list[ShadowResult] = []

    if root.is_file():
        candidates = [root] if root.suffix == ".py" else []
    else:
        candidates = _walk_python_files(root, exclude_dirs)

    for filepath in candidates:
        module_name = filepath.stem

        # Package directories: check the parent name for __init__.py
        if filepath.name == "__init__.py":
            module_name = filepath.parent.name

        if module_name in ignore_names:
            continue
        if module_name.startswith("_") and module_name != "_thread":
            continue

        if module_name in stdlib:
            results.append(
                ShadowResult(
                    path=filepath,
                    module_name=module_name,
                    shadows="stdlib",
                    severity=Severity.HIGH,
                )
            )
        elif check_installed and _is_installed_package(module_name):
            results.append(
                ShadowResult(
                    path=filepath,
                    module_name=module_name,
                    shadows=f"installed:{module_name}",
                    severity=Severity.MEDIUM,
                )
            )

    results.sort(key=lambda r: (r.severity.value, r.module_name))
    return results
