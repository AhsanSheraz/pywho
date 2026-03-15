# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
