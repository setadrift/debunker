.PHONY: help build run stop clean test migrate seed dev-frontend dev-backend setup-bias health-check load-academic analyze-batch bias-stats dev-full install-deps format lint

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker containers
	docker-compose build

run: ## Start all services
	docker-compose up -d

stop: ## Stop all services
	docker-compose down

clean: ## Stop services and remove volumes
	docker-compose down -v

test: ## Run tests
	docker-compose exec api pytest

migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

seed: ## Seed database with sample data
	docker-compose exec api python -m app.ingest

dev-frontend: ## Start frontend in development mode
	cd frontend && npm run dev

dev-backend: ## Start backend in development mode
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Enhanced Bias Analysis System
setup-bias: ## Setup enhanced bias analysis system
	python scripts/setup_bias_system.py

health-check: ## Check bias analysis system health
	python scripts/setup_bias_system.py --health

load-academic: ## Load academic sources from CSV
	python -m app.etl.academic_loader data/academic_sources_sample.csv

analyze-batch: ## Trigger batch bias analysis
	curl -X POST "http://localhost:8000/api/bias/analyze/batch?limit=20"

bias-stats: ## View bias analysis statistics
	curl -s "http://localhost:8000/api/bias/bias-stats" | python -m json.tool

# Development helpers
dev-full: ## Start full development environment
	make build
	make run
	make migrate
	make load-academic
	make setup-bias

install-deps: ## Install Python dependencies
	pip install -r requirements.txt

format: ## Format code with black and isort
	black app/ tests/
	isort app/ tests/

lint: ## Run linting checks
	flake8 app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

# Development with local Postgres container
.PHONY: dev-db-up dev-db-down dev-migrate dev-setup

dev-db-up:
	docker compose -f docker-compose.dev.yml up -d

dev-db-down:
	docker compose -f docker-compose.dev.yml down

dev-migrate:
	@echo "Using local development database..."
	@if [ -f .env.dev ]; then \
		export $$(cat .env.dev | grep -v '^#' | xargs) && PYTHONPATH=. alembic upgrade head; \
	else \
		echo "Please create .env.dev file with local database URL"; \
		exit 1; \
	fi

dev-setup: dev-db-up
	@echo "Waiting for database to be ready..."
	@sleep 3
	@$(MAKE) dev-migrate
	@echo "Development environment ready!" 