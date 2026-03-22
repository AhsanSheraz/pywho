# Installation

## Requirements

- Python 3.9 or later
- No additional dependencies (stdlib only)

## With pip

```bash
pip install pywho
```

## With uv

```bash
uv pip install pywho
```

## Run as module

If you prefer not to install, you can run pywho directly:

```bash
python -m pywho
```

!!! warning "Why not `uvx pywho`?"
    `uvx` runs tools inside an ephemeral sandbox environment. This means `pywho` would report that temporary environment instead of your actual project environment. Always install pywho into the environment you want to inspect.

## From source

```bash
git clone https://github.com/AhsanSheraz/pywho.git
cd pywho
pip install .
```

## Development install

```bash
git clone https://github.com/AhsanSheraz/pywho.git
cd pywho
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Verify installation

```bash
pywho --version
```
