.PHONY: migrate

migrate:
	PYTHONPATH=. alembic upgrade head

.PHONY: migrate-reset

migrate-reset:
	PYTHONPATH=. alembic stamp head

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