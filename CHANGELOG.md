# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-03-15

### Added

- `pywho scan` subcommand for project-wide shadow detection
- Scans directory trees for `.py` files that shadow stdlib or installed packages
- Severity levels: HIGH (stdlib) and MEDIUM (installed)
- `--no-installed` flag to check stdlib only
- `--json` flag for machine-readable output
- `scan_path()` Python API with `ShadowResult` dataclass
- Smart exclusions: skips .venv, __pycache__, node_modules, dist, build, etc.
- Ignores common non-module files: setup.py, conftest.py, manage.py

## [0.2.0] - 2026-03-15

### Added

- `pywho trace <module>` subcommand for import resolution tracing
- Shows where an import resolves and the full sys.path search order
- Shadow detection: warns when local files shadow stdlib or installed packages
- `--verbose` flag for full sys.path search log
- `--json` flag for trace output
- `trace_import()` Python API with `TraceReport` dataclass
- New docs pages for the trace feature

## [0.1.0] - 2026-03-15

### Added

- Initial release
- Core environment inspection: interpreter, platform, venv, paths, packages
- Virtual environment detection: venv, virtualenv, uv, conda, poetry, pipenv
- Package manager detection: pip, uv, conda, poetry, pipenv, pyenv
- CLI with `--json`, `--packages`, and `--no-pip` flags
- `python -m pywho` support
- Cross-platform support: Linux, macOS, Windows
- Python 3.9 - 3.14 support
- Typed (py.typed marker)
