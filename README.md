# FastAPI PostgreSQL Template

A backend template for building APIs and event-driven workers with FastAPI, PostgreSQL, and AWS (SNS/SQS).

It includes two example domains (Users and Invoices) that show how the pieces fit together.

## What's in the box

- **FastAPI** REST API with Pydantic request/response validation
- **PostgreSQL** with raw asyncpg queries (no ORM)
- **SNS/SQS** event publishing and consumption
- **Docker workspace** with all dev tools pre-installed (Python 3.12, Poetry, AWS CLI, golang-migrate)
- **Ruff** for linting/formatting, **mypy** for type checking, **pytest** for tests

## Project structure

```
entry/                          # Entrypoints
  api/main.py                   # FastAPI server
  worker/main.py                # SQS event consumer

app/
  domain/                       # Business logic
    user/                       # User domain (model, service, repo, validators, handlers)
    billing/invoice/            # Invoice domain
    events/                     # Event registry (payloads, envelope, router, publisher)
  adapters/                     # External integrations
    sql/                        # asyncpg pool, transaction manager, context
    events/                     # SNS publisher, SQS consumer
    aws/                        # Boto3 client config
    user/repo.py                # User SQL repository
    billing/invoice/repo.py     # Invoice SQL repository
  presentation/fastapi/         # HTTP layer (routes, schemas, deps)
  config/                       # Settings
  observability/                # Structured logging

tests/unit/                     # Unit tests (mocked dependencies)
resources/
  db/migrations/                # SQL migrations (golang-migrate)
  docker/                       # Dockerfiles
  scripts/                      # Setup scripts (LocalStack, migrations)
```

## Quick start

```bash
git clone <repository-url>
cd fastapi-postgres-template

# Build and start the workspace container
make workspace-build
make workspace-up
make poetry-install

# Set up database and LocalStack
make localstack-setup
make migrate

# Run the API and worker (in separate terminals)
make run-api
make run-worker
```

API docs: http://localhost:8000/docs

## Example endpoints

```bash
# Create a user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "Jane", "age": 30}'

# Create an invoice
curl -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<user_id>", "amount": 100.00}'

# Request payment (triggers async worker processing)
curl -X POST http://localhost:8000/invoices/<invoice_id>/request-payment
```

## Further reading

- [ARCHITECTURE.md](ARCHITECTURE.md) -- how the code is organized and why
- [DEVELOPMENT.md](DEVELOPMENT.md) -- workspace setup, make commands, workflows

## License

MIT
