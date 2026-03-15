# Contributing to pywho

Thanks for your interest in contributing! Here's how to get started.

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/pywho.git
cd pywho
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
pre-commit install
```

## Running checks

```bash
pytest -v          # Run tests
mypy src/pywho     # Type check
ruff check src/ tests/   # Lint
ruff format src/ tests/  # Format
```

Or use the Makefile shortcuts:

```bash
make test       # Tests
make typecheck  # mypy
make lint       # ruff check
make format     # ruff format
make all        # Everything
```

## Making changes

1. Fork the repo and create a feature branch from `main`
2. Make your changes
3. Add or update tests as needed
4. Ensure all checks pass
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `test:`, `chore:`
6. Open a pull request against `main`

## Pull request guidelines

- Keep PRs focused — one feature or fix per PR
- Add tests for new functionality
- Update documentation if you're changing user-facing behavior
- Update `CHANGELOG.md` for user-facing changes

## Adding support for a new venv type

1. Add detection logic in `src/pywho/inspector.py` in the `_detect_venv()` function
2. Add the type string to the `VenvInfo.type` field documentation
3. Add a test in `tests/test_inspector.py`
4. Update the README table

## Reporting bugs

Use the [bug report template](https://github.com/AhsanSheraz/pywho/issues/new?template=bug_report.md) and include the output of `pywho --json`.

## Suggesting features

Open an issue using the [feature request template](https://github.com/AhsanSheraz/pywho/issues/new?template=feature_request.md).

## Code of conduct

Be respectful, constructive, and welcoming. We're all here to make Python debugging easier.
