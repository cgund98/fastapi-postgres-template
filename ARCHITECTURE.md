# Architecture Documentation

This document provides detailed information about the application architecture, design patterns, and conventions used in this codebase.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Layer Responsibilities](#layer-responsibilities)
- [Design Patterns](#design-patterns)
- [Data Flow](#data-flow)
- [Conventions](#conventions)
- [Adding New Domains](#adding-new-domains)

## Architecture Overview

This application follows a **3-Tier Architecture** with **Domain-Driven Design** principles:

```
┌─────────────────────────────────────────────────────────┐
│              Presentation Layer                          │
│  (FastAPI Routes, Schemas, Dependency Injection)       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                 Domain Layer                            │
│  (Services, Models, Repositories, Events, Validators)  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            Infrastructure Layer                         │
│  (Database, Messaging, External Services)              │
└─────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Presentation Layer (`app/presentation/`)

**Purpose**: Handle HTTP requests/responses and API concerns.

**Components**:
- **Routes** (`routes.py`): FastAPI route handlers
- **Schemas** (`schema.py`): Pydantic models for request/response validation
- **Dependencies** (`deps.py`): FastAPI dependency injection for services

**Responsibilities**:
- Validate HTTP requests
- Transform HTTP requests to domain operations
- Transform domain models to HTTP responses
- Handle HTTP errors and status codes
- Pagination and filtering

**Example**:
```python
# app/presentation/user/routes.py
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user."""
    user = await service.create_user(
        email=request.email,
        name=request.name,
        age=request.age,
    )
    return UserResponse.from_domain(user)
```

### Domain Layer (`app/domain/`)

**Purpose**: Contain business logic and domain rules.

**Components**:
- **Models** (`model.py`): Domain entities with business logic (pure Pydantic models)
- **Services** (`service.py`): Orchestrate business operations
- **Repositories** (`repo/`): Data access interfaces and implementations
  - **Base** (`repo/base.py`): Repository interface
  - **SQL** (`repo/sql.py`): SQLModel ORM implementation with ORM models
- **Commands** (`commands.py`): Command objects for operations (CreateUser, UserUpdate)
- **Events** (`events/`): Domain events for event-driven communication
- **Consumers** (`consumers/`): Event handlers
- **Validators** (`validators.py`): Business rule validation

**Responsibilities**:
- Enforce business rules
- Coordinate domain operations
- Manage transactions
- Publish domain events
- Validate domain invariants

**Example**:
```python
# app/domain/user/service.py
class UserService[TContext]:
    async def create_user(self, email: str, name: str, age: int | None = None) -> User:
        """Create a new user."""
        async with self._tx_manager.transaction() as context:
            # Validate business rules
            await validate_create_user_request(email, name, self._repo, context)
            
            # Create domain entity
            user = await self._repo.create(context, create_user)
            
            # Publish domain event
            event = UserCreatedEvent(...)
            await self._event_publisher.publish(event)
            
            return user
```

### Infrastructure Layer (`app/infrastructure/`)

**Purpose**: Provide technical capabilities and external integrations.

**Components**:
- **Database** (`db/`): Transaction management, connection pooling
- **Messaging** (`messaging/`): Event publishing (SNS) and consumption (SQS)
- **AWS** (`aws/`): AWS service clients
- **SQL** (`sql/`): SQLAlchemy connection and transaction management

**Responsibilities**:
- Manage database connections
- Handle transactions
- Publish/consume events
- Integrate with external services
- Provide technical utilities

## Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract data access and enable easy testing.

**Structure**:
- **Base Interface** (`repo/base.py`): Defines repository contract (generic on context type)
- **SQL Implementation** (`repo/sql.py`): Implements repository using SQLModel ORM
  - Contains ORM models (e.g., `UserORM`) defined at the top of the file
  - Uses `SQLContext` for database session access

**Example**:
```python
# app/domain/user/repo/base.py
class UserRepository[TContext](ABC, Generic[TContext]):
    @abstractmethod
    async def get_by_id(self, context: TContext, user_id: UUID) -> User | None: ...
    
    @abstractmethod
    async def create(self, context: TContext, create_user: CreateUser) -> User: ...

# app/domain/user/repo/sql.py
class UserORM(SQLModel, table=True):
    """User ORM model for database persistence."""
    __tablename__ = "users"
    id: UUID = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    # ... other fields

class UserRepository(BaseUserRepository[SQLContext]):
    async def get_by_id(self, context: SQLContext, user_id: UUID) -> User | None:
        orm_user = await context.session.get(UserORM, user_id)
        return self._orm_to_domain(orm_user) if orm_user else None
```

### 2. Unit of Work Pattern

**Purpose**: Manage transactions at the application level.

**Implementation**: `TransactionManager` wraps database operations in transactions and yields a context object.

**Usage**:
```python
async with transaction_manager.transaction() as context:
    # Context provides access to database session
    # All operations here are in a single transaction
    user = await repo.create(context, user)
    invoice = await invoice_repo.create(context, invoice)
    # If any operation fails, entire transaction rolls back
    # Context is automatically committed on success, rolled back on error
```

### 3. Domain Events Pattern

**Purpose**: Enable decoupled communication between domains.

**Flow**:
1. Domain operation completes
2. Service publishes domain event
3. Event is sent to SNS topic
4. Worker consumes from SQS queue
5. Event handler processes event

**Example**:
```python
# In service
event = UserCreatedEvent(aggregate_id=str(user.id), email=user.email)
await self._event_publisher.publish(event)

# In consumer
@event_handler(UserCreatedEvent)
async def handle_user_created(event: UserCreatedEvent) -> None:
    # Process event asynchronously
    pass
```

### 4. Dependency Injection

**Purpose**: Enable loose coupling and testability.

**Implementation**: FastAPI's dependency injection system.

**Example**:
```python
# app/presentation/user/deps.py
async def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    tx_manager: Annotated[SQLTransactionManager, Depends(get_transaction_manager)],
    event_publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    invoice_service: Annotated[InvoiceService, Depends(get_invoice_service)],
) -> AsyncGenerator[UserService, None]:
    """Create and return UserService with dependencies."""
    yield UserService(repository, tx_manager, event_publisher, invoice_service)
```

### 5. SQLModel ORM Pattern

**Purpose**: Use SQLModel for type-safe ORM operations with minimal boilerplate.

**Structure**:
- **ORM Models**: Defined in `repo/sql.py` files alongside repository implementations
- **Domain Models**: Pure Pydantic models in `model.py` (separated from ORM concerns)
- **Mapping**: Repositories convert between ORM and domain models

**Example**:
```python
# app/domain/user/repo/sql.py
class UserORM(SQLModel, table=True):
    """User ORM model for database persistence."""
    __tablename__ = "users"
    id: UUID = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    # ... other fields

class UserRepository(BaseUserRepository[SQLContext]):
    @staticmethod
    def _orm_to_domain(orm_user: UserORM) -> User:
        """Convert ORM model to domain model."""
        return User(
            id=orm_user.id,
            email=orm_user.email,
            name=orm_user.name,
            # ... map other fields
        )
    
    async def get_by_id(self, context: SQLContext, user_id: UUID) -> User | None:
        orm_user = await context.session.get(UserORM, user_id)
        return self._orm_to_domain(orm_user) if orm_user else None
```

## Data Flow

### Request Flow

```
HTTP Request
    ↓
FastAPI Route Handler
    ↓
Dependency Injection (creates Service)
    ↓
Domain Service
    ↓
Transaction Manager (starts transaction)
    ↓
Repository (executes query)
    ↓
Database
    ↓
Repository (maps result to domain model)
    ↓
Service (publishes domain event)
    ↓
Event Publisher (sends to SNS)
    ↓
Service (returns domain model)
    ↓
Route Handler (maps to response schema)
    ↓
HTTP Response
```

### Event Flow

```
Domain Operation Completes
    ↓
Service Publishes Event
    ↓
Event Publisher → SNS Topic
    ↓
SQS Queue (subscribed to topic)
    ↓
Worker Consumes Event
    ↓
Event Handler Processes Event
    ↓
Domain Operation (if needed)
```

## Conventions

### Naming Conventions

- **Models**: PascalCase (e.g., `User`, `Invoice`)
- **Services**: `{Domain}Service` (e.g., `UserService`)
- **Repositories**: `{Domain}Repository` (e.g., `UserRepository`)
- **Events**: `{Domain}{Action}Event` (e.g., `UserCreatedEvent`)
- **Routes**: kebab-case URLs (e.g., `/users`, `/invoices/{id}/request-payment`)
- **Files**: snake_case (e.g., `user_service.py`, `invoice_repo.py`)

### Code Organization

Each domain follows this structure:
```
app/domain/{domain}/
├── model.py              # Domain models (pure Pydantic)
├── commands.py           # Command objects (CreateUser, UserUpdate)
├── service.py            # Domain service (generic on context type)
├── validators.py         # Business rule validators
├── diff.py               # Change tracking utilities
├── repo/
│   ├── base.py          # Repository interface (generic on context type)
│   └── sql.py           # SQLModel ORM implementation + ORM models
├── events/
│   └── {domain}_events.py  # Event definitions
└── consumers/
    └── {domain}_events.py  # Event handlers
```

### Transaction Management

- **Always** wrap database operations in transactions
- Use `async with transaction_manager.transaction():`
- Transactions are application-level, not database-level
- If an exception occurs, the transaction automatically rolls back

### Error Handling

- Use specific exception types from `app.domain.exceptions`
- Raise exceptions in domain layer
- Catch and transform in presentation layer
- Use appropriate HTTP status codes

### Type Safety

- All code must pass mypy strict type checking
- Use type hints for all function parameters and return values
- Use `UUID` for IDs, not strings
- Use optional fields (`str | None = None`) for PATCH operations (no UNSET sentinels)
- Services and repositories are generic on context type for type-safe transaction management

## Adding New Domains

When adding a new domain (e.g., `product`), follow these steps:

1. **Create domain structure**:
   ```bash
   app/domain/product/
   ├── model.py
   ├── commands.py
   ├── service.py
   ├── validators.py
   ├── diff.py
   ├── repo/
   │   ├── base.py
   │   └── sql.py  # Contains ORM model + repository implementation
   ├── events/
   └── consumers/
   ```

2. **Create database migration**:
   ```bash
   make migrate-create NAME=create_products_table
   ```

3. **Create presentation layer**:
   ```bash
   app/presentation/product/
   ├── routes.py
   ├── schema.py
   └── deps.py
   ```

4. **Register routes** in `entry/api/main.py`

5. **Write tests** in `tests/unit/domain/product/`

6. **Update documentation**

## Key Principles

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Dependency Inversion**: Domain layer doesn't depend on infrastructure
3. **Testability**: All dependencies are injected and mockable
4. **Type Safety**: Comprehensive type hints throughout with generic context types
5. **Event-Driven**: Use events for cross-domain communication
6. **Transaction Safety**: All database operations are transactional with context objects
7. **SQLModel ORM**: Use SQLModel for type-safe ORM operations with domain/ORM separation
8. **Lifecycle Management**: Application-scoped dependencies managed via AppContainer

## Related Documentation

- [README.md](README.md) - Project overview and quick start
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide and workflows
- [.cursorrules](.cursorrules) - Cursor-specific rules and conventions
