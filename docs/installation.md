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
uv add --dev pywho
```

For one-off usage without changing project dependencies:

```bash
uv run --with pywho pywho
```

## Run as module

If you prefer not to install, you can run pywho directly:

```bash
python -m pywho
```

!!! warning "Why not `uvx pywho`?"
    `uvx` runs tools inside an ephemeral sandbox environment. This means `pywho` would report that temporary environment instead of your actual project environment. Use `uv add --dev pywho` for regular project use, or `uv run --with pywho pywho` for one-off checks.

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
