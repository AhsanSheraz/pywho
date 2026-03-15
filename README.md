# pywho

**One command to explain your Python environment.**

Ever asked *"Which Python am I running? Why is it using that venv? Where are my packages?"* — pywho answers all of it instantly.

```
$ pywho

  pywho - Python Environment Inspector
  ==============================================

  Interpreter
    Executable: /Users/dev/.venv/bin/python3
    Version:    3.12.3 (CPython)
    Compiler:   Clang 15.0.0 (clang-1500.3.9.4)
    Architecture: 64-bit

  Platform
    System:  Darwin 24.1.0
    Machine: arm64

  Virtual Environment
    Active: Yes
    Type:   uv
    Path:   /Users/dev/myproject/.venv
    Prompt: myproject

  Paths
    Prefix:        /Users/dev/myproject/.venv
    Base Prefix:   /opt/homebrew/Cellar/python@3.12/3.12.3/Frameworks/Python.framework/Versions/3.12
    Site-packages: /Users/dev/myproject/.venv/lib/python3.12/site-packages

  Package Manager
    Detected:    uv
    pip version: 24.0

  sys.path
    [0] (empty string = cwd)
    [1] /opt/homebrew/Cellar/python@3.12/3.12.3/Frameworks/Python.framework/Versions/3.12/lib/python312.zip
    [2] /opt/homebrew/Cellar/python@3.12/3.12.3/Frameworks/Python.framework/Versions/3.12/lib/python3.12
    ...
```

## Why pywho?

- **"Works on my machine"** is the #1 debugging friction in Python. pywho kills it with one command.
- **Paste the output** into a GitHub issue, Slack message, or Stack Overflow question. Done.
- **Zero dependencies.** Pure stdlib. Works everywhere Python runs.
- **Cross-platform.** Linux, macOS, Windows. Python 3.9+.

## Installation

```bash
pip install pywho
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install pywho
```

Or run without installing:

```bash
uvx pywho
```

## Usage

### Basic inspection

```bash
pywho
```

### JSON output (for CI, scripts, sharing)

```bash
pywho --json
```

```json
{
  "interpreter": {
    "executable": "/usr/bin/python3",
    "version": "3.11.6",
    "implementation": "CPython",
    ...
  },
  "venv": {
    "is_active": false,
    "type": "none",
    ...
  },
  ...
}
```

### Include installed packages

```bash
pywho --packages
```

### Skip pip version check (faster)

```bash
pywho --no-pip
```

### Run as module

```bash
python -m pywho
```

## As a Python library

```python
from pywho import inspect_environment

report = inspect_environment()

print(report.executable)        # /usr/bin/python3
print(report.venv.is_active)    # True
print(report.venv.type)         # "uv"
print(report.package_manager)   # "uv"

# Get JSON-serializable dict
data = report.to_dict()
```

## What it detects

### Interpreters
- CPython, PyPy, and other implementations
- Version, compiler, architecture (32/64-bit)
- Build date

### Virtual environments
| Type | Detection method |
|------|-----------------|
| **venv** | `sys.prefix != sys.base_prefix` |
| **virtualenv** | `orig-prefix.txt` in lib directory |
| **uv** | `uv =` in `pyvenv.cfg` |
| **conda** | `CONDA_DEFAULT_ENV` env var |
| **poetry** | `POETRY_ACTIVE` env var |
| **pipenv** | `PIPENV_ACTIVE` env var |

### Package managers
Detects: pip, uv, conda, poetry, pipenv, pyenv

### Paths
- `sys.prefix`, `sys.base_prefix`, `sys.exec_prefix`
- All `site-packages` directories
- Full `sys.path` with index numbers

### Packages
With `--packages`: lists all installed packages with versions and locations.

## Use cases

- **Debugging**: Paste `pywho --json` output into bug reports
- **Onboarding**: New team member runs `pywho` to verify their setup
- **CI/CD**: Add `pywho --json` to your pipeline for environment snapshots
- **Support**: Ask users to run `pywho` instead of 5 separate commands

## Platforms

| Platform | Status |
|----------|--------|
| Linux | Supported |
| macOS | Supported |
| Windows | Supported |

| Python | Status |
|--------|--------|
| 3.9 | Supported |
| 3.10 | Supported |
| 3.11 | Supported |
| 3.12 | Supported |
| 3.13 | Supported |
| 3.14 | Supported |

## Development

```bash
git clone https://github.com/AhsanSheraz/pywho.git
cd pywho
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest -v
mypy src/pywho
```

## License

MIT
