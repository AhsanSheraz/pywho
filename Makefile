.PHONY: help install dev test lint format fix-code typecheck build publish clean docs

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	uv pip install .

dev: ## Install with dev dependencies
	uv pip install -e ".[dev]"

test: ## Run tests
	pytest -v

lint: ## Run linter
	ruff check src/ tests/
	ruff format --check src/ tests/

format: ## Format code
	ruff check --fix src/ tests/
	ruff format src/ tests/

fix-code: ## Fix unused imports, sort imports, and reformat code
	@echo "Removing unused imports..."
	ruff check src/ tests/ --select F401 --fix
	@echo "Sorting imports..."
	ruff check src/ tests/ --select I --fix
	@echo "Running code formatter..."
	ruff format src/ tests/
	@echo "Done! Code is clean."

typecheck: ## Run type checker
	mypy src/pywho

build: clean ## Build distribution packages
	uv build

publish: build ## Publish to PyPI
	uv publish

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docs: ## Build documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

all: format lint typecheck test ## Run all checks
