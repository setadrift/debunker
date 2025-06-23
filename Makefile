.PHONY: migrate

migrate:
	PYTHONPATH=. alembic upgrade head

.PHONY: migrate-reset

migrate-reset:
	PYTHONPATH=. alembic stamp head 