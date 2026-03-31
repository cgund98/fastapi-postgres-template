# Architecture Rules

## Layers

- **Presentation** (`app/presentation/fastapi/`): FastAPI routes, Pydantic schemas, dependency injection
- **Domain** (`app/domain/`): Business logic, models, services, abstract repos, validators, event payloads, handlers
- **Adapters** (`app/adapters/`): Concrete implementations -- asyncpg repos, SNS publisher, SQS consumer, AWS clients

## Domain structure

Each domain follows this layout:

```
app/domain/{name}/
  model.py        # Frozen Pydantic domain model
  commands.py     # Dataclasses for create/update inputs
  service.py      # Business logic (generic on TContext)
  repo.py         # Abstract repository (ABC, generic on TContext)
  validators.py   # Business rule checks
  handlers.py     # Event handlers for incoming events
```

Adapter repos live separately:

```
app/adapters/{name}/repo.py   # SQL implementation using raw asyncpg
```

## Patterns

### Repositories
- Domain defines abstract interface (`app/domain/{name}/repo.py`)
- Adapter provides concrete implementation with raw asyncpg SQL (`app/adapters/{name}/repo.py`)
- Repos are stateless -- context is passed per method call
- Use `$1`, `$2` positional params. For optional filters, prefer `COALESCE` or branching over dynamic query building.

### Transactions
- Services wrap operations: `async with self._tx_manager.transaction() as context:`
- Context holds the asyncpg connection
- Pass context to every repository method
- Auto-commits on success, rolls back on exception

### Events
- Payloads are `Payload` subclasses in `app/domain/events/registry/{domain}/v1/`
- Services publish via `EventPublisher` using `PublishArgs(payload=..., source=...)`
- SNS publisher wraps in CloudEvents `Envelope` with `event_type` message attribute
- SQS consumer parses `Envelope`, `EventRouter` dispatches to registered `EventHandler`
- Handlers receive `(event: TPayload, envelope: Envelope)`

### Dependency injection
- `app/presentation/fastapi/deps.py` creates repos, services, transaction managers
- `AppContainer` on app state holds long-lived objects (db pool, transaction manager)
- Use `Annotated[Type, Depends(...)]`

## Conventions

- Type hints everywhere (mypy strict)
- IDs are `UUID`, never strings
- Optional PATCH fields: `str | None = None`
- Domain models are frozen Pydantic `BaseModel`
- Services and repos are generic on `TContext`
- Domain exceptions in `app.domain.exceptions`
- DB exceptions in `app.adapters.db.exceptions`

## Tech stack

- Python 3.12, FastAPI, asyncpg (no ORM), PostgreSQL
- Poetry, SNS/SQS, structlog, ruff, mypy, pytest

## Adding features

1. Domain model in `app/domain/{name}/model.py`
2. Commands in `app/domain/{name}/commands.py`
3. Abstract repo in `app/domain/{name}/repo.py`
4. Concrete repo in `app/adapters/{name}/repo.py` (raw asyncpg SQL)
5. Service in `app/domain/{name}/service.py`
6. Validators in `app/domain/{name}/validators.py`
7. Event payloads in `app/domain/events/registry/{name}/v1/`
8. Handlers in `app/domain/{name}/handlers.py`
9. Routes in `app/presentation/fastapi/{name}/routes.py`
10. Schemas in `app/presentation/fastapi/{name}/schema.py`
11. Deps in `app/presentation/fastapi/{name}/deps.py`
12. Tests in `tests/unit/domain/{name}/`
