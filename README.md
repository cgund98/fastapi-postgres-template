# 🚀 FastAPI PostgreSQL Template

<div align="center">

**A production-ready FastAPI backend template demonstrating efficient organization and modern design patterns**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Poetry](https://img.shields.io/badge/Poetry-Latest-orange.svg)](https://python-poetry.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Built with ❤️ using Domain-Driven Design and Event-Driven Architecture*

[Features](#-features) • [Quick Start](#-getting-started) • [Architecture](#-architecture) • [Example](#-example-business-case) • [Development Guide](DEVELOPMENT.md)

</div>

## 👥 Who Is This For?

This template is designed for **backend engineers** building:

- RESTful APIs with clean separation between HTTP handlers, business logic, and data access
- Event-driven microservices with async message processing (SQS/SNS)
- Type-safe codebases with comprehensive type hints and fast unit tests
- Production-ready systems with proper transaction management and error handling

## ✨ Features

### 🏗️ Architecture & Design Patterns

- **3-Tier Architecture**: Clear separation between presentation, domain, and infrastructure layers
- **Domain-Driven Design**: Business logic encapsulated in domain services with rich domain models
- **Repository Pattern**: Data access abstraction enabling easy testing and database swapping
- **Unit of Work**: Application-level transaction management for consistent data operations
- **Event-Driven Architecture**: Decoupled communication via domain events and message queues
- **Dependency Injection**: Loose coupling through constructor injection, enabling testability

### 🛠️ Technology Choices

- **FastAPI**: Modern, high-performance web framework with automatic API documentation
- **PostgreSQL**: SQLAlchemy Core query builders (no ORM) for type-safe, composable SQL queries
- **Async/Await**: Fully asynchronous Python for optimal I/O-bound performance
- **Type Safety**: Comprehensive type hints with mypy for compile-time error detection

### 📊 Observability & Operations

- **Structured Logging**: JSON-formatted logs with structlog for easy parsing and analysis
- **Health Checks**: Built-in health check endpoints for monitoring

### 👨‍💻 Developer Experience

- **Modern Tooling**: Ruff for fast linting/formatting, mypy for type checking
- **Comprehensive Testing**: Unit tests with mocked dependencies for fast, reliable test suites
- **Docker Support**: Containerized API and worker services for consistent deployments
- **Infrastructure as Code**: AWS CDK for reproducible cloud infrastructure
- **CI/CD Ready**: GitHub Actions pipeline configuration included

## 🏛️ Architecture

This template follows a **3-tier architecture** with clear separation of concerns:

### Presentation Layer (`app/presentation/`)
- **API Routes**: FastAPI route handlers
- **Schemas**: Pydantic models for request/response validation

### Domain Layer (`app/domain/`)
- **Models**: Domain entities with business logic
- **Services**: Domain-specific business logic with integrated transaction management
- **Repositories**: Data access interfaces using SQLAlchemy Core query builders
- **Persistence**: Query builder functions (`persistence/queries.py`) and table definitions (`persistence/table.py`)
- **Events**: Domain events for event-driven communication
- **Consumers**: Event handlers for processing domain events

### Infrastructure Layer (`app/infrastructure/`)
- **Database**: SQLAlchemy async connection pooling and transaction management
- **Messaging**: Event publishing (SNS) and consumption (SQS)
- **Tasks**: Async task execution helpers

### Observability (`app/observability/`)
- **Logging**: Structured logging with structlog

## 📁 Project Structure

```
fastapi-postgres-template/
├── entry/
│   ├── api/
│   │   └── main.py                 # FastAPI server entrypoint
│   └── worker/
│       └── main.py                 # Async event consumer entrypoint
│
├── app/
│   ├── config/
│   │   └── settings.py             # Environment/config variables
│   │
│   ├── domain/
│   │   ├── user/                   # User domain
│   │   │   ├── model.py
│   │   │   ├── persistence/       # SQLAlchemy Core query builders
│   │   │   │   ├── table.py        # Table definitions
│   │   │   │   └── queries.py      # Query builder functions
│   │   │   ├── events/
│   │   │   ├── repo/               # Repository implementations
│   │   │   ├── service.py
│   │   │   └── consumers/
│   │   │
│   │   └── billing/invoice/        # Invoice domain
│   │
│   ├── presentation/
│   │   ├── billing/                # Billing routes and schemas
│   │   └── user/                   # User routes and schemas
│   │
│   ├── infrastructure/
│   │   ├── db/                     # Transaction manager interface
│   │   ├── postgres/               # SQLAlchemy connection pool
│   │   ├── messaging/              # Event publishing/consumption
│   │   └── tasks/                  # Task execution
│   │
│   └── observability/              # Logging
│
├── tests/
│   └── unit/                       # Unit tests with mocked dependencies
│       └── domain/                 
│
├── resources/
│   ├── db/migrations/              # Database migrations
│   ├── docker/                     # Dockerfiles (shared image for API/worker)
│   ├── scripts/                    # Utility scripts
│   └── infra/cdk/                  # AWS CDK infrastructure
│
├── Makefile
├── pyproject.toml
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (required)
- **AWS CLI** (optional, for infrastructure deployment)

> 💡 **Note**: This project uses a **workspace container** with all development tools pre-installed. See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

### Running the Example

1. **Clone and start services:**
```bash
git clone <repository-url>
cd fastapi-postgres-template
make workspace-build
make workspace-up
make poetry-install
```

2. **Set up database and LocalStack:**
```bash
docker compose up -d postgres localstack
make localstack-setup
make migrate
```

3. **Run the API server:**
```bash
make run-api

# In a seperate terminal, start the consumer
make run-worker
```

4. **Visit the API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

5. **Try the example endpoints:**
   - Create a user: `POST /users` with `{"email": "user@example.com", "name": "John Doe", "age": 30}`
   - Create an invoice: `POST /invoices` with `{"user_id": "<user_id>", "amount": 100.00}`
   - Request payment: `POST /invoices/{invoice_id}/request-payment`

> 📖 For detailed development instructions, Makefile commands, and workflows, see [DEVELOPMENT.md](DEVELOPMENT.md).

### 🔧 Query Builder Pattern

Repositories use **SQLAlchemy Core query builders** defined in `persistence/queries.py`. This provides:

- **Type Safety**: Query builders return typed query objects (`Select`, `Insert`, `Update`, `Delete`)
- **Composability**: Queries can be built programmatically and reused across repositories
- **Performance**: Direct SQL generation without ORM overhead
- **Flexibility**: Full control over SQL while maintaining type safety

**Example query builder:**
```python
# In app/domain/user/persistence/queries.py
def select_user_by_id() -> "Select":
    """Create a SELECT query to get a user by ID."""
    return select(
        users_table.c.id,
        users_table.c.email,
        users_table.c.name,
        users_table.c.age,
        users_table.c.created_at,
        users_table.c.updated_at,
    ).where(users_table.c.id == bindparam("user_id"))
```

**Usage in repository:**
```python
# In app/domain/user/repo/sql.py
async def get_by_id(self, user_id: UUID) -> User | None:
    stmt = select_user_by_id()
    result = await self._conn.execute(stmt, {"user_id": str(user_id)})
    row = result.first()
    return User(**row._mapping) if row else None
```

## 💼 Example Business Case

This template implements a **User Management and Billing System** to demonstrate real-world patterns:

> 💡 **Note**: This example showcases how multiple domains interact through events and service orchestration.

### 👤 User Domain
- **User Registration**: Create users with email uniqueness validation
- **User Updates**: Update user information (e.g., name changes)
- **User Deletion**: Cascade deletion of associated invoices when a user is removed
- **Event Publishing**: Emits `UserCreatedEvent` and `UserUpdatedEvent` for downstream processing

### 💰 Invoice/Billing Domain
- **Invoice Creation**: Create invoices linked to users with amount tracking
- **Payment Processing**: Mark invoices as paid with business rule validation (prevents double-payment)
- **Payment Requests**: Request payment for invoices, triggering async processing
- **Event-Driven Workflow**: 
  - When an invoice is created, a `InvoiceCreatedEvent` is published
  - A `InvoicePaymentRequestedEvent` triggers a worker to automatically process payment
  - The worker publishes `InvoicePaidEvent` upon completion

### 🔑 Key Patterns Demonstrated
- **Cross-Domain Relationships**: UserService orchestrates InvoiceService for cascading operations
- **Event-Driven Processing**: Async workers consume events from SQS queues
- **Transaction Management**: All operations use application-level transactions
- **Business Rule Enforcement**: Prevents invalid states (e.g., paying an already-paid invoice)
- **Domain Events**: Decoupled communication between services via events

This example showcases how to structure a multi-domain system with event-driven workflows, making it easy to extend with additional domains and business logic.

## 🗄️ Database Schema

The template includes example domains (User and Invoice). Database migrations are managed using [golang-migrate](https://github.com/golang-migrate/migrate) and located in `resources/db/migrations/`.

The schema includes:

- **Users table**: Stores user information with email uniqueness
- **Invoices table**: Stores invoices linked to users with status tracking

> 📖 For migration commands and database setup, see [DEVELOPMENT.md](DEVELOPMENT.md#-database-migrations).

## 📨 Event System

The template includes a **generic event system** for decoupled communication:

| Component | Purpose |
|-----------|---------|
| **BaseEvent** | Base class for all domain events with metadata |
| **Event Publishing** | Events published to SNS topics |
| **Event Consumption** | Workers consume events from SQS queues |
| **Event Handlers** | Domain-specific consumers process events |

1. **BaseEvent**: All domain events extend this base class with metadata
2. **Event Publishing**: Events are published to SNS topics
3. **Event Consumption**: Workers consume events from SQS queues
4. **Event Handlers**: Domain-specific consumers process events

**Example: Publishing a domain event**

```python
# In UserService.create_user()
event = UserCreatedEvent(
    aggregate_id=str(user.id),
    email=user.email,
    name=user.name
)
await event_publisher.publish(event)
```

**Example: Consuming events in a worker**

```python
# Worker automatically processes events from SQS
# Event handlers execute domain logic asynchronously
await invoice_payment_requested_handler.handle(event)
```

## 🐳 Docker

The project uses Docker for both development and production:

- **Workspace Container**: Consistent development environment with all tools pre-installed
- **Production Images**: Optimized images for API, worker, and migrations

> 📖 For Docker setup and usage, see [DEVELOPMENT.md](DEVELOPMENT.md#-docker).

## ☁️ Infrastructure

Deploy infrastructure using **AWS CDK**:

```bash
cd resources/infra/cdk
npm install -g aws-cdk
cdk bootstrap
cdk deploy
```

## 🎯 Design Patterns

This template demonstrates the following patterns:

- **3-Tier Architecture**: Clear separation of concerns
- **Repository Pattern**: Data access abstraction
- **Unit of Work**: Transaction management
- **Domain Events**: Event-driven communication
- **Dependency Injection**: Loose coupling
- **Factory Pattern**: Service creation

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. ✅ Follow the existing code structure and patterns
2. ✅ Maintain type hints throughout (mypy must pass)
3. ✅ Write tests for new features with mocked dependencies
4. ✅ Run linting and type checking before committing (`make lint`)
5. ✅ Use the workspace container for all development tasks
6. ✅ Follow the Makefile commands for common tasks
7. ✅ Update documentation for any architectural changes

> 📖 For detailed development workflow and guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md#-contributing).

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the Python backend community**

⭐ Star this repo if you find it useful!

</div>

