# Architecture

## Layers

The app has three layers. Each layer only depends on the one below it.

```
Presentation  (app/presentation/)   -- HTTP routes, schemas, FastAPI deps
     |
  Domain      (app/domain/)         -- Services, models, repos, validators, events
     |
  Adapters    (app/adapters/)       -- Database, messaging, AWS clients
```

### Presentation

Handles HTTP concerns: request validation, response formatting, dependency wiring.

Lives in `app/presentation/fastapi/`. Each domain has its own folder with `routes.py`, `schema.py`, and optionally `deps.py`.

- **Routes** receive a validated Pydantic request, call a domain service, and return a Pydantic response. No business logic lives here.
- **Schemas** define the shape of HTTP requests and responses. They map to and from domain models but are not the same thing (e.g. a response might omit internal fields).
- **Deps** are FastAPI `Depends()` factories that wire together services, repos, and transaction managers for each request.

### Domain

Contains all business logic. No knowledge of HTTP or specific databases.

Each domain (e.g. `user`, `billing/invoice`) has:

```
app/domain/{name}/
  model.py          # Domain model (frozen Pydantic BaseModel)
  commands.py       # Input objects for create/update operations
  service.py        # Business logic, transaction management, event publishing
  repo.py           # Abstract repository interface (ABC)
  validators.py     # Business rule checks (uniqueness, existence, etc.)
  handlers.py       # Event handlers for incoming events
```

- **Services** are the entry point for all business operations. They open a transaction, validate inputs, call repos, publish events, and return domain models. They are generic on a context type (`TContext`) so they work with any database backend.
- **Models** are frozen Pydantic objects that represent domain entities. They carry no database or framework concerns.
- **Repos** define abstract interfaces (ABCs) for data access. The domain layer never knows how data is stored — it just calls methods like `get_by_id` and `create`.
- **Validators** enforce business rules (e.g. "email must be unique") by querying repos within a transaction context. They raise domain exceptions on failure.
- **Commands** are simple dataclasses that group the inputs for a create or update operation.
- **Handlers** process incoming events from other domains or external systems.

### Adapters

Concrete implementations of abstract interfaces defined in the domain layer. This is where framework and infrastructure details live.

- `app/adapters/sql/` -- asyncpg connection pool, transaction manager, context object
- `app/adapters/events/` -- SNS publisher, SQS consumer
- `app/adapters/aws/` -- Boto3 client factory
- `app/adapters/user/repo.py` -- SQL implementation of `UserRepository`
- `app/adapters/billing/invoice/repo.py` -- SQL implementation of `InvoiceRepository`

Adapter repos use raw asyncpg SQL with parameterized queries. There is no ORM — rows are fetched as `asyncpg.Record` and mapped to domain models in a `_row_to_domain` helper.

## Key patterns

### Repository

Domain defines an abstract repo (`app/domain/user/repo.py`). The adapter provides a concrete implementation using raw asyncpg SQL (`app/adapters/user/repo.py`). Tests mock the abstract interface.

### Transaction management

Services wrap operations in `async with self._tx_manager.transaction() as context:`. The context object holds the asyncpg connection. If the block raises, the transaction rolls back. The context is passed to every repository method.

### Events

Events use a CloudEvents-compatible envelope format:

1. Service creates a `Payload` subclass (e.g. `UserCreatedEvent`) and publishes it via `EventPublisher`
2. `SNSPublisher` wraps it in an `Envelope` and sends to SNS with an `event_type` message attribute
3. SNS delivers to SQS (filtered by event type)
4. `SQSConsumer` reads from SQS, parses the `Envelope`, passes it to `EventRouter`
5. `EventRouter` deserializes the payload and calls the registered `EventHandler`

Event payloads live in `app/domain/events/registry/` organized by domain and version (e.g. `user/v1/events.py`).

### Dependency injection

FastAPI's `Depends()` wires everything together. `app/presentation/fastapi/deps.py` creates repositories, transaction managers, and services. The `AppContainer` (created in the lifespan) holds long-lived objects like the database pool.

## Conventions

- **Models**: `User`, `Invoice` (PascalCase)
- **Services**: `UserService`, `InvoiceService`
- **Repos**: `UserRepository`, `InvoiceRepository`
- **Events**: `UserCreatedEvent`, `InvoicePaidEvent`
- **URLs**: kebab-case (`/invoices/{id}/request-payment`)
- **Files**: snake_case (`user_service.py`)
- **IDs**: Always `UUID`, never strings
- **PATCH fields**: `str | None = None` (None means "not provided")

## Adding a new domain

1. Create the domain module:
   ```
   app/domain/product/
     model.py, commands.py, service.py, repo.py, validators.py
   ```

2. Create the adapter repo:
   ```
   app/adapters/product/repo.py
   ```

3. Create a database migration:
   ```bash
   make migrate-create NAME=create_products_table
   ```

4. Create the presentation layer:
   ```
   app/presentation/fastapi/product/
     routes.py, schema.py, deps.py
   ```

5. Register routes in `entry/api/main.py`

6. (Optional) Add event payloads in `app/domain/events/registry/product/v1/` and handlers in `app/domain/product/handlers.py`. Register them in the worker's `EventRouter`.

7. Write tests in `tests/unit/domain/product/`
