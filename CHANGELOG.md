# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.3] - 2026-03-22

### Changed

- Replaced `uvx pywho` recommendation with caveat about ephemeral environments
- Re-release to include updated README on PyPI

## [0.3.2] - 2026-03-22

### Fixed

- Respect `NO_COLOR` / `FORCE_COLOR` environment variables (https://no-color.org/)
- Cache `supports_color()` with `lru_cache` to avoid redundant syscalls
- Replace private `dist._path` with public `dist.locate_file()` API
- Narrow bare `except Exception` to `(ImportError, StopIteration, OSError)`
- Complete Python 3.9 stdlib fallback (100 to 205 modules)
- Eliminate redundant `pyvenv.cfg` read in `_detect_package_manager()`
- Add explicit `encoding="utf-8"` for `pyvenv.cfg` reads
- Add `if __name__ == "__main__"` guard to `__main__.py`

### Changed

- Extract duplicated `_get_stdlib_names()` to shared `_stdlib.py` module
- Use `frozenset` for `_EXCLUDE_DIRS` and `_IGNORE_NAMES` constants
- Upgrade classifier to `Development Status :: 5 - Production/Stable`

## [0.3.1] - 2026-03-15

### Added

- Release workflow: publish to PyPI automatically on GitHub Release creation
- 95% minimum test coverage enforced in CI
- Comprehensive test suite: 131 tests with 97% coverage
- Tests for all venv types (conda, pipenv, virtualenv, uv, poetry)
- Cross-platform test fixes for Windows and Python 3.9

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
