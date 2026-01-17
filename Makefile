.PHONY: help poetry-install poetry-lock poetry-add poetry-dev-add lint fix test clean run-api run-worker build-api build-worker build-migrations migrate migrate-up migrate-down migrate-version migrate-force migrate-create localstack-up localstack-down localstack-setup localstack-logs workspace-up workspace-down workspace-build workspace-shell local-venv

# Docker Compose service name
SERVICE := workspace

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Workspace container management
workspace-up: ## Start the workspace container
	docker compose up -d $(SERVICE)

workspace-build: ## Build the workspace container
	docker compose build $(SERVICE)

workspace-down: ## Stop and remove the workspace container
	docker compose down $(SERVICE)

workspace-shell: ## Open a shell in the workspace container
	docker compose exec $(SERVICE) /bin/bash

# Development commands (run in workspace container)
poetry-install: ## Install dependencies
	docker compose exec $(SERVICE) poetry install --all-groups

poetry-lock: ## Update poetry.lock file
	docker compose exec $(SERVICE) poetry lock

poetry-add: ## Add a package (usage: make poetry-add PKG=package-name)
	@if [ -z "$(PKG)" ]; then \
		echo "Error: PKG is required. Usage: make poetry-add PKG=package-name"; \
		exit 1; \
	fi
	docker compose exec $(SERVICE) poetry add $(PKG)

poetry-dev-add: ## Add a dev package (usage: make poetry-dev-add PKG=package-name)
	@if [ -z "$(PKG)" ]; then \
		echo "Error: PKG is required. Usage: make poetry-dev-add PKG=package-name"; \
		exit 1; \
	fi
	docker compose exec $(SERVICE) poetry add --group dev $(PKG)

lint: ## Run linters
	docker compose exec $(SERVICE) poetry run ruff check .
	docker compose exec $(SERVICE) poetry run mypy .

fix: ## Format code and fix linting issues
	docker compose exec $(SERVICE) poetry run ruff format .
	docker compose exec $(SERVICE) poetry run ruff check --fix .

test: ## Run unit tests
	docker compose exec $(SERVICE) poetry run pytest tests/unit

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

run-api: ## Run API server
	docker compose exec $(SERVICE) poetry run uvicorn entry.api.main:app --reload --host 0.0.0.0 --port 8000

run-worker: ## Run worker
	docker compose exec $(SERVICE) poetry run python -m entry.worker.main

# Production Docker image builds
build: ## Build shared Docker image for API and worker
	docker build -f resources/docker/app.Dockerfile -t app:latest .

build-api: build ## Alias for build (API and worker share the same image)
build-worker: build ## Alias for build (API and worker share the same image)

build-migrations: ## Build migrations Docker image
	docker build -f resources/docker/migrate.Dockerfile -t app-migrations:latest .

# Database migration commands (using dedicated migrate container)
migrate: build-migrations ## Run database migrations (up)
	docker compose run --rm migrate -path /migrations -database "postgres://postgres:postgres@postgres:5432/app?sslmode=disable" up

migrate-up: migrate ## Alias for migrate

migrate-down: build-migrations ## Rollback last migration
	docker compose run --rm migrate -path /migrations -database "postgres://postgres:postgres@postgres:5432/app?sslmode=disable" down

migrate-version: build-migrations ## Show current migration version
	docker compose run --rm migrate -path /migrations -database "postgres://postgres:postgres@postgres:5432/app?sslmode=disable" version

migrate-force: build-migrations ## Force set migration version (usage: make migrate-force VERSION=1)
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make migrate-force VERSION=1"; \
		exit 1; \
	fi
	docker compose run --rm migrate -path /migrations -database "postgres://postgres:postgres@postgres:5432/app?sslmode=disable" force $(VERSION)

migrate-create: ## Create a new migration (usage: make migrate-create NAME=my_migration)
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required. Usage: make migrate-create NAME=my_migration"; \
		exit 1; \
	fi
	bash resources/scripts/migrate.sh create $(NAME)

# LocalStack commands
localstack-up: ## Start LocalStack services
	@echo "Starting LocalStack..."
	docker compose up -d localstack
	@echo "Waiting for LocalStack to be ready..."
	@timeout=60; \
	while [ $$timeout -gt 0 ]; do \
		if docker compose exec -T localstack curl -f http://localhost:4566/_localstack/health >/dev/null 2>&1; then \
			echo "LocalStack is ready!"; \
			exit 0; \
		fi; \
		sleep 2; \
		timeout=$$((timeout - 2)); \
	done; \
	echo "Warning: LocalStack may not be fully ready yet"

localstack-setup: localstack-up ## Setup LocalStack resources (SNS topics and SQS queues)
	@echo "Setting up LocalStack resources (SNS topics and SQS queues)..."
	@docker compose exec $(SERVICE) bash resources/scripts/setup_localstack.sh

localstack-down: ## Stop LocalStack services
	@echo "Stopping LocalStack..."
	docker compose stop localstack

localstack-logs: ## View LocalStack logs
	docker compose logs -f localstack

# Local IDE support (run on host machine)
local-venv: ## Export requirements and create local .venv.local for IDE support
	@echo "Exporting requirements from workspace container..."
	@docker compose exec $(SERVICE) poetry export -f requirements.txt --output requirements.local.txt --without-hashes
	@echo "Removing existing .venv.local if it exists..."
	@rm -rf .venv.local
	@echo "Creating local virtual environment..."
	@python3 -m venv .venv.local
	@echo "Installing requirements in local .venv.local..."
	@.venv.local/bin/pip install --upgrade pip
	@.venv.local/bin/pip install -r requirements.local.txt
	@echo "Local .venv.local created successfully! Activate with: source .venv.local/bin/activate"
