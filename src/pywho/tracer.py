"""Import resolution tracer — explains where an import resolves and why."""

from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ModuleType(Enum):
    """Classification of a resolved module."""

    STDLIB = "stdlib"
    THIRD_PARTY = "third-party"
    LOCAL = "local"
    BUILTIN = "builtin"
    FROZEN = "frozen"
    NOT_FOUND = "not-found"


class SearchResult(Enum):
    """Result of checking a single sys.path entry."""

    FOUND = "found"
    NOT_FOUND = "not-found"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class PathSearchEntry:
    """One entry in the sys.path search log."""

    path: str
    result: SearchResult
    candidate: str | None = None  # file that was found (if any)


@dataclass(frozen=True)
class ShadowWarning:
    """A detected import shadow."""

    shadow_path: str
    shadowed_module: str
    description: str


@dataclass(frozen=True)
class TraceReport:
    """Complete import resolution trace for a single module."""

    module_name: str
    resolved_path: str | None
    module_type: ModuleType
    is_package: bool
    is_cached: bool
    submodule_of: str | None
    search_log: list[PathSearchEntry] = field(default_factory=list)
    shadows: list[ShadowWarning] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "module_name": self.module_name,
            "resolved_path": self.resolved_path,
            "module_type": self.module_type.value,
            "is_package": self.is_package,
            "is_cached": self.is_cached,
            "submodule_of": self.submodule_of,
            "search_log": [
                {
                    "path": e.path,
                    "result": e.result.value,
                    "candidate": e.candidate,
                }
                for e in self.search_log
            ],
            "shadows": [
                {
                    "shadow_path": s.shadow_path,
                    "shadowed_module": s.shadowed_module,
                    "description": s.description,
                }
                for s in self.shadows
            ],
        }


def _get_stdlib_names() -> set[str]:
    """Return stdlib module names."""
    if hasattr(sys, "stdlib_module_names"):
        return set(sys.stdlib_module_names)
    # Fallback for 3.9
    return {
        "abc",
        "argparse",
        "ast",
        "asyncio",
        "base64",
        "bisect",
        "builtins",
        "calendar",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "collections",
        "configparser",
        "contextlib",
        "copy",
        "csv",
        "ctypes",
        "dataclasses",
        "datetime",
        "decimal",
        "difflib",
        "dis",
        "email",
        "enum",
        "errno",
        "fnmatch",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "getpass",
        "glob",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "importlib",
        "inspect",
        "io",
        "itertools",
        "json",
        "keyword",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "math",
        "mimetypes",
        "multiprocessing",
        "numbers",
        "operator",
        "os",
        "pathlib",
        "pdb",
        "pickle",
        "platform",
        "pprint",
        "profile",
        "pstats",
        "queue",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "sched",
        "secrets",
        "select",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtplib",
        "socket",
        "socketserver",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "struct",
        "subprocess",
        "sys",
        "sysconfig",
        "tarfile",
        "tempfile",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "token",
        "tokenize",
        "traceback",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uuid",
        "venv",
        "warnings",
        "weakref",
        "webbrowser",
        "xml",
        "xmlrpc",
        "zipfile",
        "zipimport",
        "zlib",
    }


def _classify_module(
    name: str,
    spec: importlib.machinery.ModuleSpec | None,
) -> ModuleType:
    """Classify a module based on its spec."""
    if spec is None:
        return ModuleType.NOT_FOUND

    if spec.origin == "built-in":
        return ModuleType.BUILTIN

    if spec.origin == "frozen":
        return ModuleType.FROZEN

    origin = spec.origin or ""

    # Check site-packages FIRST — on some platforms (macOS system Python),
    # site-packages lives under the same prefix as stdlib
    if "site-packages" in origin or "dist-packages" in origin:
        return ModuleType.THIRD_PARTY

    if name in _get_stdlib_names() or name in sys.builtin_module_names:
        return ModuleType.STDLIB

    stdlib_path = os.path.dirname(os.__file__)
    if origin.startswith(stdlib_path):
        return ModuleType.STDLIB

    return ModuleType.LOCAL


def _find_candidates_on_path(
    name: str,
    search_paths: list[str],
) -> list[PathSearchEntry]:
    """Walk sys.path and check each entry for the module."""
    top_level = name.split(".")[0]
    entries: list[PathSearchEntry] = []

    for path_str in search_paths:
        if not path_str:
            path_str = os.getcwd()

        path = Path(path_str)
        if not path.is_dir():
            entries.append(
                PathSearchEntry(
                    path=path_str,
                    result=SearchResult.SKIPPED,
                )
            )
            continue

        # Check for package (directory with __init__.py)
        pkg_init = path / top_level / "__init__.py"
        if pkg_init.exists():
            entries.append(
                PathSearchEntry(
                    path=path_str,
                    result=SearchResult.FOUND,
                    candidate=str(pkg_init),
                )
            )
            continue

        # Check for single-file module
        module_file = path / f"{top_level}.py"
        if module_file.exists():
            entries.append(
                PathSearchEntry(
                    path=path_str,
                    result=SearchResult.FOUND,
                    candidate=str(module_file),
                )
            )
            continue

        # Check for compiled extensions
        for ext in importlib.machinery.EXTENSION_SUFFIXES:
            ext_file = path / f"{top_level}{ext}"
            if ext_file.exists():
                entries.append(
                    PathSearchEntry(
                        path=path_str,
                        result=SearchResult.FOUND,
                        candidate=str(ext_file),
                    )
                )
                break
        else:
            entries.append(
                PathSearchEntry(
                    path=path_str,
                    result=SearchResult.NOT_FOUND,
                )
            )

    return entries


def _detect_shadows(
    name: str,
    search_log: list[PathSearchEntry],
    module_type: ModuleType,
) -> list[ShadowWarning]:
    """Detect if any earlier path entries shadow the resolved module."""
    stdlib_names = _get_stdlib_names()
    shadows: list[ShadowWarning] = []

    found_entries = [e for e in search_log if e.result == SearchResult.FOUND]
    if len(found_entries) <= 1:
        return shadows

    # The first FOUND entry is what Python actually uses.
    # Any subsequent FOUND entries are being shadowed.
    winner = found_entries[0]

    top_level = name.split(".")[0]

    # If a local file shadows a stdlib or third-party module
    if top_level in stdlib_names:
        winner_in_stdlib = False
        stdlib_path = os.path.dirname(os.__file__)
        if winner.candidate and stdlib_path in winner.candidate:
            winner_in_stdlib = True

        if not winner_in_stdlib:
            shadows.append(
                ShadowWarning(
                    shadow_path=winner.candidate or "unknown",
                    shadowed_module=top_level,
                    description=f"'{winner.candidate}' shadows stdlib module '{top_level}'",
                )
            )

    # If multiple found, the first one shadows the rest
    for other in found_entries[1:]:
        if (
            other.candidate
            and winner.candidate
            and other.candidate != winner.candidate
            and "site-packages" in (other.candidate or "")
        ):
            shadows.append(
                ShadowWarning(
                    shadow_path=winner.candidate or "unknown",
                    shadowed_module=top_level,
                    description=(
                        f"'{winner.candidate}' shadows installed package at '{other.candidate}'"
                    ),
                )
            )

    return shadows


def trace_import(
    module_name: str,
    *,
    verbose: bool = False,
) -> TraceReport:
    """
    Trace the import resolution for a module name.

    Args:
        module_name: The module to trace (e.g., "requests", "json", "os.path").
        verbose: Include all sys.path entries in the search log.

    Returns:
        TraceReport with full resolution details.
    """
    # Check if already in sys.modules
    is_cached = module_name in sys.modules

    # Try to find the module spec without importing it
    try:
        spec = importlib.util.find_spec(module_name)
    except (ModuleNotFoundError, ValueError):
        spec = None

    resolved_path: str | None = None
    is_package = False
    submodule_of: str | None = None

    if spec is not None:
        resolved_path = spec.origin
        is_package = spec.submodule_search_locations is not None
        if "." in module_name:
            submodule_of = module_name.rsplit(".", 1)[0]

    module_type = _classify_module(module_name, spec)

    # Build the search log
    search_log = _find_candidates_on_path(module_name, sys.path)

    # Detect shadows
    shadows = _detect_shadows(module_name, search_log, module_type)

    # In non-verbose mode, only keep FOUND entries and the first few NOT_FOUND
    if not verbose:
        filtered: list[PathSearchEntry] = []
        not_found_count = 0
        for entry in search_log:
            if entry.result == SearchResult.FOUND:
                filtered.append(entry)
            elif entry.result == SearchResult.NOT_FOUND and not_found_count < 3:
                filtered.append(entry)
                not_found_count += 1
            elif entry.result == SearchResult.SKIPPED:
                continue
        search_log = filtered

    return TraceReport(
        module_name=module_name,
        resolved_path=resolved_path,
        module_type=module_type,
        is_package=is_package,
        is_cached=is_cached,
        submodule_of=submodule_of,
        search_log=search_log,
        shadows=shadows,
    )
