# 👨‍💻 Development Guide

This guide covers everything you need to know about developing with this project, including workspace container setup, Makefile commands, and development workflows.

> 📖 For project overview, architecture, and examples, see [README.md](README.md).

## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (required for workspace container)
- **AWS CLI** (for infrastructure deployment, optional for local development)

> 💡 **Note**: This project uses a **workspace container** that includes all development tools (Python 3.12, Poetry, AWS CLI). You don't need to install Python or Poetry locally!

### Workspace Container Setup

This project uses a Docker workspace container to ensure consistent development environments across all developers. The container includes:

- Python 3.12
- Poetry 2.2.1 (with export plugin)
- golang-migrate (for database migrations)
- AWS CLI v2
- All development dependencies

**Initial Setup:**

1. Clone the repository:
```bash
git clone <repository-url>
cd fastapi-postgres-template
```

2. Build and start the workspace container:
```bash
make workspace-build
make workspace-up

# You can always stop the workspace container with
make workspace-down
```

3. Install dependencies in the workspace container:
```bash
make poetry-install
```

4. (Optional) Create local `.venv.local` for IDE support:
```bash
make local-venv
```

This creates a local virtual environment with all dependencies for IDE autocomplete and type checking.

### Installation

1. Set up LocalStack (for local development):
```bash
make localstack-up
make localstack-setup

# Copy the output values to your .env.local file
```

2. Set up the database:
```bash
# Start PostgreSQL (if not already running)
docker compose up -d postgres

# Run migrations
make migrate
```

## 🛠️ Makefile Commands Reference

### Workspace Container Management

| Command | Description |
|---------|-------------|
| `make workspace-build` | Build the workspace container image |
| `make workspace-up` | Start the workspace container |
| `make workspace-down` | Stop and remove the workspace container |
| `make workspace-shell` | Open an interactive shell in the workspace container |

### Poetry Commands

| Command | Description |
|---------|-------------|
| `make poetry-install` | Install all dependencies |
| `make poetry-lock` | Update `poetry.lock` file |
| `make poetry-add PKG=package-name` | Add a production dependency |
| `make poetry-dev-add PKG=package-name` | Add a development dependency |

### Development Commands

| Command | Description |
|---------|-------------|
| `make lint` | Run linters (ruff + mypy) |
| `make fix` | Format code and fix linting issues |
| `make test` | Run tests |
| `make clean` | Clean build artifacts |

### Running Services

| Command | Description |
|---------|-------------|
| `make run-api` | Run API server |
| `make run-worker` | Run worker |

### Database Migrations

| Command | Description |
|---------|-------------|
| `make migrate` | Run database migrations (up) |
| `make migrate-down` | Rollback last migration |
| `make migrate-version` | Show current migration version |
| `make migrate-force VERSION=1` | Force set migration version |
| `make migrate-create NAME=my_migration` | Create a new migration |

### LocalStack Commands

| Command | Description |
|---------|-------------|
| `make localstack-up` | Start LocalStack services |
| `make localstack-setup` | Setup LocalStack resources (SNS/SQS) |
| `make localstack-down` | Stop LocalStack services |
| `make localstack-logs` | View LocalStack logs |

### IDE Support

| Command | Description |
|---------|-------------|
| `make local-venv` | Export requirements and create local `.venv.local` for IDE support |

### Production Builds

| Command | Description |
|---------|-------------|
| `make build` | Build shared Docker image for API and worker |
| `make build-migrations` | Build migrations Docker image |

## 🔄 Development Workflow

### Daily Development

1. **Start the workspace container:**
   ```bash
   make workspace-up
   ```

2. **Make your changes** to the codebase

3. **Run linting** to check code quality:
   ```bash
   make lint
   ```

4. **Format and fix code:**
   ```bash
   make fix
   ```

5. **Run tests:**
   ```bash
   make test
   ```

6. **Test your changes locally:**
   ```bash
   # Start API server
   make run-api
   
   # Or start worker
   make run-worker
   ```

### Adding Dependencies

**Add a production dependency:**
```bash
make poetry-add PKG=package-name
```

**Add a development dependency:**
```bash
make poetry-dev-add PKG=package-name
```

After adding dependencies, update your local IDE venv:
```bash
make local-venv
```

### Database Migrations

**Create a new migration:**
```bash
make migrate-create NAME=my_migration
```

**Run migrations:**
```bash
make migrate
```

**Rollback last migration:**
```bash
make migrate-down
```

**Check current migration version:**
```bash
make migrate-version
```

### Testing

The test suite uses mocked dependencies for fast, isolated unit tests. All service tests mock repositories and transaction managers, ensuring tests run quickly without requiring a database connection.

```bash
# Run all tests
make test

# Run tests in workspace container
docker compose exec workspace poetry run pytest

# Run specific test file
docker compose exec workspace poetry run pytest tests/domain/user/test_service.py
```

## 🔧 SQLModel ORM Pattern

Repositories use **SQLModel ORM** for type-safe database operations. ORM models are defined in `repo/sql.py` files alongside repository implementations. This provides:

- **Type Safety**: ORM models with full type hints and IDE support
- **Domain Separation**: Pure Pydantic domain models separate from ORM concerns
- **Simplicity**: Minimal boilerplate with automatic mapping
- **Query Building**: Use SQLModel's query API for type-safe queries

**Example ORM model and repository:**
```python
# In app/domain/user/repo/sql.py
class UserORM(SQLModel, table=True):
    """User ORM model for database persistence."""
    __tablename__ = "users"
    id: UUID = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    age: int | None = None
    created_at: datetime
    updated_at: datetime

class UserRepository(BaseUserRepository[SQLContext]):
    @staticmethod
    def _orm_to_domain(orm_user: UserORM) -> User:
        """Convert ORM model to domain model."""
        return User(
            id=orm_user.id,
            email=orm_user.email,
            name=orm_user.name,
            age=orm_user.age,
            created_at=orm_user.created_at,
            updated_at=orm_user.updated_at,
        )
    
    async def get_by_id(self, context: SQLContext, user_id: UUID) -> User | None:
        orm_user = await context.session.get(UserORM, user_id)
        return self._orm_to_domain(orm_user) if orm_user else None
```

## 🗄️ Database Migrations

Database migrations are managed using [golang-migrate](https://github.com/golang-migrate/migrate) and located in `resources/db/migrations/`.

Migrations run in a dedicated Docker container:

```bash
# Run migrations
make migrate

# Rollback last migration
make migrate-down

# Create a new migration
make migrate-create NAME=my_migration

# Check migration version
make migrate-version
```

The schema includes:

- **Users table**: Stores user information with email uniqueness
- **Invoices table**: Stores invoices linked to users with status tracking

## 🐳 Docker

### Workspace Container

The workspace container provides a consistent development environment with all tools pre-installed. All development commands run inside this container to ensure consistency across all developers.

### Production Images

The API and worker **share the same Docker image**, with different entrypoints:

```bash
# Build the shared image
make build

# Build migrations image
make build-migrations
```

The production images are optimized for deployment and don't include development dependencies.

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. ✅ Follow the existing code structure and patterns
2. ✅ Maintain type hints throughout (mypy must pass)
3. ✅ Write tests for new features with mocked dependencies
4. ✅ Run linting and type checking before committing (`make lint`)
5. ✅ Use the workspace container for all development tasks
6. ✅ Follow the Makefile commands for common tasks
7. ✅ Update documentation for any architectural changes

**Development Workflow:**

1. Ensure workspace container is running: `make workspace-up`
2. Make your changes
3. Run linting: `make lint`
4. Run tests: `make test`
5. Format code: `make fix`
6. Commit your changes

## 📚 Additional Resources

- [README.md](README.md) - Project overview and architecture
- [Project Structure](README.md#-project-structure) - Code organization
- [Example Business Case](README.md#-example-business-case) - Real-world usage examples
- [Event System](README.md#-event-system) - Event-driven architecture details
