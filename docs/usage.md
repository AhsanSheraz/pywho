# Usage

## CLI

### Basic inspection

```bash
pywho
```

Prints a formatted report of your current Python environment.

### JSON output

```bash
pywho --json
```

Outputs a JSON object — useful for CI pipelines, scripting, or sharing in bug reports.

### Include installed packages

```bash
pywho --packages
```

Adds a full list of installed packages with versions to the output.

### Skip pip version check

```bash
pywho --no-pip
```

Skips the subprocess call to detect pip version, making the output slightly faster.

### Run as a module

```bash
python -m pywho
```

### Combine flags

```bash
pywho --json --packages
```

## Import tracing

### Trace where an import resolves

```bash
pywho trace requests
```

Shows:

- The resolved file path
- Module type (stdlib, third-party, local, builtin)
- Whether it's cached in `sys.modules`
- The sys.path search order
- Shadow warnings (if a local file shadows a real module)

### Full search log

```bash
pywho trace json --verbose
```

Shows every sys.path entry that was checked, not just the abbreviated version.

### JSON trace output

```bash
pywho trace requests --json
```

### Shadow detection

If a local file shadows a stdlib or installed package, you'll see:

```
WARNING: './requests.py' shadows installed package 'requests'
```

## Shadow scanning

### Scan a project for shadows

```bash
pywho scan .
```

Recursively scans for `.py` files that shadow stdlib or installed packages.

### Scan stdlib only (faster)

```bash
pywho scan . --no-installed
```

### Scan with JSON output

```bash
pywho scan . --json
```

### Scan a specific directory

```bash
pywho scan src/
```

### Scan a single file

```bash
pywho scan math.py
```

Smart exclusions — these directories are automatically skipped:

- `.venv`, `venv`, `env`, `.env`
- `__pycache__`, `.git`, `.tox`, `.mypy_cache`
- `node_modules`, `dist`, `build`, `.eggs`

Common non-module files are ignored: `setup.py`, `conftest.py`, `manage.py`, `__init__.py`.

### Scan in Python code

```python
from pywho import scan_path
from pathlib import Path

results = scan_path(Path("."))
for r in results:
    print(f"[{r.severity.value.upper()}] {r.path} shadows {r.module_name}")
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Success (no shadows for `trace` / `scan`) |
| `1`  | Shadows detected (for `trace` / `scan`) |
| `2`  | Error (e.g., path does not exist for `scan`) |

## Python library

```python
from pywho import inspect_environment

report = inspect_environment()

# Access fields directly
print(report.executable)
print(report.version)
print(report.venv.is_active)
print(report.venv.type)
print(report.package_manager)

# Skip package listing for speed
report = inspect_environment(include_packages=False)

# Serialize to dict (JSON-compatible)
data = report.to_dict()
```

## Common workflows

### Paste into a GitHub issue

```bash
pywho --json | pbcopy  # macOS
pywho --json | xclip   # Linux
```

### Save environment snapshot in CI

```bash
pywho --json --packages > environment.json
```

### Compare two environments

```bash
# On machine A
pywho --json > env-a.json

# On machine B
pywho --json > env-b.json

# Diff
diff env-a.json env-b.json
```

### Debug a mysterious ImportError

```bash
pywho trace requests
# Shows exactly which file Python is loading and if it's shadowed
```

### Trace imports in Python code

```python
from pywho import trace_import

trace = trace_import("requests")
print(trace.resolved_path)
print(trace.module_type)

if trace.shadows:
    for s in trace.shadows:
        print(f"WARNING: {s.description}")
```
