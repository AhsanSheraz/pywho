"""Core environment inspection engine."""

from __future__ import annotations

import os
import platform
import site
import struct
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PackageInfo:
    """Metadata for an installed package."""

    name: str
    version: str
    location: str


@dataclass(frozen=True)
class VenvInfo:
    """Virtual environment details."""

    is_active: bool
    type: str  # "venv", "virtualenv", "conda", "poetry", "pipenv", "uv", "none"
    path: Optional[str]
    prompt: Optional[str]


@dataclass(frozen=True)
class EnvironmentReport:
    """Complete snapshot of the current Python environment."""

    # Interpreter
    executable: str
    version: str
    version_info: str
    implementation: str
    compiler: str
    architecture: str
    build_date: str

    # Platform
    platform_system: str
    platform_release: str
    platform_machine: str

    # Virtual environment
    venv: VenvInfo

    # Paths
    prefix: str
    base_prefix: str
    exec_prefix: str
    sys_path: List[str]
    site_packages: List[str]

    # Package manager hints
    package_manager: str
    pip_version: Optional[str]

    # Installed packages (top-level only for speed)
    packages: List[PackageInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialize to a plain dictionary for JSON output."""
        return {
            "interpreter": {
                "executable": self.executable,
                "version": self.version,
                "version_info": self.version_info,
                "implementation": self.implementation,
                "compiler": self.compiler,
                "architecture": self.architecture,
                "build_date": self.build_date,
            },
            "platform": {
                "system": self.platform_system,
                "release": self.platform_release,
                "machine": self.platform_machine,
            },
            "venv": {
                "is_active": self.venv.is_active,
                "type": self.venv.type,
                "path": self.venv.path,
                "prompt": self.venv.prompt,
            },
            "paths": {
                "prefix": self.prefix,
                "base_prefix": self.base_prefix,
                "exec_prefix": self.exec_prefix,
                "sys_path": self.sys_path,
                "site_packages": self.site_packages,
            },
            "package_manager": self.package_manager,
            "pip_version": self.pip_version,
            "packages": [
                {"name": p.name, "version": p.version, "location": p.location}
                for p in self.packages
            ],
        }


def _detect_venv() -> VenvInfo:
    """Detect virtual environment type and details."""
    # Standard venv / virtualenv: prefix != base_prefix
    in_venv = sys.prefix != sys.base_prefix

    # Check for conda
    if os.environ.get("CONDA_DEFAULT_ENV"):
        return VenvInfo(
            is_active=True,
            type="conda",
            path=os.environ.get("CONDA_PREFIX"),
            prompt=os.environ.get("CONDA_DEFAULT_ENV"),
        )

    # Check for pipenv
    if os.environ.get("PIPENV_ACTIVE") == "1":
        return VenvInfo(
            is_active=True,
            type="pipenv",
            path=sys.prefix,
            prompt=Path(sys.prefix).name,
        )

    if not in_venv:
        return VenvInfo(is_active=False, type="none", path=None, prompt=None)

    venv_path = sys.prefix
    venv_type = "venv"
    prompt = Path(venv_path).name

    # Distinguish venv from virtualenv
    # virtualenv creates an orig-prefix.txt file:
    #   Unix:    lib/pythonX.Y/orig-prefix.txt
    #   Windows: Lib/orig-prefix.txt (no pythonX.Y subdirectory)
    if sys.platform == "win32":
        orig_prefix_file = Path(venv_path) / "Lib" / "orig-prefix.txt"
    else:
        orig_prefix_file = (
            Path(venv_path) / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "orig-prefix.txt"
        )
    if orig_prefix_file.exists():
        venv_type = "virtualenv"

    # Check for uv-created venvs (uv leaves a pyvenv.cfg with uv = ...)
    pyvenv_cfg = Path(venv_path) / "pyvenv.cfg"
    if pyvenv_cfg.exists():
        try:
            cfg_text = pyvenv_cfg.read_text()
            if "uv = " in cfg_text or "uv=" in cfg_text:
                venv_type = "uv"
            # Read prompt from pyvenv.cfg if available
            for line in cfg_text.splitlines():
                if line.startswith("prompt"):
                    _, _, value = line.partition("=")
                    value = value.strip().strip("'\"")
                    if value:
                        prompt = value
                    break
        except OSError:
            pass

    # Check for Poetry (look for poetry.lock near the venv)
    # Poetry venvs are typically in {cache}/virtualenvs/ or .venv/
    if os.environ.get("POETRY_ACTIVE") == "1":
        venv_type = "poetry"

    return VenvInfo(
        is_active=True,
        type=venv_type,
        path=venv_path,
        prompt=prompt,
    )


def _get_site_packages() -> List[str]:
    """Return active site-packages directories."""
    dirs: List[str] = []
    try:
        dirs.extend(site.getsitepackages())
    except AttributeError:
        pass
    user_site = site.getusersitepackages()
    if isinstance(user_site, str) and os.path.isdir(user_site):
        dirs.append(user_site)
    return dirs


def _detect_package_manager() -> str:
    """Best-effort guess at the tool managing this environment."""
    if os.environ.get("CONDA_DEFAULT_ENV"):
        return "conda"
    if os.environ.get("PIPENV_ACTIVE") == "1":
        return "pipenv"
    if os.environ.get("POETRY_ACTIVE") == "1":
        return "poetry"

    # Check pyvenv.cfg for uv
    pyvenv_cfg = Path(sys.prefix) / "pyvenv.cfg"
    if pyvenv_cfg.exists():
        try:
            cfg_text = pyvenv_cfg.read_text()
            if "uv = " in cfg_text or "uv=" in cfg_text:
                return "uv"
        except OSError:
            pass

    # Check if pyenv is managing the interpreter
    if "pyenv" in sys.executable:
        return "pyenv"

    return "pip"


def _get_pip_version() -> Optional[str]:
    """Get installed pip version without importing it."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # "pip 24.0 from /path/to/pip (python 3.12)"
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                return parts[1]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _get_installed_packages() -> List[PackageInfo]:
    """List installed packages using importlib.metadata."""
    try:
        from importlib.metadata import distributions

        packages: List[PackageInfo] = []
        seen = set()
        for dist in distributions():
            name = dist.metadata["Name"]
            if name in seen:
                continue
            seen.add(name)
            version = dist.metadata["Version"] or "unknown"
            location = str(dist._path.parent) if hasattr(dist, "_path") else "unknown"
            packages.append(PackageInfo(name=name, version=version, location=location))

        packages.sort(key=lambda p: p.name.lower())
        return packages
    except Exception:
        return []


def inspect_environment(*, include_packages: bool = True) -> EnvironmentReport:
    """
    Inspect the current Python environment and return a structured report.

    Args:
        include_packages: Whether to list installed packages (slightly slower).

    Returns:
        EnvironmentReport with all environment details.
    """
    venv = _detect_venv()
    # Extract build info: "3.11.15 (main, Mar 3 2026, 15:47:15)" -> "main, Mar 3 2026, 15:47:15"
    build_info = ""
    if "(" in sys.version:
        # Take only the first parenthesized group
        after_paren = sys.version.split("(", 1)[1]
        build_info = after_paren.split(")")[0].strip()

    return EnvironmentReport(
        executable=sys.executable,
        version=platform.python_version(),
        version_info=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        implementation=platform.python_implementation(),
        compiler=platform.python_compiler(),
        architecture=f"{struct.calcsize('P') * 8}-bit",
        build_date=build_info,
        platform_system=platform.system(),
        platform_release=platform.release(),
        platform_machine=platform.machine(),
        venv=venv,
        prefix=sys.prefix,
        base_prefix=sys.base_prefix,
        exec_prefix=sys.exec_prefix,
        sys_path=sys.path.copy(),
        site_packages=_get_site_packages(),
        package_manager=_detect_package_manager(),
        pip_version=_get_pip_version(),
        packages=_get_installed_packages() if include_packages else [],
    )
