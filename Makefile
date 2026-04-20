.PHONY: help install test lint clean build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install project with dev dependencies
	uv sync

test: ## Run test suite
	uv run pytest -v

test-cov: ## Run tests with coverage
	uv run pytest --cov=shadetriptxt --cov-report=term-missing --cov-fail-under=80

lint: ## Run linter
	uv run ruff check .

lint-fix: ## Run linter with auto-fix
	uv run ruff check . --fix

format: ## Format code
	uv run ruff format .

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .mypy_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build: ## Build package
	uv build

check: lint test ## Run lint + test
