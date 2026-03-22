<p align="center">
  <b>pywho</b><br>
  <i>One command to explain your Python environment, trace imports, and detect shadows.</i>
</p>

<p align="center">
  <a href="https://github.com/AhsanSheraz/pywho/actions/workflows/ci.yml"><img src="https://github.com/AhsanSheraz/pywho/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/pywho/"><img src="https://img.shields.io/pypi/v/pywho.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/pywho/"><img src="https://img.shields.io/pypi/pyversions/pywho.svg" alt="Python versions"></a>
  <a href="https://github.com/AhsanSheraz/pywho/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/pywho.svg" alt="License"></a>
  <a href="https://pypi.org/project/pywho/"><img src="https://img.shields.io/pypi/dm/pywho.svg" alt="Downloads"></a>
  <a href="https://codecov.io/gh/AhsanSheraz/pywho"><img src="https://codecov.io/gh/AhsanSheraz/pywho/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="https://pywho.readthedocs.io/"><img src="https://readthedocs.org/projects/pywho/badge/?version=latest" alt="Documentation"></a>
</p>

---

Ever asked *"Which Python am I running? Why did `import X` load that file? Do I have any files shadowing real modules?"* — **pywho** answers all of it instantly.

📖 **[Read the full documentation](https://pywho.readthedocs.io/)**

## Quick Reference

| Command | Description |
|---------|-------------|
| `pywho` | Show a full report of your Python environment |
| `pywho --json` | Output environment report as JSON |
| `pywho --packages` | Include all installed packages in the report |
| `pywho --no-pip` | Skip pip version detection (faster) |
| `pywho trace <module>` | Trace where an import resolves and show search order |
| `pywho trace <module> --verbose` | Trace with full sys.path search log |
| `pywho trace <module> --json` | Trace output as JSON |
| `pywho scan .` | Scan project for files that shadow stdlib/installed packages |
| `pywho scan . --no-installed` | Scan against stdlib only (skip installed packages) |
| `pywho scan . --json` | Scan output as JSON |
| `python -m pywho` | Run as a Python module |

## Table of Contents

- [Getting Started](#getting-started)
- [Why pywho?](#why-pywho)
- [Usage](#usage)
  - [Environment Inspection](#environment-inspection)
  - [Import Tracing](#import-tracing)
  - [Shadow Scanning](#shadow-scanning)
- [Python API](#python-api)
- [What It Detects](#what-it-detects)
- [Use Cases](#use-cases)
- [Platforms](#platforms)
- [Development](#development)
- [License](#license)

## Getting Started

```bash
pip install pywho
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install pywho
```

> **Note:** `uvx pywho` is not recommended — it runs inside uv's ephemeral sandbox, so the output reflects that temporary environment instead of your actual project. Always install pywho into the environment you want to inspect.

## Why pywho?

- **"Works on my machine"** is the #1 debugging friction in Python. pywho kills it with one command.
- **Paste the output** into a GitHub issue, Slack message, or Stack Overflow question. Done.
- **Zero dependencies.** Pure stdlib. Works everywhere Python runs.
- **Cross-platform.** Linux, macOS, Windows. Python 3.9+.

## Usage

### Environment Inspection

```bash
pywho
```

```
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
    Base Prefix:   /opt/homebrew/Cellar/python@3.12/...
    Site-packages: /Users/dev/myproject/.venv/lib/python3.12/site-packages

  Package Manager
    Detected:    uv
    pip version: 24.0

  sys.path
    [0] (empty string = cwd)
    [1] /opt/homebrew/.../python312.zip
    [2] /opt/homebrew/.../python3.12
    ...
```

#### JSON output (for CI, scripts, sharing)

```bash
pywho --json
```

#### Include installed packages

```bash
pywho --packages
```

#### Skip pip version check (faster)

```bash
pywho --no-pip
```

#### Run as module

```bash
python -m pywho
```

### Import Tracing

Trace exactly where an import resolves and why:

```bash
pywho trace requests
```

```
  Import Resolution: requests
  ========================================

  Resolved to: /Users/dev/.venv/lib/python3.12/site-packages/requests/__init__.py
  Module type: third-party (package)
  Cached:      No

  Search order:
    [0] /Users/dev/myproject        -> not found
    [1] /usr/lib/python3.12         -> not found
    [2] ~/.venv/lib/.../site-packages -> FOUND
```

#### Full search log

```bash
pywho trace json --verbose
```

#### JSON trace output

```bash
pywho trace requests --json
```

#### Shadow detection (single module)

```bash
$ pywho trace requests

  WARNING: './requests.py' shadows installed package 'requests'
```

### Shadow Scanning

Scan an entire project for files that shadow stdlib or installed packages:

```bash
$ pywho scan .

  Found 2 shadow(s)
    2 HIGH (stdlib)

  [HIGH] math.py
         shadows stdlib module 'math'
  [HIGH] json.py
         shadows stdlib module 'json'
```

#### Scan with JSON output

```bash
pywho scan . --json
```

#### Scan stdlib only (skip installed packages)

```bash
pywho scan . --no-installed
```

Smart exclusions — these directories are automatically skipped: `.venv`, `__pycache__`, `node_modules`, `dist`, `build`, `.git`, and more.

## Python API

### Environment inspection

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

### Import tracing

```python
from pywho import trace_import

trace = trace_import("requests")
print(trace.resolved_path)    # /path/to/requests/__init__.py
print(trace.module_type)      # ModuleType.THIRD_PARTY
print(trace.is_cached)        # True
print(trace.shadows)          # [] (empty = no shadows)

if trace.shadows:
    for s in trace.shadows:
        print(f"WARNING: {s.description}")
```

### Shadow scanning

```python
from pywho import scan_path
from pathlib import Path

results = scan_path(Path("."))
for r in results:
    print(f"[{r.severity.value.upper()}] {r.path} shadows {r.module_name}")
```

## What It Detects

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

### Import shadows
- Single-module detection via `pywho trace`
- Project-wide scanning via `pywho scan`
- Severity levels: **HIGH** (stdlib) and **MEDIUM** (installed)

## Use Cases

| Scenario | Command |
|----------|---------|
| Debug "works on my machine" | `pywho --json` → paste into issue |
| Verify onboarding setup | `pywho` |
| CI environment snapshots | `pywho --json --packages > env.json` |
| Find why an import is wrong | `pywho trace <module>` |
| Audit project for shadows | `pywho scan .` |
| Ask users for their env | "Please run `pywho`" |

## Platforms

| Platform | Status |
|----------|--------|
| Linux | ✅ Supported |
| macOS | ✅ Supported |
| Windows | ✅ Supported |

| Python | Status |
|--------|--------|
| 3.9+ | ✅ Supported |
| 3.10 – 3.14 | ✅ Tested in CI |

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

[MIT](LICENSE)
