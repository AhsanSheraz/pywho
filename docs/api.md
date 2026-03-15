# API Reference

## `inspect_environment`

```python
from pywho import inspect_environment

report = inspect_environment(include_packages=True)
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `include_packages` | `bool` | `True` | Whether to list installed packages. Set to `False` for faster output. |

**Returns:** `EnvironmentReport`

---

## `EnvironmentReport`

Frozen dataclass containing the full environment snapshot.

### Interpreter fields

| Field | Type | Description |
|-------|------|-------------|
| `executable` | `str` | Path to the Python executable |
| `version` | `str` | Python version string (e.g., `"3.12.3"`) |
| `version_info` | `str` | Major.minor.micro version |
| `implementation` | `str` | Python implementation (e.g., `"CPython"`) |
| `compiler` | `str` | Compiler used to build Python |
| `architecture` | `str` | `"64-bit"` or `"32-bit"` |
| `build_date` | `str` | Build info string |

### Platform fields

| Field | Type | Description |
|-------|------|-------------|
| `platform_system` | `str` | OS name (e.g., `"Darwin"`, `"Linux"`, `"Windows"`) |
| `platform_release` | `str` | OS release version |
| `platform_machine` | `str` | Machine architecture (e.g., `"arm64"`, `"x86_64"`) |

### Virtual environment

| Field | Type | Description |
|-------|------|-------------|
| `venv` | `VenvInfo` | Virtual environment details |

### Path fields

| Field | Type | Description |
|-------|------|-------------|
| `prefix` | `str` | `sys.prefix` |
| `base_prefix` | `str` | `sys.base_prefix` |
| `exec_prefix` | `str` | `sys.exec_prefix` |
| `sys_path` | `list[str]` | Copy of `sys.path` |
| `site_packages` | `list[str]` | Active site-packages directories |

### Package management

| Field | Type | Description |
|-------|------|-------------|
| `package_manager` | `str` | Detected package manager |
| `pip_version` | `str \| None` | pip version if available |
| `packages` | `list[PackageInfo]` | Installed packages (if requested) |

### Methods

#### `to_dict() -> dict`

Returns a JSON-serializable dictionary of the full report.

---

## `VenvInfo`

Frozen dataclass for virtual environment details.

| Field | Type | Description |
|-------|------|-------------|
| `is_active` | `bool` | Whether a venv is active |
| `type` | `str` | One of: `"venv"`, `"virtualenv"`, `"uv"`, `"conda"`, `"poetry"`, `"pipenv"`, `"none"` |
| `path` | `str \| None` | Path to the virtual environment |
| `prompt` | `str \| None` | Venv prompt name |

---

## `PackageInfo`

Frozen dataclass for an installed package.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Package name |
| `version` | `str` | Installed version |
| `location` | `str` | Installation path |

---

## `trace_import`

```python
from pywho import trace_import

report = trace_import("requests", verbose=False)
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `module_name` | `str` | *(required)* | Module to trace (e.g., `"requests"`, `"os.path"`) |
| `verbose` | `bool` | `False` | Include all sys.path entries in search log |

**Returns:** `TraceReport`

---

## `TraceReport`

Frozen dataclass containing the full import resolution trace.

| Field | Type | Description |
|-------|------|-------------|
| `module_name` | `str` | The module that was traced |
| `resolved_path` | `str \| None` | File path the import resolves to (`None` if not found) |
| `module_type` | `ModuleType` | Classification: `STDLIB`, `THIRD_PARTY`, `LOCAL`, `BUILTIN`, `FROZEN`, `NOT_FOUND` |
| `is_package` | `bool` | Whether the module is a package (has `__init__.py`) |
| `is_cached` | `bool` | Whether the module was already in `sys.modules` |
| `submodule_of` | `str \| None` | Parent module name for dotted imports (e.g., `"os"` for `"os.path"`) |
| `search_log` | `list[PathSearchEntry]` | sys.path entries that were checked |
| `shadows` | `list[ShadowWarning]` | Detected import shadows |

### Methods

#### `to_dict() -> dict`

Returns a JSON-serializable dictionary of the full trace.

---

## `PathSearchEntry`

Frozen dataclass for one entry in the sys.path search log.

| Field | Type | Description |
|-------|------|-------------|
| `path` | `str` | The sys.path entry that was checked |
| `result` | `SearchResult` | `FOUND`, `NOT_FOUND`, or `SKIPPED` |
| `candidate` | `str \| None` | File path found (if result is `FOUND`) |

---

## `ShadowWarning`

Frozen dataclass for a detected import shadow.

| Field | Type | Description |
|-------|------|-------------|
| `shadow_path` | `str` | Path of the file causing the shadow |
| `shadowed_module` | `str` | Name of the module being shadowed |
| `description` | `str` | Human-readable description of the shadow |

---

## `scan_path`

```python
from pywho import scan_path
from pathlib import Path

results = scan_path(Path("."), check_installed=True)
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `root` | `Path` | *(required)* | Directory or file to scan |
| `check_installed` | `bool` | `True` | Also check against installed packages (not just stdlib) |
| `exclude_dirs` | `set[str] \| None` | `None` | Additional directory names to skip (merged with defaults) |
| `ignore_names` | `set[str] \| None` | `None` | Additional filenames to ignore (merged with defaults) |

**Returns:** `list[ShadowResult]`

---

## `ShadowResult`

Frozen dataclass for a detected shadow file.

| Field | Type | Description |
|-------|------|-------------|
| `path` | `Path` | Path to the shadowing file |
| `module_name` | `str` | Name of the module being shadowed |
| `shadows` | `str` | What it shadows: `"stdlib"` or `"installed:<pkg>"` |
| `severity` | `Severity` | `HIGH` (stdlib) or `MEDIUM` (installed) |
| `description` | `str` | Human-readable description |

---

## `Severity`

Enum for shadow severity levels.

| Value | Description |
|-------|-------------|
| `Severity.HIGH` | Shadows a stdlib module |
| `Severity.MEDIUM` | Shadows an installed package |
