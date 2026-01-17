# FastAPI PostgreSQL Template - Cursor Rules

## Architecture Overview

This project follows a **3-tier architecture** with Domain-Driven Design principles:

- **Presentation Layer** (`app/presentation/`): FastAPI routes, Pydantic schemas, dependency injection
- **Domain Layer** (`app/domain/`): Business logic, domain models, services, repositories, events
- **Infrastructure Layer** (`app/infrastructure/`): Database, messaging, external services

## Key Patterns

### 1. Domain Services
- Services contain business logic and orchestrate repositories
- All database operations happen within transaction contexts (`async with transaction_manager.transaction()`)
- Services publish domain events after state changes
- Services can call other domain services for cross-domain operations

### 2. Repository Pattern
- Repositories abstract data access (`app/domain/{domain}/repo/`)
- Use SQLModel ORM for database operations
- ORM models are defined in `repo/sql.py` files alongside repository implementations
- Repositories are generic on context type (`TContext`) for type-safe transaction management
- Repositories convert between ORM models and domain models
- Repositories are stateless - context is passed per method call

### 3. Transaction Management
- Use `TransactionManager` from `app.infrastructure.db.transaction` (generic on context type)
- Wrap all database operations in `async with transaction_manager.transaction() as context:`
- The transaction manager yields a context object (e.g., `SQLContext`) that provides database session access
- Pass the context to all repository method calls
- Transactions are application-level, not database-level
- Context is automatically committed on success, rolled back on error

### 4. Domain Events
- Events inherit from `BaseEvent` in `app.infrastructure.messaging.base`
- Events are published via `EventPublisher` after domain operations
- Events are consumed by workers from SQS queues
- Event handlers are in `app/domain/{domain}/consumers/`

### 5. Dependency Injection
- FastAPI dependencies in `app/presentation/{domain}/deps.py` and `app/presentation/deps.py`
- Use `Annotated[Type, Depends(...)]` for dependency injection (modern FastAPI pattern)
- Application-scoped dependencies (database pool, transaction manager) stored in `AppContainer` on app state
- Services are created via factory functions
- All dependencies are injected via constructors
- Repositories are stateless and created per request

## Code Conventions

### Type Hints
- Use comprehensive type hints throughout (mypy strict mode)
- Use `UUID` from `uuid` module for IDs
- Use optional fields (`str | None = None`) for PATCH operations - no UNSET sentinels
- Domain models use Pydantic BaseModel (pure domain models, separate from ORM)
- Services and repositories are generic on context type: `Service[TContext]`, `Repository[TContext]`

### Error Handling
- Domain exceptions in `app.domain.exceptions`
- Infrastructure exceptions in `app.infrastructure.db.exceptions`
- Presentation exceptions in `app.presentation.exceptions`
- Use specific exception types (e.g., `NotFoundError`, `ValidationError`)

### Testing
- Unit tests in `tests/unit/domain/`
- Mock all external dependencies (repositories, transaction managers, event publishers)
- Tests should be fast and isolated (no database required)

### File Organization
- Each domain has its own directory: `app/domain/{domain}/`
- Domain structure: `model.py`, `commands.py`, `service.py`, `repo/`, `events/`, `consumers/`, `validators.py`, `diff.py`
  - `repo/sql.py` contains both ORM models and repository implementation
- Presentation structure: `routes.py`, `schema.py`, `deps.py`
- Infrastructure: `app/infrastructure/sql/` for SQL-specific infrastructure
- Application container: `app/presentation/container.py` for lifecycle management

## Technology Stack

- **Python 3.12+** with async/await
- **FastAPI** for API framework
- **SQLModel** (SQLAlchemy ORM) for type-safe database operations
- **Poetry** for dependency management
- **PostgreSQL** for database
- **SNS/SQS** for event-driven messaging
- **structlog** for structured logging

## Important Notes

- **SQLModel ORM**: We use SQLModel for type-safe ORM operations with domain/ORM separation
- **Async Everything**: All I/O operations are async
- **Type Safety**: All code must pass mypy strict type checking with generic context types
- **Transaction Boundaries**: All database operations must be within transaction contexts with context objects
- **Event-Driven**: Use domain events for cross-domain communication, not direct service calls
- **Repository Abstraction**: Never access database directly from services, always use repositories
- **Context Pattern**: Repositories and services are generic on context type for type-safe session passing
- **Lifecycle Management**: Application-scoped dependencies managed via AppContainer on app state
- **Health Checks**: `/health` endpoint tests database connectivity

## When Adding New Features

1. Create domain model in `app/domain/{domain}/model.py` (pure Pydantic)
2. Create command objects in `app/domain/{domain}/commands.py` (CreateUser, UserUpdate)
3. Create repository interface in `app/domain/{domain}/repo/base.py` (generic on TContext)
4. Implement repository in `app/domain/{domain}/repo/sql.py`:
   - Define ORM model at top of file (e.g., `UserORM`)
   - Implement repository with `_orm_to_domain` mapping method
5. Create service in `app/domain/{domain}/service.py` (generic on TContext)
6. Create validators in `app/domain/{domain}/validators.py`
7. Create diff utilities in `app/domain/{domain}/diff.py` (for change tracking)
8. Create events in `app/domain/{domain}/events/`
9. Create consumers in `app/domain/{domain}/consumers/`
10. Create API routes in `app/presentation/{domain}/routes.py`
11. Create schemas in `app/presentation/{domain}/schema.py`
12. Create dependencies in `app/presentation/{domain}/deps.py` (use Annotated[Type, Depends(...)])
13. Write tests in `tests/unit/domain/{domain}/`
