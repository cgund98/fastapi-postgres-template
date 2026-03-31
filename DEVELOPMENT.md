# Development

## Prerequisites

- Docker and Docker Compose

That's it. The workspace container has Python, Poetry, AWS CLI, and golang-migrate pre-installed.

## Setup

```bash
# Build and start the workspace container
make workspace-build
make workspace-up

# Install Python dependencies
make poetry-install

# Start Postgres and run migrations
docker compose up -d postgres
make migrate

# Set up LocalStack (SNS/SQS)
make localstack-setup
```

## Running

```bash
# API server (http://localhost:8000)
make run-api

# Event consumer worker (separate terminal)
make run-worker
```

## Make commands

### Workspace

| Command | Description |
|---------|-------------|
| `make workspace-build` | Build workspace container |
| `make workspace-up` | Start workspace container |
| `make workspace-down` | Stop workspace container |
| `make workspace-shell` | Open a shell in the container |

### Dependencies

| Command | Description |
|---------|-------------|
| `make poetry-install` | Install all dependencies |
| `make poetry-lock` | Regenerate lock file |
| `make poetry-add PKG=name` | Add a production dependency |
| `make poetry-dev-add PKG=name` | Add a dev dependency |

### Code quality

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff + mypy |
| `make fix` | Auto-format and fix lint issues |
| `make test` | Run unit tests |

### Database

| Command | Description |
|---------|-------------|
| `make migrate` | Run migrations |
| `make migrate-down` | Rollback last migration |
| `make migrate-version` | Show current version |
| `make migrate-create NAME=...` | Create a new migration |
| `make migrate-force VERSION=N` | Force-set version |

### LocalStack

| Command | Description |
|---------|-------------|
| `make localstack-up` | Start LocalStack |
| `make localstack-setup` | Create SNS topic and SQS queue |
| `make localstack-down` | Stop LocalStack |
| `make localstack-logs` | Tail LocalStack logs |

### Builds

| Command | Description |
|---------|-------------|
| `make build` | Build production image (shared by API and worker) |
| `make build-migrations` | Build migrations image |

### IDE support

```bash
make local-venv
```

Creates a `.venv` on the host with all dependencies exported from the container. Point your IDE at it for autocomplete and type checking.

## Testing

Tests use mocked dependencies. No database or network needed.

```bash
make test

# Run a specific test file
docker compose exec workspace poetry run pytest tests/unit/domain/user/test_service.py -v
```

## Workflow

1. `make workspace-up`
2. Make changes
3. `make fix` (format + auto-fix)
4. `make lint` (check)
5. `make test`
6. Commit
