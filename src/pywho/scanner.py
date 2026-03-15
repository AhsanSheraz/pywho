"""Project-wide shadow scanner — detects .py files that shadow stdlib or installed packages."""

from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set


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


def _get_stdlib_names() -> Set[str]:
    """Return stdlib module names."""
    if hasattr(sys, "stdlib_module_names"):
        return set(sys.stdlib_module_names)
    # Fallback for 3.9
    return {
        "abc", "argparse", "ast", "asyncio", "base64", "bisect", "builtins",
        "calendar", "cmath", "cmd", "code", "codecs", "collections",
        "configparser", "contextlib", "copy", "csv", "ctypes", "dataclasses",
        "datetime", "decimal", "difflib", "dis", "email", "enum", "errno",
        "fnmatch", "fractions", "ftplib", "functools", "gc", "getpass",
        "glob", "gzip", "hashlib", "heapq", "hmac", "html", "http",
        "importlib", "inspect", "io", "itertools", "json", "keyword",
        "linecache", "locale", "logging", "lzma", "math", "mimetypes",
        "multiprocessing", "numbers", "operator", "os", "pathlib", "pdb",
        "pickle", "platform", "pprint", "profile", "pstats", "queue",
        "random", "re", "readline", "reprlib", "resource", "sched",
        "secrets", "select", "shelve", "shlex", "shutil", "signal",
        "site", "smtplib", "socket", "socketserver", "sqlite3", "ssl",
        "stat", "statistics", "string", "struct", "subprocess", "sys",
        "sysconfig", "tarfile", "tempfile", "textwrap", "threading",
        "time", "timeit", "token", "tokenize", "traceback", "types",
        "typing", "unicodedata", "unittest", "urllib", "uuid", "venv",
        "warnings", "weakref", "webbrowser", "xml", "xmlrpc", "zipfile",
        "zipimport", "zlib",
    }


# Files that are common project files, not intended as importable modules
_IGNORE_NAMES: Set[str] = {
    "setup", "conftest", "manage", "__init__", "__main__",
}

# Directories to skip during scanning
_EXCLUDE_DIRS: Set[str] = {
    ".git", ".hg", ".svn", "__pycache__", ".tox", ".nox",
    ".mypy_cache", ".pytest_cache", "node_modules", ".venv",
    "venv", "env", ".env", "site-packages", ".eggs", "dist",
    "build", ".ruff_cache",
}


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
        if origin in ("built-in", "frozen"):
            return False
        return True
    except (ModuleNotFoundError, ValueError):
        return False


def _walk_python_files(root: Path, exclude_dirs: Set[str]) -> List[Path]:
    """Walk directory tree yielding .py files, respecting exclusions."""
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in exclude_dirs and not d.endswith(".egg-info")
        ]
        for fname in filenames:
            if fname.endswith(".py"):
                files.append(Path(dirpath) / fname)
    return files


def scan_path(
    root: Path,
    *,
    check_installed: bool = True,
    exclude_dirs: Optional[Set[str]] = None,
    ignore_names: Optional[Set[str]] = None,
) -> List[ShadowResult]:
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

    stdlib = _get_stdlib_names()
    results: List[ShadowResult] = []

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
            results.append(ShadowResult(
                path=filepath,
                module_name=module_name,
                shadows="stdlib",
                severity=Severity.HIGH,
            ))
        elif check_installed and _is_installed_package(module_name):
            results.append(ShadowResult(
                path=filepath,
                module_name=module_name,
                shadows=f"installed:{module_name}",
                severity=Severity.MEDIUM,
            ))

    results.sort(key=lambda r: (r.severity.value, r.module_name))
    return results
