.PHONY: install dev test lint format run docker-build docker-run clean help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev: ## Install development dependencies
	pip install -e ".[dev]"

test: ## Run test suite with coverage
	pytest tests/ -v --tb=short --cov=src/netai_chatbot --cov-report=term-missing

test-quick: ## Run tests without coverage
	pytest tests/ -v --tb=short --no-header

lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Run type checker
	mypy src/

run: ## Run the application locally
	uvicorn netai_chatbot.main:app --host 0.0.0.0 --port 8000 --reload

docker-build: ## Build Docker image
	docker build -t netai-chatbot:latest .

docker-run: ## Run with Docker Compose
	docker compose up --build

docker-down: ## Stop Docker Compose
	docker compose down

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
