.PHONY: help install dev-install lint format sort-imports type-check test clean run-api run-worker build-api build-worker docker-build-api docker-build-worker migrate localstack-up localstack-down localstack-setup localstack-logs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	poetry install --no-dev

dev-install: ## Install development dependencies
	poetry install

lint: ## Run linters
	poetry run ruff check .
	poetry run mypy .

format: ## Format code
	poetry run ruff format .
	poetry run ruff check --select I --fix .

test: ## Run tests
	poetry run pytest

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

run-api: ## Run API server locally
	poetry run uvicorn entry.api.main:app --reload --host 0.0.0.0 --port 8000

run-worker: ## Run worker locally
	poetry run python -m entry.worker.main

build: ## Build shared Docker image for API and worker
	docker build -f resources/docker/app.Dockerfile -t app:latest .

build-api: build ## Alias for build (API and worker share the same image)
build-worker: build ## Alias for build (API and worker share the same image)

build-migrations: ## Build migrations Docker image
	docker build -f resources/docker/migrate.Dockerfile -t app-migrations:latest .

docker-build-api: build-api ## Alias for build-api
docker-build-worker: build-worker ## Alias for build-worker
docker-build-migrations: build-migrations ## Alias for build-migrations

migrate: ## Run database migrations (up)
	bash resources/scripts/migrate.sh up

migrate-down: ## Rollback last migration
	bash resources/scripts/migrate.sh down

migrate-create: ## Create a new migration (usage: make migrate-create NAME=my_migration)
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required. Usage: make migrate-create NAME=my_migration"; \
		exit 1; \
	fi
	bash resources/scripts/migrate.sh create $(NAME)

migrate-version: ## Show current migration version
	bash resources/scripts/migrate.sh version

migrate-docker: build-migrations ## Run migrations using Docker (builds image first)
	docker-compose run --rm migrate

migrate-docker-up: build-migrations ## Run migrations up using Docker
	docker-compose run --rm migrate -path /migrations -database "postgres://postgres:postgres@postgres:5432/app?sslmode=disable" up

migrate-docker-down: build-migrations ## Rollback migrations using Docker
	docker-compose run --rm migrate -path /migrations -database "postgres://postgres:postgres@postgres:5432/app?sslmode=disable" down

migrate-docker-version: build-migrations ## Show migration version using Docker
	docker-compose run --rm migrate -path /migrations -database "postgres://postgres:postgres@postgres:5432/app?sslmode=disable" version

migrate-force: ## Force set migration version (usage: make migrate-force VERSION=1)
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make migrate-force VERSION=1"; \
		exit 1; \
	fi
	bash resources/scripts/migrate.sh force $(VERSION)

localstack-up: ## Start LocalStack services
	docker-compose up -d localstack

localstack-down: ## Stop LocalStack services
	docker-compose stop localstack

localstack-setup: ## Setup LocalStack resources (SNS topics and SQS queues)
	bash resources/scripts/setup_localstack.sh

localstack-logs: ## View LocalStack logs
	docker-compose logs -f localstack

